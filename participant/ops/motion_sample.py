#!/usr/bin/env python3
"""Derive bounded, contiguous human motion clips from a closed rendered prefix.

An interrupted full export stays incomplete. Only independently validated slices
are marked complete in a new directory. No training approval or success labels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src/PhyRC_Sim'))
from Policy.dataset_reader import PolicyDataset


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', type=Path, required=True)
    p.add_argument('--recording', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    events = [json.loads(line) for line in (a.recording / 'events.jsonl').read_text().splitlines()]
    actions = [e for e in events if e['kind'] == 'policy_action']
    manifest = json.loads((a.recording / 'manifest.json').read_text())
    assert manifest['complete']
    assert digest(a.recording / 'events.jsonl') == manifest['events_sha256']
    with h5py.File(a.prefix / 'policy.hdf5', 'r') as source, h5py.File(a.prefix / 'audit.hdf5', 'r') as audit:
        demo = source['data/demo_0']
        # A signal can interrupt the last row; select only fully written rows.
        lengths = []
        demo.visititems(lambda name, obj: lengths.append(len(obj)) if isinstance(obj, h5py.Dataset) else None)
        audit['demo_0'].visititems(lambda name, obj: lengths.append(len(obj)) if isinstance(obj, h5py.Dataset) else None)
        n = min(int(demo.attrs['num_samples']), *lengths)
        applied = demo['actions'][:n].reshape(n, 2, 9)
        np.testing.assert_array_equal(applied, np.asarray([e['action'] for e in actions[:n]], np.float32))
        joint_delta = np.max(np.abs(demo['next_obs/joint_position'][:n] - demo['obs/joint_position'][:n]), axis=1)
        base_delta = np.linalg.norm((demo['next_obs/base_pose_world'][:n] - demo['obs/base_pose_world'][:n]).reshape(n, 2, 7)[:, :, :3], axis=2).max(axis=1)
        active = np.any(applied[:, :, :8] != 0, axis=(1, 2)) & ((joint_delta > 1e-5) | (base_delta > 1e-5))
        runs, start = [], None
        for i, moving in enumerate(np.r_[active, False]):
            if moving and start is None:
                start = i
            if not moving and start is not None:
                if i - start >= 2:
                    runs.append((start, min(i, start + 20)))
                start = None
        runs = runs[:3]
        if not runs:
            raise ValueError('No two-step commanded and measured motion in rendered prefix')
        selected = {i for lo, hi in runs for i in range(lo, hi + 1)}
        # Verify source public state against checksummed original archive frames.
        matched = set()
        for chunk in manifest['chunks']:
            path = a.recording / chunk['file']
            with np.load(path, allow_pickle=False) as z:
                headers = json.loads(str(z['_headers']))
                candidates = [(i, h) for i, h in enumerate(headers) if h['kind'] == 'policy_observation' and h['tick'] // 12 in selected]
                if not candidates:
                    continue
                assert digest(path) == chunk['sha256']
                stacked = set(json.loads(str(z['_stacked'])))
                def value(i, key):
                    return z['stack/' + key][i] if key in stacked else z[f'f{i:04d}/' + key]
                for i, header in candidates:
                    frame = int(value(i, 'policy_frame'))
                    assert int(value(i, 'policy_episode')) == 0
                    for group, row in [('obs', frame), ('next_obs', frame - 1)]:
                        if row < 0 or row >= n:
                            continue
                        for key in demo[group]:
                            if key in json.loads(source.attrs['contract_json'])['observations'] and key not in ('rgb', 'depth', 'depth_valid'):
                                np.testing.assert_array_equal(demo[group][key][row], value(i, 'policy_obs/' + key).reshape(-1))
                    matched.add(frame)
        assert matched == selected, (matched, selected)
        a.output.mkdir(parents=True, exist_ok=False)
        provenance = {'source': 'human', 'purpose': 'teleoperation_format_test', 'review': 'format_only_not_for_sft',
                      'source_run': a.recording.name, 'raw_manifest_sha256': digest(a.recording / 'manifest.json'),
                      'rendered_prefix_sha256': digest(a.prefix / 'policy.hdf5'), 'source_prefix_complete': bool(source.attrs['complete']),
                      'selection': 'nonzero movement command AND (public joint delta >1e-5 rad/m OR base translation >1e-5 m); contiguous runs, at most 3 clips of 20 transitions',
                      'clips': [{'source_episode': 'demo_0', 'start_index': lo, 'end_index_exclusive': hi} for lo, hi in runs],
                      'success_known': False, 'physics_resimulated': False}
        with h5py.File(a.output / 'policy.hdf5', 'x') as target, h5py.File(a.output / 'audit.hdf5', 'x') as target_audit:
            target.attrs.update(dict(source.attrs)); target.attrs['complete'] = False
            target.attrs['provenance_json'] = json.dumps(provenance)
            data = target.create_group('data'); data.attrs.update(dict(source['data'].attrs)); data.attrs['total'] = sum(hi-lo for lo, hi in runs)
            target_audit.attrs.update(schema='phyrc-policy-audit-v1', complete=False, metadata_json=json.dumps(provenance))
            for j, (lo, hi) in enumerate(runs):
                dst = data.create_group(f'demo_{j}'); dst.attrs.update(num_samples=hi-lo, complete=True, termination_reason='derived_motion_clip_boundary')
                adst = target_audit.create_group(f'demo_{j}'); adst.attrs.update(metadata_json=json.dumps(provenance['clips'][j]), result_json='null', success_known=False, success=False)
                for src, dest in [(demo, dst), (audit['demo_0'], adst)]:
                    def copy(name, obj):
                        if isinstance(obj, h5py.Group):
                            dest.require_group(name)
                        else:
                            dest.create_dataset(name, data=obj[lo:hi], compression='lzf')
                    src.visititems(copy)
                for name in ('dones', 'terminated', 'truncated'):
                    dst[name][:] = 0
                dst['dones'][-1] = 1; dst['truncated'][-1] = 1
                np.testing.assert_array_equal(dst['next_obs/previous_action'][:], dst['actions'][:])
                for key in dst['obs']:
                    np.testing.assert_array_equal(dst['obs'][key][1:], dst['next_obs'][key][:-1])
                np.testing.assert_allclose(dst['next_obs/simulation_time_s'][:] - dst['obs/simulation_time_s'][:], .05, atol=1e-7, rtol=0)
                for group in ('obs', 'next_obs'):
                    for camera in json.loads(source.attrs['contract_json'])['cameras']:
                        key = camera['id']; rgb = dst[group][key+'_rgb'][:]; depth = dst[group][key+'_depth'][:]; valid = dst[group][key+'_depth_valid'][:]
                        assert rgb.dtype == np.uint8 and all(np.ptp(frame)>0 for frame in rgb)
                        assert depth.dtype == np.float32 and np.isfinite(depth).all()
                        assert valid.dtype == bool and all(frame.any() for frame in valid)
                        assert np.all(depth[~valid] == 0)
                assert np.all(adst['end_tick'][:] - adst['start_tick'][:] == 12)
            target.attrs['complete'] = True; target_audit.attrs['complete'] = True
        dataset = PolicyDataset(a.output / 'policy.hdf5')
        count = len(dataset); dataset.close()
        report = dict(provenance, verified=True, episodes=len(runs), transitions=count, simulation_s=count*.05,
                      checks=['original raw public states and journal actions', 'five-camera RGB-D validity', 'obs/action/next_obs continuity', '20 Hz timing', 'official PolicyDataset load'])
        (a.output / 'sample-report.json').write_text(json.dumps(report, indent=2)+'\n')
        (a.output / 'capture.json').write_text(json.dumps({'status':'ready','complete':True,'derived_sample':True,'samples':count,'source':'human','purpose':'teleoperation_format_test'},indent=2)+'\n')
        print(json.dumps(report))


if __name__ == '__main__':
    main()
