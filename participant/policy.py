"""Offline official adapter for the participant pi0.5 JAX LoRA checkpoint."""
import os
from pathlib import Path
import sys
from collections import deque
import numpy as np


def load_policy(checkpoint,observation_space,action_space):
    # checkpoint is optional: Orbax params are a directory, located by bundle.json.
    root=Path(__file__).resolve().parent
    if checkpoint is not None:
        raise ValueError('This bundle uses local Orbax params via bundle.json, not checkpoint.pt')
    import json
    config=json.loads((root/'bundle.json').read_text())
    def asset(name):
        value=(root/config[name]).resolve()
        if value!=root and root not in value.parents:raise ValueError('bundle path escapes root')
        if not value.exists():raise FileNotFoundError(value)
        return value
    os.environ['XLA_PYTHON_CLIENT_PREALLOCATE']='false'
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['TRANSFORMERS_OFFLINE']='1'
    sys.path[:0]=[str(root),str(asset('openpi_src'))]
    from participant.pi05.local_tokenizer import install
    install(asset('tokenizer'))
    # Refuse every remote asset resolution, including transitive openpi helpers.
    import openpi.shared.download as download
    def local_only(path,**kwargs):
        value=Path(path)
        if not value.is_absolute() or not value.exists():raise RuntimeError('offline asset unavailable')
        return value
    download.maybe_download=local_only
    import jax
    import jax.numpy as jnp
    import logging
    logging.getLogger('jax').setLevel(logging.WARNING)
    from participant.pi05.config import model_config,model_transforms
    from participant.pi05.preprocessing import inputs,restore_actions
    from openpi.models import model as models
    from openpi.policies.policy import Policy as OpenpiPolicy
    from openpi.shared import normalize
    from openpi import transforms
    if tuple(action_space.shape)!=(2,9):raise ValueError('unexpected official action interface')
    stats=normalize.load(asset('norm_stats'))
    model=model_config().load(models.restore_params(asset('params'),dtype=jnp.bfloat16))
    model_policy=OpenpiPolicy(model,transforms=[transforms.Normalize(stats,use_quantiles=True),*model_transforms().inputs],
                       output_transforms=[transforms.Unnormalize(stats,use_quantiles=True)],
                       sample_kwargs={'num_steps':config['diffusion_steps']})
    execute_steps=config['execute_steps']
    if not isinstance(execute_steps,int) or not 1<=execute_steps<=10:raise ValueError('bad chunk execution horizon')
    class Policy:
        def __init__(self):self.pending=deque()
        def reset(self):
            self.pending.clear()
            model_policy._rng=jax.random.key(0)
        def __call__(self,obs):
            if not self.pending:
                chunk=restore_actions(model_policy.infer(inputs(obs))['actions'])
                self.pending.extend(chunk[:execute_steps])
            return np.array(self.pending.popleft(),dtype=np.float32,copy=True)
    return Policy()
