"""Public report privacy, evidence, chronology, and no-overwrite regressions."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import h5py
import numpy as np
from PIL import Image

from participant.collection.boundary import CONTRACT
from participant.collection.export_report import export_report, milestone_path
from participant.collection.validate_capture import sha256, validate_capture
from Policy.training_dataset import DatasetWriter


class CollectionReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.trace, self.capture, self.output = [self.root / name for name in ('trace', 'capture', 'public-report')]
        self.trace.mkdir()
        self.run_id = 'test-wiring'
        self.prompt = 'Use the public camera observations. Return a small lift and stop.'
        self.prompt_hash = hashlib.sha256(self.prompt.encode()).hexdigest()

    def make_trace(self, *, failed=False):
        (self.trace / 'prompt.txt').write_text(self.prompt)
        attempt = {'run_id': self.run_id, 'parent_attempt': 'earlier-attempt', 'retry_reason': 'protocol_fixed',
                   'source_group': 'fixture', 'source': 'integration_test', 'mode': 'wiring',
                   'model': 'gpt-6-astra', 'reasoning_effort': 'ultra', 'prompt_sha256': self.prompt_hash,
                   'status': 'failed' if failed else 'completed', 'finished': not failed,
                   'started_at_utc': '2026-11-06T02:23:14Z', 'ended_at_utc': '2026-11-06T02:24:39Z',
                   'wall_s': 85.7, 'actor_call_wall_s': 24., 'simulation_time_s': 0 if failed else .15,
                   'simulation_steps': 0 if failed else 3, 'decisions_completed': 0 if failed else 1,
                   'actor_usage': {'input_tokens': 100, 'hidden_reasoning': 'never-export-hidden-reasoning'},
                   'source_snapshot': {'commit': 'a'*40, 'working_tree_modified': True,
                                       'private_path': '/home/private-auth.json'},
                   'session_id': 'session-canary', 'auth': 'secret-auth-canary',
                   'private_endpoint': 'http://192.0.2.27:9999',
                   'error': {'type': 'RuntimeError', 'message': 'startup failed'} if failed else None}
        (self.trace / 'attempt.json').write_text(json.dumps(attempt))
        action = [[0., 0., 0., .03, 0., 0., 0., 0., -1.]] * 2
        events = [] if failed else [
            {'type': 'decision', 'decision_index': 0, 'input_sha256': 'b'*64,
             'observation_simulation_time_s': 1.5, 'wall_s': 8., 'model': 'gpt-6-astra',
             'effort': 'ultra', 'cli_version': 'codex-cli 0.166.0', 'prompt_sha256': self.prompt_hash,
             'session_id': 'session-canary', 'reasoning': 'never-export-hidden-reasoning',
             'decision': {'tool': 'act', 'action': action, 'steps': 3, 'stage': 'preparation',
                          'visual_assessment': 'uncertain', 'reason': 'Small public-observation wiring motion.',
                          'internal_state': 'never-export-geometry'},
             'usage': {'input_tokens': 100, 'output_tokens': 10}},
            {'type': 'applied_segment', 'segment_id': 'test-wiring:00000', 'decision_index': 0,
             'start_step': 0, 'end_step': 3, 'simulation_start_s': 1.5, 'simulation_end_s': 1.65,
             'environment_dispatch_wall_s': 2., 'stage_intent': 'preparation',
             'visual_assessment': 'uncertain', 'assessment_source': 'actor_public_observations',
             'requested_steps': 3, 'applied_action': action, 'actual_steps': 3, 'quality_status': 'unreviewed',
             'object_pose': 'never-export-geometry'},
        ]
        (self.trace / 'decisions.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))

    def make_capture(self):
        contract = copy.deepcopy(CONTRACT)
        contract['default_dimensions'].update(height=16, width=16)
        dims = contract['default_dimensions']
        action = np.zeros((2, 9), np.float32)
        def observation(step):
            value = {key: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
                     for key, spec in contract['observations'].items()}
            value['simulation_time_s'] = np.asarray(1.5 + step*.05, np.float64)
            value['previous_action'] = action.copy()
            for i in range(5):
                value['rgb'][i, :, :, 0] = 20 + i
                value['rgb'][i, :, :, 1] = step*30
            return value
        writer = DatasetWriter(self.capture, contract, {'source': 'integration_test', 'raw_archive': False,
                                                        'secret': 'audit-only-canary'})
        writer.start_episode({'operator_source': 'integration_test', 'source_group': 'fixture'})
        for i in range(3):
            writer.append(observation(i), action, observation(i+1), start_tick=i*12, end_tick=(i+1)*12, audit={})
        writer.finish_episode('test_done')
        writer.close()
        hashes = {name: sha256(self.capture / name) for name in ('policy.hdf5', 'audit.hdf5')}
        (self.capture / 'capture.json').write_text(json.dumps({'schema': 'participant-live-capture-v2',
            'complete': True, 'raw_archive': False, 'steps': 3, 'files': hashes,
            'private': 'http://192.0.2.27:9999'}))
        (self.capture / 'validation.json').write_text(json.dumps(validate_capture(self.capture)))
        breakdown = dict.fromkeys(('pickup', 'first_sleeve', 'opposite_shoulder', 'second_sleeve',
                                  'left_upper_arm', 'right_upper_arm', 'neck', 'front_orientation'), 0)
        report = {'valid': True, 'metadata': {'episode_seed': 999, 'neck_chain_world_m': 'never-export-geometry'},
                  'result': {'raw_points': 0, 'max_raw_points': 50, 'success': False, 'success_evaluated': True,
                             'score_status': 'no_contact', 'final_score': None, 'breakdown': breakdown,
                             'milestone_times_s': {}, 'private': 'secret-auth-canary'}}
        evaluation = {'evaluation_path': 'evaluation/fixture', 'report': report}
        (self.capture / 'evaluation_summary.json').write_text(json.dumps(evaluation))
        folder = self.capture / 'evaluation/fixture'; folder.mkdir(parents=True)
        event = {'event': 'evaluation_started', 'physics_tick': 0, 'evaluation_time_s': 0,
                 'raw_points': 0, 'breakdown': breakdown, 'success': False, 'success_evaluated': True,
                 'hidden_geometry': 'never-export-geometry'}
        (folder / 'score_events.jsonl').write_text(json.dumps(event)+'\n')

    def test_public_allowlist_preserves_evidence_but_excludes_private_metadata(self):
        self.make_trace(); self.make_capture()
        manifest = export_report(self.trace, self.capture, self.output)
        texts = '\n'.join(p.read_text() for p in self.output.iterdir() if p.suffix in ('.json', '.jsonl', '.md', '.txt'))
        for secret in ('session-canary', 'session_id', 'secret-auth-canary', 'never-export-hidden-reasoning',
                       'never-export-geometry', '/home/private-auth.json', '192.0.2.27', 'episode_seed',
                       'neck_chain_world_m', 'audit-only-canary'):
            self.assertNotIn(secret, texts)
        self.assertEqual(len(manifest['media']['images']), 10)
        self.assertTrue(manifest['quality']['quality_passed'])
        self.assertEqual(manifest['media']['transitions'], 3)
        self.assertEqual(manifest['evaluation']['raw_points'], 0)
        self.assertIsNone(manifest['evaluation']['final_score'])
        self.assertFalse(manifest['evaluation']['success'])
        self.assertEqual(manifest['milestone_path']['time_origin_public_simulation_s'], 1.5)
        self.assertEqual((self.output / 'prompt.txt').read_text(), self.prompt)
        for i, camera in enumerate(CONTRACT['competition_access']['allowed_cameras']):
            with Image.open(self.output / 'images' / f'initial-{camera}.png') as image:
                self.assertEqual(image.getpixel((0, 0)), (20+i, 0, 0))
            with Image.open(self.output / 'images' / f'final-{camera}.png') as image:
                self.assertEqual(image.getpixel((0, 0)), (20+i, 90, 0))
        self.assertEqual(manifest['source_files']['capture/policy.hdf5']['sha256'], sha256(self.capture / 'policy.hdf5'))

    def test_failed_startup_has_no_fabricated_score_or_images(self):
        self.make_trace(failed=True)
        manifest = export_report(self.trace, self.capture, self.output)
        self.assertEqual(manifest['attempt']['status'], 'failed')
        self.assertIsNone(manifest['evaluation']['raw_points'])
        self.assertIsNone(manifest['evaluation']['success'])
        self.assertFalse(manifest['quality']['available'])
        self.assertEqual(manifest['media']['images'], [])
        self.assertFalse((self.output / 'images').exists())
        self.assertIn('startup failed', (self.output / 'README.ko.md').read_text())

    def test_same_tick_awards_form_one_unordered_batch_and_success_stays_separate(self):
        initial = {'event': 'evaluation_started', 'physics_tick': 0, 'evaluation_time_s': 0,
                   'raw_points': 0, 'breakdown': {'pickup': 0, 'first_sleeve': 0}}
        awarded = dict(initial, physics_tick=24, evaluation_time_s=.1, raw_points=10,
                       breakdown={'pickup': 5, 'first_sleeve': 5})
        events = [initial, dict(awarded, event='score_awarded', stage='pickup'),
                  dict(awarded, event='score_awarded', stage='first_sleeve'),
                  dict(awarded, event='dressing_success', physics_tick=36, evaluation_time_s=.15)]
        result = milestone_path(events, valid=True, simulation_origin=1.5)
        self.assertEqual(len(result['award_batches']), 1)
        batch = result['award_batches'][0]
        self.assertTrue(batch['simultaneous'])
        self.assertEqual(batch['order_within_batch'], 'not_inferred')
        self.assertEqual(batch['raw_points_before'], 0)
        self.assertEqual(batch['raw_points_after'], 10)
        self.assertEqual(batch['transition_boundary_step'], 2)
        self.assertEqual(batch['public_simulation_time_s'], 1.6)
        self.assertEqual(result['success_events'][0]['physics_tick'], 36)

    def test_private_prompt_or_action_reason_requires_review_before_any_output(self):
        for where in ('prompt', 'reason'):
            with self.subTest(where=where):
                self.make_trace()
                if where == 'prompt':
                    (self.trace / 'prompt.txt').write_text('Connect to http://192.0.2.27:9999')
                else:
                    values = [json.loads(line) for line in (self.trace / 'decisions.jsonl').read_text().splitlines()]
                    values[0]['decision']['reason'] = 'Inspect /home/private/auth.json'
                    (self.trace / 'decisions.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in values))
                with self.assertRaises(ValueError):
                    export_report(self.trace, self.capture, self.output)
                self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten_and_stale_qc_is_rejected(self):
        self.make_trace(); self.make_capture()
        self.output.mkdir(); marker = self.output / 'keep.txt'; marker.write_text('keep')
        with self.assertRaises(FileExistsError):
            export_report(self.trace, self.capture, self.output)
        self.assertEqual(marker.read_text(), 'keep')
        with h5py.File(self.capture / 'policy.hdf5', 'r+') as file:
            file.attrs['changed'] = True
        alternate = self.output.with_name('alternate')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            export_report(self.trace, self.capture, alternate)
        self.assertFalse(alternate.exists())

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg/ffprobe unavailable')
    def test_short_video_is_explicitly_slowed_and_frame_cap_is_reported(self):
        self.make_trace(); self.make_capture()
        manifest = export_report(self.trace, self.capture, self.output, video=True, max_video_frames=2)
        video = manifest['media']['video']
        self.assertEqual(video['available_frames'], 3)
        self.assertEqual(video['exported_frames'], 2)
        self.assertEqual(video['slowdown_factor'], 20)
        self.assertTrue(video['truncated'])
        probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_frames,r_frame_rate', '-of', 'json', str(self.output / 'overview.mp4')],
            capture_output=True, text=True, check=True)
        stream = json.loads(probe.stdout)['streams'][0]
        self.assertEqual(int(stream['nb_frames']), 2)
        self.assertEqual(stream['r_frame_rate'], '1/1')
        self.assertIn('앞부분만', (self.output / 'README.ko.md').read_text())


if __name__ == '__main__':
    unittest.main()
