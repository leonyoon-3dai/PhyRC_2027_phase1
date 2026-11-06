"""B1b offline scene-specific color components -> public RGB-D pixel probes.

Blue/yellow appearance heuristics are not semantic segmentation, geometry,
correspondence, graspability or grasp-success labels. No live runtime imports.
"""
import argparse
import base64
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import time

import numpy as np
from PIL import Image

from participant.research.depth_backprojection import analyze_pixel, intrinsics, CAMERAS


@dataclass(frozen=True)
class ColorRules:
    blue_min_b: int = 120
    blue_min_b_minus_r: int = 40
    blue_min_b_minus_g: int = 40
    yellow_min_r: int = 150
    yellow_min_g: int = 130
    yellow_max_b: int = 120
    yellow_min_r_minus_b: int = 70
    yellow_min_g_minus_b: int = 60
    minimum_blue_pixels: int = 64
    minimum_component_pixels: int = 128
    minimum_yellow_pixels: int = 8
    minimum_yellow_horizontal_span_px: int = 4
    component_link_radius_px: int = 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _window_sum(mask, radius):
    height, width = mask.shape
    padded = np.pad(mask.astype(np.int32), radius)
    return sum(padded[y:y+height, x:x+width]
               for y in range(2*radius+1) for x in range(2*radius+1))


def _components(mask):
    """Eight-connected components, deterministic row-major traversal."""
    height, width = mask.shape
    visited = np.zeros_like(mask)
    for y, x in zip(*np.nonzero(mask)):
        if visited[y, x]:
            continue
        visited[y, x] = True
        queue, points = deque([(int(y), int(x))]), []
        while queue:
            cy, cx = queue.popleft(); points.append((cy, cx))
            for dy, dx in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
                ny, nx = cy+dy, cx+dx
                if 0 <= ny < height and 0 <= nx < width and mask[ny,nx] and not visited[ny,nx]:
                    visited[ny,nx] = True; queue.append((ny,nx))
        yield np.asarray(points, np.int32)


def color_candidates(rgb, rules=ColorRules()):
    """Choose two image-left/right yellow probes using RGB only, never depth."""
    rgb = np.asarray(rgb)
    require(rgb.ndim == 3 and rgb.shape[2] == 3 and rgb.dtype == np.uint8, 'Expected HxWx3 uint8 RGB')
    require(0 <= rules.component_link_radius_px <= 2, 'Link radius must be 0..2')
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    blue = ((b >= rules.blue_min_b) & (b-r >= rules.blue_min_b_minus_r)
            & (b-g >= rules.blue_min_b_minus_g))
    yellow = ((r >= rules.yellow_min_r) & (g >= rules.yellow_min_g) & (b <= rules.yellow_max_b)
              & (r-b >= rules.yellow_min_r_minus_b) & (g-b >= rules.yellow_min_g_minus_b))
    union = blue | yellow
    linked = _window_sum(union, rules.component_link_radius_px) > 0
    choices, count = [], 0
    for points in _components(linked):
        count += 1
        yy, xx = points.T
        original = union[yy,xx]
        yy, xx = yy[original], xx[original]
        blue_count = int(blue[yy,xx].sum())
        if len(yy) >= rules.minimum_component_pixels and blue_count >= rules.minimum_blue_pixels:
            choices.append((len(yy), blue_count, yy, xx))
    result = {'rules': asdict(rules), 'selection_input': 'RGB_only_depth_not_used_for_selection',
              'connected_components': count, 'eligible_components': len(choices),
              'selected_component': None, 'candidates': [], 'status': 'no_supported_color_component',
              'semantic_segmentation_validated': False, 'physical_edge_validated': False,
              'two_gripper_grasp_success_evaluated': False}
    if not choices:
        return result
    # A large yellow-only distractor is not eligible. Ties retain row-major order.
    area, blue_count, yy, xx = max(choices, key=lambda value: (value[0], value[1]))
    yellow_roi = np.zeros_like(yellow)
    yellow_roi[yy,xx] = yellow[yy,xx]
    ys, xs = np.nonzero(yellow_roi)
    result['selected_component'] = {'original_color_pixels': area, 'blue_pixels': blue_count,
        'yellow_pixels': len(xs), 'bbox_xyxy_exclusive': [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],
        'linking': 'dilated union for connectivity; candidates remain ORIGINAL yellow pixels'}
    if len(xs) < rules.minimum_yellow_pixels:
        result['status'] = 'insufficient_yellow_pixels'; return result
    if int(xs.max()-xs.min()) < rules.minimum_yellow_horizontal_span_px:
        result['status'] = 'insufficient_horizontal_separation'; return result
    support = _window_sum(yellow_roi, 1)
    for label, quantile in [('image_left', .1), ('image_right', .9)]:
        target = float(np.quantile(xs, quantile))
        nearby = np.abs(xs-target) <= 2
        py, px = ys[nearby], xs[nearby]
        if not len(px):
            distance = np.abs(xs-target); nearby = distance == distance.min()
            py, px = ys[nearby], xs[nearby]
        median_y = float(np.median(py))
        # More original yellow neighbors, then quantile distance, then y median.
        ranking = sorted(range(len(px)), key=lambda i: (-int(support[py[i],px[i]]),
            abs(float(px[i])-target), abs(float(py[i])-median_y), int(py[i]), int(px[i])))
        chosen = ranking[0]; u, v = int(px[chosen]), int(py[chosen])
        result['candidates'].append({'candidate_id': label, 'pixel_uv': [u,v],
            'yellow_3x3_support_pixels': int(support[v,u]), 'target_u_quantile': quantile,
            'selection': 'yellow u quantile +/-2px; maximize 3x3 color support; deterministic ties',
            'semantic_label': 'colored_band_edge_candidate_unverified', 'grasp_point_validated': False})
    if result['candidates'][0]['pixel_uv'] == result['candidates'][1]['pixel_uv']:
        result['candidates'] = result['candidates'][:1]
        result['status'] = 'one_distinct_candidate'
    else:
        result['status'] = 'two_color_candidates'
    return result


