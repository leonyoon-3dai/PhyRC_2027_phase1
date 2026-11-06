"""B1c offline A/B/C comparison, preserving the immutable B1/B1b baselines.

A: original largest component. B: union of eligible color components with a
wide image-space pair. C: explicit abstention on component/depth ambiguity.
None of these methods establishes cloth semantics or a valid robot grasp.
"""
import argparse
import base64
from dataclasses import asdict
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import shutil
import time

import numpy as np
from PIL import Image

from participant.research.color_depth_roi import (ColorRules, analyze_rgbd,
                                                  _components, _window_sum, _json, _sha)
from participant.research.depth_backprojection import analyze_pixel, intrinsics, CAMERAS


def require(condition, message):
    if not condition:
        raise ValueError(message)


def component_context(rgb, rules=ColorRules()):
    """Same B1b color and eligibility thresholds; retain ALL eligible regions."""
    rgb=np.asarray(rgb)
    require(rgb.ndim==3 and rgb.shape[2]==3 and rgb.dtype==np.uint8,'Expected uint8 RGB')
    r,g,b=(rgb[...,i].astype(np.int16) for i in range(3))
    blue=((b>=rules.blue_min_b)&(b-r>=rules.blue_min_b_minus_r)&(b-g>=rules.blue_min_b_minus_g))
    yellow=((r>=rules.yellow_min_r)&(g>=rules.yellow_min_g)&(b<=rules.yellow_max_b)
            &(r-b>=rules.yellow_min_r_minus_b)&(g-b>=rules.yellow_min_g_minus_b))
    original=blue|yellow
    labels=np.full(blue.shape,-1,np.int32)
    components=[]
    for points in _components(_window_sum(original,rules.component_link_radius_px)>0):
        yy,xx=points.T;inside=original[yy,xx];yy,xx=yy[inside],xx[inside]
        blue_count=int(blue[yy,xx].sum())
        if len(xx)<rules.minimum_component_pixels or blue_count<rules.minimum_blue_pixels:
            continue
        component_id=len(components);labels[yy,xx]=component_id
        components.append({'component_id_local':component_id,'original_color_pixels':len(xx),
            'blue_pixels':blue_count,'yellow_pixels':int(yellow[yy,xx].sum()),
            'bbox_xyxy_exclusive':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]})
    ys,xs=np.nonzero(labels>=0)
    bbox=None if not len(xs) else [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    return {'components':components,'union_bbox_xyxy_exclusive':bbox,
            'component_ids_are_frame_local':True},labels,yellow&(labels>=0)


def union_candidates(yellow, rules=ColorRules()):
    """Preserve B1b's 10/90% and 3x3 support selector, applied to the union."""
    ys,xs=np.nonzero(yellow)
    if len(xs)<rules.minimum_yellow_pixels:
        return []
    if xs.max()-xs.min()<rules.minimum_yellow_horizontal_span_px:
        return []
    support=_window_sum(yellow,1);candidates=[]
    for label,q in [('image_left',.1),('image_right',.9)]:
        target=float(np.quantile(xs,q));near=np.abs(xs-target)<=2
        py,px=ys[near],xs[near]
        if not len(px):
            distances=np.abs(xs-target);near=distances==distances.min();py,px=ys[near],xs[near]
        median_y=float(np.median(py))
        chosen=min(range(len(px)),key=lambda i:(-int(support[py[i],px[i]]),abs(float(px[i])-target),
                                               abs(float(py[i])-median_y),int(py[i]),int(px[i])))
        u,v=int(px[chosen]),int(py[chosen])
        candidates.append({'candidate_id':label,'pixel_uv':[u,v],
            'yellow_3x3_support_pixels':int(support[v,u]),'target_u_quantile':q,
            'semantic_label':'colored_band_edge_candidate_unverified','grasp_point_validated':False})
    if candidates[0]['pixel_uv']==candidates[1]['pixel_uv']:
        return candidates[:1]
    return candidates


def pair_diagnostics(candidates, labels, context):
    ids=[int(labels[c['pixel_uv'][1],c['pixel_uv'][0]]) for c in candidates]
    span=(abs(candidates[1]['pixel_uv'][0]-candidates[0]['pixel_uv'][0]) if len(candidates)==2 else None)
    bbox=context['union_bbox_xyxy_exclusive']
    width=None if bbox is None else bbox[2]-bbox[0]
    return {'candidate_component_ids_local':ids,'horizontal_separation_px':span,
            'eligible_union_bbox_width_px':width,
            'horizontal_separation_fraction_of_union_width':None if span is None or not width else span/width,
            'both_on_one_fragment_while_other_components_exist':
                len(ids)==2 and ids[0]==ids[1] and len(context['components'])>1}


def compare_methods(rgb, depth, valid, matrix, *, minimum_pair_span_fraction=.55):
    require(np.isfinite(minimum_pair_span_fraction) and 0<minimum_pair_span_fraction<=1,
            'Minimum pair span fraction must be in (0,1]')
    rules=ColorRules();context,labels,yellow=component_context(rgb,rules)
    baseline=analyze_rgbd(rgb,depth,valid,matrix,rules)
    a=baseline['candidates'];a_diagnostics=pair_diagnostics(a,labels,context)
    b=union_candidates(yellow,rules)
    for candidate in b:
        candidate['depth_probe']=analyze_pixel(depth,valid,matrix,candidate['pixel_uv'],rgb=rgb)
    b_diagnostics=pair_diagnostics(b,labels,context)
    b_reasons=[]
    if len(b)!=2:b_reasons.append('two_distinct_color_candidates_unavailable')
    elif b_diagnostics['horizontal_separation_fraction_of_union_width']<minimum_pair_span_fraction:
        b_reasons.append('insufficient_image_horizontal_separation')
    c_reasons=list(b_reasons)
    if len(context['components'])>1:c_reasons.append('multiple_color_components_semantically_ambiguous')
    if b_diagnostics['both_on_one_fragment_while_other_components_exist']:
        c_reasons.append('both_candidates_on_same_fragment_with_other_components_present')
    for candidate in b:
        probe=candidate['depth_probe']
        if not probe['center_valid']:c_reasons.append(candidate['candidate_id']+'_depth_invalid')
        elif probe['status']!='valid_depth_sample':c_reasons.append(candidate['candidate_id']+'_depth_patch_requires_review')
    def method(name,proposed,reasons,diagnostics):
        return {'method':name,'proposed_candidates':proposed,
                'emitted_candidates':proposed if len(proposed)==2 and not reasons else [],
                'emits_pair':len(proposed)==2 and not reasons,'abstention_reasons':reasons,
                'diagnostics':diagnostics,'cloth_edge_or_grasp_approved':False}
    return {'color_rules_unchanged_from_B1b':asdict(rules),'context':context,
        'new_pair_rule':{'minimum_horizontal_span_fraction_of_eligible_union_bbox':minimum_pair_span_fraction,
                        'basis':'unvalidated development heuristic requiring separation over half the image ROI'},
        'methods':{
            'A':method('original_largest_component',a,[] if len(a)==2 else [baseline['status']],a_diagnostics),
            'B':method('eligible_color_component_union_wide_pair',b,b_reasons,b_diagnostics),
            'C':method('union_pair_with_component_and_depth_abstention',b,c_reasons,b_diagnostics)},
        'semantic_segmentation_validated':False,'physical_edges_validated':False,
        'cross_frame_correspondence_established':False,'two_gripper_grasp_success_evaluated':False}


def comparison_svg(original_bytes,width,height,result,title):
    encoded=base64.b64encode(original_bytes).decode('ascii')
    footer=67;total_width=width*3
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width*1.5:g}" height="{(height+footer)*1.5:g}" viewBox="0 0 {total_width} {height+footer}">',
           f'<defs><image id="original" width="{width}" height="{height}" href="data:image/png;base64,{encoded}"/></defs>']
    for col,key in enumerate(('A','B','C')):
        method=result['methods'][key];offset=col*width
        lines.append(f'<g transform="translate({offset},0)"><use href="#original"/>')
        for component in result['context']['components']:
            x0,y0,x1,y1=component['bbox_xyxy_exclusive']
            lines.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="#ff55cc" stroke-width=".7"/>')
        color='#00ff88' if method['emits_pair'] else '#ff5555'
        for candidate in method['proposed_candidates']:
            u,v=candidate['pixel_uv'];label='L' if candidate['candidate_id']=='image_left' else 'R'
            dash='' if method['emits_pair'] else ' stroke-dasharray="2 1"'
            lines.append(f'<circle cx="{u}" cy="{v}" r="4" fill="none" stroke="{color}" stroke-width="1.5"{dash}/>')
            lines.append(f'<text x="{u+5}" y="{v-5}" font-size="10" font-family="sans-serif" fill="{color}" stroke="#000" stroke-width=".25">{label}</text>')
        status='PAIR CANDIDATE' if method['emits_pair'] else 'ABSTAIN (proposals only)'
        fraction=method['diagnostics']['horizontal_separation_fraction_of_union_width']
        separation='N/A' if fraction is None else f'{fraction:.3f}'
        lines += [f'<rect y="{height}" width="{width}" height="{footer}" fill="#15202b"/>',
            f'<text x="5" y="{height+12}" fill="white" font-size="9" font-family="sans-serif">{key}: {status}</text>',
            f'<text x="5" y="{height+25}" fill="white" font-size="8" font-family="sans-serif">span fraction: {separation}; color components: {len(result["context"]["components"])}</text>',
            f'<text x="5" y="{height+38}" fill="white" font-size="8" font-family="sans-serif">{html.escape(title)}</text>',
            f'<text x="5" y="{height+51}" fill="white" font-size="8" font-family="sans-serif">Not verified cloth sides or valid grasps</text>',
            '</g>']
    return '\n'.join(lines+['</svg>'])+'\n'


