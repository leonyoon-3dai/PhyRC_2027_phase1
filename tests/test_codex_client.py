"""Public-payload and action rejection tests, independent of GPU or model access."""
import copy
import json
from pathlib import Path
import tempfile
import sys
import time
import unittest

import numpy as np
from PIL import Image
from participant.collection.boundary import CONTRACT
from participant.collection.codex_client import Simulator, prepare_observation, public_interface, validate_decision


def observation():
    dims = CONTRACT['default_dimensions']
    return {name: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
            for name, spec in CONTRACT['observations'].items()}


class CodexClientTest(unittest.TestCase):
    def test_transport_drains_after_invalid_initial_response(self):
        command = [sys.executable, '-c',
                   "import sys; print('native-not-json',flush=True); "
                   "[print('x'*1000,flush=True) for _ in range(10000)]; sys.stdin.read()"]
        with tempfile.TemporaryDirectory() as tmp, open(Path(tmp)/'log', 'w') as log:
            sim = Simulator(command, Path(tmp), log, timeout_s=5)
            with self.assertRaisesRegex(ValueError, 'non-JSON simulator output'):
                sim.receive()
            time.sleep(.1)
            started = time.monotonic()
            self.assertEqual(sim.close(), 0)
            self.assertLess(time.monotonic() - started, 5)

    def test_public_payload_ignores_privileged_fields_and_preserves_rgb(self):
        obs = observation()
        obs['rgb'][2, 12, 27] = [17, 222, 80]
        obs['depth'][0, :16, :16, 0] = 1.2345
        obs['depth_valid'][0, :16, :16, 0] = True
        obs.update(score=50, success=True, seed=54321, cloth_world_positions='do-not-copy')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'observation'
            payload, images = prepare_observation(obs, path)
            self.assertEqual(len(images), 5)
            text = json.dumps(payload)
            for secret in ('do-not-copy', '54321', '"success"', '"score"'):
                self.assertNotIn(secret, text)
            self.assertEqual(np.asarray(Image.open(images[2]))[12, 27].tolist(), [17, 222, 80])
            self.assertEqual(payload['depth_16x16_grid_m']['overview'][0][0], 1.235)
            self.assertIsNone(payload['depth_16x16_grid_m']['overview'][1][0])
            with np.load(path / 'public_depth.npz') as archive:
                self.assertEqual(set(archive.files), {'depth', 'depth_valid'})
            with self.assertRaises(FileExistsError):
                prepare_observation(obs, path)

    def test_invalid_public_sensor_data_fails_closed(self):
        for field in ('joint_position', 'depth'):
            obs = observation()
            obs[field].flat[0] = np.nan
            with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
                prepare_observation(obs, Path(tmp) / 'obs')

    def test_decision_validation_and_wiring_bounds(self):
        valid = dict(tool='act', action=[[0.0]*9, [0.0]*9], steps=2,
                     stage='preparation', visual_assessment='uncertain', reason='small lift')
        valid['action'][0][3] = .03
        self.assertEqual(validate_decision(valid, wiring=True).dtype, np.float32)
        invalid = []
        for key, value in [('steps', True), ('stage', '50_points'), ('tool', 'reset'),
                           ('score', 50), ('reason', ''), ('tool', 'finish_episode')]:
            item = copy.deepcopy(valid); item[key] = value; invalid.append(item)
        for value in (True, float('inf'), float('nan'), 1.001, '0'):
            item = copy.deepcopy(valid); item['action'][0][0] = value; invalid.append(item)
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                validate_decision(item)
        excessive = copy.deepcopy(valid); excessive['action'][0][3] = .1
        with self.assertRaises(ValueError):
            validate_decision(excessive, wiring=True)

    def test_static_metadata_allowlist(self):
        value = dict(action_scales={'LIFT_RATE': .2}, joint_names=['lift'], joint_units=['m'],
                     camera_intrinsics=[1, 2], camera_poses='dynamic-forbidden', human_spawn='forbidden',
                     episode_seed=99, evaluation={'success': True})
        result = public_interface(value)
        self.assertEqual(set(result), {'action_scales', 'joint_names', 'joint_units', 'camera_intrinsics'})


if __name__ == '__main__':
    unittest.main()
