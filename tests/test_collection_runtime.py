"""CPU contracts for trusted timing/evaluation and spectator-only collection."""
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from participant.collection.boundary import CONTRACT, Operator
from participant.collection.evaluation import (
    CollectionEvaluation, RecordedEnvironment, RecordedWriter, public_interface)
from participant.streaming.collector_stream import observer_response, render_without_physics
from Policy.evaluation import Phase1Scorer, RATE_RULE
from Policy.training_dataset import DatasetWriter

spec = importlib.util.spec_from_file_location('collect_operator', Path(__file__).resolve().parents[1] / 'scripts/collect_operator.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def sample(tick, pickup=False):
    return dict(time_s=tick/240, physics_tick=tick, physics_dt_s=1/240,
                first_contact_tick=None, first_contact_time_s=None,
                rate_rule=RATE_RULE, gripper_holding=[pickup, False],
                garment_lifted_clear=pickup, gripper_lifted=[pickup, False],
                dressing_complete=False, wrist_in_sleeve={'left': False, 'right': False},
                garment_beyond_shoulder={'left': False, 'right': False},
                arm_coverage={'left': 0., 'right': 0.},
                upper_arm_coverage={'left': 0., 'right': 0.},
                upper_arm_sleeve_covered={'left': False, 'right': False},
                hand_out_of_sleeve={'left': False, 'right': False},
                neck_out=False, neck_passed=False, front_facing=False)


class Session:
    """Official CPU scorer with synthetic measurements; no simulation claim."""
    def __init__(self, output):
        self.output = output
        self.active = False
        self.last_report = None
        self.pickup = False
    def start(self, metadata):
        self.metadata = metadata
        self.path = self.output / 'test-episode'
        self.path.mkdir(parents=True)
        self.scorer = Phase1Scorer()
        self.dt = 1/240
        self.ticks = 0
        self.clock = SimpleNamespace(first_contact_tick=None)
        self.active = True
        self._record(sample(0, self.pickup))
    def _record(self, value):
        self.scorer.update(value)
    def advance(self):
        self.ticks += 12
        self._record(sample(self.ticks, self.pickup))
    def clock_result(self, _):
        return self.scorer.rate_result()
    def finish(self, reason, valid=True, take_final=True):
        self.active = False
        self.last_report = dict(valid=valid, reason=reason,
                                result=self.scorer.result() if valid else None)
        return self.last_report


class Env:
    def __init__(self, session=None):
        self.contract = deepcopy(CONTRACT)
        self.contract['default_dimensions'].update(height=16, width=16)
        self._runtime = dict(BASE_LINEAR_RATE=.1, BASE_ANGULAR_RATE=.2,
                             LIFT_RATE=.3, ARM_RATE=.4, WRIST_RATE=.5)
        self.session = session
    def observation(self, t, action=None):
        dims=self.contract['default_dimensions']
        out={}
        for name, item in self.contract['observations'].items():
            shape=tuple(dims.get(x,x) if isinstance(x,str) else x for x in item['shape'])
            out[name]=np.zeros(shape,dtype=item['dtype'])
        out['simulation_time_s']=np.array(t,np.float64)
        if action is not None: out['previous_action']=action.copy()
        return out
    def reset(self, **_):
        self.t=0
        joints=[{'name':f'joint_{i}', 'unit':'rad', 'secret':'do-not-copy'} for i in range(13)]
        self.info={'episode_id':1,'episode_seed':12345,'source_commit':'test',
                   'state':{'robots':[{'joints':joints},{'joints':joints}], 'cloth':'hidden'},
                   'cameras':[{'world_from_optical_column_vectors':'hidden'}]}
        return self.observation(0),self.info
    def step(self, action):
        self.t+=.05
        if self.session:self.session.advance()
        return self.observation(self.t,action),0,False,False,{'hidden':'never-public'}


class CollectionRuntimeTest(unittest.TestCase):
    def test_prompt_file_preserves_utf8_and_inline_compatibility(self):
        base = ['--output', '/unused-test-output', '--source', 'integration_test',
                '--source-group', 'prompt-test', '--model-id', 'test']
        prompt = '공개 관측만 사용합니다.\n두 번째 줄\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'prompt.txt'
            path.write_text(prompt, encoding='utf-8')
            parsed = collector.parse_arguments(base + ['--prompt-file', str(path)])
            self.assertEqual(parsed.prompt, prompt)
            self.assertEqual(collector.parse_arguments(base + ['--prompt', prompt]).prompt, prompt)
            path.write_bytes(b'a' * collector.MAX_PROMPT_BYTES)
            self.assertEqual(len(collector.parse_arguments(base + ['--prompt-file', str(path)]).prompt),
                             collector.MAX_PROMPT_BYTES)

    def test_prompt_file_rejects_oversize_invalid_utf8_and_dual_options(self):
        base = ['--output', '/unused-test-output', '--source', 'integration_test',
                '--source-group', 'prompt-test', '--model-id', 'test']
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(sys, 'stderr', io.StringIO()):
            path = Path(directory) / 'prompt.txt'
            for data in (b'a' * (collector.MAX_PROMPT_BYTES + 1), b'\xff'):
                path.write_bytes(data)
                with self.assertRaises(SystemExit) as error:
                    collector.parse_arguments(base + ['--prompt-file', str(path)])
                self.assertEqual(error.exception.code, 2)
            with self.assertRaises(SystemExit):
                collector.parse_arguments(base + ['--prompt', 'inline', '--prompt-file', str(path)])
            path.unlink()
            with self.assertRaises(SystemExit):
                collector.parse_arguments(base + ['--prompt-file', str(path)])

    def test_main_isolates_long_multiline_options_before_simulator_import(self):
        long_prompt = 'Public-only actor guidance\n--/app/renderer/unsafe-option=false\n' * 100
        original = ['collect_operator.py', '--output', '/unused-test-output',
                    '--source', 'integration_test', '--source-group', 'argv-test',
                    '--model-id', 'test', '--prompt', long_prompt, '--max-steps', '73']
        seen = {}
        fake_environment = ModuleType('Policy.environment')
        class SentinelEnvironment:
            def __init__(self, **config):
                seen['argv'] = list(sys.argv)
                seen['config'] = config
                raise RuntimeError('intentional CPU-only sentinel before Isaac startup')
        fake_environment.DressingEnv = SentinelEnvironment
        output, errors = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, 'argv', original.copy()), \
             mock.patch.dict(sys.modules, {'Policy.environment': fake_environment}), \
             mock.patch.object(collector, 'open_protocol_stream', return_value=output), \
             mock.patch.object(collector.signal, 'signal'), \
             mock.patch.object(sys, 'stderr', errors):
            result = collector.main()
        self.assertEqual(result, 1)
        self.assertEqual(seen['argv'], ['collect_operator.py'])
        self.assertEqual(seen['config'], {'max_episode_steps': 73})
        self.assertEqual(json.loads(output.getvalue()), {'ok': False, 'error': 'collector_error'})
        self.assertNotIn(long_prompt, output.getvalue())

    def test_native_stdout_cannot_contaminate_public_protocol(self):
        source = """
import contextlib, importlib.util, os, sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('collector',Path('scripts/collect_operator.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
protocol=module.open_protocol_stream()
with contextlib.redirect_stdout(sys.stderr):
    os.write(1,b'native simulator diagnostic\\n')
    print('Python simulator diagnostic')
    protocol.write('{"ready":true}\\n')
    protocol.flush()
protocol.close()
"""
        run = subprocess.run([sys.executable, '-c', source], capture_output=True, text=True,
                             cwd=Path(__file__).resolve().parents[1], check=True)
        self.assertEqual(run.stdout, '{"ready":true}\n')
        self.assertIn('native simulator diagnostic', run.stderr)
        self.assertIn('Python simulator diagnostic', run.stderr)

    def test_request_rejection_and_replay_guard(self):
        valid={'tool':'act','arguments':{'action':[[0.0]*9]*2,'steps':1},
               'request_id':'one','observation_step':0}
        self.assertEqual(collector.parse_request(json.dumps(valid),current_step=0,seen=set()),valid)
        for line,code in [('{"tool":"act","arguments":{"action":NaN}}','invalid_json'),
                          ('{"tool":"read","path":"private-evaluation.json"}','invalid_request'),
                          (json.dumps(dict(valid,observation_step=9)),'stale_observation'),
                          (json.dumps(valid),'duplicate_request')]:
            with self.assertRaises(collector.ProtocolError) as caught:
                collector.parse_request(line,current_step=0,seen={'one'})
            self.assertEqual(str(caught.exception),code)

    def test_stdin_reader_eof_and_oversized_line_recovery(self):
        inbox=queue.Queue()
        collector.read_requests(io.StringIO('x'*(collector.MAX_REQUEST_BYTES+1)+'\n{"tool":"stop"}\n'),inbox,threading.Event())
        self.assertEqual(inbox.get(),('error','request_too_large'))
        self.assertEqual(inbox.get(),('line','{"tool":"stop"}\n'))
        self.assertEqual(inbox.get(),('eof',None))

    def test_static_interface_does_not_copy_privileged_fields(self):
        env=Env();_,info=env.reset()
        value=public_interface(env,info)
        self.assertEqual(value['joint_names'][0][0],'joint_0')
        self.assertEqual(value['action_scales']['LIFT_RATE'],.3)
        self.assertEqual(len(value['camera_intrinsics']),5)
        text=json.dumps(value)
        for forbidden in ('hidden','episode_seed','world_from_optical','secret','cloth','spawn'):
            self.assertNotIn(forbidden,text)
        self.assertNotIn('eye_world_m',text)

    def test_render_only_clock_invariant_and_spectator_response(self):
        world=SimpleNamespace(current_time=1.,render=lambda:None)
        evaluation=SimpleNamespace(ticks=24)
        render_without_physics(SimpleNamespace(world=world),evaluation)
        world.render=lambda:setattr(world,'current_time',1.01)
        with self.assertRaisesRegex(RuntimeError,'observer_render_advanced_physics'):
            render_without_physics(SimpleNamespace(world=world),evaluation)
        payload=observer_response()
        self.assertFalse(payload['controls_enabled'])
        self.assertEqual(payload['server_keys'],[])
        self.assertEqual(payload['applied_keys'],[])

    def test_evaluation_zero_score_and_hdf5_remain_separate(self):
        import h5py
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'capture'
            session=Session(out/'evaluation')
            env=Env(session)
            wrapped=RecordedEnvironment(env)
            dataset=DatasetWriter(out,env.contract,{'source':'integration_test'})
            evaluation=CollectionEvaluation(env,out/'evaluation',session=session)
            writer=RecordedWriter(dataset,wrapped,evaluation)
            op=Operator(wrapped,writer,source='integration_test',source_group='test',model_id='test',prompt='test')
            public=op.begin()
            result=op.act(np.zeros((2,9),np.float32),2)
            op.finish_episode();writer.close()
            self.assertNotIn('score',public)
            self.assertEqual(set(result),{'active','observation'})
            report=json.loads((out/'evaluation_summary.json').read_text())['report']
            self.assertTrue(report['valid'])
            self.assertEqual(report['result']['raw_points'],0)
            self.assertEqual(report['result']['score_status'],'no_contact')
            self.assertIsNone(report['result']['final_score'])
            self.assertFalse(report['result']['success'])
            snapshots=[json.loads(x) for x in (session.path/'score_samples.jsonl').read_text().splitlines()]
            self.assertEqual([x['physics_tick'] for x in snapshots],[0,12,24])
            timings=[json.loads(x) for x in (out/'step_timings.jsonl').read_text().splitlines()]
            self.assertEqual(len(timings),2)
            with h5py.File(out/'audit.hdf5') as f:
                self.assertTrue(f['demo_0'].attrs['success_known'])
                self.assertFalse(f['demo_0'].attrs['success'])
            with h5py.File(out/'policy.hdf5') as f:
                self.assertNotIn('evaluation',f)
                np.testing.assert_array_equal(f['data/demo_0/actions'][:],f['data/demo_0/next_obs/previous_action'][:])

    def test_pickup_event_uses_official_hold_and_keeps_no_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=Session(Path(tmp)/'evaluation');session.pickup=True
            evaluation=CollectionEvaluation(None,session.output,session=session)
            evaluation.start({'source':'integration_test'})
            for _ in range(60):session.advance()
            report=evaluation.finish('test')
            events=[json.loads(x) for x in (session.path/'score_events.jsonl').read_text().splitlines()]
            pickup=[e for e in events if e['event']=='score_awarded' and e['stage']=='pickup']
            self.assertEqual(len(pickup),1)
            self.assertEqual(pickup[0]['physics_tick'],720)
            self.assertEqual(pickup[0]['points'],5)
            self.assertEqual(report['result']['score_status'],'no_contact')
            self.assertIsNone(report['result']['final_score'])
            self.assertFalse(report['result']['success'])


if __name__=='__main__':unittest.main()
