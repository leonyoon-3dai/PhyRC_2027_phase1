#!/usr/bin/env python3
"""Small reviewed HDF5 dataset → upstream openpi JAX LoRA trainer.

Use the pinned openpi environment. Saves upstream full params + optimizer state.
The deterministic training seed is preserved; dataloader cursor is NOT restored.
"""
import argparse
import dataclasses
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--openpi',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--base-params',type=Path,required=True)
    p.add_argument('--tokenizer',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--steps',type=int,default=30)
    p.add_argument('--batch-size',type=int,default=1)
    p.add_argument('--resume',action='store_true')
    a = p.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from participant.pi05.local_tokenizer import install
    install(a.tokenizer)
    from participant.pi05.config import train_config,model_transforms
    from participant.pi05.data import Episodes
    from openpi.shared import normalize
    from openpi import transforms
    from openpi.training.config import DataConfig
    import jax
    from openpi.models.model import Observation
    import openpi.training.data_loader as dl
    dataset = Episodes(a.manifest,'train',10)
    stats = {}
    for key in ('state','actions'):
        data = np.concatenate([dataset[i][key].reshape(-1,32) for i in range(len(dataset))])
        stats[key] = normalize.NormStats(mean=data.mean(0),std=data.std(0),
                          q01=np.quantile(data,.01,axis=0),q99=np.quantile(data,.99,axis=0))
    config = train_config(a.base_params.resolve(),a.output.resolve(),a.steps,a.batch_size,a.resume)
    data_config = DataConfig(asset_id='phyrc',repo_id='participant-reviewed',norm_stats=stats,
                            use_quantile_norm=True,model_transforms=model_transforms())
    transform = transforms.compose([transforms.Normalize(stats,use_quantiles=True),*data_config.model_transforms.inputs])
    class Loader:
        def __init__(self,sharding): self.sharding=sharding
        def data_config(self): return data_config
        def __iter__(self):
            rng = np.random.default_rng(config.seed)
            while True:
                indices=rng.integers(len(dataset),size=config.batch_size)
                values=[transform(dataset[int(i)]) for i in indices]
                batch=jax.tree.map(lambda *x:np.stack(x),*values)
                batch=jax.tree.map(lambda x:jax.make_array_from_process_local_data(self.sharding,x),batch)
                yield Observation.from_dict(batch),batch['actions']
    dl.create_data_loader = lambda config,sharding,shuffle:Loader(sharding)
    spec=importlib.util.spec_from_file_location('pinned_openpi_train',a.openpi.resolve()/'scripts/train.py')
    trainer=importlib.util.module_from_spec(spec); spec.loader.exec_module(trainer)
    started=time.monotonic()
    config.checkpoint_dir.parent.mkdir(parents=True,exist_ok=True)
    # Save input manifest/config before training, even if compile or OOM fails.
    record={'steps':a.steps,'batch_size':a.batch_size,'dataset_samples':len(dataset),
            'requested_processed_samples':a.steps*a.batch_size,
            'requested_effective_epochs':a.steps*a.batch_size/len(dataset),
            'manifest_sha256':__import__('hashlib').sha256(a.manifest.read_bytes()).hexdigest(),
            'model':dataclasses.asdict(config.model),'seed':config.seed,'resume':a.resume,
            'dataloader_cursor_restored':False,'rng_basis':'upstream train_rng seed + train_state.step',
            'tokenizer':str(a.tokenizer.resolve()),'base_params':str(a.base_params.resolve())}
    record_path=config.checkpoint_dir.parent/('request-'+str(time.time_ns())+'.json')
    record_path.write_text(json.dumps(record,indent=2)+'\n')
    trainer.main(config)
    record.update(wall_s=time.monotonic()-started,training_returned=True)
    record_path.write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__': main()
