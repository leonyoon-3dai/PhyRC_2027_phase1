"""Trusted score navigation and future branch boundaries; never actor input.

This index references recorded transitions. It does not serialize physics or
claim that a live/incomplete HDF5 can already be used for action replay.
"""
import json
from pathlib import Path

from participant.collection.export_report import milestone_path, public_score, public_score_events


def build_index(collection, *, run_id, source_group, acknowledged_steps,
                simulation_origin, replay_prefix_steps=0, capture_complete=False):
    collection = Path(collection)
    paths = list((collection / 'evaluation').glob('*/score_events.jsonl'))
    if len(paths) != 1:
        raise ValueError('expected one official event stream for milestone index')
    evaluation = {'evaluation_path': str(paths[0].parent.relative_to(collection))}
    events, _ = public_score_events(collection, evaluation)
    summary_path = collection / 'evaluation_summary.json'
    valid = None
    if summary_path.is_file():
        valid = public_score(json.loads(summary_path.read_text()).get('report'))['valid']
    path = milestone_path(events, valid=valid, simulation_origin=simulation_origin)
    previous = 0
    for milestone in path['award_batches']:
        boundary = milestone['transition_boundary_step']
        if not milestone['step_alignment_exact'] or not previous <= boundary <= acknowledged_steps:
            raise ValueError('score milestone is outside acknowledged recorded transitions')
        milestone['segment_start_step'] = previous
        milestone['segment_end_step_exclusive'] = boundary
        milestone['segment_simulation_s'] = (boundary - previous) / 20
        milestone['transition_image_reference'] = {
            'file': 'policy.hdf5', 'episode': 'demo_0',
            'dataset': 'next_obs/overview_rgb', 'index': boundary - 1,
            'camera': 'overview', 'available_after_capture_close': True,
        }
        milestone['continuation_recipe'] = {
            'kind': 'action_replay', 'source_run_id': run_id,
            'source_prefix_steps': boundary, 'exact_physics_restore': False,
            'requires': 'completed_capture_and_full_quality_validation',
        }
        milestone['action_source_at_boundary'] = (
            'replayed_parent' if boundary <= replay_prefix_steps else 'model_or_supervisor')
        previous = boundary
    return {
        'schema': 'phyrc-score-segment-index-v1', 'run_id': run_id,
        'source_group': source_group, 'actor_receives_index': False,
        'capture_complete': capture_complete, 'training_approval': 'unreviewed',
        'acknowledged_steps': acknowledged_steps,
        'replayed_parent_steps': min(acknowledged_steps, replay_prefix_steps),
        'new_recorded_suffix_steps': max(0, acknowledged_steps - replay_prefix_steps),
        'counting_rule': 'parent replay is separately labeled, not a new independent demonstration',
        **path,
    }


def write_index(path, **kwargs):
    result = build_index(**kwargs)
    path = Path(path)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)
    return result
