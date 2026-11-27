"""CPU coverage for the archived lineage and actual collector argv of the concurrent study."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from participant.collection import checkpoint, codex_client
from participant.ops import demo_pair as pair


class StopBeforeSimulator(Exception):
    pass


class PairTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.addendum = b'Use current cameras first.\n'
        self.base = b'Original rendered prompt with named action channels.'
        self.put(pair.ADDENDUM, self.addendum)
        self.put('participant/collection/prompts/autonomous_full_dressing.txt', b'Ordinary prompt')
        for file in checkpoint.SOURCE_FILES:
            self.put(file, b'original source')

    def put(self, key, data):
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode())
        return path

    def fixture(self, source):
        demo, old_demo, step, name = source
        old = f'original-{old_demo}'
        def member(path):
            return {'sha256': pair.digest(path), 'bytes': path.stat().st_size}
        key = f'step-{step}'
        prefix = f'output/collections/{old}/checkpoints/{key}'
        slot = self.put(f'{prefix}/slot_{key}.npz', b'save')
        receipt = self.put(f'{prefix}/receipt.json', {
            'schema': 'phyrc-held-checkpoint-v1', 'key': key, 'source_group': 'family',
            'run_id': old, 'observation_step': step, 'slot_sha256': pair.digest(slot), 'slot_bytes': 4,
            'source_files_sha256': {file: pair.digest(self.root / file) for file in checkpoint.SOURCE_FILES}})
        trace = f'output/operator-traces/{old}'
        prompt = self.put(trace + '/prompt.txt', self.base)
        attempt = self.put(trace + '/attempt.json', dict(run_id=old, finished=True, prompt_sha256=pair.digest(prompt),
            model='gpt-6.2-sol', reasoning_effort='ultra', actor_backend='exec', plan_size=1, decisions_requested=5))
        config = self.put(f'output/collections/{old}/run_metadata.json',
                          dict(source_group='family', max_steps=18000, evaluation_enabled=True))
        manifest = self.put(f'output/demo33-34-sources/demo{old_demo}-manifest.json',
                            {str(f.relative_to(self.root)):member(f) for f in (prompt, attempt, config)})
        self.put('docs/active/' + name, {'runs':[dict(run_id=old, demonstration=old_demo, manifest_sha256=pair.digest(manifest),
                 transitions=2346 if demo==33 else 2905, checkpoints=[dict(step=step, archive_member_prefix=prefix,
                 slot=dict(member(slot), path=slot.name), receipt=dict(member(receipt), path=receipt.name))])]})
        return prompt

    def test_actual_argv_reaches_expected_simulator_with_one_copy_of_each_prompt(self):
        for source in pair.SOURCES:
            with self.subTest(demo=source[0]):
                self.fixture(source)
                with patch.object(checkpoint, 'ROOT', self.root):
                    run = pair.source_plan(self.root, source, 'test')
                cmd = pair.collector_command(run)
                self.assertNotIn('--replay-prefix-run', cmd)
                self.assertEqual(run['local_stop'], 1146 if source[0] == 33 else None)
                path = cmd.index('--slot-study-original-prompt') + 1
                cmd[path] = str(self.root / cmd[path])
                with patch.object(codex_client, '__file__', str(self.root / 'participant/collection/codex_client.py')), \
                     patch.object(codex_client.signal, 'signal'), \
                     patch.object(codex_client, 'source_snapshot', return_value={}), \
                     patch.object(codex_client, 'Simulator', side_effect=StopBeforeSimulator) as sim, \
                     patch.object(sys, 'argv', cmd[2:]), self.assertRaises(StopBeforeSimulator):
                    codex_client.main()
                collector = sim.call_args.args[0]
                self.assertIn('/' + run['slot'], collector)
                self.assertNotIn('--nearest-table', collector)
                self.assertNotIn('--reset-seed', collector)
                trace = self.root / 'output/operator-traces' / run['run_id']
                actual = (trace / 'prompt.txt').read_bytes()
                self.assertEqual(actual, self.base + b'\n\n' + self.addendum)
                info = pair.read(trace / 'attempt.json')
                self.assertEqual(info['prompt_sha256'], hashlib.sha256(actual).hexdigest())
                self.assertEqual(info['slot_study']['stop_step'], run['local_stop'])
                self.assertEqual(info['slot_study']['historical_prompt_sha256'], run['source_prompt_sha256'])

    def test_two_workers_share_gpu_while_the_monitor_and_publisher_follow_one_manifest(self):
        folder = self.root / 'output/demo33-34/pair'
        args = SimpleNamespace(pair_id='pair', destination=self.root, proxy_port=8773)
        runs = []
        for source in pair.SOURCES:
            self.fixture(source)
            with patch.object(checkpoint, 'ROOT', self.root):
                run = pair.source_plan(self.root, source, 'pair')
            runs.append(dict(run, lane=f'lane{run["demo"]}', command=pair.collector_command(run)))
        plan = dict(schema='phyrc-concurrent-pair-v1', gpu_uuid='GPU-abcdef', runs=runs)
        jobs = []
        def start(cmd, env, log):
            proc = Mock(pid=len(jobs) + 10, returncode=0)
            proc.wait.return_value = 0
            proc.poll.return_value = 0
            jobs.append((cmd, env, log.name))
            if log.name == 'publisher.log':
                proc.poll.return_value = None
                pair.write(args.destination / 'PhyRC-compare.json', {'runs':runs})
            elif log.name == 'performance.log':
                proc.poll.return_value = None
                pair.write(folder / 'telemetry.json', {})
            elif log.name in ('demo33.log', 'demo34.log'):
                run_id = cmd[cmd.index('--run-id') + 1]
                self.put(f'output/operator-traces/{run_id}/attempt.json', {'status':'completed'})
                self.put(f'output/collections/{run_id}/capture.json', {'complete':True})
            return proc
        with patch.object(pair, 'ROOT', self.root), patch.object(pair, 'prepare_lanes'), \
             patch.object(pair, 'spawn', side_effect=start):
            self.assertEqual(pair.run_pair(args, folder, plan, {}), 0)
        self.assertEqual([j[2] for j in jobs], ['publisher.log','performance.log','demo33.log','demo34.log',
                                                  'demo33-qc.log','demo34-qc.log'])
        self.assertEqual([j[1]['PHYRC_STUDY_GPU_UUID'] for j in jobs[2:4]], ['GPU-abcdef']*2)
        self.assertEqual([j[1]['PHYRC_STUDY_LANE'] for j in jobs[2:4]], ['lane33','lane34'])
        final = pair.read(folder/'finished.json')
        self.assertEqual(final['state'], 'finished')
        self.assertTrue(all(r['qc_returncode'] == 0 for r in final['runs']))

    def test_modified_historical_prompt_or_physics_fails_before_launch(self):
        source = pair.SOURCES[0]
        prompt = self.fixture(source)
        with patch.object(checkpoint, 'ROOT', self.root):
            prompt.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'differs from archive'):
                pair.source_plan(self.root, source, 'test')
            prompt.write_bytes(self.base)
            (self.root / checkpoint.SOURCE_FILES[-1]).write_text('different source')
            with self.assertRaisesRegex(ValueError, 'compatibility'):
                pair.source_plan(self.root, source, 'test')

    def test_elbow_study_uses_one_shared_slot_with_distinct_tasks(self):
        original = self.fixture(pair.ELBOW_SOURCES[0])
        shared = self.put(pair.ELBOW_COMMON, b'Common elbow criterion')
        tasks = {35: b'Outer hem task', 36: b'Near cuff task'}
        for demo, path in pair.ELBOW_PROMPTS.items():
            self.put(path, tasks[demo])
        for source in pair.ELBOW_SOURCES:
            demo = source[0]
            with self.subTest(demo=demo), patch.object(checkpoint, 'ROOT', self.root):
                run = pair.source_plan(self.root, source, 'elbow')
                cmd = pair.collector_command(run)
                self.assertEqual(run['source_step'], 1200)
                self.assertEqual(run['local_stop'], 400)
                self.assertNotIn('--until-full-score-or-feedback', cmd)
                cmd[cmd.index('--slot-study-original-prompt') + 1] = str(original)
                task_args = [i + 1 for i, value in enumerate(cmd) if value == '--slot-study-task-prompt']
                self.assertEqual([cmd[i] for i in task_args], [str(pair.ELBOW_COMMON), str(pair.ELBOW_PROMPTS[demo])])
                for i in task_args:
                    cmd[i] = str(self.root / cmd[i])
                with patch.object(codex_client, '__file__', str(self.root / 'participant/collection/codex_client.py')), \
                     patch.object(codex_client.signal, 'signal'), \
                     patch.object(codex_client, 'source_snapshot', return_value={}), \
                     patch.object(codex_client, 'Simulator', side_effect=StopBeforeSimulator) as sim, \
                     patch.object(sys, 'argv', cmd[2:]), self.assertRaises(StopBeforeSimulator):
                    codex_client.main()
                self.assertIn('/' + run['slot'], sim.call_args.args[0])
                trace = self.root / 'output/operator-traces' / run['run_id']
                actual = (trace / 'prompt.txt').read_bytes()
                self.assertIn(shared.read_bytes() + b'\n\n' + tasks[demo], actual)
                self.assertNotIn(self.base, actual)
                for other_demo, other_task in tasks.items():
                    if other_demo != demo:
                        self.assertNotIn(other_task, actual)
                info = pair.read(trace / 'attempt.json')
                self.assertEqual(info['slot_study']['historical_prompt_sha256'], pair.digest(original))


if __name__ == '__main__':
    unittest.main()
