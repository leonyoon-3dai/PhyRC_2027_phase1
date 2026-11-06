"""CPU-only call-preservation and numeric timing partition checks."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

from participant.collection.evaluation import RecordedEnvironment, RecordedWriter
from participant.collection.step_profile import StepProfiler


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class Sensors:
    def __init__(self, env):
        self.env = env

    def capture(self):
        self.env.calls.append('capture')
        self.env.clock.advance(5)
        if self.env.failure is not None:
            raise self.env.failure
        return self.env.frame


class Environment:
    def __init__(self, clock):
        self.clock, self.calls, self.failure = clock, [], None
        self.frame = {'private_scene_canary': object()}
        self.sensors = Sensors(self)
        self.observation = {'simulation_time_s': .05}
        self.result = (self.observation, 0, False, False, {'private_scene_canary': object()})
        self.received_action = None

    def _observe(self):
        self.calls.append('observe')
        self.clock.advance(3)
        if self.sensors is not None:
            assert self.sensors.capture() is self.frame
        self.clock.advance(7)
        return self.observation

    def step(self, action):
        self.calls.append('step')
        self.received_action = action
        self.clock.advance(2)
        assert self._observe() is self.observation
        self.clock.advance(11)
        return self.result


class StepProfileTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.env = Environment(self.clock)
        self.action = object()

    def test_default_off_has_existing_fields_and_no_method_changes(self):
        recorder = RecordedEnvironment(self.env)
        with mock.patch('participant.collection.evaluation.time.perf_counter', self.clock):
            result = recorder.step(self.action)
        self.assertIs(result, self.env.result)
        self.assertIs(self.env.received_action, self.action)
        self.assertEqual(self.env.calls, ['step', 'observe', 'capture'])
        self.assertEqual(recorder.last_step, {'environment_step_wall_s': 28., 'simulation_time_s': .05})
        self.assertNotIn('_observe', vars(self.env))
        self.assertNotIn('capture', vars(self.env.sensors))

    def test_profile_exact_partition_same_calls_identity_and_numeric_only(self):
        recorder = RecordedEnvironment(self.env, profile_step_phases=True)
        with mock.patch('participant.collection.evaluation.time.perf_counter', self.clock):
            result = recorder.step(self.action)
        self.assertIs(result, self.env.result)
        self.assertIs(self.env.received_action, self.action)
        self.assertEqual(self.env.calls, ['step', 'observe', 'capture'])
        self.assertEqual(recorder.last_step, {
            'environment_step_wall_s': 28., 'simulation_time_s': .05,
            'step_observe_wall_s': 15., 'step_capture_wall_s': 5.,
            'step_observe_without_capture_wall_s': 10., 'step_without_observe_wall_s': 13.,
            'step_observe_calls': 1, 'step_capture_calls': 1,
            'step_capture_outside_observe_calls': 0})
        self.assertTrue(all(type(value) in (int, float) for value in recorder.last_step.values()))
        self.assertNotIn('private_scene_canary', json.dumps(recorder.last_step))
        self.assertNotIn('_observe', vars(self.env))
        self.assertNotIn('capture', vars(self.env.sensors))

    def test_each_step_has_fresh_counters_and_same_action_boundary(self):
        recorder = RecordedEnvironment(self.env, profile_step_phases=True)
        with mock.patch('participant.collection.evaluation.time.perf_counter', self.clock):
            first = recorder.step(self.action)
            first_timing = dict(recorder.last_step)
            second = recorder.step(self.action)
        self.assertIs(first, second)
        self.assertEqual(recorder.last_step, first_timing)
        self.assertEqual(self.env.calls, ['step', 'observe', 'capture'] * 2)

    def test_collector_flag_is_explicitly_opt_in(self):
        path = Path(__file__).resolve().parents[1] / 'scripts/collect_operator.py'
        spec = importlib.util.spec_from_file_location('profile_test_collector', path)
        collector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(collector)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'unused-output'
            args = ['--output', str(output), '--source', 'integration_test',
                    '--source-group', 'cpu-profile', '--model-id', 'cpu-fake', '--prompt', 'CPU test.']
            self.assertFalse(collector.parse_arguments(args).profile_step_phases)
            self.assertTrue(collector.parse_arguments(args + ['--profile-step-phases']).profile_step_phases)
            self.assertFalse(output.exists())

    def test_exception_identity_and_restore_including_base_exception(self):
        for error in (RuntimeError('capture failed'), KeyboardInterrupt('interrupt')):
            with self.subTest(error=type(error)):
                self.env.failure = error
                recorder = RecordedEnvironment(self.env, profile_step_phases=True)
                with mock.patch('participant.collection.evaluation.time.perf_counter', self.clock):
                    with self.assertRaises(type(error)) as caught:
                        recorder.step(self.action)
                self.assertIs(caught.exception, error)
                self.assertIsNone(recorder.last_step)
                self.assertNotIn('_observe', vars(self.env))
                self.assertNotIn('capture', vars(self.env.sensors))

    def test_instance_overrides_restore_exactly_and_no_sensor_is_supported(self):
        custom_observe = self.env._observe
        self.env._observe = custom_observe
        self.env.sensors = None
        with StepProfiler(self.env, clock=self.clock) as profiler:
            self.assertIs(self.env.step(self.action), self.env.result)
        self.assertIs(self.env._observe, custom_observe)
        metrics = profiler.metrics(self.clock.value)
        self.assertEqual(metrics['step_observe_calls'], 1)
        self.assertEqual(metrics['step_capture_calls'], 0)
        self.assertEqual(metrics['step_capture_wall_s'], 0)
        self.assertEqual(metrics['step_observe_without_capture_wall_s'], 10)

    def test_other_thread_calls_are_preserved_but_not_counted(self):
        returned = []
        with StepProfiler(self.env, clock=self.clock) as profiler:
            thread = threading.Thread(target=lambda: returned.append(self.env._observe()))
            thread.start()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertIs(returned[0], self.env.observation)
            self.assertEqual(profiler.metrics(self.clock.value)['step_capture_calls'], 0)
            self.env.step(self.action)
        self.assertEqual(profiler.metrics(self.clock.value)['step_observe_calls'], 1)
        self.assertEqual(profiler.metrics(self.clock.value)['step_capture_calls'], 1)
        self.assertEqual(self.env.calls, ['observe', 'capture', 'step', 'observe', 'capture'])

    def test_overlapping_scope_rejects_without_disturbing_original_scope(self):
        with StepProfiler(self.env, clock=self.clock) as first:
            wrapped = self.env._observe
            with self.assertRaisesRegex(RuntimeError, 'overlapping'):
                with StepProfiler(self.env, clock=self.clock):
                    self.fail('overlapping profiling entered')
            self.assertIs(self.env._observe, wrapped)
            self.env.step(self.action)
        self.assertEqual(first.metrics(self.clock.value)['step_capture_calls'], 1)
        self.assertNotIn('_observe', vars(self.env))

    def test_existing_writer_records_only_numeric_phases_and_original_arguments(self):
        recorder = RecordedEnvironment(self.env, profile_step_phases=True)
        with mock.patch('participant.collection.evaluation.time.perf_counter', self.clock):
            recorder.step(self.action)
        with tempfile.TemporaryDirectory() as temp:
            writer = mock.Mock(path=Path(temp))
            measured_writer = RecordedWriter(writer, recorder)
            before = {'simulation_time_s': 0.}
            measured_writer.append(before, self.action, self.env.observation,
                                   start_tick=0, end_tick=12, audit={})
            measured_writer.close()
            writer.append.assert_called_once_with(before, self.action, self.env.observation,
                                                  start_tick=0, end_tick=12, audit={})
            rows = (Path(temp) / 'step_timings.jsonl').read_text().splitlines()
            self.assertEqual(len(rows), 1)
            row = json.loads(rows[0])
            self.assertEqual(row['step_capture_wall_s'], 5)
            self.assertEqual(row['step_observe_calls'], 1)
            self.assertNotIn('private_scene_canary', rows[0])


if __name__ == '__main__':
    unittest.main()
