#!/usr/bin/env python3
"""Build a complete offline ZIP from an actual completed upstream checkpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--tokenizer',type=Path,required=True)
    p.add_argument('--openpi',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute-steps',type=int,default=5)
    a=p.parse_args()
    checkpoint=a.checkpoint.resolve(strict=True)
    for name in ('params','train_state','assets/phyrc/norm_stats.json'):
        if not (checkpoint/name).exists():raise ValueError('missing checkpoint item '+name)
    if any('tmp' in p.name for p in checkpoint.rglob('*')):raise ValueError('checkpoint contains temporary items')
    bundle=a.output.resolve()
    bundle.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(ROOT/'participant/policy.py',bundle/'policy.py')
    shutil.copyfile(a.tokenizer,bundle/'tokenizer.model')
    shutil.copytree(checkpoint/'params',bundle/'params')
    shutil.copytree(checkpoint/'assets/phyrc',bundle/'norm_stats')
    (bundle/'participant').mkdir()
    shutil.copyfile(ROOT/'participant/__init__.py',bundle/'participant/__init__.py')
    shutil.copytree(ROOT/'participant/pi05',bundle/'participant/pi05',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(a.openpi/'src',bundle/'vendor/openpi/src',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(a.openpi/'packages/openpi-client/src/openpi_client',bundle/'vendor/openpi/src/openpi_client',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(a.openpi/'LICENSE',bundle/'vendor/openpi/LICENSE')
    for name in ('Dockerfile','requirements-additions.txt','requirements-extra.txt'):
        shutil.copyfile(ROOT/'participant/runtime'/name,bundle/name)
    config={'params':'params','tokenizer':'tokenizer.model','norm_stats':'norm_stats',
            'openpi_src':'vendor/openpi/src','diffusion_steps':10,'execute_steps':a.execute_steps,
            'model':'pi05 JAX gemma_2b_lora + gemma_300m_lora','conversion':'none; full LoRA architecture and params',
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'openpi_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.openpi,text=True).strip()}
    (bundle/'bundle.json').write_text(json.dumps(config,indent=2)+'\n')
    inventory={path.relative_to(bundle).as_posix():hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
               for path in sorted(bundle.rglob('*')) if path.is_file()}
    (bundle/'SHA256.json').write_text(json.dumps(inventory,indent=2)+'\n')
    archive=bundle.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for path in sorted(bundle.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(bundle))
    with archive.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    archive.with_suffix('.zip.sha256').write_text(sha+'  '+archive.name+'\n')
    print(json.dumps({'zip':str(archive),'sha256':sha,'bytes':archive.stat().st_size}))

if __name__=='__main__':main()
