"""Private backup selection, completion gates, hashes, and source immutability."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from participant.ops import artifacts
from scripts import preserve_collection as preservation


class PreserveCollectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = 'test-closed'
        self.collection = self.root / 'output/collections' / self.run
        self.trace = self.root / 'output/operator-traces' / self.run
        self.obs = self.root / 'output/actors' / self.run / 'observations/00000'
        for folder in (self.collection, self.trace, self.obs, self.root / 'config'):
            folder.mkdir(parents=True)
        (self.root / 'config/policy_interface.json').write_text('{}')
        for name in ('policy.hdf5', 'audit.hdf5'):
            (self.collection / name).write_bytes(('fixture-' + name).encode())
        hashes = {name: artifacts.digest(self.collection / name) for name in ('policy.hdf5', 'audit.hdf5')}
        self.write(self.collection / 'capture.json', {'complete': True, 'raw_archive': False, 'steps': 2,
                                                    'files': hashes, 'evaluation_enabled': True})
        self.write(self.collection / 'validation.json', {
            'schema': 'phyrc-capture-validation-v1', 'quality_passed': True, 'errors': [],
            'total_transitions': 2, 'validated_transitions': 2, 'sha256': hashes,
            'episodes': [{'complete': True, 'quality_passed': True, 'transitions': 2}]})
        for name in ('operator.jsonl', 'run_metadata.json', 'evaluation_summary.json', 'step_timings.jsonl'):
            (self.collection / name).write_text('{}\n')
        evaluation = self.collection / 'evaluation/test-evaluation'
        evaluation.mkdir(parents=True)
        for name in preservation.EVALUATION_FILES:
            (evaluation / name).write_text('{}\n')
        for name in ('decisions.jsonl', 'review_gate.json', 'score_segments.json'):
            (self.trace / name).write_text('{}\n')
        (self.trace / 'prompt.txt').write_text('public task')
        source = self.trace / 'source_snapshot/run.sh'
        source.parent.mkdir()
        source.write_text('# test script\n')
        self.write(self.trace / 'attempt.json', {
            'run_id': self.run, 'activity': 'closed', 'status': 'completed',
            'simulator_returncode': 0, 'simulation_steps': 2, 'actor_calls_attempted': 1,
            'prompt_sha256': artifacts.digest(self.trace / 'prompt.txt'),
            'source_snapshot': {'commit': 'example', 'files_sha256': {'run.sh': artifacts.digest(source)}}})
        for name in preservation.OBS_REQUIRED:
            (self.obs / name).write_bytes(b'public observation fixture')
        # These forbidden sources must be ignored without even parsing their contents.
        (self.trace / 'simulator.log').write_text('PRIVATE_LOG_SENTINEL')
        runtime = self.obs.parent.parent / 'runtime/actor_events'
        runtime.mkdir(parents=True)
        (runtime / '00000.jsonl').write_text('PRIVATE_REASONING_SENTINEL')
        (runtime.parent / 'auth.json').write_text('PRIVATE_AUTH_SENTINEL')

    def write(self, path, obj):
        path.write_text(json.dumps(obj))

    def modify(self, path, **changes):
        value = json.loads(path.read_text())
        value.update(changes)
        self.write(path, value)

    def test_preserves_exact_allowed_sources_and_excludes_private_runtime(self):
        before = artifacts.digest(self.collection / 'policy.hdf5')
        receipt = preservation.preserve(self.root, self.run, 'bundle')
        stage = self.root / receipt['stage_relative_path']
        inventory = artifacts.verify(stage)
        self.assertTrue(receipt['private_storage_required'])
        self.assertFalse(receipt['remote_uploaded'])
        self.assertFalse(receipt['training_approval_changed'])
        self.assertIn('output/collections/test-closed/audit.hdf5', inventory)
        self.assertIn('output/collections/test-closed/evaluation/test-evaluation/result.json', inventory)
        self.assertIn('output/actors/test-closed/observations/00000/public_depth.npz', inventory)
        for path in stage.rglob('*'):
            self.assertNotIn(path.name, ('simulator.log', 'auth.json', 'actor_events'))
            if path.is_file():
                self.assertNotIn(b'PRIVATE_', path.read_bytes())
        self.assertEqual(artifacts.digest(self.collection / 'policy.hdf5'), before)
        self.assertEqual(stage.stat().st_mode & 0o777, 0o700)
        self.assertEqual((stage / 'scope.json').stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            preservation.preserve(self.root, self.run, 'bundle')

    def test_active_attempt_or_incomplete_validation_rejected_before_output(self):
        self.modify(self.trace / 'attempt.json', activity='model_request')
        with self.assertRaisesRegex(ValueError, 'not closed'):
            preservation.preserve(self.root, self.run, 'active')
        self.assertFalse((self.root / 'output/preservation').exists())
        self.modify(self.trace / 'attempt.json', activity='closed')
        self.modify(self.collection / 'validation.json', validated_transitions=1)
        with self.assertRaisesRegex(ValueError, 'counts disagree'):
            preservation.preserve(self.root, self.run, 'partial')
        self.assertFalse((self.root / 'output/preservation').exists())

    def test_hdf5_and_snapshot_tampering_rejected(self):
        policy = self.collection / 'policy.hdf5'
        original = policy.read_bytes()
        policy.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'HDF5 hash mismatch'):
            preservation.preserve(self.root, self.run, 'changed')
        policy.write_bytes(original)
        (self.trace / 'source_snapshot/run.sh').write_text('# modified\n')
        with self.assertRaisesRegex(ValueError, 'source snapshot hash mismatch'):
            preservation.preserve(self.root, self.run, 'changed-source')
        self.assertFalse((self.root / 'output/preservation').exists())

    def test_unknown_collection_or_observation_file_is_not_silently_backed_up(self):
        unexpected = self.collection / 'extra-debug.log'
        unexpected.write_text('do not copy')
        with self.assertRaisesRegex(ValueError, 'unreviewed collection'):
            preservation.preserve(self.root, self.run, 'unexpected')
        unexpected.unlink()
        (self.obs / 'session.sqlite').write_bytes(b'do not copy')
        with self.assertRaisesRegex(ValueError, 'unreviewed or incomplete observation'):
            preservation.preserve(self.root, self.run, 'unexpected-observation')

    def test_symlinked_observation_rejected_and_forbidden_source_manifest_rejected(self):
        path = self.obs / 'overview.png'
        path.unlink()
        path.symlink_to(self.obs / 'robot_0_head.png')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            preservation.preserve(self.root, self.run, 'link')
        path.unlink()
        path.write_bytes(b'public')
        secret = self.trace / 'source_snapshot/auth.json'
        secret.write_text('secret')
        attempt = json.loads((self.trace / 'attempt.json').read_text())
        attempt['source_snapshot']['files_sha256']['auth.json'] = artifacts.digest(secret)
        self.write(self.trace / 'attempt.json', attempt)
        with self.assertRaisesRegex(ValueError, 'unreviewed source snapshot'):
            preservation.preserve(self.root, self.run, 'secret-manifest')

    def test_source_mutation_during_copy_keeps_unfinalized_stage(self):
        original = preservation.shutil.copyfileobj
        changed = False
        def mutate(reader, writer, *args, **kwargs):
            nonlocal changed
            original(reader, writer, *args, **kwargs)
            if not changed:
                changed = True
                with open(reader.name, 'ab') as stream:
                    stream.write(b'changed-during-copy')
        with mock.patch.object(preservation.shutil, 'copyfileobj', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'changed during copy'):
                preservation.preserve(self.root, self.run, 'race')
        stage = self.root / 'output/preservation/race'
        self.assertTrue(stage.exists())
        self.assertFalse((stage / 'SHA256.json').exists())
        self.assertFalse((self.root / 'output/preservation/race.receipt.json').exists())

    def test_validation_parent_traversal_rejected_before_read_or_staging(self):
        with tempfile.TemporaryDirectory(dir=self.root.parent) as outside:
            external = Path(outside) / 'validation.json'
            external.write_bytes((self.collection / 'validation.json').read_bytes())
            traversal = self.root / '..' / Path(outside).name / 'validation.json'
            with mock.patch.object(preservation, 'read_json', wraps=preservation.read_json) as reader:
                with self.assertRaisesRegex(ValueError, 'parent traversal'):
                    preservation.preserve(self.root, self.run, 'traversal', validation=traversal)
                reader.assert_not_called()
            self.assertFalse((self.root / 'output/preservation').exists())

    def test_optional_depth_snapshot_preserved_but_other_research_paths_rejected(self):
        # Existing runs need no depth module; the ordinary fixture already passes.
        original = preservation.preserve(self.root, self.run, 'without-depth')
        self.assertNotIn('participant/research/depth_backprojection.py', json.dumps(
            artifacts.verify(self.root / original['stage_relative_path'])))
        name = 'participant/research/depth_backprojection.py'
        source = self.trace / 'source_snapshot' / name
        source.parent.mkdir(parents=True)
        source.write_text('# recorded depth backprojection source\n')
        attempt_path = self.trace / 'attempt.json'
        attempt = json.loads(attempt_path.read_text())
        attempt['source_snapshot']['files_sha256'][name] = artifacts.digest(source)
        self.write(attempt_path, attempt)
        receipt = preservation.preserve(self.root, self.run, 'with-depth')
        stage = self.root / receipt['stage_relative_path']
        relative = f'output/operator-traces/{self.run}/source_snapshot/{name}'
        self.assertEqual(artifacts.verify(stage)[relative]['sha256'], artifacts.digest(source))
        self.assertEqual((stage / relative).read_bytes(), source.read_bytes())
        other_name = 'participant/research/unreviewed_geometry.py'
        other = self.trace / 'source_snapshot' / other_name
        other.write_text('# unreviewed research source\n')
        attempt['source_snapshot']['files_sha256'][other_name] = artifacts.digest(other)
        self.write(attempt_path, attempt)
        with self.assertRaisesRegex(ValueError, 'unreviewed source snapshot path'):
            preservation.preserve(self.root, self.run, 'with-unreviewed-research')
        self.assertFalse((self.root / 'output/preservation/with-unreviewed-research').exists())

    def guided_fixture(self):
        self.modify(self.trace / 'attempt.json', user_guided={'enabled': True})
        guided = self.obs.parent / 'guided-00000'
        self.obs.rename(guided)
        self.obs = guided
        self.write(self.collection / 'supervisor_state.json',
                   {'schema': 'phyrc-supervisor-state-v1', 'active': False, 'held': False})
        hold = self.trace / 'user-review/hold-0001'
        hold.mkdir(parents=True)
        for name in preservation.OBS_REQUIRED:
            (hold / name).write_bytes(b'public observation fixture')
        cameras = {name.removesuffix('.png'): artifacts.digest(hold / name)
                   for name in preservation.OBS_REQUIRED if name.endswith('.png')}
        meta = {'schema': 'phyrc-user-review-v1', 'run_id': self.run, 'hold_id': hold.name,
                'observation_id': 'b' * 64, 'camera_sha256': cameras}
        self.write(hold / 'hold.json', meta)
        self.write(hold / 'published.json', dict(meta, commit_sha='a' * 40,
                                               verified_camera_sha256=cameras))
        inbox = hold / 'inbox'
        inbox.mkdir()
        (inbox / 'rejected.json').write_text('PRIVATE_UNREVIEWED_INBOX_SENTINEL')
        # Accepted human text lives in the private decisions event log.
        (self.trace / 'decisions.jsonl').write_text('accepted direction event\n')
        reset = self.collection / 'slot_reset'
        reset.mkdir()
        for name in ('before_settle.npz', 'after_settle.npz'):
            (reset / name).write_bytes(b'public reset observation fixture')
        return hold

    def checkpoint_fixture(self, directory, run_id):
        directory.mkdir(parents=True)
        key = directory.name
        slot = directory / ('slot_' + key + '.npz')
        slot.write_bytes(b'trusted slot fixture')
        receipt = {'schema': 'phyrc-held-checkpoint-v1', 'run_id': run_id,
                   'source_group': 'original-group', 'key': key,
                   'slot_path': '/output/' + slot.relative_to(self.root / 'output').as_posix(),
                   'slot_sha256': artifacts.digest(slot), 'slot_bytes': slot.stat().st_size,
                   'exact_physics_checkpoint': False}
        self.write(directory / 'receipt.json', receipt)
        return slot, receipt

    def test_guided_artifacts_preserved_without_inbox_or_runtime(self):
        self.guided_fixture()
        slot, receipt = self.checkpoint_fixture(self.collection / 'checkpoints/start', self.run)
        self.write(self.trace / 'start-checkpoint.json', {'active': True, 'held': True, 'checkpoint': receipt})
        result = preservation.preserve(self.root, self.run, 'guided')
        stage = self.root / result['stage_relative_path']
        inventory = artifacts.verify(stage)
        expected = [slot, slot.parent / 'receipt.json', self.trace / 'start-checkpoint.json',
                    self.trace / 'user-review/hold-0001/public_depth.npz',
                    self.collection / 'supervisor_state.json',
                    self.collection / 'slot_reset/before_settle.npz', self.obs / 'overview.png']
        for path in expected:
            self.assertIn(path.relative_to(self.root).as_posix(), inventory)
        for path in stage.rglob('*'):
            self.assertNotEqual(path.name, 'inbox')
            if path.is_file():
                self.assertNotIn(b'PRIVATE_', path.read_bytes())

    def test_web_segment_evidence_selects_acknowledged_actions_only(self):
        self.modify(self.trace / 'attempt.json', segment_review={'source_hz': 20},
                    user_guided={'enabled': True, 'hold_count': 2, 'current_hold': 'hold-0002',
                                 'observation_id': 'b' * 64})
        base = self.trace / 'segment-evidence'
        for number, end in ((1, 0), (2, 2)):
            hold = f'hold-{number:04d}'
            folder = base / hold
            folder.mkdir(parents=True)
            self.write(folder / 'actions.json', {'hold': hold, 'observation_id': 'ab'[number - 1] * 64,
                       'start_step': 0, 'end_step': end, 'actions': [] if not end else [{'start': 0, 'end': 2}]})
            (folder / 'segment.mp4').write_bytes(b'large transient clip')
        unpublished = base / 'hold-0003'
        unpublished.mkdir()
        (unpublished / 'actions.json').write_text('unpublished')
        receipt = preservation.preserve(self.root, self.run, 'segments')
        inventory = artifacts.verify(self.root / receipt['stage_relative_path'])
        self.assertEqual({name for name in inventory if '/segment-evidence/' in name},
                         {(base / hold / 'actions.json').relative_to(self.root).as_posix()
                          for hold in ('hold-0001', 'hold-0002')})
        final = base / 'hold-0002/actions.json'
        self.modify(final, start_step=1)
        with self.assertRaisesRegex(ValueError, 'range'):
            preservation.preserve(self.root, self.run, 'bad-range')
        self.modify(final, start_step=0, actions=[])
        with self.assertRaisesRegex(ValueError, 'incomplete segment action range'):
            preservation.preserve(self.root, self.run, 'missing-actions')
        self.modify(final, actions=[{'start': 0, 'end': 2}], observation_id='e' * 64)
        with self.assertRaisesRegex(ValueError, 'final acknowledged hold'):
            preservation.preserve(self.root, self.run, 'bad-observation')
        final.unlink()
        with self.assertRaisesRegex(ValueError, 'missing/non-regular'):
            preservation.preserve(self.root, self.run, 'missing-segment')
        final.symlink_to(base / 'hold-0001/actions.json')
        with self.assertRaisesRegex(ValueError, 'symlink rejected'):
            preservation.preserve(self.root, self.run, 'linked-segment')

    def test_autonomous_review_preserves_actions_observations_and_prompt(self):
        hold = 'hold-0002'
        control = {'mode': 'gpt_only', 'hold_count': 2, 'current_hold': hold, 'observation_step': 2}
        attempt_path = self.trace / 'attempt.json'
        prompt_name = 'participant/collection/prompts/autonomous_full_dressing.txt'
        prompt = self.trace / 'source_snapshot' / prompt_name
        prompt.parent.mkdir(parents=True)
        prompt.write_text('autonomous task fixture')
        snapshot = json.loads(attempt_path.read_text())['source_snapshot']
        snapshot['files_sha256'][prompt_name] = artifacts.digest(prompt)
        self.modify(attempt_path, segment_review={'source_hz': 20}, autonomous_control=control,
                    source_snapshot=snapshot)
        observation = self.obs.with_name('autonomous-00000')
        self.obs.rename(observation)
        state = self.collection / 'supervisor_state.json'
        self.write(state, {'schema': 'phyrc-supervisor-state-v1', 'active': False})
        evidence = self.trace / 'segment-evidence'
        for name, end in [('hold-0001', 0), (hold, 2)]:
            folder = evidence / name
            folder.mkdir(parents=True)
            self.write(folder / 'actions.json', {'hold': name, 'observation_id': 'a' * 64,
                       'start_step': 0, 'end_step': end, 'actions': [{'start': 0, 'end': end}] if end else []})
        receipt = preservation.preserve(self.root, self.run, 'autonomous')
        inventory = artifacts.verify(self.root / receipt['stage_relative_path'])
        for path in [state, prompt, observation / 'public_depth.npz', observation / 'robot_1_wrist.png',
                     evidence / hold / 'actions.json', evidence / 'hold-0001/actions.json']:
            self.assertIn(path.relative_to(self.root).as_posix(), inventory)
        self.modify(attempt_path, autonomous_control=dict(control, observation_step=1))
        with self.assertRaisesRegex(ValueError, 'final acknowledged hold'):
            preservation.preserve(self.root, self.run, 'bad-endpoint')
        self.modify(attempt_path, autonomous_control=control)
        observation.rename(self.obs.with_name('guided-00000'))
        with self.assertRaisesRegex(ValueError, 'unexpected observation directory'):
            preservation.preserve(self.root, self.run, 'wrong-mode')

    def test_guided_checkpoint_hash_and_unreviewed_files_rejected(self):
        hold = self.guided_fixture()
        slot, _ = self.checkpoint_fixture(self.collection / 'checkpoints/start', self.run)
        original = slot.read_bytes()
        slot.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'checkpoint hash mismatch'):
            preservation.preserve(self.root, self.run, 'tampered-slot')
        slot.write_bytes(original)
        (hold / 'auth.json').write_text('secret')
        with self.assertRaisesRegex(ValueError, 'unreviewed user review file'):
            preservation.preserve(self.root, self.run, 'unreviewed-hold')
        self.assertFalse((self.root / 'output/preservation').exists())

    def test_initial_slot_reference_includes_parent_pair_and_checks_provenance(self):
        self.guided_fixture()
        slot, _ = self.checkpoint_fixture(self.root / 'output/states/parent-slot', 'parent-run')
        receipt_path = slot.parent / 'receipt.json'
        initial = {'path': '/output/states/parent-slot/' + slot.name,
                   'sha256': artifacts.digest(slot), 'receipt_path': '/output/states/parent-slot/receipt.json',
                   'receipt_sha256': artifacts.digest(receipt_path)}
        self.write(self.collection / 'run_metadata.json', {'initial_slot': initial})
        result = preservation.preserve(self.root, self.run, 'parent-slot')
        inventory = artifacts.verify(self.root / result['stage_relative_path'])
        self.assertIn('output/states/parent-slot/' + slot.name, inventory)
        initial['receipt_sha256'] = '0' * 64
        self.write(self.collection / 'run_metadata.json', {'initial_slot': initial})
        with self.assertRaisesRegex(ValueError, 'initial slot provenance mismatch'):
            preservation.preserve(self.root, self.run, 'bad-parent-slot')

    def test_guided_artifacts_rejected_without_explicit_guided_mode(self):
        self.guided_fixture()
        self.modify(self.trace / 'attempt.json', user_guided={'enabled': False})
        with self.assertRaisesRegex(ValueError, 'unreviewed'):
            preservation.preserve(self.root, self.run, 'not-guided')

    def test_start_validation_preserves_only_bound_evidence_and_rejects_logs(self):
        self.guided_fixture()
        validation = self.root / 'output/guided-validation/check-001'
        validation.mkdir(parents=True)
        evidence = []
        for name in ('report.json', 'checkpoint.json', 'original-held/public.npz',
                     'restored-before-settle/overview.png', 'restored-after-probe/robot_1_head.png'):
            path = validation / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'verified evidence fixture')
            evidence.append({'path': path.relative_to(self.root).as_posix(),
                             'sha256': artifacts.digest(path)})
        log = validation / 'simulator.log'
        log.write_text('PRIVATE_VALIDATION_LOG_SENTINEL')
        receipt = self.trace / 'start-state-validation.json'
        record = {'schema': 'phyrc-start-state-validation-v1', 'status': 'validated',
                  'evidence': evidence}
        self.write(receipt, record)
        result = preservation.preserve(self.root, self.run, 'with-validation-evidence')
        stage = self.root / result['stage_relative_path']
        inventory = artifacts.verify(stage)
        for item in evidence:
            self.assertIn(item['path'], inventory)
        self.assertNotIn(log.relative_to(self.root).as_posix(), inventory)
        record['evidence'][0]['sha256'] = '0' * 64
        self.write(receipt, record)
        with self.assertRaisesRegex(ValueError, 'evidence hash mismatch'):
            preservation.preserve(self.root, self.run, 'bad-evidence-hash')
        record['evidence'] = [{'path': log.relative_to(self.root).as_posix(),
                               'sha256': artifacts.digest(log)}]
        self.write(receipt, record)
        with self.assertRaisesRegex(ValueError, 'excluded source path'):
            preservation.preserve(self.root, self.run, 'secret-evidence')

    def test_archive_uses_existing_artifacts_format_and_restores(self):
        # Actual artifacts CLI, synthetic small data; no upload or GPU.
        script = self.root / 'participant/ops/artifacts.py'
        script.parent.mkdir(parents=True)
        script.write_text(Path(artifacts.__file__).read_text())
        receipt = preservation.preserve(self.root, self.run, 'packed', pack=True)
        archive = self.root / receipt['archive_relative_path']
        self.assertEqual(artifacts.digest(archive), receipt['archive_sha256'])
        import subprocess
        import sys
        restored = self.root / 'restored'
        subprocess.run([sys.executable, str(script), 'restore', str(restored), '--archive', str(archive)],
                       check=True, capture_output=True)
        manifest = artifacts.verify(restored)
        self.assertEqual(len(manifest), receipt['manifest_entries'])


if __name__ == '__main__':
    unittest.main()
