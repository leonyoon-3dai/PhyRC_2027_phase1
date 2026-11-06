"""Read-only full validation of immediate DatasetWriter captures, without Isaac.

Run ``python -m participant.collection.validate_capture CAPTURE --output REPORT``.
The report is a quality check, not a dressing-success label or training approval.
Large arrays are checked in bounded batches; hashes are streamed from disk.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

import h5py
import numpy as np

from participant.collection.boundary import CONTRACT


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_json(value):
    def reject_constant(constant):
        raise ValidationError('non-finite JSON constant: ' + constant)
    return json.loads(value, parse_constant=reject_constant)


def complete_flag(attrs):
    value = attrs.get('complete')
    require(isinstance(value, (bool, np.bool_)), 'complete attribute is missing or not boolean')
    return bool(value)


def episode_identity(name, episode, audit):
    require(isinstance(episode, h5py.Group) and isinstance(audit, h5py.Group), 'episode must be a group')
    metadata = load_json(audit.attrs.get('metadata_json', '{}'))
    require(isinstance(metadata, dict), 'episode metadata must be an object')
    source = {key: metadata[key] for key in
              ('operator_source', 'source', 'source_group', 'model_id', 'episode_id') if key in metadata}
    n = episode.attrs.get('num_samples')
    require(isinstance(n, (int, np.integer)) and not isinstance(n, (bool, np.bool_)), 'num_samples must be an integer')
    return {'episode': name, 'transitions': int(n), 'complete': complete_flag(episode.attrs),
            'source': source, 'quality_passed': False}


def expected_observations(contract):
    """Resolve packed fields from the recorded contract, checking its semantics."""
    require(contract['observations'] == CONTRACT['observations'], 'observation contract differs from supported schema')
    require(contract['timing'] == CONTRACT['timing'], 'timing contract differs from 20 Hz / 240 Hz')
    cameras = [camera['id'] for camera in contract['cameras']]
    require(cameras == CONTRACT['competition_access']['allowed_cameras'], 'unexpected camera order')
    dims = contract['default_dimensions']
    for key in ('robots', 'joints', 'cameras'):
        require(dims[key] == CONTRACT['default_dimensions'][key], 'unexpected dimension: ' + key)
    for key in ('height', 'width'):
        require(type(dims[key]) is int and 16 <= dims[key] <= 2048, 'invalid image dimension: ' + key)
    fields = {}
    for name, spec in contract['observations'].items():
        shape = tuple(dims.get(item, item) for item in spec['shape'])
        if name in ('rgb', 'depth', 'depth_valid'):
            for camera in cameras:
                fields[camera + '_' + name] = (shape[1:], np.dtype(spec['dtype']))
        else:
            fields[name] = ((math.prod(shape),), np.dtype(spec['dtype']))
    return fields


def evaluation_summary(audit):
    report = load_json(audit.attrs.get('result_json', 'null'))
    require(report is None or isinstance(report, dict), 'evaluation report must be object or null')
    valid = isinstance(report, dict) and report.get('valid') is True
    result = report.get('result') if valid else None
    require(not valid or isinstance(result, dict), 'valid evaluation has no result object')
    score = result or {}
    known = bool(valid and score.get('success_evaluated', 'dressing_complete' in score))
    require(bool(audit.attrs.get('success_known', False)) == known, 'audit success_known disagrees with report')
    success = bool(score.get('success', score.get('dressing_complete', False))) if known else None
    if known:
        require(bool(audit.attrs.get('success', False)) == success, 'audit success disagrees with report')
    return {
        'evaluated': isinstance(report, dict),
        'valid': valid if report is not None else None,
        'raw_points': score.get('raw_points') if valid else None,
        'success_known': known,
        'dressing_success': success,
        'score_status': score.get('score_status') if valid else None,
        'final_score_points_per_s': score.get('final_score') if valid else None,
        'reason': report.get('reason') if report else None,
    }


def validate_episode(name, episode, audit, fields, batch_size):
    summary = episode_identity(name, episode, audit)
    n = summary['transitions']
    require(n > 0, 'episode contains no recorded transitions')
    require(summary['complete'], 'episode is incomplete')
    for group in ('obs', 'next_obs'):
        require(group in episode and isinstance(episode[group], h5py.Group), 'missing ' + group)
        require(set(episode[group]) == set(fields), group + ' observation field set differs from public contract')
        for key, (shape, dtype) in fields.items():
            dataset = episode[group][key]
            require(isinstance(dataset, h5py.Dataset), group + '/' + key + ' is not a dataset')
            require(dataset.shape == (n, *shape), group + '/' + key + ' has incorrect shape')
            require(dataset.dtype == dtype, group + '/' + key + ' has incorrect dtype')
    for key, shape, dtype in (
        ('actions', (n, 18), np.float32), ('rewards', (n,), np.float32),
        ('dones', (n,), np.uint8), ('terminated', (n,), np.uint8), ('truncated', (n,), np.uint8),
    ):
        require(key in episode and isinstance(episode[key], h5py.Dataset), 'missing dataset ' + key)
        require(episode[key].shape == shape and episode[key].dtype == np.dtype(dtype), key + ' has incorrect shape/dtype')
    for key in ('start_tick', 'end_tick'):
        require(key in audit and audit[key].shape == (n,) and audit[key].dtype == np.dtype('int64'),
                key + ' has incorrect shape/dtype')
    require(int(audit['start_tick'][0]) == 0, 'episode-relative start_tick must begin at zero')
    for start in range(0, n, batch_size):
        end = min(n, start + batch_size)
        actions = episode['actions'][start:end]
        require(np.isfinite(actions).all() and not (abs(actions) > 1).any(), 'non-finite or out-of-range action')
        require(np.array_equal(actions, episode['next_obs/previous_action'][start:end]),
                'next_obs.previous_action differs from applied action')
        before = episode['obs/simulation_time_s'][start:end, 0]
        after = episode['next_obs/simulation_time_s'][start:end, 0]
        require(np.allclose(after - before, .05, atol=1e-7, rtol=0), 'transition duration is not 0.05 seconds')
        ticks_start, ticks_end = audit['start_tick'][start:end], audit['end_tick'][start:end]
        require(np.array_equal(ticks_end - ticks_start, np.full(end - start, 12)), 'transition does not span 12 physics ticks')
        continuity_start = max(1, start)
        require(np.array_equal(audit['start_tick'][continuity_start:end], audit['end_tick'][continuity_start-1:end-1]),
                'physics tick sequence is discontinuous')
        for key in fields:
            for group in ('obs', 'next_obs'):
                values = episode[group][key][start:end]
                require(np.isfinite(values).all(), group + '/' + key + ' has non-finite values')
                if key.endswith('_depth'):
                    require(not (values < 0).any(), group + '/' + key + ' has negative depth')
            require(np.array_equal(episode['obs'][key][continuity_start:end],
                                   episode['next_obs'][key][continuity_start-1:end-1]),
                    'observation continuity failed: ' + key)
        require(np.isfinite(episode['rewards'][start:end]).all(), 'non-finite reward')
        flags = {key: episode[key][start:end] for key in ('dones', 'terminated', 'truncated')}
        require(all(not (value > 1).any() for value in flags.values()), 'terminal flag is not binary')
        expected = (np.arange(start, end) == n - 1).astype(np.uint8)
        require(np.array_equal(flags['dones'], expected), 'dones must mark only the last transition')
        require(np.array_equal(flags['dones'], flags['terminated'] | flags['truncated']),
                'terminated/truncated flags disagree with dones')
    return {
        **summary,
        'simulation_seconds': float(episode['next_obs/simulation_time_s'][-1, 0] - episode['obs/simulation_time_s'][0, 0]),
        'termination_reason': str(episode.attrs.get('termination_reason', '')),
        'evaluation': evaluation_summary(audit),
        'quality_passed': True,
    }


def validate_capture(directory, *, batch_size=8):
    """Return a report on success or corruption, without modifying the capture."""
    if type(batch_size) is not int or not 1 <= batch_size <= 64:
        raise ValueError('batch_size must be an integer in [1,64]')
    directory = Path(directory)
    report = {'schema': 'phyrc-capture-validation-v1', 'quality_passed': False,
              'training_approval': 'unreviewed', 'scope': 'immediate_sensor_capture',
              'episodes': [], 'total_transitions': 0, 'validated_transitions': 0, 'sha256': {}, 'errors': [],
              'checks': ['manifest_sha256', 'file_episode_complete', 'public_observation_schema',
                         'all_transition_action_shape_dtype_range', 'actual_previous_action',
                         '0.05s_intervals', 'contiguous_12_physics_ticks',
                         'all_observation_continuity', 'finite_numeric_arrays', 'terminal_markers',
                         'evaluation_label_consistency']}
    try:
        manifest = load_json((directory / 'capture.json').read_text())
        require(isinstance(manifest, dict), 'capture manifest must be an object')
        require(manifest.get('raw_archive') is False, 'validator requires immediate capture with raw_archive=false')
        if manifest.get('complete') is not True:
            report['errors'].append('capture manifest is incomplete')
        checksums = manifest.get('files', manifest.get('checksums'))
        require(isinstance(checksums, dict), 'manifest lacks checksums')
        require({'policy.hdf5', 'audit.hdf5'} <= set(checksums), 'manifest lacks HDF5 checksums')
        for name, expected in checksums.items():
            require(isinstance(name, str) and Path(name).name == name and name not in ('.', '..'),
                    'checksum path must be a file basename')
            require(isinstance(expected, str) and re.fullmatch(r'[0-9a-f]{64}', expected), 'invalid SHA256 in manifest')
            actual = sha256(directory / name)
            report['sha256'][name] = actual
            if actual != expected:
                report['errors'].append('SHA256 mismatch: ' + name)
        with h5py.File(directory / 'policy.hdf5', 'r') as policy, h5py.File(directory / 'audit.hdf5', 'r') as audit:
            require(policy.attrs.get('schema') == 'phyrc-policy-dataset-v1', 'unsupported policy schema')
            require(audit.attrs.get('schema') == 'phyrc-policy-audit-v1', 'unsupported audit schema')
            for name, file in [('policy', policy), ('audit', audit)]:
                if not complete_flag(file.attrs):
                    report['errors'].append(name + ' HDF5 file is incomplete')
            fields = expected_observations(load_json(policy.attrs['contract_json']))
            require('data' in policy and isinstance(policy['data'], h5py.Group), 'missing policy data group')
            names = sorted(policy['data'])
            require(bool(names), 'capture has no episodes')
            require(set(names) == set(audit), 'policy and audit episode sets disagree')
            for name in names:
                episode = {'episode': name, 'quality_passed': False}
                try:
                    episode = episode_identity(name, policy['data'][name], audit[name])
                    episode = validate_episode(name, policy['data'][name], audit[name], fields, batch_size)
                    report['validated_transitions'] += episode['transitions']
                except (ValidationError, KeyError, ValueError, TypeError, OSError) as exc:
                    episode['error'] = str(exc)
                    report['errors'].append(name + ': ' + str(exc))
                report['episodes'].append(episode)
                report['total_transitions'] += max(0, episode.get('transitions', 0))
            if all(episode['quality_passed'] for episode in report['episodes']):
                require(int(policy['data'].attrs.get('total', -1)) == report['total_transitions'],
                        'file transition total disagrees with episode counts')
                if 'episodes' in manifest:
                    require(manifest['episodes'] == len(names), 'manifest episode count disagrees')
        report['quality_passed'] = not report['errors']
    except (ValidationError, KeyError, ValueError, TypeError, OSError) as exc:
        report['errors'].append(str(exc))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', type=Path, required=True, help='New report file; never overwrites existing evidence')
    parser.add_argument('--batch-size', type=int, default=8)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('--output already exists; choose a new report path')
    if not args.output.parent.is_dir():
        parser.error('--output parent directory must already exist')
    report = validate_capture(args.capture, batch_size=args.batch_size)
    with args.output.open('x') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'quality_passed': report['quality_passed'],
                      'total_transitions': report['total_transitions'], 'errors': report['errors']}, ensure_ascii=False))
    raise SystemExit(0 if report['quality_passed'] else 1)


if __name__ == '__main__':
    main()
