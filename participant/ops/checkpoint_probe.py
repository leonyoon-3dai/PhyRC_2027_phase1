#!/usr/bin/env python3
"""Restore the complete upstream training state on CPU, without a training step.

This verifies full parameter/optimizer/step restoration, not dataloader cursor
restoration or bitwise continuation. Set JAX_PLATFORMS=cpu explicitly.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    if os.environ.get('JAX_PLATFORMS')!='cpu':raise RuntimeError('this probe requires JAX_PLATFORMS=cpu')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--openpi',type=Path,required=True)
    p.add_argument('--checkpoint-parent',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import jax
    import numpy as np
    from participant.pi05.config import train_config
    from openpi.training import checkpoints,sharding
    spec=importlib.util.spec_from_file_location('pinned_train',a.openpi/'scripts/train.py')
    trainer=importlib.util.module_from_spec(spec);spec.loader.exec_module(trainer)
    config=train_config(a.checkpoint_parent/'29/params',a.output.parent,31,1,True)
    rng=jax.random.key(config.seed)
    train_rng,init_rng=jax.random.split(rng)
    started=time.monotonic()
    manager,resuming=checkpoints.initialize_checkpoint_dir(a.checkpoint_parent,keep_period=10,overwrite=False,resume=True)
    if not resuming:raise ValueError('no completed training checkpoint')
    mesh=sharding.make_mesh(1)
    template,_=trainer.init_train_state(config,init_rng,mesh,resume=True)
    state=checkpoints.restore_state(manager,template,None)
    jax.block_until_ready(state)
    step=int(state.step)
    if step!=30:raise ValueError('expected saved optimizer step 30')
    from flax.traverse_util import flatten_dict
    flat=flatten_dict(state.params.to_pure_dict(),sep='/')
    leaves=jax.tree.leaves(state.opt_state)
    trainable=flatten_dict(state.params.filter(config.trainable_filter).to_pure_dict(),sep='/')
    report={'scope':'CPU full upstream training-state restoration, no optimizer step',
       'step':step,'parameter_leaves':len(flat),'lora_leaves':sum('lora' in key for key in flat),
       'parameter_elements':sum(value.size for value in flat.values()),
       'trainable_elements':sum(value.size for value in trainable.values()),
       'trainable_leaves':len(trainable),
       'freeze_scope':'upstream get_freeze_filter; vision/projection parameters remain trainable',
       'optimizer_array_leaves':len(leaves),'optimizer_elements':sum(getattr(v,'size',0) for v in leaves),
       'train_rng_key_data':np.asarray(jax.random.key_data(train_rng)).tolist(),
       'init_rng_key_data':np.asarray(jax.random.key_data(init_rng)).tolist(),
       'seed':config.seed,'wall_s':time.monotonic()-started,'dataloader_cursor_restored':False,
       'bitwise_physics_restored':False,'devices':[str(d) for d in jax.devices()]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    manager.close()
    print(json.dumps(report))

if __name__=='__main__':main()
