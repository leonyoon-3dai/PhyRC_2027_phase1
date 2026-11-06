"""Deterministic offline visualization of CLOSED public RGB-D observations only."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[4])
parser.add_argument('--output',type=Path,required=True,help='New output directory; existing paths are rejected')
args=parser.parse_args()
ROOT=args.root.resolve()
OUT=args.output.resolve()
OUT.mkdir(parents=True,exist_ok=False)
FRAMES=[('E10','20261106-astra-sleeve-branch700-003','00008'),
        ('E11','20261106-astra-sleeve-history-001','00000'),
        ('E11','20261106-astra-sleeve-history-001','00008')]
WRISTS=['robot_0_wrist','robot_1_wrist']
LOW,HIGH=.03,1.20
INVALID=(255,0,255);BELOW=(0,255,255);ABOVE=(255,128,0)
FONT='DejaVuSans.ttf'
font=ImageFont.truetype(FONT,12);titlefont=ImageFont.truetype(FONT,15)
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def render_depth(z,valid):
 effective=valid & np.isfinite(z) & (z>0)
 q=np.zeros(z.shape,dtype=np.uint8)
 q[effective]=np.rint(np.clip((z[effective]-LOW)/(HIGH-LOW),0,1)*255).astype(np.uint8)
 gray=255-q;rgb=np.repeat(gray[...,None],3,axis=-1)
 rgb[~effective]=INVALID;rgb[effective&(z<LOW)]=BELOW;rgb[effective&(z>HIGH)]=ABOVE
 return Image.fromarray(rgb)
report={'schema':'phyrc-offline-wrist-depth-review-v1','scope':'closed public RGB/depth/mask only; no actor input change; no HDF5/audit/evaluation/hidden geometry or model calls',
 'selected_frames':[], 'selection_basis':'E10 late orientation; E11 initial transport boundary and later wrist/lift orientation, chosen from closed public RGB',
 'transform':{'depth_semantics':'optical_axis_Z_metres_not_ray_range','range_m':[LOW,HIGH],
   'inside_range':'q=rint(255*(Z-0.03)/(1.20-0.03)); gray=255-q; same range for every frame/camera',
   'invalid_rgb':list(INVALID),'below_range_rgb':list(BELOW),'above_range_rgb':list(ABOVE),
   'quantization_step_m':(HIGH-LOW)/255,'maximum_rounding_error_m':(HIGH-LOW)/510,
   'invalid_rule':'not depth_valid OR nonfinite OR Z<=0; no interpolation or inpainting',
   'coarse_display':'saved actor16x16 medians (rounded0.001m), expanded16x16 by exact nearest replication',
   'range_selection_basis':'Public wrist depth distributions inspected first; upper bound1.20m includes the RGB-selected boundary surface sample up to0.934m while retaining a fixed near-field display. No frame-specific range.',
   'spatial_interpolation':'none','auto_contrast':False,'below_above_distinct_from_invalid':True},
 'interpretation':'Depth discontinuity/within-tile spread can reflect occlusion, multiple surfaces or slope. It is not a semantic label, contact test, hole center or object pose.',
 'cameras':[]}
for label,run,index in FRAMES:
 source=ROOT/'output/actors'/run/'observations'/index
 capture=ROOT/'output/collections'/run/'capture.json'
 assert json.loads(capture.read_text())['complete'] is True
 observation=json.loads((source/'observation.json').read_text())
 order=observation['rgb_image_order'];clock=observation['public_robot_observation']['simulation_time_s']
 frame={'label':label,'run_id':run,'observation_index':index,'public_simulation_time_s':clock,
        'camera_order':order,'sources':{str((source/f).relative_to(ROOT)):sha(source/f) for f in ['observation.json','public_depth.npz']}}
 report['selected_frames'].append(frame)
 with np.load(source/'public_depth.npz',allow_pickle=False) as archive:
  assert set(archive.files)=={'depth','depth_valid'}
  depths=archive['depth'];masks=archive['depth_valid']
 assert depths.shape==masks.shape==(5,256,256,1) and masks.dtype==bool and depths.dtype==np.float32
 canvas=Image.new('RGB',(870,708),'#17202a');draw=ImageDraw.Draw(canvas)
 draw.text((15,10),f'{label} observation {index} | t={clock:.6f}s | CURRENT saved wrist views',font=titlefont,fill='white')
 draw.text((15,34),'Optical Z: 0.03m white -> 1.20m black | fixed mapping | no interpolation',font=font,fill='white')
 for x,color,text in [(15,INVALID,'invalid/missing'),(235,BELOW,'valid below0.03m'),(490,ABOVE,'valid above1.20m')]:
  draw.rectangle((x,57,x+14,71),fill=color);draw.text((x+20,55),text,font=font,fill='white')
 for row,camera in enumerate(WRISTS):
  k=order.index(camera);z=depths[k,:,:,0];valid=masks[k,:,:,0]&np.isfinite(z)&(z>0)
  rgb_path=source/(camera+'.png');frame['sources'][str(rgb_path.relative_to(ROOT))]=sha(rgb_path)
  rgb=Image.open(rgb_path).convert('RGB');assert rgb.size==(256,256)
  coarse=np.zeros((16,16),np.float32);coarsevalid=np.zeros((16,16),bool);tiles=[]
  for ty in range(16):
   for tx in range(16):
    a=z[ty*16:(ty+1)*16,tx*16:(tx+1)*16];m=valid[ty*16:(ty+1)*16,tx*16:(tx+1)*16];vals=a[m]
    median=round(float(np.median(vals)),3) if len(vals) else None
    assert median==observation['depth_16x16_grid_m'][camera][ty][tx]
    coarsevalid[ty,tx]=len(vals)>0
    if len(vals):coarse[ty,tx]=median
    tiles.append({'tile_xy':[tx,ty],'bounds_uv_exclusive':[tx*16,ty*16,(tx+1)*16,(ty+1)*16],
        'valid_pixels':int(m.sum()),'valid_fraction':float(m.mean()),'actor_median_m':median,
        'minimum_m':float(vals.min()) if len(vals) else None,'maximum_m':float(vals.max()) if len(vals) else None,
        'p10_p90_m':np.quantile(vals,[.1,.9]).tolist() if len(vals) else None,
        'p90_minus_p10_m':float(np.quantile(vals,.9)-np.quantile(vals,.1)) if len(vals) else None})
  vals=z[valid];mixed=[t for t in tiles if 0<t['valid_pixels']<256];wide=[t for t in tiles if t['valid_pixels']>=16 and t['p90_minus_p10_m']>.05]
  datum={'label':label,'run_id':run,'observation_index':index,'camera':camera,'public_simulation_time_s':clock,
    'valid_pixels':int(valid.sum()),'invalid_pixels':int((~valid).sum()),
    'valid_below_range':int((valid&(z<LOW)).sum()),'valid_above_range':int((valid&(z>HIGH)).sum()),
    'above_range_fraction_of_valid':float((valid&(z>HIGH)).sum()/valid.sum()),
    'valid_quantiles_m':{str(p):float(np.quantile(vals,p)) for p in (0,.01,.05,.25,.5,.75,.95,.99,1)},
    'partly_invalid_tiles':len(mixed),'valid_tiles':int(coarsevalid.sum()),
    'tiles_with_at_least16valid_and_p90_minus_p10_above0_05m':len(wide),'tile_statistics':tiles}
  report['cameras'].append(datum)
  y=108+row*288
  for x,heading,img in [(15,'RGB (unchanged pixels)',rgb),(302,'256x256 original depth',render_depth(z,valid)),
                         (589,'16x16 actor median depth',render_depth(coarse,coarsevalid).resize((256,256),resample=Image.Resampling.NEAREST))]:
   draw.text((x,y-24),camera+' | '+heading,font=font,fill='white');canvas.paste(img,(x,y))
 draw.text((15,682),'Colors encode depth validity/range only; no cloth/hand labels, contact inference or actor use.',font=font,fill='white')
 name=f'{label.lower()}-{index}-wrists.png';canvas.save(OUT/name)
 frame['panel']=name;frame['panel_sha256']=sha(OUT/name)
anchors=[('E11','00000','robot_1_wrist',5,9,'Pale robot structure beside striped visible surface; mixed boundary, contact unconfirmed.'),
         ('E11','00008','robot_0_wrist',3,8,'Sloped blue/yellow textile silhouette against pale background; partly crosses tile.'),
         ('E10','00008','robot_1_wrist',10,8,'Yellow textile upper silhouette against pale background; mixed validity expected.')]
anchor_panel=Image.new('RGB',(1030,630),'#17202a');adraw=ImageDraw.Draw(anchor_panel)
adraw.text((15,10),'RGB-selected boundary tiles | each16x16 tile enlarged8x by exact pixel replication',font=titlefont,fill='white')
adraw.text((15,34),'Same fixed0.03..1.20m depth mapping; magenta=invalid, cyan=below, orange=above',font=font,fill='white')
report['rgb_selected_boundary_tiles']=[]
for row,(label,index,camera,tx,ty,description) in enumerate(anchors):
 datum=next(c for c in report['cameras'] if (c['label'],c['observation_index'],c['camera'])==(label,index,camera))
 tile=next(t for t in datum['tile_statistics'] if t['tile_xy']==[tx,ty])
 selection=dict(tile,label=label,observation_index=index,camera=camera,public_simulation_time_s=datum['public_simulation_time_s'],
                selection_basis='Independent RGB-only visible-boundary selection before depth query',visual_description_uncertain=description)
 report['rgb_selected_boundary_tiles'].append(selection)
 source=ROOT/'output/actors'/datum['run_id']/'observations'/index
 obs=json.loads((source/'observation.json').read_text());k=obs['rgb_image_order'].index(camera)
 with np.load(source/'public_depth.npz',allow_pickle=False) as archive:
  z=archive['depth'][k,:,:,0];valid=archive['depth_valid'][k,:,:,0]
 bounds=tuple(tile['bounds_uv_exclusive']);x0,y0,x1,y1=bounds
 rgb=Image.open(source/(camera+'.png')).convert('RGB').crop(bounds)
 fine=render_depth(z[y0:y1,x0:x1],valid[y0:y1,x0:x1])
 coarse=render_depth(np.full((16,16),tile['actor_median_m'],np.float32),np.ones((16,16),bool))
 y=96+row*175
 for x,name,img in [(15,'RGB tile',rgb),(165,'Original depth',fine),(315,'Actor median tile',coarse)]:
  adraw.text((x,y-20),name,font=font,fill='white');anchor_panel.paste(img.resize((128,128),resample=Image.Resampling.NEAREST),(x,y))
 lines=[f'{label} {index} {camera} | x[{x0},{x1}) y[{y0},{y1})',
        f'Valid {tile["valid_pixels"]}/256; actor median {tile["actor_median_m"]:.3f}m',
        f'Valid range {tile["minimum_m"]:.3f}..{tile["maximum_m"]:.3f}m',
        f'Valid p10..p90 {tile["p10_p90_m"][0]:.3f}..{tile["p10_p90_m"][1]:.3f}m',
        'No semantic ground truth, contact or aperture-center inference.']
 for line,text in enumerate(lines):adraw.text((465,y+line*22),text,font=font,fill='white')
anchor_panel.save(OUT/'boundary-tiles.png')
report['boundary_panel_sha256']=sha(OUT/'boundary-tiles.png')
report['findings']={
 'observed_information_loss':'The16x16 median hides sub-tile surface mixtures and partial invalidity. RGB-selected E11 initial wrist1 tile spans0.132..0.934m while its actor median is0.161m.',
 'visible_silhouette_example':'E11obs8 wrist0 tile has95/256valid pixels but is represented by a full cell at0.232m. Original depth retains the invalid boundary shape.',
 'interpretation_limit':'Depth shows first visible surfaces; visible gap depth may be background, not an opening center. Large within-cell range alone does not establish different objects or contact.',
 'next_trial_assessment':'Worth one bounded future actor-input-only comparison with a paired current wrist-depth panel; evidence is representation preservation, not measured policy or task accuracy improvement.',
 'unchanged':'E12 input and source, active capture data, existing B1/B1b/B1c baselines.'}
report['script_sha256']=sha(__file__)
(OUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'panels':len(FRAMES),'camera_samples':len(report['cameras']),
 'mapping_range_m':[LOW,HIGH],'quantization_step_mm':1000*(HIGH-LOW)/255,
 'output_directory_name':OUT.name}))
for c in report['cameras']:
 print(json.dumps({k:c[k] for k in ('label','observation_index','camera','valid_pixels','invalid_pixels','valid_below_range','valid_above_range','above_range_fraction_of_valid','partly_invalid_tiles','valid_tiles','tiles_with_at_least16valid_and_p90_minus_p10_above0_05m')}))