def analyze_rgbd(rgb, depth, valid, matrix, rules=ColorRules()):
    result = color_candidates(rgb, rules)
    for candidate in result['candidates']:
        candidate['depth_probe'] = analyze_pixel(depth, valid, matrix, candidate['pixel_uv'], rgb=rgb)
    result['cross_frame_correspondence_established'] = False
    return result


def _sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def _json(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2*1024*1024,
            'Missing, linked or oversized saved metadata')
    return json.loads(path.read_text())


def annotation_svg(rgb_bytes, width, height, result, title):
    """Code-generated labels over an embedded original image, no synthesized pixels."""
    encoded = base64.b64encode(rgb_bytes).decode('ascii')
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width*2}" height="{height*2+92}" viewBox="0 0 {width} {height+46}">',
             f'<image width="{width}" height="{height}" href="data:image/png;base64,{encoded}"/>']
    component = result['selected_component']
    if component:
        x0,y0,x1,y1 = component['bbox_xyxy_exclusive']
        lines.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="#ff55cc" stroke-width="1"/>')
    for candidate in result['candidates']:
        u,v = candidate['pixel_uv']; label = 'L' if candidate['candidate_id']=='image_left' else 'R'
        lines += [f'<circle cx="{u}" cy="{v}" r="4" fill="none" stroke="#00ff88" stroke-width="1.5"/>',
                  f'<text x="{u+5}" y="{v-5}" fill="#00ff88" stroke="#000" stroke-width=".3" font-size="11" font-family="sans-serif">{label}</text>']
    lines += [f'<rect y="{height}" width="{width}" height="46" fill="#15202b"/>',
              f'<text x="5" y="{height+13}" fill="white" font-size="9" font-family="sans-serif">{html.escape(title)}</text>',
              f'<text x="5" y="{height+26}" fill="white" font-size="8" font-family="sans-serif">RGB color ROI / L,R: image-space candidates only</text>',
              f'<text x="5" y="{height+39}" fill="white" font-size="8" font-family="sans-serif">Not verified edges, grasps or tracked points</text>', '</svg>']
    return '\n'.join(lines)+'\n'


