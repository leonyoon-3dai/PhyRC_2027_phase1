"""Load a verified action prefix for trusted replay, never a physics checkpoint.

This module reads only a CLOSED public policy dataset and selected metadata.
It does not read audit HDF5, geometry, actor sessions, or raw simulator state.
The reset seed remains in trusted_metadata, which MUST NOT be sent to an actor
or copied into a public manifest. Replay must produce new observations/labels.
"""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re

import h5py
import numpy as np


RUN_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}')
SHA256 = re.compile(r'[0-9a-f]{64}')
STATE_FIELDS = ('joint_position', 'base_pose_world', 'controller_target',
                'gripper_close_command', 'previous_action', 'simulation_time_s')


@dataclass(frozen=True)
class ReplayPrefix:
    actions: np.ndarray = field(repr=False)
    trusted_metadata: dict = field(repr=False)
    initial_public_state: dict = field(repr=False)
    final_public_state: dict = field(repr=False)
    public_lineage: dict


@dataclass(frozen=True)
class ReplayChunk:
    action: np.ndarray = field(repr=False)
    steps: int
    start_step: int
    end_step: int


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _inside(root, relative):
    relative = Path(relative)
    _require(not relative.is_absolute() and '..' not in relative.parts,
             'Source reference must be relative and inside its root')
    path = root / relative
    _require(not any(p.is_symlink() for p in [path, *path.parents] if p != root.parent),
             'Symlink source reference rejected')
    _require(path.resolve().is_relative_to(root), 'Source reference escapes its root')
    return path


def _json(path):
    _require(path.is_file() and path.stat().st_size <= 2 * 1024 * 1024,
             'Missing or oversized source metadata')
    value = json.loads(path.read_text())
    _require(isinstance(value, dict), 'Expected metadata object')
    return value


def _hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _digest(value):
    if isinstance(value, dict):
        value = value.get('sha256')
    _require(isinstance(value, str) and SHA256.fullmatch(value), 'Missing policy SHA256')
    return value


def _positive(value):
    return type(value) is int and value > 0


def _state(episode, group, index, contract):
    result = {}
    dimensions = contract['default_dimensions']
    for name in STATE_FIELDS:
        spec = contract['observations'][name]
        shape = tuple(dimensions.get(v, v) for v in spec['shape'])
        value = np.asarray(episode[group][name][index])
        _require(value.dtype == np.dtype(spec['dtype']) and value.size == int(np.prod(shape)),
                 'Public state shape or dtype mismatch')
        _require(np.isfinite(value).all(), 'Nonfinite public state')
        value = value.reshape(shape).copy()
        value.flags.writeable = False
        result[name] = value
    return result


def _seed_source(root, capture, run_metadata, source_group):
    """Select the seed without forwarding the surrounding evaluation metadata."""
    has_run_seed = 'episode_seed' in run_metadata
    if has_run_seed:
        path = capture / 'run_metadata.json'
        seed = run_metadata['episode_seed']
        source_field = 'episode_seed'
    summary_path = _inside(capture, 'evaluation_summary.json')
    if not has_run_seed or summary_path.exists():
        summary = _json(summary_path)
        reference = summary.get('evaluation_path')
        _require(isinstance(reference, str) and Path(reference).parts[:1] == ('evaluation',),
                 'Missing trusted evaluation reference')
        evaluation_path = _inside(capture, Path(reference) / 'result.json')
        report = _json(evaluation_path)
        metadata = report.get('metadata', {})
        summary_metadata = summary.get('report', {}).get('metadata', {})
        _require(metadata.get('source_group') == source_group
                 and summary_metadata.get('source_group') == source_group,
                 'Seed source group mismatch')
        evaluation_seed = metadata.get('episode_seed')
        _require(type(evaluation_seed) is int and evaluation_seed == summary_metadata.get('episode_seed'),
                 'Seed source disagrees with summary')
        if has_run_seed:
            _require(seed == evaluation_seed, 'Run seed disagrees with evaluation source')
        else:
            path, seed, source_field = evaluation_path, evaluation_seed, 'metadata.episode_seed'
    _require(type(seed) is int and 0 <= seed < 2**63, 'Missing or invalid trusted reset seed')
    return seed, {'relative_file': str(path.relative_to(root)), 'json_field': source_field,
                  'sha256': _hash(path)}


