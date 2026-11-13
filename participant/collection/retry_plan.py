"""Validate an explicit suffix-retry boundary on CPU; never restore physics.

Run after capture close and full validate_capture. The result is a trusted review
artifact, not an actor prompt, executable job, or independent training example.
It does not start a simulator, mutate the source, or grant training approval.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from participant.collection.continuation import load_replay_prefix, RUN_ID


def build_plan(root, source_run_id, steps, *, reason):
    """Verify the entire closed source before recording a selected [0, steps)."""
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        raise ValueError('A concise review reason (1..2000 characters) is required')
    if type(steps) is not int or steps < 1:
        raise ValueError('An explicit positive exclusive transition boundary is required')
    prefix = load_replay_prefix(root, source_run_id, steps=steps)
    lineage = prefix.public_lineage
    return {
        'schema': 'phyrc-suffix-retry-plan-v1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'source_verified_execution_not_yet_tested',
        'actor_receives_plan': False,
        'reason': reason.strip(),
        'lineage': lineage,
        'boundary': {
            'exclusive_step': steps,
            'source_observation_file': f'output/collections/{source_run_id}/policy.hdf5',
            'source_observation_group': 'data/demo_0/next_obs',
            'source_observation_index': steps - 1,
            'source_public_simulation_time_s': float(prefix.final_public_state['simulation_time_s']),
            'source_remaining_steps': lineage['source_steps'] - steps,
        },
        'continuation_arguments': [
            '--replay-prefix-run', source_run_id,
            '--replay-prefix-steps', str(steps),
            '--parent-attempt', source_run_id,
            '--source-group', lineage['source_group'],
            '--retry-reason', reason.strip(),
        ],
        'execution_requirements': [
            'Choose a new run ID, an implemented strategy, and an explicit decision/step budget.',
            'The max-steps budget includes the replay prefix, new actions, and settling.',
            'Choose review-points above the retained prefix score to allow suffix actions.',
            'Recheck current cloth support and opening from freshly replayed public observations.',
            'Replay every prefix action in a fresh environment; no prefix actor calls are needed.',
            'Re-evaluate all awards in the new episode; old awards are not copied.',
            'Close, validate, visually review, and privately preserve the new capture separately.',
        ],
        'limitations': {
            'bitwise_physics_restored': False,
            'new_score_guaranteed': False,
            'independent_demonstration': False,
            'training_approval': 'unreviewed',
            'score_is_not_success': True,
            'source_observations_are_review_only': True,
        },
    }


def write_plan(root, plan_id, plan):
    """Write an immutable review artifact outside collection/trace originals."""
    root = Path(root).resolve()
    if not isinstance(plan_id, str) or not RUN_ID.fullmatch(plan_id):
        raise ValueError('Invalid plan ID')
    parent = root / 'output/retry-plans'
    for node in (parent, parent.parent):
        if node.is_symlink():
            raise ValueError('Symlink output directory rejected')
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = parent / (plan_id + '.json')
    # Exclusive creation also rejects a pre-existing symlink or plan.
    with path.open('x') as stream:
        stream.write(json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--run-id', required=True, help='Closed, fully validated direct parent')
    parser.add_argument('--steps', type=int, required=True, help='Exclusive prefix boundary N; source image is next_obs[N-1]')
    parser.add_argument('--reason', required=True, help='One intended suffix change and its visual review basis')
    parser.add_argument('--plan-id', required=True, help='New immutable artifact name under output/retry-plans/')
    args = parser.parse_args()
    plan = build_plan(args.root, args.run_id, args.steps, reason=args.reason)
    path = write_plan(args.root, args.plan_id, plan)
    print(json.dumps({'plan': str(path), 'parent': args.run_id, 'replay_steps': args.steps,
                      'source_group': plan['lineage']['source_group'],
                      'physics_restored': False, 'simulator_started': False}))


if __name__ == '__main__':
    main()
