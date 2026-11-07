"""Named-output mapping and orchestration tests, with no model or physics."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest import mock

import numpy as np

from participant.collection import codex_client as client, named_actions as named
from participant.collection import codex_actor, export_report as exporter
from participant.collection.boundary import CONTRACT
import test_depth_query as query


ROOT = Path(__file__).resolve().parents[1]
BASE = '5767a4829fc08d8a0ffdeb1a5037f300a0d2111d'
baseline = ModuleType('named_action_baseline')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(subprocess.check_output(['git', 'show', BASE + ':participant/collection/codex_client.py'],
    cwd=ROOT, text=True), baseline.__file__, 'exec'), baseline.__dict__)
# An independent explicit index oracle, not derived from the candidate mapper.
CHANNELS = ('base_forward', 'base_left', 'base_CCW_yaw', 'lift', 'arm_extension',
            'wrist_yaw', 'wrist_pitch', 'wrist_roll', 'gripper')


def encode(value, _index=0, _schema=None):
    result = deepcopy(value)
    result['action'] = {f'robot_{i}': dict(zip(CHANNELS, row))
                        for i, row in enumerate(value['action'])}
    return result


class NamedActionsTest(unittest.TestCase):
    def run_client(self, **kwargs):
        return query.QueryTests().run_client(extra_flags=['--named-actions'],
            response_transform=kwargs.pop('response_transform', encode), **kwargs)

    def test_each_of_18_channels_and_both_signs_reaches_only_its_official_cell(self):
        expected_fields = ['base_forward_velocity', 'base_left_velocity', 'base_yaw_velocity',
            'lift_velocity', 'arm_extension_velocity', 'wrist_yaw_velocity',
            'wrist_pitch_velocity', 'wrist_roll_velocity', 'gripper_command']
        self.assertEqual([field['name'] for field in CONTRACT['action']['fields']], expected_fields)
        for robot in range(2):
            for channel in range(9):
                for sign in (-1, 1):
                    with self.subTest(robot=robot, channel=channel, sign=sign):
                        value = query.action(); value.update(tool='act', steps=2)
                        value['action'][robot][channel] = sign
                        # Key insertion order must not affect robot/channel order.
                        raw = encode(value)
                        raw['action'] = {r: dict(reversed(list(channels.items())))
                            for r, channels in reversed(list(raw['action'].items()))}
                        result = named.normalize_result({'decision': raw})
                        actual = client.validate_decision(result['decision'])
                        np.testing.assert_array_equal(actual, np.asarray(value['action'], np.float32))
                        self.assertEqual(actual.dtype, np.float32)
                        self.assertEqual(result['named_action']['raw_action'], raw['action'])
                        self.assertEqual(encode(result['decision'])['action'], raw['action'])

    def test_advance_and_close_does_not_populate_roll_but_intentional_roll_is_available(self):
        value = encode(query.action()); value['tool'] = 'act'
        value['action']['robot_1'].update(base_forward=.35, gripper=1)
        result = named.normalize_result({'decision': value})
        self.assertEqual(result['decision']['action'][1], [.35, 0, 0, 0, 0, 0, 0, 0, 1])
        value['action']['robot_1']['wrist_roll'] = 1
        actual = client.validate_decision(named.normalize_result({'decision': value})['decision'])
        self.assertEqual(actual[1, 7], 1)

    def test_missing_unknown_wrong_type_and_out_of_range_rejected_before_pack(self):
        raw = encode(query.action())['action']
        mutations = []
        for key in ('robot_0', 'robot_1'):
            missing = deepcopy(raw); del missing[key]; mutations.append(missing)
        for channel in CHANNELS:
            missing = deepcopy(raw); del missing['robot_0'][channel]; mutations.append(missing)
        extra_robot = deepcopy(raw); extra_robot['robot_2'] = deepcopy(raw['robot_0']); mutations.append(extra_robot)
        extra_name = deepcopy(raw); extra_name['robot_1']['roll'] = 0; mutations.append(extra_name)
        for value in (True, None, '0', float('nan'), float('inf'), -float('inf'), 10**1000, 1.000000001, -1.000000001):
            bad = deepcopy(raw); bad['robot_1']['wrist_roll'] = value; mutations.append(bad)
        mutations += [[[0]*9, [0]*9], [], None]
        for bad in mutations:
            with self.subTest(value=repr(bad)), self.assertRaises(ValueError):
                named.pack(bad)

    def test_exec_parser_rejects_duplicate_robot_channel_and_outer_fields(self):
        serialized = json.dumps(encode(query.action()))
        for malformed in (serialized.replace('"wrist_roll": 0.0', '"wrist_roll": 0.0, "wrist_roll": 1'),
                          serialized.replace('"robot_0": {', '"robot_0": {}, "robot_0": {'),
                          serialized.replace('"action": {', '"action": {}, "action": {')):
            with self.subTest(malformed=malformed), self.assertRaisesRegex(ValueError, 'duplicate'):
                codex_actor._json_loads(malformed)

    def test_stop_finish_and_query_placeholder_keep_zero_and_step_rules(self):
        from participant.collection.depth_query import route_initial
        for tool in ('stop', 'finish_episode'):
            good = encode(query.action()); good['tool'] = tool
            client.validate_decision(named.normalize_result({'decision': good})['decision'])
            for channel in CHANNELS:
                bad = deepcopy(good); bad['action']['robot_0'][channel] = .1
                with self.subTest(tool=tool, channel=channel), self.assertRaises(ValueError):
                    client.validate_decision(named.normalize_result({'decision': bad})['decision'])
            good['steps'] = 2
            with self.assertRaises(ValueError):
                client.validate_decision(named.normalize_result({'decision': good})['decision'])
        placeholder = encode(query.action()); placeholder.update(tool='depth_query', depth_query={})
        canonical = named.normalize_result({'decision': placeholder})['decision']
        self.assertEqual(route_initial(canonical, client.SCHEMA, client.validate_decision), (None, {}))
        placeholder['action']['robot_1']['gripper'] = 1
        with self.assertRaises(ValueError):
            route_initial(named.normalize_result({'decision': placeholder})['decision'],
                          client.SCHEMA, client.validate_decision)

    def test_default_off_matches_fixed_public_oracle_with_and_without_query(self):
        for enabled in (False, True):
            for strategy in ('general', 'coordinated', 'coordinated-sleeve',
                    'coordinated-hem-route', 'coordinated-opening-first',
                    'coordinated-support-diagnostic', 'coordinated-regrasp-hem',
                    'coordinated-support-guide', 'coordinated-neckline-first'):
                with self.subTest(enabled=enabled, strategy=strategy):
                    flags = dict(enabled=enabled, strategy=strategy, history=True, depth_panel=True)
                    old = query.QueryTests().run_client(module=baseline, **flags)
                    new = query.QueryTests().run_client(**flags)
                    self.assertIsNone(old['error']); self.assertIsNone(new['error'])
                    for key in ('calls', 'requests', 'order', 'commands'):
                        self.assertEqual(old[key], new[key])
                    self.assertNotIn('named_actions', new['attempt'])
                    self.assertTrue(all('named_action' not in event for event in new['events']))

    def test_query_keeps_frozen_16_images_named_followup_and_zero_intermediate_dispatch(self):
        result = self.run_client(strategy='coordinated-neckline-first', history=True, depth_panel=True)
        self.assertIsNone(result['error'])
        self.assertEqual(result['order'][-3:], ['call0', 'call1', 'finish_episode'])
        first, second = result['calls']
        self.assertEqual(len(first['images']), 16)
        self.assertEqual(first['images'], second['images'])
        self.assertEqual(second['schema'], named.response_schema(client.SCHEMA))
        self.assertEqual(first['schema']['properties']['action'], second['schema']['properties']['action'])
        self.assertTrue(second['prompt'].startswith(first['prompt']))
        self.assertNotIn('all-zero 2x9 action', first['prompt'])
        self.assertNotIn(named.POSITIONAL_DESCRIPTION, first['prompt'])
        self.assertEqual(result['attempt']['simulation_steps'], 3)  # fake replay only
        self.assertEqual(result['attempt']['named_actions'], named.MAPPING)
        events = [e for e in result['events'] if e['type'] == 'model_call']
        self.assertEqual(events[0]['frozen_observation_id'], events[1]['frozen_observation_id'])
        self.assertEqual(events[0]['observation_simulation_time_s'], events[1]['observation_simulation_time_s'])
        for event in events:
            self.assertEqual(event['named_action']['mapping_sha256'], named.MAPPING_SHA256)
        public = [e for e in result['public'] if e['type'] in ('model_call', 'decision')]
        self.assertEqual(len(public), 3)
        self.assertTrue(all('named_action' in event for event in public))
        for call in result['calls']:
            self.assertNotIn('NEVER_ACTOR', call['prompt'])

    def test_direct_action_query_or_not_records_and_dispatches_same_packed_values(self):
        def move(value, index, schema):
            if index == 0:
                value.update(tool='act', steps=2)
                value['action'][1][0], value['action'][1][8] = .35, 1
            return encode(value)
        for enabled in (False, True):
            result = self.run_client(enabled=enabled, scenario='direct', response_transform=move,
                                     strategy='coordinated-support-guide')
            self.assertIsNone(result['error'])
            dispatches = [v for tool, v in result['requests'] if tool == 'act']
            self.assertEqual(len(dispatches), 1)
            self.assertEqual(dispatches[0]['action'][1][7], 0)
            self.assertEqual(dispatches[0]['action'][1][8], 1)
            decision = next(e for e in result['events'] if e['type'] == 'decision')
            self.assertEqual(named.pack(decision['named_action']['raw_action']), decision['decision']['action'])

    def test_bad_named_response_cannot_dispatch_act_and_query_failure_has_no_followup(self):
        def malformed(value, index, schema):
            value = encode(value); del value['action']['robot_1']['wrist_pitch']; return value
        for enabled in (False, True):
            result = self.run_client(enabled=enabled, response_transform=malformed)
            self.assertIsInstance(result['error'], ValueError)
            self.assertEqual(len(result['calls']), 1)
            self.assertFalse(any(tool == 'act' for tool, _ in result['requests']))
            # Existing failure cleanup may add a separately recorded neutral step.
            self.assertEqual([tool for tool, _ in result['requests']], ['stop', 'finish_episode'])

    def test_named_query_nonzero_repeat_and_malformed_followup_never_dispatch_action(self):
        def bad_followup(value, index, schema):
            result = encode(value)
            if index == 1: del result['action']['robot_0']['gripper']
            return result
        cases = [('nonzero_placeholder', encode, 1), ('repeat_query', encode, 2),
                 ('invalid_second', encode, 2), ('query', bad_followup, 2)]
        for scenario, transform, count in cases:
            with self.subTest(scenario=scenario):
                result = self.run_client(scenario=scenario, response_transform=transform)
                self.assertIsInstance(result['error'], ValueError)
                self.assertEqual(len(result['calls']), count)
                self.assertEqual([tool for tool, _ in result['requests']], ['stop', 'finish_episode'])
                stopped = [e for e in result['events'] if e['type'] == 'depth_query_cycle_stopped']
                self.assertEqual(len(stopped), 1)
                self.assertFalse(stopped[0]['executed'])

    def test_public_export_rejects_raw_canonical_mismatch_or_extra_named_metadata(self):
        result = named.normalize_result({'decision': encode(query.action())})
        event = {'type': 'decision', **result}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'events.jsonl'
            path.write_text(json.dumps(event) + '\n')
            rows, _ = exporter.public_events(path)
            self.assertEqual(rows[0]['named_action'], result['named_action'])
            for mode in ('different_action', 'extra_metadata', 'wrong_mapping'):
                bad = deepcopy(event)
                if mode == 'different_action': bad['decision']['action'][1][7] = 1
                elif mode == 'extra_metadata': bad['named_action']['private_geometry'] = 'not public'
                else: bad['named_action']['mapping_sha256'] = '0'*64
                path.write_text(json.dumps(bad) + '\n')
                with self.subTest(mode=mode), self.assertRaises(ValueError): exporter.public_events(path)

    def test_non_exec_or_open_loop_rejected_before_simulator_and_outputs(self):
        for flags in (['--actor-backend', 'app-server'], ['--plan-size', '2'], ['--plan-size', '3']):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                argv = ['client', '--run-id', 'reject', '--named-actions', *flags]
                with mock.patch.object(client, '__file__', str(root/'participant/collection/client.py')), \
                     mock.patch.object(client.signal, 'signal'), mock.patch.object(client, 'Simulator') as sim, \
                     mock.patch.object(sys, 'argv', argv), mock.patch('sys.stderr'), self.assertRaises(SystemExit):
                    client.main()
                sim.assert_not_called()
                self.assertFalse((root/'output').exists())


if __name__ == '__main__':
    unittest.main()
