"""CPU checks for the new dataset's fixed, genuinely fresh reset contract."""
from contextlib import redirect_stderr
from io import StringIO
import os
import sys
import unittest
from unittest.mock import Mock, patch

import numpy as np

from Env_Config.Garment.RandomSpawn import sample_garment_spawn
from participant.collection import codex_client
from participant.collection.fresh_start import select_practice_reset, verify_reset


class FreshStartTest(unittest.TestCase):
    centers = np.array([(x, -1.47092, 0.285) for x in (-3.19968, -1.06656, 1.06656, 3.19968)])
    bases = [(-1.06656, -0.139, 0.03), (1.06656, -0.139, 0.03)]
    size = (0.93312, 0.69984, 0.57)

    def profile(self, seed=None):
        return select_practice_reset(self.centers, self.size, self.bases, seed)

    def test_official_reset_selects_the_same_nearest_table_for_all_requested_seeds(self):
        with patch.dict(os.environ, STRETCH4_RANDOMIZE='1'):
            self.assertEqual(self.profile()['episode_seed'], 43)
            for seed in (0, 1, 2, 42, 43, 67, 2**63-1):
                with self.subTest(seed=seed):
                    result = self.profile(seed)
                    actual = sample_garment_spawn(self.centers, self.size, seed=result['episode_seed'])
                    self.assertEqual((result['table_index'], actual['table_index']), (2, 2))
                    self.assertEqual(actual['table_prim_path'], '/World/garment_table_2')
                    np.testing.assert_allclose(result['mean_base_distance_xy_m'],
                                               [3.49206, 1.92336, 1.92336, 3.49206], atol=1e-5)
        with patch.dict(os.environ, STRETCH4_RANDOMIZE='0'), self.assertRaises(ValueError):
            self.profile()

    def test_requires_matching_measured_reset_and_upstream_material(self):
        with patch.dict(os.environ, STRETCH4_RANDOMIZE='1'):
            profile = self.profile()
            garment = sample_garment_spawn(self.centers, self.size, seed=43)
        info = dict(step_id=0, episode_seed=43, garment_spawn=garment)
        stage = Mock()
        attr = stage.GetPrimAtPath.return_value.GetAttribute.return_value
        attr.Get.return_value = np.float32(0.35)
        receipt = verify_reset(info, profile, stage)
        self.assertTrue(receipt['verified_after_reset'])
        for bad in (dict(step_id=1), dict(episode_seed=9), dict(garment_spawn=dict(garment, table_index=1))):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                verify_reset(dict(info, **bad), profile, stage)
        attr.Get.return_value = 0.0
        with self.assertRaises(RuntimeError):
            verify_reset(info, profile, stage)

    def test_active_collector_rejects_legacy_starts_and_models_before_opening_a_run(self):
        for flags in (['--initial-slot', 'old.npz'], ['--replay-prefix-run', 'old'],
                      ['--model', 'gpt-6-astra'], ['--effort', 'low']):
            argv = ['client', '--run-id', 'test-reject', '--mode', 'dressing', '--user-guided',
                    '--segment-review-dir', 'output/test-review', *flags]
            with self.subTest(flags=flags), patch.object(sys, 'argv', argv), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                codex_client.main()
