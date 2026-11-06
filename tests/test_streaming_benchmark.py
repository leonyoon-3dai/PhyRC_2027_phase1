"""CPU-only benchmark safeguards; never launch Docker, Kit, or a model."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


bench = module('benchmark_streaming')
viewport = module('collect_benchmark_viewport')


class StreamingBenchmarkTests(unittest.TestCase):
    def test_default_only_plans_abba_without_starting_simulator(self):
        with patch('subprocess.Popen', side_effect=AssertionError('process launched')), patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(bench.main(['--run-id', 'test-only']), 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data['order'], ['off', 'on', 'on', 'off'])
        self.assertFalse(data['gpu_executed'])
        self.assertFalse(data['sdk_only_isolated'])
        self.assertEqual(['--webrtc' in cmd for cmd in data['commands']], [False, True, True, False])
        for cmd in data['commands']:
            self.assertIn('--no-randomization', cmd)
            self.assertIn('--evaluate', cmd)

    def test_invalid_limits_and_paths_rejected(self):
        for extra in (['--idle-seconds', 'nan'], ['--chunk-steps', '21'], ['--chunks', '0'], ['--run-id', '../escape']):
            with self.subTest(extra=extra), patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
                bench.parse_args(['--run-id', 'test'] + extra)

    def test_idle_clock_mutation_fails_even_without_physics_inspection(self):
        class Sim:
            def dispatch(self, tool, arguments):
                return {'simulation_time_s': 1.05}
        with self.assertRaisesRegex(RuntimeError, 'idle advanced'):
            bench.idle_measure(Sim(), {'simulation_time_s': 1.0}, 0, sleep=lambda _: None)

    def test_measurement_excludes_warmup_and_checks_saved_cadence(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            capture = {'complete': True, 'steps': 3, 'wall_s': 50, 'idle_render_calls': 10,
                       'idle_render_wall_s': 2, 'evaluation_enabled': True, 'files': {'x.hdf5': 'hash'}}
            (p / 'capture.json').write_text(json.dumps(capture))
            (p / 'run_metadata.json').write_text(json.dumps({'reset_wall_s': 4}))
            rows = [{'environment_step_wall_s': t, 'dataset_write_wall_s': .1,
                     'observation_time_s': i * .05, 'next_observation_time_s': (i + 1) * .05}
                    for i, t in enumerate([100, 2, 4])]
            (p / 'step_timings.jsonl').write_text('\n'.join(map(json.dumps, rows)))
            saved = bench.summarize_saved(p, 1, 2)
            self.assertEqual(saved['environment_step_wall_s']['sum_s'], 6)
            self.assertEqual(saved['saved_transitions'], 3)
            self.assertTrue(saved['cadence_20hz_verified'])
            capture['complete'] = False
            (p / 'capture.json').write_text(json.dumps(capture))
            with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                bench.summarize_saved(p, 1, 2)

    def test_matched_viewport_preserves_other_renderer_options(self):
        original = {'headless': True, 'renderer': 'RaytracedLighting', 'anti_aliasing': 3}
        result = viewport.viewport_config(original)
        self.assertEqual((result['width'], result['height'], result['hide_ui']), (1280, 720, False))
        self.assertEqual(result['renderer'], original['renderer'])
        self.assertEqual(result['anti_aliasing'], 3)
        self.assertNotIn('width', original)
        args = bench.parse_args(['--run-id', 'test', '--viewport', 'matched'])
        self.assertIn('/scripts/collect_benchmark_viewport.py', bench.command_for(args, 0, False)[1])


if __name__ == '__main__':
    unittest.main()
