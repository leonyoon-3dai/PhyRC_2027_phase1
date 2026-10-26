#!/usr/bin/env python3
"""Editorial human-demo video from sampled checksummed recorded states only.

No physics solve and no policy. Output is presentation evidence, not training RGBD.
"""
import argparse, hashlib, json, math, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--recording',type=Path,required=True)
p.add_argument('--states',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=Path('/project') if Path('/project/src').exists() else Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'src/PhyRC_Sim'))
metadata=json.loads((a.recording/'manifest.json').read_text())
assert metadata['complete']
assert hashlib.sha256((a.recording/'scene.usdc').read_bytes()).hexdigest()==metadata['scene_sha256']
a.output.mkdir(parents=True,exist_ok=False)
# The host encoder receives PNGs after the GPU process completes.
from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'width':960,'height':540})
try:
 import omni.usd,omni.timeline
 import omni.replicator.core as rep
 from pxr import Usd
 from PIL import Image
 from Policy.teleop_playback import ReplayScene,disable_physics
 source=Usd.Stage.Open(str(a.recording/'scene.usdc'));disable_physics(source)
 with tempfile.TemporaryDirectory(prefix='phyrc_editorial_') as temporary:
  scene=Path(temporary)/'scene.usdc';source.Flatten().Export(str(scene))
  assert omni.usd.get_context().open_stage(str(scene))
  for _ in range(12):app.update()
  stage=omni.usd.get_context().get_stage();replay=ReplayScene(stage,metadata['metadata'])
  product=rep.create.render_product('/World/FullReplayCamera',(960,540))
  rgb=rep.AnnotatorRegistry.get_annotator('rgb');rgb.attach([product])
  with np.load(a.states,allow_pickle=False) as states:
   prefixes=sorted(set(k.split('/')[0] for k in states.files),key=lambda x:int(x.split('_')[1]))
   records=[]
   for key in prefixes:
    t=float(states[key+'/simulation_time_s']);records.append((t,key))
   first=records[0][0];duration=records[-1][0]-first
   def presentation(t):
    return min(t,71.15)/12+max(0,min(t,94)-71.15)/2+max(0,t-94)/1.5
   # Render only recorded samples that are used; frame duplication happens in encoder.
   plan=[];seen=set()
   for index,(t,key) in enumerate(records):
    normalized=t-first
    slot=round(presentation(normalized)*25)
    if slot in seen:continue
    seen.add(slot);plan.append({'source_time_s':t,'time_s':normalized,'key':key,'video_frame':slot})
   for i,row in enumerate(plan):
    prefix=row['key']+'/'
    values={k[len(prefix):]:states[k] for k in states.files if k.startswith(prefix)}
    replay.apply(values)
    omni.timeline.get_timeline_interface().stop()
    rep.orchestrator.step(rt_subframes=3,delta_time=0.0,pause_timeline=True,wait_for_render=True)
    image=np.asarray(rgb.get_data())
    if image.shape!=(540,960,4):raise ValueError(f'Invalid camera frame {image.shape}')
    Image.fromarray(image[:,:,:3]).save(a.output/f'{i:05d}.png')
    if i%50==0:print('DEMO RENDER',i,'/',len(plan),row['time_s'],flush=True)
   report={'source_run':a.recording.name,'source_manifest_sha256':hashlib.sha256((a.recording/'manifest.json').read_bytes()).hexdigest(),'sampled_states_sha256':hashlib.sha256(a.states.read_bytes()).hexdigest(),'physics_resimulated':False,'camera':'recorded human viewport','training_dataset':False,'state_sample_hz':5,'video_fps':25,'speed_segments':[{'start_s':0,'end_s':71.15,'simulation_speed':12},{'start_s':71.15,'end_s':94,'simulation_speed':2},{'start_s':94,'end_s':duration,'simulation_speed':1.5}],'plan':plan,'rendered_frames':len(plan),'simulation_duration_s':duration}
   (a.output/'render-report.json').write_text(json.dumps(report,indent=2)+'\n')
   print('DEMO RENDER COMPLETE',len(plan),flush=True)
finally:
 app.close()