def export_comparison(root,run_id,frames,output):
    started=time.perf_counter();root=Path(root).resolve();output=Path(output)
    require(isinstance(run_id,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}',run_id),'Invalid run ID')
    require(not output.exists(),'Output already exists; never overwrite prior comparisons')
    require(1<=len(frames)<=5 and len(set(frames))==len(frames),'Select 1..5 distinct fixed development frames')
    require(all(type(i)is int and 0<=i<=99999 and c in CAMERAS for i,c in frames),'Invalid frame selection')
    capture=root/'output/collections'/run_id;observations=root/'output/actors'/run_id/'observations'
    require(capture.resolve().is_relative_to(root) and observations.resolve().is_relative_to(root),'Source escapes root')
    require(_json(capture/'capture.json').get('complete')is True,'Only closed saved captures may be used')
    metadata_path=capture/'run_metadata.json';public=_json(metadata_path)['public_interface']
    specs={c['id']:c for c in public['camera_calibration']};prepared=[]
    sources={'run_metadata.json':{'sha256':_sha(metadata_path),'fields_used':['public_interface.camera_intrinsics',
        'public_interface.camera_calibration.id','public_interface.camera_calibration.intrinsics',
        'public_interface.camera_calibration.resolution_wh']}}
    for index,camera in frames:
        directory=observations/f'{index:05d}';require(not directory.is_symlink(),'Linked observation rejected')
        observation=_json(directory/'observation.json');require(tuple(observation['rgb_image_order'])==CAMERAS,'Unexpected camera order')
        clock=observation['public_robot_observation']['simulation_time_s']
        require(type(clock)in(int,float)and np.isfinite(clock),'Invalid public observation clock')
        rgb_path=directory/(camera+'.png');depth_path=directory/'public_depth.npz'
        require(not rgb_path.is_symlink() and not depth_path.is_symlink(),'Linked sensor input rejected')
        with Image.open(rgb_path)as image:rgb=np.asarray(image)
        with np.load(depth_path,allow_pickle=False)as data:
            require(set(data.files)=={'depth','depth_valid'},'Unexpected depth fields')
            depth,valid=data['depth'],data['depth_valid']
        height,width=rgb.shape[:2];ci=CAMERAS.index(camera)
        require(depth.shape==(5,height,width,1)and valid.shape==depth.shape
                and depth.dtype==np.float32 and valid.dtype==bool,'RGB-D shape/dtype mismatch')
        matrix=intrinsics(public['camera_intrinsics'][camera])
        require(specs[camera]['resolution_wh']==[width,height]and np.array_equal(matrix,intrinsics(specs[camera]['intrinsics'])),
                'Public calibration sources disagree')
        result=compare_methods(rgb,depth[ci,...,0],valid[ci,...,0],matrix)
        result.update(observation_index=index,camera=camera,
            public_simulation_time_s=clock,
            intrinsics=matrix.tolist(),intrinsics_source='saved run_metadata.json public_interface.camera_intrinsics.'+camera)
        prepared.append((rgb_path,width,height,result))
        for path in(rgb_path,depth_path,directory/'observation.json'):
            sources[f'observations/{index:05d}/{path.name}']={'sha256':_sha(path)}
    output.mkdir(parents=True,exist_ok=False);results=[];artifacts={}
    for original,width,height,result in prepared:
        name=f"obs{result['observation_index']:05d}-{result['camera']}";image=output/(name+'.png');svg=output/(name+'-ABC.svg')
        shutil.copyfile(original,image);svg.write_text(comparison_svg(image.read_bytes(),width,height,result,name))
        result['artifacts']={'original_rgb':image.name,'comparison_svg':svg.name};results.append(result)
        for path in(image,svg):artifacts[path.name]={'sha256':_sha(path),'bytes':path.stat().st_size}
    report={'schema':'phyrc-offline-color-pair-comparison-v1','baseline':'B1c','run_id':run_id,
        'created_at_utc':datetime.now(timezone.utc).isoformat(),'frames':results,'source_files':sources,'artifacts':artifacts,
        'dependency_sha256':{name:_sha(Path(__file__).with_name(name))for name in
                             ('color_pair_comparison.py','color_depth_roi.py','depth_backprojection.py')},
        'cpu_wall_s':time.perf_counter()-started,'model_calls':0,'split':'fixed_development_cases_not_held_out',
        'known_failure_used_to_design_method':True,'semantic_or_grasp_accuracy_evaluated':False,
        'official_demo_frames_used':False,'simulation_ground_truth_used':False,'hdf5_read':False,
        'live_runtime_modified':False,'sent_to_actor':False}
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--run-id',required=True);parser.add_argument('--frames',nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:frames=[(int(s.split(':')[0]),s.split(':')[1])for s in args.frames]
    except(ValueError,IndexError):parser.error('frames must be index:camera')
    report=export_comparison(args.root,args.run_id,frames,args.output)
    print(json.dumps({'baseline':'B1c','frames':len(report['frames']),
        'emitted_candidate_pairs':{k:sum(f['methods'][k]['emits_pair']for f in report['frames'])for k in 'ABC'},
        'cpu_wall_s':report['cpu_wall_s'],'model_calls':0,'grasp_accuracy_evaluated':False}))


if __name__=='__main__':main()
