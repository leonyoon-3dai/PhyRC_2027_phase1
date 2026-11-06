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
