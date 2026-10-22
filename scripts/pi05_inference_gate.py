#!/usr/bin/env python3
"""Official-image offline JAX pi0.5 dependency/memory gate; not a rollout score."""
import os
os.environ['XLA_PYTHON_CLIENT_PREALLOCATE']='false'
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--params',type=Path,required=True)
p.add_argument('--tokenizer',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--lora',action='store_true')
a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
sys.path[:0]=['/project','/output/vendor/openpi/src']
# Policy modules must load after SimulationApp, as required by official adapter.
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
try:
    import numpy as np
    import torch,torchvision,jax,jax.numpy as jnp
    from participant.pi05.local_tokenizer import install
    install(a.tokenizer)
    from openpi.models.pi0_config import Pi0Config
    from openpi.models import model as models
    from openpi.policies.policy import Policy
    from participant.pi05.config import model_transforms
    from participant.pi05.preprocessing import inputs
    # Block *all* automatic openpi downloads after resolving local assets.
    import openpi.shared.download as download
    def local_only(path,**kwargs):
        path=Path(path)
        if not path.is_absolute() or not path.exists():raise RuntimeError('non-local model asset requested')
        return path
    download.maybe_download=local_only
    config=Pi0Config(pi05=True,action_horizon=10,
        paligemma_variant='gemma_2b_lora' if a.lora else 'gemma_2b',
        action_expert_variant='gemma_300m_lora' if a.lora else 'gemma_300m')
    started=time.perf_counter()
    model=config.load(models.restore_params(a.params,dtype=jnp.bfloat16))
    jax.block_until_ready(model)
    load_s=time.perf_counter()-started
    policy=Policy(model,transforms=model_transforms().inputs,sample_kwargs={'num_steps':10})
    obs={'rgb':np.zeros((5,256,256,3),np.uint8),'joint_position':np.zeros((2,13),np.float32),
         'fingertip_origin_distance':np.zeros((2,1),np.float32),
         'gripper_close_command':np.zeros((2,1),bool),'previous_action':np.zeros((2,9),np.float32)}
    values=inputs(obs)
    timings=[]
    for _ in range(3):
        started=time.perf_counter()
        result=policy.infer(values)
        action=np.asarray(result['actions']); jax.block_until_ready(action)
        timings.append(time.perf_counter()-started)
        if action.shape!=(10,32) or not np.isfinite(action).all():raise ValueError('invalid inference')
    import subprocess
    report={'scope':'fixed synthetic public-input fixture; dependency/offline/memory gate, not rollout',
            'torch':torch.__version__,'torchvision':torchvision.__version__,'numpy':np.__version__,
            'jax':jax.__version__,'load_s':load_s,'inference_s':timings,
            'device_memory':jax.devices()[0].memory_stats(),
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used','--format=csv'],text=True),
            'output_shape':list(action.shape),'finite':True,
            'tokenizer_sha256':hashlib.sha256(a.tokenizer.read_bytes()).hexdigest()}
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    np.save(a.output/'fixture-output.npy',action,allow_pickle=False)
    print('PI05-INFERENCE-GATE',json.dumps(report),flush=True)
except BaseException:
    import traceback;traceback.print_exc()
    raise
finally:app.close(exit_code=1 if sys.exc_info()[0] else 0)
