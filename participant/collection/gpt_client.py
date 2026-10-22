#!/usr/bin/env python3
"""Low-frequency GPT operator. Model sees public images/state and no other tools.

API calls use only the explicitly built payload below. Simulator subprocess logs,
filesystem, Gym info, seeds, scores and raw/audit data never enter model input.
"""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import numpy as np
from PIL import Image
from participant.collection.boundary import CONTRACT,validate_action

PROMPT='''You operate two Stretch robots using only the supplied designated camera RGB and public robot observations. This is a brief data-collection wiring test, not a dressing-success attempt. First request a small lift motion (absolute velocity <=0.05 normalized) and open grippers, then close grippers, then neutral/stop and finish. Avoid contact and large motion. Return one allowed tool decision per observation. Actions have two rows, robot 0 then robot 1, each: forward,left,CCW yaw,lift,arm extension,wrist yaw,pitch,roll,gripper. All normalized [-1,1]. Gripper +1 closes,-1 opens,0 preserves intent. Steps are official 20Hz simulation steps, at most 10 for this test. Do not infer hidden state or request filesystem/simulator access. No privileged information is available. If uncertain, stop or finish. Give an action array even for other tools (all zeros).'''
SCHEMA={'type':'object','additionalProperties':False,'required':['tool','action','steps','reason'],
 'properties':{'tool':{'type':'string','enum':['observe','act','stop','finish_episode']},
 'action':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'array','minItems':9,'maxItems':9,
 'items':{'type':'number','minimum':-1,'maximum':1}}},
 'steps':{'type':'integer','minimum':1,'maximum':10},'reason':{'type':'string'}}}


def content(obs):
    result=[]
    # Explicit public-state allowlist; omit depth to reduce API payload.
    state={key:obs[key] for key in CONTRACT['competition_access']['allowed_policy_observations']
           if key not in ('rgb','depth','depth_valid') and key in obs}
    result.append({'type':'input_text','text':json.dumps({'public_robot_observation':state},allow_nan=False)})
    for i,name in enumerate(CONTRACT['competition_access']['allowed_cameras'][:3]):
        image=np.asarray(obs['rgb'][i],dtype=np.uint8)
        if image.shape!=(256,256,3):raise ValueError('unexpected public camera shape')
        buf=io.BytesIO();Image.fromarray(image).save(buf,format='PNG')
        result.extend([{'type':'input_text','text':'Designated camera: '+name},
                       {'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),'detail':'high'}])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',required=True)
    p.add_argument('--run-id',required=True)
    p.add_argument('--decisions',type=int,default=4)
    p.add_argument('--credentials',type=Path,default=Path.home()/'.config/phyrc/operator.env')
    a=p.parse_args()
    if '/' in a.run_id or not 1<=a.decisions<=10:p.error('safe run-id and 1..10 decisions required')
    key=os.environ.get('OPENAI_API_KEY')
    if not key and a.credentials.exists():
        if a.credentials.stat().st_mode & 0o077:raise ValueError('credential file must be mode 600')
        for line in a.credentials.read_text().splitlines():
            if line.startswith('OPENAI_API_KEY='):key=line.split('=',1)[1].strip().strip('\"\'')
    if not key:raise RuntimeError('OPENAI_API_KEY unavailable; never send it in chat')
    root=Path(__file__).resolve().parents[2]
    trace=root/'output/operator-traces'/a.run_id
    trace.mkdir(parents=True,exist_ok=False)
    cmd=['./run.sh','python','/scripts/collect_operator.py','--output','/output/collections/'+a.run_id,
         '--source','gpt','--source-group',a.run_id,'--model-id',a.model,'--prompt',PROMPT]
    env={k:v for k,v in os.environ.items() if k not in ('OPENAI_API_KEY','HF_TOKEN','GH_TOKEN','GITHUB_TOKEN')}
    with (trace/'simulator.log').open('w') as log, (trace/'decisions.jsonl').open('x') as audit:
        process=subprocess.Popen(cmd,cwd=root,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1)
        def receive():
            line=process.stdout.readline()
            if not line:raise RuntimeError('simulator closed; inspect separate simulator.log')
            value=json.loads(line)
            if value.get('ok') is False:raise ValueError(value['error'])
            return value
        def dispatch(tool,arguments=None):
            process.stdin.write(json.dumps({'tool':tool,'arguments':arguments or {}},allow_nan=False)+'\n');process.stdin.flush()
            return receive().get('result',{})
        finished=False
        history=[]
        try:
            value=receive()
            obs=value['observation']
            history=[]
            for i in range(a.decisions):
                parts=content(obs)
                payload={'model':a.model,'store':False,'instructions':PROMPT,
                    'input':[{'role':'user','content':[{'type':'input_text','text':'Previous decisions: '+json.dumps(history)},*parts]}],
                    'text':{'format':{'type':'json_schema','name':'phyrc_operator','schema':SCHEMA,'strict':True}},
                    'max_output_tokens':1200}
                started=time.perf_counter()
                request=urllib.request.Request('https://api.openai.com/v1/responses',
                    data=json.dumps(payload,allow_nan=False).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=120) as response:result=json.load(response)
                texts=[item['text'] for entry in result.get('output',[]) for item in entry.get('content',[]) if item.get('type')=='output_text']
                decision=json.loads(''.join(texts))
                action=validate_action(decision['action'],decision['steps'])
                if np.any(np.abs(action[:,:8])>.05):raise ValueError('wiring test motion exceeds 0.05')
                tool=decision['tool']
                audit.write(json.dumps({'decision':decision,'model':result.get('model'),'response_id':result.get('id'),
                    'usage':result.get('usage'),'api_wall_s':time.perf_counter()-started,
                    'input_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()},allow_nan=False)+'\n');audit.flush()
                if tool not in ('observe','act','stop','finish_episode'):raise ValueError('unsupported tool')
                value=dispatch(tool,{'action':action.tolist(),'steps':decision['steps']} if tool=='act' else None)
                history.append(decision)
                if tool=='finish_episode':finished=True;break
                obs=value.get('observation',value)
            if not finished:
                dispatch('stop');dispatch('finish_episode');finished=True
        finally:
            # On model/API error, explicitly stop then finish if the connection is alive.
            if not finished and process.poll() is None:
                try:dispatch('stop');dispatch('finish_episode')
                except (ValueError,RuntimeError,BrokenPipeError):pass
            process.stdin.close()
            code=process.wait(timeout=180)
            (trace/'client-result.json').write_text(json.dumps({'returncode':code,'finished':finished,'model':a.model,'decisions':len(history),'prompt_sha256':hashlib.sha256(PROMPT.encode()).hexdigest()})+'\n')
            if code:raise RuntimeError('simulator recorder failed')

if __name__=='__main__':main()