def export_saved_pilot(root, run_id, frames, output):
    started = time.perf_counter(); root = Path(root).resolve(); output = Path(output)
    require(isinstance(run_id,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}',run_id), 'Invalid run ID')
    require(not output.exists(), 'Output already exists; never overwrite a prior pilot')
    require(1 <= len(frames) <= 3 and len(set(frames)) == len(frames), 'Select 1..3 distinct fixed frames')
    require(all(type(i) is int and 0 <= i <= 99999 and c in CAMERAS for i,c in frames), 'Invalid frame selection')
    capture = root/'output/collections'/run_id; observations = root/'output/actors'/run_id/'observations'
    require(capture.resolve().is_relative_to(root) and observations.resolve().is_relative_to(root), 'Source escapes root')
    require(_json(capture/'capture.json').get('complete') is True, 'Only closed captures may be analyzed')
    metadata_path = capture/'run_metadata.json'; public = _json(metadata_path)['public_interface']
    calibration = {s['id']:s for s in public['camera_calibration']}
    sources = {'run_metadata.json':{'sha256':_sha(metadata_path),
        'fields_used':['public_interface.camera_intrinsics','public_interface.camera_calibration.id',
                       'public_interface.camera_calibration.intrinsics','public_interface.camera_calibration.resolution_wh']}}
    prepared = []
    for index,camera in frames:
        folder = observations/f'{index:05d}'; require(not folder.is_symlink(), 'Linked observation rejected')
        obs = _json(folder/'observation.json'); require(tuple(obs['rgb_image_order'])==CAMERAS,'Unexpected camera order')
        rgb_path, depth_path = folder/(camera+'.png'), folder/'public_depth.npz'
        require(not rgb_path.is_symlink() and not depth_path.is_symlink(), 'Linked sensor input rejected')
        with Image.open(rgb_path) as image: rgb = np.asarray(image)
        with np.load(depth_path,allow_pickle=False) as data:
            require(set(data.files)=={'depth','depth_valid'},'Unexpected saved depth fields')
            depth,valid = data['depth'],data['depth_valid']
        ci = CAMERAS.index(camera); height,width = rgb.shape[:2]
        require(depth.shape==(5,height,width,1) and valid.shape==depth.shape
                and depth.dtype==np.float32 and valid.dtype==bool,'Saved RGB-D shape/dtype mismatch')
        matrix = intrinsics(public['camera_intrinsics'][camera]); spec=calibration[camera]
        require(spec['resolution_wh']==[width,height] and np.array_equal(matrix,intrinsics(spec['intrinsics'])),
                'Public calibration sources disagree')
        result=analyze_rgbd(rgb,depth[ci,...,0],valid[ci,...,0],matrix)
        result.update(observation_index=index,camera=camera,public_simulation_time_s=obs['public_robot_observation']['simulation_time_s'],
                      intrinsics=matrix.tolist(),intrinsics_source='saved run_metadata.json public_interface.camera_intrinsics.'+camera)
        prepared.append((rgb_path,width,height,result))
        for file in (rgb_path,depth_path,folder/'observation.json'):
            sources[f'observations/{index:05d}/{file.name}']={'sha256':_sha(file)}
    output.mkdir(parents=True,exist_ok=False)
    results,artifacts=[],{}
    for rgb_path,width,height,result in prepared:
        name=f"obs{result['observation_index']:05d}-{result['camera']}"
        original=output/(name+'.png'); overlay=output/(name+'-annotation.svg')
        shutil.copyfile(rgb_path,original)
        overlay.write_text(annotation_svg(original.read_bytes(),width,height,result,name))
        result['artifacts']={'original_rgb':original.name,'annotation_svg':overlay.name}
        results.append(result)
        for file in (original,overlay):artifacts[file.name]={'sha256':_sha(file),'bytes':file.stat().st_size}
    report={'schema':'phyrc-offline-color-depth-roi-v1','baseline':'B1b','run_id':run_id,
        'created_at_utc':datetime.now(timezone.utc).isoformat(),'frames':results,'source_files':sources,
        'artifacts':artifacts,'module_sha256':_sha(Path(__file__)),
        'B1_dependency_sha256':_sha(Path(__file__).with_name('depth_backprojection.py')),
        'cpu_wall_s':time.perf_counter()-started,'scope':'scene-specific color-component and public RGB-D connection pilot',
        'official_demo_frames_used':False,'material_ground_truth_used':False,'simulation_geometry_used':False,
        'hdf5_read':False,'evaluation_used':False,'pose_accuracy_evaluated':False,'model_calls':0,
        'live_runtime_modified':False,'sent_to_actor':False}
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--frames',nargs='+',required=True,help='1..3 observation_index:camera selections')
    parser.add_argument('--output',type=Path,required=True,help='New directory only')
    args=parser.parse_args()
    try:
        frames=[(int(value.split(':')[0]),value.split(':')[1]) for value in args.frames]
    except (ValueError,IndexError):parser.error('frames must be index:camera')
    result=export_saved_pilot(args.root,args.run_id,frames,args.output)
    print(json.dumps({'baseline':'B1b','frames':len(result['frames']),
        'candidates':sum(len(f['candidates']) for f in result['frames']),
        'valid_candidate_depths':sum(c['depth_probe']['center_valid'] for f in result['frames'] for c in f['candidates']),
        'cpu_wall_s':result['cpu_wall_s'],'model_calls':0,'grasp_success_evaluated':False}))


if __name__=='__main__':main()
