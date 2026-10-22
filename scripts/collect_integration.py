#!/usr/bin/env python3
"""Scripted recorder integration test: real sensor data, not a GPT demonstration.

No dressing goal or success claim. Exclude from general SFT until reviewed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path('/project')
sys.path[:0]=[str(ROOT),str(ROOT/'src/PhyRC_Sim')]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    from Policy.environment import DressingEnv
    from Policy.training_dataset import DatasetWriter
    from participant.collection.boundary import Operator
    from PIL import Image
    import numpy as np
    env=DressingEnv(max_episode_steps=100)
    writer=DatasetWriter(a.output,env.contract,{'source':'integration_test','raw_archive':False,
                         'tick_basis':'episode-relative','purpose':'recorder wiring; not GPT or successful dressing'})
    op=Operator(env,writer,source='integration_test',source_group=a.output.name,
                model_id='scripted-recorder-check-v1',prompt='small lift and gripper wiring test only')
    complete=False
    started=time.monotonic()
    try:
        for episode in range(3):
            obs=op.begin(seed=4200+episode)
            Image.fromarray(obs['rgb'][0]).save(a.output/f'episode-{episode}-start.png')
            for lift,grip in ((.05,-1),(.0,1),(-.05,0),(.0,-1)):
                action=np.zeros((2,9),np.float32);action[:,3]=lift;action[:,8]=grip
                op.act(action,5)
            op.stop()
            result=op.finish_episode()
            Image.fromarray(op._obs['rgb'][0]).save(a.output/f'episode-{episode}-end.png')
            print('INTEGRATION_EPISODE',episode,result,flush=True)
        complete=True
    finally:
        writer.close(complete=complete)
        report={'schema':'participant-live-capture-v1','complete':complete,'source':'integration_test',
                'raw_archive':False,'deferred_export_check':False,'episodes':3 if complete else None,
                'wall_s':time.monotonic()-started,'simulation_time_s':3*21*.05 if complete else None,
                'checksums':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.output.glob('*.hdf5')}}
        (a.output/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        env.close()

if __name__=='__main__':main()
