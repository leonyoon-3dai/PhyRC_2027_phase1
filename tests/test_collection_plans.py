"""CPU checks for complete validation before a grouped action is dispatched."""
from copy import deepcopy
import unittest

from participant.collection.plans import plan_schema, validate_plan


def decision(tool='act', steps=2):
    return {'tool': tool, 'action': [[0.0] * 9 for _ in range(2)],
            'steps': steps, 'stage': 'preparation',
            'visual_assessment': 'uncertain', 'reason': 'Bounded test motion.'}


class PlanTest(unittest.TestCase):
    def test_small_move_stop_finish_has_three_recordable_steps(self):
        first = decision()
        for row in first['action']:
            row[3], row[8] = .03, -1
        plan = {'decisions': [first, decision('stop', 1), decision('finish_episode', 1)]}
        actions = validate_plan(plan, wiring=True, max_total_steps=3)
        self.assertEqual(len(actions), 3)
        self.assertEqual(actions[0].shape, (2, 9))
        self.assertFalse(actions[1].any())

    def test_invalid_suffix_never_produces_an_executable_prefix(self):
        base = {'decisions': [decision(), decision()]}
        for value in (float('nan'), 2, True, '0'):
            invalid = deepcopy(base)
            invalid['decisions'][1]['action'][0][0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_plan(invalid)

    def test_group_limits_finish_order_and_unrecognized_branches(self):
        invalid = [
            {'decisions': []},
            {'decisions': [decision()] * 4},
            {'decisions': [decision('finish_episode', 1), decision()]},
            {'decisions': [decision()], 'if_grasped': True},
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_plan(value)
        with self.assertRaises(ValueError):
            validate_plan({'decisions': [decision(steps=20)] * 3}, max_total_steps=40)
        for count in (True, 0, 4):
            with self.subTest(count=count), self.assertRaises(ValueError):
                plan_schema(count)

    def test_wiring_limit_applies_to_every_segment(self):
        large = decision()
        large['action'][1][3] = .06
        with self.assertRaises(ValueError):
            validate_plan({'decisions': [decision(), large]}, wiring=True)
        with self.assertRaises(ValueError):
            validate_plan({'decisions': [decision(steps=3)]}, wiring=True)


if __name__ == '__main__':
    unittest.main()
