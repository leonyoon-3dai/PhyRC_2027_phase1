"""CPU production protocol/HDF5 regressions for live HOLD; no GPU claims."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from types import SimpleNamespace

import h5py
import numpy as np
from test_collection_runtime import collector, Env
from participant.collection.boundary import Operator
from Policy.training_dataset import DatasetWriter
from participant.collection.checkpoint import save_checkpoint, verify_checkpoint

ROOT = Path(__file__).resolve().parents[1]
FAKE = '''
import sys
from types import ModuleType
sys.path.insert(0, 'tests')
from test_collection_runtime import Env, collector
class FakeEnv(Env):
    def __init__(self, **kw): super().__init__()
    def close(self): pass
m=ModuleType('Policy.environment');m.DressingEnv=FakeEnv
sys.modules['Policy.environment']=m
sys.argv=['collect_operator','--output',sys.argv[1], '--source','gpt' if '--gpt-only' in sys.argv[2:] else 'integration_test',
'--source-group','hold-test','--model-id','none','--prompt','cpu test',
'--user-guided','--input-timeout','.15','--max-requests','4', *sys.argv[2:]]
raise SystemExit(collector.main())
'''


class GuidedCollectorTest(unittest.TestCase):
    def test_gpt_only_resume_requires_a_trusted_boolean(self):
        def parse(arguments, **mode):
            return collector.parse_request(json.dumps({'tool': 'resume', 'arguments': arguments}),
                                           current_step=0, seen=set(), **mode)

        args = {'hold_id': 'h1'}
        for value in (None, 0, 1, 'false'):
            with self.subTest(value=value), self.assertRaises(collector.ProtocolError):
                parse(dict(args, human_feedback=value), user_guided=True, gpt_only=True)
        with self.assertRaises(collector.ProtocolError):
            parse(args, user_guided=True, gpt_only=True)
        for mode in ({}, {'user_guided': True}):
            with self.assertRaises(collector.ProtocolError):
                parse(dict(args, human_feedback=False), **mode)
        self.assertEqual(parse(args, user_guided=True)['arguments'], args)

    def test_autonomous_resumes_preserve_recorded_gpt_source_until_feedback(self):
        commands = []
        for i, human_feedback in enumerate((False, True, False)):
            hold = f'h{i}'
            commands.extend([
                {'tool': 'hold', 'arguments': {'hold_id': hold, 'reason': 'review'}},
                {'tool': 'resume', 'arguments': {'hold_id': hold, 'human_feedback': human_feedback}},
                {'tool': 'act', 'arguments': {'action': np.zeros((2, 9)).tolist()}},
            ])
        commands.append({'tool': 'finish_episode'})
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'capture'
            result = subprocess.run(
                [sys.executable, '-c', FAKE, str(out), '--gpt-only'], cwd=ROOT,
                input=''.join(json.dumps(command) + '\n' for command in commands),
                capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertTrue(replies[0]['ready'])
            self.assertEqual([reply['ok'] for reply in replies[1:]], [True] * len(commands))
            with h5py.File(out / 'audit.hdf5') as audit:
                np.testing.assert_array_equal(audit['demo_0/operator_source_code'][:], [1, 2, 2])
            with h5py.File(out / 'policy.hdf5') as policy:
                self.assertEqual(len(policy['data/demo_0/actions']), 3)
            metadata = json.loads((out / 'run_metadata.json').read_text())
            self.assertTrue(metadata['gpt_only'])
            self.assertFalse(metadata['user_guided'])

    def test_supervisor_tools_are_opt_in_and_validate_ids(self):
        request=json.dumps({'tool':'hold','arguments':{'hold_id':'h1','reason':'review'}})
        with self.assertRaises(collector.ProtocolError):
            collector.parse_request(request,current_step=0,seen=set())
        self.assertEqual(collector.parse_request(request,current_step=0,seen=set(),user_guided=True)['tool'],'hold')
        for args in ({'key':'../F1'}, {'key':'x','path':'/bad'}, {'key':'/tmp/a'}):
            with self.assertRaises(collector.ProtocolError):
                collector.parse_request(json.dumps({'tool':'save_checkpoint','arguments':args}),
                                        current_step=0,seen=set(),user_guided=True)

    def test_held_wait_rejection_resume_and_finish_use_no_extra_transitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'capture'
            with (Path(tmp)/'log').open('w') as log:
                p=subprocess.Popen([sys.executable,'-c',FAKE,str(out)],cwd=ROOT,
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True)
                try:
                    self.assertTrue(json.loads(p.stdout.readline())['ready'])
                    count=0
                    def send(tool,args=None,step=0):
                        nonlocal count
                        count+=1
                        p.stdin.write(json.dumps({'tool':tool,'arguments':args or {},
                            'observation_step':step,'request_id':str(count)})+'\n');p.stdin.flush()
                        return json.loads(p.stdout.readline())
                    act=send('act',{'action':[[0.]*9]*2,'steps':1})
                    held=send('hold',{'hold_id':'h1','reason':'user review'},1)
                    before=held['result']['observation']
                    time.sleep(.4)  # Exceeds real collector idle timeout.
                    for _ in range(6):  # Also exceeds request limit while held.
                        self.assertEqual(send('observe',step=1)['result'],before)
                    self.assertEqual(send('act',{'action':[[0.]*9]*2},1)['error'],'episode_held')
                    self.assertEqual(send('resume',{'hold_id':'old'},1)['error'],'stale_hold')
                    self.assertEqual(send('resume',{'hold_id':'h1'},1)['observation_step'],1)
                    moved=send('act',{'action':[[0.]*9]*2},1)
                    self.assertEqual(moved['observation_step'],2)
                    send('hold',{'hold_id':'h2','reason':'done'},2)
                    send('finish_episode',step=2)
                    p.stdin.close();self.assertEqual(p.wait(timeout=10),0)
                    with h5py.File(out/'policy.hdf5') as f:
                        self.assertTrue(f.attrs['complete'])
                        self.assertEqual(f['data/demo_0/actions'].shape[0],2)
                    events=[json.loads(s) for s in (out/'operator.jsonl').read_text().splitlines()]
                    self.assertNotIn('shutdown_neutral_step',[s['event'] for s in events])
                finally:
                    if p.poll() is None:p.terminate();p.wait(timeout=10)
                    p.stdout.close()
                    if not p.stdin.closed:p.stdin.close()

    def test_eof_stays_held_until_signal_and_signal_adds_no_motion(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'capture'
            with (Path(tmp)/'log').open('w') as log:
                p=subprocess.Popen([sys.executable,'-c',FAKE,str(out)],cwd=ROOT,
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True)
                try:
                    self.assertTrue(json.loads(p.stdout.readline())['ready'])
                    p.stdin.close();time.sleep(.4)
                    self.assertIsNone(p.poll())
                    status=json.loads((out/'supervisor_state.json').read_text())
                    self.assertTrue(status['held']);self.assertEqual(status['observation_step'],0)
                    p.terminate();self.assertEqual(p.wait(timeout=10),1)
                    capture=json.loads((out/'capture.json').read_text())
                    self.assertEqual(capture['steps'],0);self.assertFalse(capture['complete'])
                finally:
                    if p.poll() is None:p.kill();p.wait()
                    p.stdout.close()

    def test_checkpoint_never_overwrites_and_preserves_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'capture'
            env=Env();writer=DatasetWriter(output,env.contract,{})
            op=Operator(env,writer,source='gpt',source_group='sg',model_id='test',prompt='test')
            op.begin();op.act(np.zeros((2,9),np.float32));op.hold('h1','test')
            before=op.observe()
            def save(key,*args):
                np.savez_compressed(Path(module.STATE_DIR)/('slot_'+key+'.npz'),
                    scene_geometry_revision='test',g0_pos=np.zeros((3,3)),g0_vel=np.zeros((3,3)),
                    placement_human=np.eye(4),placement_chair=np.eye(4))
                return True
            module=SimpleNamespace(STATE_DIR='original',_STATE_GEOMETRY_REVISION='test',save_state_slot=save)
            sim=SimpleNamespace(M=module,world=SimpleNamespace(current_time=1.5),cloths=[],rigs=[])
            receipt=save_checkpoint(sim,op,Path(tmp)/'slots','unique',run_id='run',source_group='sg')
            self.assertFalse(receipt['exact_physics_checkpoint']);self.assertFalse(receipt['restore_validated'])
            self.assertEqual(verify_checkpoint(receipt['slot_path'],source_group='sg')['run_id'],'run')
            with self.assertRaisesRegex(ValueError,'source_group_mismatch'):
                verify_checkpoint(receipt['slot_path'],source_group='wrong')
            self.assertEqual(module.STATE_DIR,'original');self.assertEqual(op._tick,12)
            for name in before:np.testing.assert_array_equal(before[name],op.observe()[name])
            with self.assertRaises(FileExistsError):
                save_checkpoint(sim,op,Path(tmp)/'slots','unique',run_id='run',source_group='sg')
            self.assertFalse(writer.policy.attrs['complete']);self.assertFalse(writer.episode.attrs['complete'])
            receipt_path=Path(receipt['slot_path']).parent/'receipt.json'
            changed=dict(receipt,source_files_sha256={})
            receipt_path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'manifest_incomplete'):
                verify_checkpoint(receipt['slot_path'],source_group='sg')
            receipt_path.write_text(json.dumps(receipt))
            Path(receipt['slot_path']).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'hash_mismatch'):
                verify_checkpoint(receipt['slot_path'],source_group='sg')
            op.finish_episode();writer.close()


if __name__=='__main__':unittest.main()
