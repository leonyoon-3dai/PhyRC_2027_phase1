#!/usr/bin/env python3
"""Execute one command with reproducibility metadata and host resource samples."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import psutil

ROOT = Path(__file__).resolve().parents[2]


def output(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return {'returncode':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id', required=True)
    p.add_argument('--success-marker')
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    if not a.command or '/' in a.id or a.id in ('.','..'):
        p.error('provide safe unique --id and command after --')
    command = a.command[1:] if a.command[0] == '--' else a.command
    target = ROOT/'output/runs'/a.id
    target.mkdir(parents=True, exist_ok=False)
    meta = {'run_id':a.id, 'started_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'command':command, 'code_commit':output(['git','rev-parse','HEAD']),
            'dirty':output(['git','status','--porcelain']),
            'upstream':output(['git','rev-parse','upstream/main']),
            'gpu':output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv']),
            'cpu':output(['lscpu']), 'os':Path('/etc/os-release').read_text(),
            'docker':output(['docker','version','--format','{{.Server.Version}}']),
            'image':output(['docker','image','inspect',os.environ.get('PHYRC_IMAGE','phyrc-2027:isaac-6.0.1'),'--format','{{.Id}} {{json .RepoDigests}}']),
            'asset_lock_sha256':hashlib.sha256((ROOT/'config/assets.lock.json').read_bytes()).hexdigest()}
    (target/'source.patch').write_text(output(['git','diff','HEAD'])['stdout'])
    (target/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    done = threading.Event()
    def sample():
        with (target/'resources.jsonl').open('x') as f:
            while not done.is_set():
                io = psutil.disk_io_counters()
                value = {'monotonic_s':time.monotonic(),'cpu_percent':psutil.cpu_percent(percpu=True),
                         'ram':psutil.virtual_memory()._asdict(), 'disk_io':io._asdict() if io else None,
                         'gpu':output(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,utilization.encoder,power.draw','--format=csv,noheader,nounits'])}
                f.write(json.dumps(value)+'\n'); f.flush()
                done.wait(2)
    worker = threading.Thread(target=sample)
    worker.start()
    started = time.monotonic()
    try:
        with (target/'command.log').open('xb') as log:
            proc = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        code=proc.returncode
        if a.success_marker and a.success_marker not in (target/'command.log').read_text(errors='replace'):
            code=code or 1
        meta.update(returncode=code, process_returncode=proc.returncode, success_marker=a.success_marker, wall_s=time.monotonic()-started)
    finally:
        done.set(); worker.join()
        meta['ended_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (target/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'run_id':a.id,'returncode':meta['returncode'],'wall_s':meta['wall_s'],'evidence':str(target)}))
    raise SystemExit(meta['returncode'])

if __name__ == '__main__':
    main()
