"""Stage a closed, validated collection for PRIVATE backup; never upload it.

Use ``--run-id RUN --bundle-id UNIQUE --pack`` from the repository root.
Only reviewed collection, trace, source snapshot and public observation paths
are copied to a new output/preservation/UNIQUE directory. The archive and local
receipt are siblings of that directory. Existing destinations are never reused.
Validation and checksums certify technical consistency, not task success or
training approval. Trusted audit/evaluation files must never become actor input.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from participant.ops import artifacts


COLLECTION_REQUIRED = {'capture.json', 'policy.hdf5', 'audit.hdf5', 'operator.jsonl', 'run_metadata.json'}
COLLECTION_OPTIONAL = {'evaluation_summary.json', 'step_timings.jsonl', 'validation.json'}
EVALUATION_FILES = {'result.json', 'samples.jsonl', 'score_events.jsonl', 'score_samples.jsonl'}
TRACE_REQUIRED = {'attempt.json', 'decisions.jsonl', 'prompt.txt', 'review_gate.json'}
TRACE_OPTIONAL = {'score_segments.json'}
OBS_REQUIRED = {'observation.json', 'public_depth.npz', 'overview.png', 'robot_0_wrist.png',
                'robot_1_wrist.png', 'robot_0_head.png', 'robot_1_head.png'}
OBS_OPTIONAL = {'current_wrist_depth.json', 'current_wrist_depth.png'}
SOURCE_FIXED = {'run.sh', 'scripts/collect_operator.py', 'participant/streaming/collector_stream.py',
                'config/policy_interface.json', 'config/assets.lock.json',
                'participant/research/depth_backprojection.py'}
FORBIDDEN_PARTS = {'runtime', 'actor_events', 'codex_home', '.git', '.ssh', '__pycache__',
                   'auth.json', 'token', 'stored_tokens', 'simulator.log'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def reject(value):
        raise ValueError('non-finite JSON value: ' + value)
    return json.loads(Path(path).read_text(), parse_constant=reject)


def signature(path):
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def safe_source(path, root):
    """Reject symlinks in every parent before following a selected source."""
    path = Path(path).absolute()
    # absolute() retains '..'. Reject lexical traversal before inspecting or
    # reading the path; resolve() here would hide traversed symlink components.
    require('..' not in path.parts, 'parent traversal rejected in source path')
    relative = path.relative_to(root)
    require(not any(p in FORBIDDEN_PARTS or p.startswith('.env') or p.endswith(('.key', '.pem'))
                    for p in relative.parts), 'excluded source path: ' + str(relative))
    for node in (path, *path.parents):
        require(not node.is_symlink(), 'symlink rejected: ' + str(relative))
        if node == root:
            break
    require(path.is_file(), 'missing/non-regular source: ' + str(relative))
    return relative


def tree_files(directory):
    require(directory.is_dir() and not directory.is_symlink(), 'missing or symlink source directory')
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), 'symlink in selected tree: ' + str(path))
        if path.is_dir():
            continue
        require(path.is_file(), 'non-regular file in selected tree: ' + str(path))
        yield path


def observation_files(directory, *, required):
    if not directory.exists():
        require(not required, 'public observations directory missing')
        return []
    require(directory.is_dir() and not directory.is_symlink(), 'invalid observations directory')
    result = []
    for folder in sorted(directory.iterdir()):
        require(folder.is_dir() and not folder.is_symlink() and re.fullmatch(r'\d{5,}', folder.name),
                'unexpected observation directory: ' + folder.name)
        paths = list(tree_files(folder))
        names = {p.relative_to(folder).as_posix() for p in paths}
        require(OBS_REQUIRED <= names <= OBS_REQUIRED | OBS_OPTIONAL,
                'unreviewed or incomplete observation files in ' + folder.name)
        require(('current_wrist_depth.json' in names) == ('current_wrist_depth.png' in names),
                'incomplete wrist-depth panel pair')
        result.extend(paths)
    if required:
        require(result, 'public observation set is empty')
    return result


def select_sources(root, run_id, validation_path):
    collection = root / 'output/collections' / run_id
    trace = root / 'output/operator-traces' / run_id
    for path in (collection / 'capture.json', trace / 'attempt.json', validation_path):
        safe_source(path, root)
    capture, attempt, validation = map(read_json, (collection / 'capture.json', trace / 'attempt.json', validation_path))
    require(capture.get('complete') is True and capture.get('raw_archive') is False,
            'capture must be complete immediate-sensor data')
    require(attempt.get('run_id') == run_id and attempt.get('activity') == 'closed'
            and attempt.get('status') in ('completed', 'review_ready', 'interrupted', 'failed')
            and attempt.get('simulator_returncode') == 0, 'attempt/simulator is not closed cleanly')
    require(validation.get('schema') == 'phyrc-capture-validation-v1'
            and validation.get('quality_passed') is True and validation.get('errors') == [],
            'full passing validation is required')
    count = validation.get('validated_transitions')
    require(type(count) is int and count > 0 and count == validation.get('total_transitions')
            == capture.get('steps') == attempt.get('simulation_steps'), 'transition counts disagree')
    episodes = validation.get('episodes')
    require(isinstance(episodes, list) and episodes and all(
        e.get('complete') is True and e.get('quality_passed') is True
        and type(e.get('transitions')) is int and e['transitions'] > 0 for e in episodes)
        and sum(e['transitions'] for e in episodes) == count, 'validation episodes are incomplete')
    checksums = capture.get('files', capture.get('checksums'))
    require(isinstance(checksums, dict) and set(checksums) == {'policy.hdf5', 'audit.hdf5'},
            'unreviewed capture checksum file set')
    for name, expected in checksums.items():
        require(isinstance(expected, str) and re.fullmatch(r'[a-f0-9]{64}', expected)
                and validation.get('sha256', {}).get(name) == expected,
                'capture and validation hashes disagree: ' + name)

    selected = []
    observed_root = set()
    evaluation_names = {}
    for path in tree_files(collection):
        relative = path.relative_to(collection)
        if len(relative.parts) == 1:
            require(path.name in COLLECTION_REQUIRED | COLLECTION_OPTIONAL,
                    'unreviewed collection file: ' + str(relative))
            observed_root.add(path.name)
        else:
            require(len(relative.parts) == 3 and relative.parts[0] == 'evaluation'
                    and re.fullmatch(r'[A-Za-z0-9_-]+', relative.parts[1])
                    and relative.parts[2] in EVALUATION_FILES,
                    'unreviewed evaluation path: ' + str(relative))
            evaluation_names.setdefault(relative.parts[1], set()).add(relative.parts[2])
        selected.append(path)
    require(COLLECTION_REQUIRED <= observed_root, 'required collection files missing')
    require(all(names == EVALUATION_FILES for names in evaluation_names.values()),
            'incomplete evaluation files')
    if capture.get('evaluation_enabled') is True:
        require(evaluation_names and 'evaluation_summary.json' in observed_root,
                'enabled evaluation is missing')
    for name in TRACE_REQUIRED | TRACE_OPTIONAL:
        path = trace / name
        if name in TRACE_REQUIRED or path.exists():
            selected.append(path)

    snapshot = attempt.get('source_snapshot', {})
    hashes = snapshot.get('files_sha256')
    require(isinstance(hashes, dict) and hashes, 'source snapshot checksum map missing')
    source_paths = list(tree_files(trace / 'source_snapshot'))
    require({p.relative_to(trace / 'source_snapshot').as_posix() for p in source_paths} == set(hashes),
            'source snapshot differs from recorded exact file list')
    for name, expected in hashes.items():
        require(name in SOURCE_FIXED or re.fullmatch(r'participant/collection/[A-Za-z0-9_]+\.py', name),
                'unreviewed source snapshot path: ' + name)
        require(isinstance(expected, str) and re.fullmatch(r'[a-f0-9]{64}', expected),
                'invalid source snapshot hash')
    selected.extend(source_paths)
    selected.extend(observation_files(root / 'output/actors' / run_id / 'observations',
                                      required=bool(attempt.get('actor_calls_attempted', 0))))
    selected.extend(observation_files(trace / 'replay_observations', required=False))
    for path in selected:
        safe_source(path, root)
    return selected, capture, attempt, validation


def preserve(root, run_id, bundle_id, *, validation=None, pack=False):
    root = Path(root).resolve()
    require(root.is_dir() and (root / 'config/policy_interface.json').is_file(), 'invalid repository root')
    require(all(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', value)
                for value in (run_id, bundle_id)), 'unsafe run/bundle ID')
    parent = root / 'output/preservation'
    stage, archive, receipt_path = parent / bundle_id, parent / (bundle_id + '.tar.gz'), parent / (bundle_id + '.receipt.json')
    require(not any(p.exists() or p.is_symlink() for p in (stage, archive, receipt_path)),
            'destination already exists; choose a new bundle ID')
    validation = Path(validation).absolute() if validation else root / 'output/collections' / run_id / 'validation.json'
    selected, capture, attempt, report = select_sources(root, run_id, validation)
    # Check all selected hashes before creating output. Additional file mutation
    # checks below prevent a changed source from yielding a valid staged bundle.
    sources = {}
    for path in selected + [validation]:
        stamp = signature(path)
        digest = artifacts.digest(path)
        require(signature(path) == stamp, 'source changed while hashing: ' + str(path))
        sources[path] = {'sha256': digest, 'bytes': path.stat().st_size, 'signature': stamp}
    collection = root / 'output/collections' / run_id
    for name, expected in capture.get('files', capture.get('checksums')).items():
        require(sources[collection / name]['sha256'] == expected, 'HDF5 hash mismatch: ' + name)
    for name, expected in attempt['source_snapshot']['files_sha256'].items():
        path = root / 'output/operator-traces' / run_id / 'source_snapshot' / name
        require(sources[path]['sha256'] == expected, 'source snapshot hash mismatch: ' + name)
    prompt = root / 'output/operator-traces' / run_id / 'prompt.txt'
    require(sources[prompt]['sha256'] == attempt.get('prompt_sha256'), 'prompt hash mismatch')

    for node in (parent, *parent.parents):
        require(not node.is_symlink(), 'symlink destination parent')
        if node == root:
            break
    old_umask = os.umask(0o077)
    try:
        parent.mkdir(parents=True, exist_ok=True)
        stage.mkdir(mode=0o700)
        copied = {}
        for source in selected:
            relative = source.relative_to(root)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as reader, target.open('xb') as writer:
                shutil.copyfileobj(reader, writer, length=8 * 1024 * 1024)
            require(signature(source) == sources[source]['signature'], 'source changed during copy')
            require(artifacts.digest(target) == sources[source]['sha256'], 'staged copy hash mismatch')
            copied[relative.as_posix()] = {k: sources[source][k] for k in ('sha256', 'bytes')}
        # External validation remains separate; original collection records stay byte exact.
        validation_target = stage / 'preservation_validation.json'
        with validation.open('rb') as reader, validation_target.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        require(artifacts.digest(validation_target) == sources[validation]['sha256'], 'validation copy mismatch')
        for path, metadata in sources.items():
            require(signature(path) == metadata['signature'], 'source changed before finalization')
        receipt = {
            'schema': 'phyrc-private-preservation-v1', 'run_id': run_id, 'bundle_id': bundle_id,
            'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'private_storage_required': True, 'trusted_audit_evaluation_not_actor_input': True,
            'originals_unchanged': True, 'training_approval_changed': False,
            'attempt_status': attempt['status'], 'source_commit': attempt['source_snapshot'].get('commit'),
            'validated_transitions': report['validated_transitions'],
            'validation_source': str(validation.relative_to(root)),
            'validation_sha256': sources[validation]['sha256'],
            'source_files': len(copied), 'source_bytes': sum(v['bytes'] for v in copied.values()),
            'scope': 'reviewed collection + trace + source snapshot + public actor/replay observations',
            'excluded': ['simulator.log', 'actor runtime', 'actor_events', 'credentials',
                         'session databases', 'raw CLI reasoning', 'unreviewed files'],
            'remote_uploaded': False, 'remote_download_verified': False,
        }
        (stage / 'scope.json').write_text(json.dumps(receipt, indent=2) + '\n')
        manifest = artifacts.inventory(stage)
        require(all(manifest[name] == value for name, value in copied.items()), 'staged manifest mismatch')
        (stage / artifacts.MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n')
        artifacts.verify(stage)
        receipt.update(stage_relative_path=str(stage.relative_to(root)), manifest_entries=len(manifest),
                       manifest_sha256=artifacts.digest(stage / artifacts.MANIFEST))
        if pack:
            subprocess.run([sys.executable, str(root / 'participant/ops/artifacts.py'), 'pack',
                            str(stage), '--archive', str(archive)], check=True)
            receipt.update(archive_relative_path=str(archive.relative_to(root)), archive_bytes=archive.stat().st_size,
                           archive_sha256=artifacts.digest(archive))
        with receipt_path.open('x') as stream:
            stream.write(json.dumps(receipt, indent=2) + '\n')
        return receipt
    finally:
        os.umask(old_umask)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--bundle-id', required=True)
    parser.add_argument('--validation', type=Path)
    parser.add_argument('--pack', action='store_true')
    args = parser.parse_args()
    print(json.dumps(preserve(args.root, args.run_id, args.bundle_id, validation=args.validation, pack=args.pack)))


if __name__ == '__main__':
    main()
