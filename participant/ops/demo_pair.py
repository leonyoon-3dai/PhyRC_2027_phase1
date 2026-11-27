#!/usr/bin/env python3
"""Preflight or run two independent demo collectors on one GPU."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ((33, 25, 1200, '20261126-demo24-25-private-backup.json'),
           (34, 26, 2905, '20261126-demo26-32-private-backup.json'))
ELBOW_SOURCES = tuple((demo, *SOURCES[0][1:]) for demo in (35, 36))
PROMPTS = Path('participant/collection/prompts')
ADDENDUM = PROMPTS / 'demo33_34_dressing_addendum.txt'
ELBOW_PROMPTS = {35: PROMPTS / 'demo35_outer_hem_elbow.txt',
                 36: PROMPTS / 'demo36_near_cuff_elbow.txt'}
ELBOW_COMMON = PROMPTS / 'demo35_36_elbow_common.txt'
PYTHON = Path('.venv/bin/python')
sys.path.insert(0, str(ROOT))
from participant.collection.checkpoint import verify_checkpoint
from participant.collection.codex_actor import ACTOR_IMAGE, SUPPORTED_CLI


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_bytes())


def write(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def output(command, *, env=None):
    return subprocess.check_output(command, cwd=ROOT, text=True, env=env, timeout=45).strip()


def source_plan(root, source, pair_id):
    demo, old_demo, offset, receipt_name = source
    backup = read(root / 'docs/active' / receipt_name)
    old = next(r for r in backup['runs'] if r['demonstration'] == old_demo)
    old_id = old['run_id']
    checkpoint = next(c for c in old['checkpoints'] if c['step'] == offset)
    slot_dir = root / checkpoint['archive_member_prefix']
    for key in ('slot', 'receipt'):
        path = slot_dir / Path(checkpoint[key]['path']).name
        if path.stat().st_size != checkpoint[key]['bytes'] or digest(path) != checkpoint[key]['sha256']:
            raise ValueError(f'Demo {old_demo}: {key} differs from pinned source')
    slot = slot_dir / Path(checkpoint['slot']['path']).name
    group = read(slot_dir / 'receipt.json')['source_group']
    try:
        saved = verify_checkpoint(slot, source_group=group)
    except (ValueError, FileNotFoundError) as exc:
        raise ValueError(f'Demo {old_demo} checkpoint compatibility failed ({exc}). '
                         'Use the verified source files listed in its receipt before preparing the runtime.') from exc
    if saved['observation_step'] != offset or saved['run_id'] != old_id:
        raise ValueError(f'Demo {old_demo}: wrong starting checkpoint')
    original = root / 'output/operator-traces' / old_id
    prompt = original / 'prompt.txt'
    metadata = root / 'output/collections' / old_id / 'run_metadata.json'
    recorded = root / 'output/demo33-34-sources' / f'demo{old_demo}-manifest.json'
    if digest(recorded) != old['manifest_sha256']:
        raise ValueError(f'Demo {old_demo}: restore the pinned archive manifest')
    members = read(recorded)
    for path in (prompt, original / 'attempt.json', metadata):
        if members[str(path.relative_to(root))] != {'bytes': path.stat().st_size, 'sha256': digest(path)}:
            raise ValueError(f'Demo {old_demo}: restored source differs from archive: {path.name}')
    attempt, config = read(original / 'attempt.json'), read(metadata)
    if (attempt['run_id'] != old_id or not attempt['finished'] or attempt['prompt_sha256'] != digest(prompt)
            or attempt['model'] != 'gpt-6.2-sol' or attempt['reasoning_effort'] != 'ultra'
            or attempt['actor_backend'] != 'exec' or attempt['plan_size'] != 1
            or config['source_group'] != group or not config['evaluation_enabled']):
        raise ValueError(f'Demo {old_demo}: unexpected original collection or prompt')
    run_id = f'{pair_id}-demo{demo}-sol-ultra'
    run = dict(demo=demo, run_id=run_id, root=str(root), source_run=old_id, source_step=offset,
                source_end=old['transitions'], source_group=group, slot=str(slot.relative_to(root)),
                slot_sha256=saved['slot_sha256'], source_prompt=str(prompt.relative_to(root)),
                source_prompt_sha256=attempt['prompt_sha256'],
                source_decisions_per_review=attempt['decisions_requested'], local_horizon=config['max_steps'],
                local_stop=old['transitions'] - offset if demo == 33 else None)
    if demo in ELBOW_PROMPTS:
        task_files = (ELBOW_COMMON, ELBOW_PROMPTS[demo])
        task_hashes = {}
        for path in task_files:
            contents = (root / path).read_text(encoding='utf-8')
            if not contents.strip():
                raise ValueError(f'Empty task prompt: {path}')
            task_hashes[str(path)] = digest(root / path)
        run.update(local_stop=400, addendum_sha256=None, task_prompt_sha256=task_hashes)
    else:
        run['addendum_sha256'] = digest(root / ADDENDUM)
    return run


def collector_command(run):
    run_id = run['run_id']
    options = [str(PYTHON), '-m', 'participant.collection.codex_client', '--run-id', run_id,
               '--mode', 'dressing', '--gpt-only',
               '--model', 'gpt-6.2-sol', '--effort', 'ultra', '--actor-backend', 'exec',
               '--plan-size', '1', '--named-actions', '--camera-briefing', '--wrist-depth-panel',
               '--segment-review-dir', 'output/segment-review', '--segment-decisions',
               str(run['source_decisions_per_review']), '--segment-steps', '80', '--post-action-settle-steps', '0',
               '--max-steps', str(run['local_horizon']), '--model-timeout', '180', '--parent-attempt',
               run['source_run'], '--retry-reason', 'approximate_slot_fresh_model_continuation', '--source-group', run['source_group'], '--initial-slot', '/' + run['slot'],
               '--slot-study-original-prompt', run['source_prompt'], '--checkpoint-step', 'finish']
    if run['demo'] in ELBOW_PROMPTS:
        for path in (ELBOW_COMMON, ELBOW_PROMPTS[run['demo']]):
            options += ['--slot-study-task-prompt', str(path)]
    else:
        options.append('--until-full-score-or-feedback')
    if run['local_stop'] is not None:
        options += ['--slot-study-stop-step', str(run['local_stop'])]
    if run['demo'] == 33:
        options += ['--checkpoint-step', '100']
    return options


def gpu_info(selector):
    lines = output(['nvidia-smi', '--query-gpu=index,uuid,name,memory.total,memory.free',
                    '--format=csv,noheader,nounits']).splitlines()
    for line in lines:
        index, uuid, name, total, free = [part.strip() for part in line.split(',')]
        if selector in (index, uuid) and re.fullmatch(r'GPU-[0-9a-fA-F-]+', uuid):
            return dict(index=int(index), uuid=uuid, name=name, memory_total_mib=int(total), memory_free_mib=int(free))
    raise ValueError(f'No matching physical GPU: {selector}')


def preflight(args):
    elbow_study = args.study == '35-36'
    pair_dir = ROOT / 'output' / f'demo{args.study}' / args.pair_id
    if pair_dir.exists():
        raise FileExistsError(f'Use a new pair ID: {pair_dir}')
    runs = [source_plan(ROOT, s, args.pair_id) for s in (ELBOW_SOURCES if elbow_study else SOURCES)]
    for run in runs:
        run['lane'] = f'{args.pair_id}-demo{run["demo"]}'
        for path in (*(ROOT / 'output' / x / run['run_id'] for x in ('operator-traces', 'collections', 'actors')),
                     ROOT / '.runtime/study-lanes' / run['lane'], ROOT / 'cache/study-lanes' / run['lane']):
            if path.exists():
                raise FileExistsError(f'Run output already exists: {path}')
        run['command'] = collector_command(run)
    for run in runs:
        recorded = read((ROOT / run['slot']).with_name('receipt.json'))['source_files_sha256']
        for source_file, expected in recorded.items():
            if source_file.startswith('src/PhyRC_Sim/'):
                prepared = ROOT / '.runtime/PhyRC_Sim' / Path(source_file).relative_to('src/PhyRC_Sim')
                if not prepared.is_file() or digest(prepared) != expected:
                    raise ValueError(f'Prepared physics source differs: {prepared}. Run ./run.sh prepare from the verified checkout.')
    dependencies = [PYTHON, Path('.runtime/PhyRC_Sim/Assets/Garment/Tops/Modelink/t_shirt_short.usd'),
                    Path('participant/ops/pair_performance.py')]
    if not elbow_study:
        dependencies.append(Path('tools/publish_demo_pair.py'))
    for relative in dependencies:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f'Missing server dependency: {path}')
    for name in ('docker', 'ffmpeg', 'nvidia-smi', 'flock', 'cp'):
        if not shutil.which(name):
            raise FileNotFoundError(f'Missing executable: {name}')
    if not (ROOT / '.runtime/RCareWorld-2.0/assets/robots').is_dir():
        raise ValueError('Prepare the Isaac runtime and assets first')
    # Credentials are only checked for existence/permissions. The isolated actor opens them itself.
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file() or auth.stat().st_mode & 0o077:
        raise ValueError('Codex CLI needs a private auth.json (mode 0600)')
    # run.sh deliberately forwards these namespaces in ordinary runs. A study inherits
    # the recorded asset/physics defaults, never unrelated overrides from the operator shell.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('STRETCH4_', 'HUMAN_', 'BOX_', 'ROBOT_', 'ROBOT1_', 'ROBOT2_'))
           and k != 'GARMENT_X_OFFSETS'}
    env.update(PATH=str(ROOT / '.runtime/codex-0.166.0/node_modules/.bin') + os.pathsep + env['PATH'],
               PYTHONPATH='.:src/PhyRC_Sim')
    if not shutil.which('codex', path=env['PATH']) or output(['codex', '--version'], env=env) != SUPPORTED_CLI:
        raise ValueError(f'Required actor CLI: {SUPPORTED_CLI}')
    output([str(PYTHON), '-c', 'import PIL,h5py,numpy; import participant.collection.codex_client'], env=env)
    image = env.get('PHYRC_IMAGE', 'phyrc-2027:isaac-6.0.1')
    sim_image = output(['docker', 'image', 'inspect', '--format', '{{.Id}}', image])
    output(['docker', 'image', 'inspect', '--format', '{{.Id}}', ACTOR_IMAGE])
    gpu = gpu_info(args.gpu)
    if not elbow_study:
        if not args.destination.is_dir() or not os.access(args.destination, os.W_OK | os.X_OK):
            raise ValueError('Destination must be a writable directory served by the authenticated Jupyter instance')
        lock_path = args.destination / '.PhyRC-compare.lock'
        if lock_path.exists():
            with lock_path.open('r') as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise ValueError('Another pair publisher owns this destination. Choose a different destination and port.') from exc
        with socket.socket() as check:
            check.bind(('127.0.0.1', args.proxy_port))
    plan = dict(schema='phyrc-concurrent-pair-v1', pair_id=args.pair_id, runs=runs, gpu_uuid=gpu['uuid'],
                gpu=gpu, image=image, image_id=sim_image, git_commit=output(['git', 'rev-parse', 'HEAD']),
                dirty=bool(output(['git', 'status', '--porcelain', '--untracked-files=no'])),
                review_destination=str(args.destination), proxy_port=args.proxy_port)
    if elbow_study:
        plan['internal_publisher'] = False
    return pair_dir, plan, env


def prepare_lanes(runs):
    (ROOT / 'cache').mkdir(exist_ok=True)
    with (ROOT / 'cache/runtime.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        for run in runs:
            lane = ROOT / '.runtime/study-lanes' / run['lane']
            lane.mkdir(parents=True)
            for name in ('PhyRC_Sim', 'RCareWorld-2.0'):
                subprocess.run(['cp', '-a', '--reflink=auto', '--', str(ROOT / '.runtime' / name),
                                str(lane / name)], check=True)
    for name in ('', 'collections', 'operator-traces'):
        directory = ROOT / 'output' / name
        directory.mkdir(exist_ok=True)
        directory.chmod(directory.stat().st_mode | (0o050 if name == 'operator-traces' else 0o070))


def spawn(command, env, log):
    with log.open('xb') as stream:
        return subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)


def run_pair(args, folder, plan, env):
    folder.mkdir(parents=True, exist_ok=False)
    spec = folder / 'pair.json'
    write(spec, {**plan, 'created_at': utc()})
    states = [dict(demo=r['demo'], run_id=r['run_id'], returncode=None) for r in plan['runs']]
    children = {}
    interrupted = None
    def stop(signum, _frame):
        nonlocal interrupted
        interrupted = signum
        for process in children.values():
            if process.poll() is None:
                process.terminate()  # supervisor drains the in-flight ACK and recorder
    def state(value, **extra):
        record = dict(state=value, runs=states, updated_at=utc(), **extra)
        write(folder / 'pair-state.json', record)
        return record
    state('starting')
    previous = {s: signal.signal(s, stop) for s in (signal.SIGTERM, signal.SIGINT)}
    monitor = publisher = None
    failure = None
    try:
        prepare_lanes(plan['runs'])
        if interrupted:
            raise InterruptedError('Pair interrupted during preparation')
        if plan.get('internal_publisher', True):
            publisher = spawn([str(PYTHON), 'tools/publish_demo_pair.py', '--pair', str(spec),
                               '--destination', str(args.destination), '--proxy-port', str(args.proxy_port)],
                              env, folder / 'publisher.log')
        monitor = spawn([str(PYTHON), 'participant/ops/pair_performance.py', 'sample', '--pair', str(spec)],
                        env, folder / 'performance.log')
        ready_by = time.monotonic() + 35
        while True:
            if interrupted:
                raise InterruptedError('Pair interrupted before collector startup')
            if (publisher is not None and publisher.poll() is not None) or monitor.poll() is not None:
                raise OSError('A review or performance worker failed at startup; see publisher.log/performance.log')
            if (folder / 'telemetry.json').is_file():
                if publisher is None:
                    break
                snapshot = args.destination / 'PhyRC-compare.json'
                if snapshot.is_file():
                    rows = read(snapshot).get('runs', [])
                    if [r.get('run_id') for r in rows] == [r['run_id'] for r in plan['runs']]:
                        break
            if time.monotonic() >= ready_by:
                raise TimeoutError('Review or telemetry worker did not publish its first paired state')
            time.sleep(0.25)
        for num, run in enumerate(plan['runs']):
            if interrupted:
                break
            worker = spawn(run['command'], dict(env, PHYRC_STUDY_LANE=run['lane'],
                           PHYRC_STUDY_GPU_UUID=plan['gpu_uuid']), folder / f'demo{run["demo"]}.log')
            children[num] = worker
            if interrupted and worker.poll() is None:
                worker.terminate()
            states[num]['pid'] = worker.pid
        publisher_pid = publisher.pid if publisher else None
        state('running', publisher_pid=publisher_pid, monitor_pid=monitor.pid)
        review_link = f' Review through Jupyter /proxy/{args.proxy_port}/PhyRC-compare.html' if publisher else ''
        print(f'Pair {args.pair_id} started.{review_link}', flush=True)
        while True:
            active = False
            for i, process in children.items():
                code = process.poll()
                active |= code is None
                if states[i]['returncode'] != code:
                    states[i]['returncode'] = code
                    state('running', publisher_pid=publisher_pid, monitor_pid=monitor.pid)
            if not active:
                break
            time.sleep(1)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        failure = str(exc)
        for worker in children.values():
            if worker.poll() is None:
                worker.terminate()
    finally:
        for i, process in children.items():
            states[i]['returncode'] = process.wait()
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    # Validate each closed HDF5 after both collectors release the GPU. QC is outside the measured collection window.
    for r, row in zip(plan['runs'], states):
        row.update(collector_status=None, close_reason=None, qc_returncode=None)
        try:
            attempt_path = ROOT / 'output/operator-traces' / r['run_id'] / 'attempt.json'
            attempt = read(attempt_path) if attempt_path.is_file() else {}
            row['collector_status'] = attempt.get('status')
            row['close_reason'] = attempt.get('autonomous_control', {}).get('close_reason')
            capture = ROOT / 'output/collections' / r['run_id']
            if (capture / 'capture.json').is_file():
                qc = spawn([str(PYTHON), '-m', 'participant.collection.validate_capture', str(capture),
                            '--output', str(capture / 'validation.json')], env, folder / f'demo{r["demo"]}-qc.log')
                row['qc_returncode'] = qc.wait()
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            row['qc_error'] = str(exc)
    ok = all(r['returncode'] == 0 and r['qc_returncode'] == 0 and r['collector_status'] in ('completed', 'incomplete') for r in states)
    terminal = 'interrupted' if interrupted else ('finished' if ok and not failure else 'failed')
    final = state(terminal, error=failure, finished_at=utc(), publisher_pid=publisher.pid if publisher else None)
    write(folder / 'finished.json', final)
    if monitor:
        monitored = monitor.wait()
        if monitored:
            print('Telemetry failed. See performance.log and rebuild with pair_performance.py report.', file=sys.stderr)
    if not children and publisher and publisher.poll() is None:
        publisher.terminate()
        publisher.wait()
    if publisher and publisher.poll() is not None:
        print('Review publisher exited. See publisher.log and restart tools/publish_demo_pair.py.', file=sys.stderr)
    return 0 if terminal == 'finished' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'run'))
    parser.add_argument('--study', choices=('33-34', '35-36'), default='33-34')
    parser.add_argument('--pair-id', required=True)
    parser.add_argument('--gpu', default='0', help='Physical nvidia-smi index or GPU UUID')
    parser.add_argument('--destination', type=Path, default=Path.home())
    parser.add_argument('--proxy-port', type=int, default=8773)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,59}', args.pair_id):
        parser.error('pair-id must be a new safe ASCII ID of 1..60 characters')
    if not 1 <= args.proxy_port <= 65535:
        parser.error('proxy-port must be in 1..65535')
    args.destination = args.destination.expanduser().resolve()
    os.umask(0o027)
    try:
        folder, plan, env = preflight(args)
        if args.action == 'preflight':
            print(json.dumps(plan, indent=2))
            return 0
        lock_dir = ROOT / 'output/demo33-34'
        lock_dir.mkdir(parents=True, exist_ok=True)
        with (lock_dir / (plan['gpu_uuid'] + '.lock')).open('a') as device:
            fcntl.flock(device, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return run_pair(args, folder, plan, env)
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'Pair {args.action} failed: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
