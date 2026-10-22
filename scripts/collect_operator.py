#!/usr/bin/env python3
"""JSON-lines restricted operator on stdin/stdout; simulator logs remain on stderr.

Use only observe/act/stop/finish_episode. No seed, reset options, info, score,
free viewport or arbitrary paths are part of this protocol. Controller must be
an isolated client with no shell or filesystem access to the simulation server.
"""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path('/project') if Path('/project').is_dir() else Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src/PhyRC_Sim')]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--source', choices=['human','gpt','human_corrected_gpt','integration_test'], required=True)
    p.add_argument('--source-group', required=True)
    p.add_argument('--model-id', required=True)
    p.add_argument('--prompt', required=True)
    p.add_argument('--max-steps', type=int, default=400)
    args = p.parse_args()
    protocol = sys.stdout
    with contextlib.redirect_stdout(sys.stderr):
        from Policy.environment import DressingEnv
        from Policy.training_dataset import DatasetWriter
        from participant.collection.boundary import Operator
        env = DressingEnv(max_episode_steps=args.max_steps)
        writer = DatasetWriter(args.output, env.contract, {'recorder':'participant-live-v1',
                               'raw_archive':False, 'tick_basis':'episode-relative',
                               'source':args.source, 'source_group':args.source_group})
        operator = Operator(env, writer, source=args.source, source_group=args.source_group,
                            model_id=args.model_id, prompt=args.prompt)
        started = time.monotonic()
        transcript = (args.output/'operator.jsonl').open('x')
        complete = False
        def encode(value):
            return value.tolist() if hasattr(value, 'tolist') else value
        def emit(value):
            print(json.dumps(value, default=encode, allow_nan=False), file=protocol, flush=True)
        try:
            emit({'ready':True, 'observation':operator.begin()})
            for line in sys.stdin:
                try:
                    request = json.loads(line)
                    method = request['tool']
                    if method not in ('observe','act','stop','finish_episode') or set(request)-{'tool','arguments'}:
                        raise ValueError('unsupported tool/request fields')
                    arguments = request.get('arguments', {})
                    if method != 'act' and arguments:
                        raise ValueError('this tool takes no arguments')
                    result = getattr(operator,method)(**arguments)
                    transcript.write(json.dumps({'request':request,'wall_s':time.monotonic()-started}, allow_nan=False)+'\n')
                    transcript.flush()
                    emit({'ok':True,'result':result})
                    if method == 'finish_episode' or not operator._active:
                        complete = result.get('complete', operator._tick > 0)
                        break
                except (ValueError, TypeError, KeyError) as exc:
                    emit({'ok':False,'error':str(exc)})
        finally:
            if operator._active:
                operator.finish_episode('input_closed')
                complete = False  # explicit finish required
            writer.close(complete=complete)
            transcript.close()
            manifest = {'schema':'participant-live-capture-v1','complete':complete,
                        'raw_archive':False,'deferred_export_check':False,
                        'wall_s':time.monotonic()-started,'files':{}}
            for path in sorted(args.output.glob('*.hdf5')):
                manifest['files'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            (args.output/'capture.json').write_text(json.dumps(manifest, indent=2)+'\n')
            env.close()

if __name__ == '__main__':
    main()
