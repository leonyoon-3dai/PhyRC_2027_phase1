"""Named action encoding checks; no simulator, model or action dispatch."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

import numpy as np

from participant.research.action_encoding import (
    CHANNELS, OFFICIAL_FIELDS, ROBOT_IDS, array_to_named, named_json_to_array, named_to_array)


def neutral():
    return {'robots': [{'robot_id': name, 'action': {key: 0 for key in CHANNELS}}
                       for name in ROBOT_IDS]}


class ActionEncodingTest(unittest.TestCase):
    def test_alias_order_matches_official_public_contract(self):
        root = Path(__file__).resolve().parents[1]
        action = json.loads((root/'config/policy_interface.json').read_text())['action']
        self.assertEqual(tuple(field['name'] for field in action['fields']), OFFICIAL_FIELDS)
        self.assertEqual(action['shape'], ['robots', 9])
        self.assertEqual(action['dtype'], 'float32')
        self.assertEqual(action['range'], [-1, 1])
        self.assertEqual(action['robot_order'], ['/World/Stretch4', '/World/Stretch4_2'])

    def test_each_named_channel_occupies_only_its_exact_column_and_robot(self):
        for robot in range(2):
            for column, name in enumerate(CHANNELS):
                with self.subTest(robot=robot, channel=name):
                    payload = neutral(); payload['robots'][robot]['action'][name] = .5
                    actual = named_to_array(payload)
                    expected = np.zeros((2, 9), np.float32); expected[robot, column] = .5
                    np.testing.assert_array_equal(actual, expected)
                    self.assertEqual(actual.dtype, np.float32)

    def test_float32_roundtrip_and_channel_key_order_do_not_change_commands(self):
        original = np.linspace(-1, 1, 18, dtype=np.float32).reshape(2, 9)
        named = array_to_named(original)
        for robot in named['robots']:
            robot['action'] = dict(reversed(list(robot['action'].items())))
        before = deepcopy(named)
        np.testing.assert_array_equal(named_json_to_array(json.dumps(named)), original)
        self.assertEqual(named, before)
        changed = named_to_array(named); changed[0, 0] = 0
        self.assertEqual(original[0, 0], -1)

    def test_known_decision_27_exposes_roll_plus_one_without_correction(self):
        original = [[-.65, 0, 0, 0, 0, 0, 0, 0, 1],
                    [-.65, 0, 0, 0, 0, 0, 0, 1, 0]]
        before = deepcopy(original)
        named = array_to_named(original)
        self.assertEqual(named['robots'][0]['action']['gripper'], 1)
        self.assertEqual(named['robots'][1]['action']['base_forward'], -.65)
        self.assertEqual(named['robots'][1]['action']['wrist_roll'], 1)
        self.assertEqual(named['robots'][1]['action']['gripper'], 0)
        np.testing.assert_array_equal(named_to_array(named), np.array(original, np.float32))
        self.assertEqual(original, before)

    def test_left_ccw_and_gripper_values_are_not_rescaled_or_reinterpreted(self):
        payload = neutral(); action = payload['robots'][1]['action']
        action.update(base_left=1, base_CCW_yaw=-1, gripper=.5)
        result = named_to_array(payload)
        self.assertEqual(result[1, 1], 1)
        self.assertEqual(result[1, 2], -1)
        self.assertEqual(result[1, 8], .5)
        self.assertEqual(array_to_named(result)['robots'][0]['action']['gripper'], 0)

    def test_reversed_duplicate_missing_and_unknown_robots_are_rejected(self):
        bad = []
        p = neutral(); p['robots'].reverse(); bad.append(p)
        p = neutral(); p['robots'][1]['robot_id'] = 'robot_0'; bad.append(p)
        p = neutral(); p['robots'].pop(); bad.append(p)
        p = neutral(); p['robots'][0]['robot_id'] = 'robot0'; bad.append(p)
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                named_to_array(payload)

    def test_missing_extra_and_wrong_case_keys_are_rejected_at_each_level(self):
        bad = []
        p = neutral(); p['reason'] = 'must not infer semantics'; bad.append(p)
        p = neutral(); p['robots'][0]['extra'] = 1; bad.append(p)
        p = neutral(); del p['robots'][0]['action']['wrist_roll']; bad.append(p)
        p = neutral(); p['robots'][0]['action']['wristRoll'] = p['robots'][0]['action'].pop('wrist_roll'); bad.append(p)
        p = neutral(); p['robots'][0]['action']['unknown'] = 0; bad.append(p)
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                named_to_array(payload)

    def test_non_numbers_bool_nonfinite_and_out_of_range_are_rejected_both_ways(self):
        for value in (True, False, None, '0', {}, [], float('nan'), float('inf'),
                      -float('inf'), 1.00001, -1.00001, 10**1000):
            with self.subTest(value=repr(value)):
                payload = neutral(); payload['robots'][0]['action']['wrist_roll'] = value
                with self.assertRaises(ValueError): named_to_array(payload)
                array = [[0]*9 for _ in range(2)]; array[0][7] = value
                with self.assertRaises(ValueError): array_to_named(array)

    def test_wrong_array_shape_dtype_and_mixed_boolean_are_rejected(self):
        for value in ([0]*18, [[0]*9], [[0]*8, [0]*9], np.zeros((2, 9), np.float64),
                      np.zeros((2, 9), bool), np.zeros((18,), np.float32)):
            with self.subTest(shape=getattr(value, 'shape', None)), self.assertRaises(ValueError):
                array_to_named(value)
        mixed = [[0.]*9 for _ in range(2)]; mixed[1][8] = True
        with self.assertRaises(ValueError): array_to_named(mixed)

    def test_raw_json_duplicate_keys_and_nonstandard_constants_are_rejected(self):
        text = json.dumps(neutral())
        for malformed in (text.replace('"wrist_roll": 0', '"wrist_roll": 0, "wrist_roll": 1', 1),
                          text.replace('"gripper": 0', '"gripper": NaN', 1),
                          text.replace('"gripper": 0', '"gripper": Infinity', 1)):
            with self.subTest(text=malformed), self.assertRaises(ValueError):
                named_json_to_array(malformed)


if __name__ == '__main__':
    unittest.main()