def load_replay_prefix(root, source_run_id, steps=None):
    """Read a fully checked, closed one-episode source without modifying it.

    ``steps`` is an exclusive prefix boundary; None selects all recorded actions,
    including any supervisor cleanup transition. Full-source QC is mandatory
    even when only an earlier prefix is selected. Call after other GPU benchmarks
    finish: the complete policy file is hashed before HDF5 is opened read-only.
    """
    root = Path(root).resolve()
    _require(isinstance(source_run_id, str) and RUN_ID.fullmatch(source_run_id), 'Invalid source run ID')
    capture = _inside(root, Path('output/collections') / source_run_id)
    trace = _inside(root, Path('output/operator-traces') / source_run_id)
    attempt = _json(_inside(trace, 'attempt.json'))
    manifest_path = _inside(capture, 'capture.json')
    validation_path = _inside(capture, 'validation.json')
    manifest, validation = _json(manifest_path), _json(validation_path)
    run_metadata = _json(_inside(capture, 'run_metadata.json'))
    _require(attempt.get('run_id') == source_run_id and attempt.get('finished') is True
             and attempt.get('capture_complete') is True
             and attempt.get('status') in {'completed', 'review_ready', 'failed', 'interrupted'},
             'Source attempt has not finished with a closed capture')
    _require(manifest.get('complete') is True, 'Source capture is incomplete')
    _require(validation.get('quality_passed') is True and validation.get('errors') == [],
             'Source full quality validation did not pass')
    total = validation.get('total_transitions')
    _require(_positive(total) and validation.get('validated_transitions') == total,
             'Source validation did not cover every transition')
    _require(manifest.get('steps') == total and attempt.get('simulation_steps') == total,
             'Source transition totals disagree')
    episodes = validation.get('episodes', [])
    _require(len(episodes) == 1 and episodes[0].get('quality_passed') is True
             and episodes[0].get('complete') is True and episodes[0].get('transitions') == total,
             'Expected one complete fully validated source episode')
    name = episodes[0].get('episode')
    _require(name == 'demo_0', 'Unsupported source episode name')
    group = attempt.get('source_group')
    _require(isinstance(group, str) and RUN_ID.fullmatch(group)
             and run_metadata.get('source_group') == group
             and episodes[0].get('source', {}).get('source_group') == group,
             'Source group metadata mismatch')
    selected = total if steps is None else steps
    _require(_positive(selected) and selected <= total, 'Prefix must contain 1..source_steps transitions')
    expected = _digest(manifest.get('files', manifest.get('checksums', {})).get('policy.hdf5'))
    _require(_digest(validation.get('sha256', {}).get('policy.hdf5')) == expected,
             'Validation policy checksum does not match capture')
    policy_path = _inside(capture, 'policy.hdf5')
    before = policy_path.stat()
    _require(_hash(policy_path) == expected, 'Source policy checksum mismatch')
    seed, seed_source = _seed_source(root, capture, run_metadata, group)
    with h5py.File(policy_path, 'r') as policy:
        _require(bool(policy.attrs.get('complete', False)), 'Source policy is incomplete')
        _require(list(policy['data']) == [name] and int(policy['data'].attrs.get('total', -1)) == total,
                 'Source policy episode or total mismatch')
        episode = policy['data'][name]
        _require(bool(episode.attrs.get('complete', False))
                 and int(episode.attrs.get('num_samples', -1)) == total, 'Source episode is incomplete')
        dataset = episode['actions']
        _require(dataset.shape == (total, 18) and dataset.dtype == np.float32,
                 'Source actions must be float32 (T,18)')
        actions = np.asarray(dataset[:selected]).reshape(selected, 2, 9).copy()
        _require(np.isfinite(actions).all() and np.all(np.abs(actions) <= 1), 'Invalid source action values')
        contract = json.loads(policy.attrs['contract_json'])
        initial = _state(episode, 'obs', 0, contract)
        final = _state(episode, 'next_obs', selected - 1, contract)
        _require(np.array_equal(final['previous_action'], actions[-1]), 'Source final previous action mismatch')
        _require(np.isclose(float(final['simulation_time_s']) - float(initial['simulation_time_s']),
                            selected * .05, rtol=0, atol=selected * 1e-7), 'Source prefix clock mismatch')
    after = policy_path.stat()
    _require((before.st_ino, before.st_size, before.st_mtime_ns)
             == (after.st_ino, after.st_size, after.st_mtime_ns), 'Source policy changed while loading')
    actions.flags.writeable = False
    lineage = {'resume_kind': 'action_replay', 'parent_attempt': source_run_id,
               'source_group': group, 'source_episode': name,
               'source_policy_sha256': expected, 'source_capture_sha256': _hash(manifest_path),
               'source_validation_sha256': _hash(validation_path),
               'source_steps': total, 'replay_steps': selected,
               'source_start_step': 0, 'source_end_step_exclusive': selected,
               'bitwise_physics_restored': False, 'fresh_actor': True,
               'replay_validation': 'source_verified_execution_not_yet_tested'}
    trusted = {**lineage, 'source_run_id': source_run_id, 'steps': selected,
               'root': root, 'source_capture': capture, 'reset_seed': seed, 'seed_source': seed_source}
    return ReplayPrefix(actions, trusted, initial, final, lineage)


def iter_action_chunks(actions, max_steps=20):
    """Group only identical consecutive actions, never average or skip a step."""
    _require(type(max_steps) is int and 1 <= max_steps <= 20, 'Chunk size must be 1..20')
    values = np.asarray(actions)
    _require(values.ndim == 3 and values.shape[1:] == (2, 9) and values.dtype == np.float32
             and np.isfinite(values).all() and np.all(np.abs(values) <= 1),
             'Replay actions must be finite bounded float32 (T,2,9)')
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and end - start < max_steps and values[end].tobytes() == values[start].tobytes():
            end += 1
        value = values[start].copy()
        value.flags.writeable = False
        yield ReplayChunk(value, end - start, start, end)
        start = end
