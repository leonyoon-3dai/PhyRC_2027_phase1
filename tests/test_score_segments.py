import json
from pathlib import Path
import tempfile
import unittest

from participant.collection.milestones import build_index


class ScoreSegmentTest(unittest.TestCase):
    def test_simultaneous_awards_and_replay_lineage_remain_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'evaluation/episode/score_events.jsonl'
            path.parent.mkdir(parents=True)
            rows = []
            for tick, stage, breakdown in [
                (120, 'pickup', {'pickup': 5}),
                (240, 'first_sleeve', {'pickup': 5, 'first_sleeve': 5, 'opposite_shoulder': 5}),
                (240, 'opposite_shoulder', {'pickup': 5, 'first_sleeve': 5, 'opposite_shoulder': 5}),
            ]:
                rows.append({'event': 'score_awarded', 'physics_tick': tick,
                             'evaluation_time_s': tick / 240, 'stage': stage,
                             'raw_points': sum(breakdown.values()), 'breakdown': breakdown})
            path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
            result = build_index(root, run_id='branch', source_group='family',
                                 acknowledged_steps=21, simulation_origin=1.5,
                                 replay_prefix_steps=10)
            batches = result['award_batches']
            self.assertEqual(len(batches), 2)
            self.assertEqual([b['raw_points_after'] for b in batches], [5, 15])
            self.assertEqual([b['segment_start_step'] for b in batches], [0, 10])
            self.assertEqual([b['segment_end_step_exclusive'] for b in batches], [10, 20])
            self.assertTrue(batches[1]['simultaneous'])
            self.assertEqual(batches[0]['action_source_at_boundary'], 'replayed_parent')
            self.assertEqual(batches[1]['transition_image_reference']['index'], 19)
            self.assertFalse(batches[1]['continuation_recipe']['exact_physics_restore'])
            self.assertEqual(result['new_recorded_suffix_steps'], 11)
            self.assertFalse(result['actor_receives_index'])
            with self.assertRaises(ValueError):
                build_index(root, run_id='branch', source_group='family',
                            acknowledged_steps=19, simulation_origin=1.5)


if __name__ == '__main__':
    unittest.main()
