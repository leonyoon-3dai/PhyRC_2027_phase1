"""CPU optional-depth orchestration tests; no real model/Docker/simulator."""
from copy import deepcopy
import ast
import hashlib
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

from types import ModuleType, SimpleNamespace
import subprocess

from participant.collection import codex_actor, codex_client as client
from participant.collection import depth_query as dq, export_report as exporter

# Fixed pre-feature source is an independent oracle for flag-OFF behavior.
# The tests run in this repository checkout; no source is delivered to an actor.
ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '05152fa4bf250257481cae988b6f8f26c817084a'
baseline = ModuleType('pixel_query_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(subprocess.check_output(['git', 'show', BASE_COMMIT + ':participant/collection/codex_client.py'],
    cwd=ROOT, text=True), baseline.__file__, 'exec'), baseline.__dict__)
# The approved E17 table-support alternative changed only A's prompt after the
# pre-query baseline. Keep the old execution oracle and import that one approved
# string from a fixed publication, rather than from the code under test.
PUBLIC_A_SOURCE = subprocess.check_output(
    ['git', 'show', '75492d7:participant/collection/codex_client.py'], cwd=ROOT, text=True)
PUBLIC_A_TASK = next(ast.literal_eval(node.value) for node in ast.parse(PUBLIC_A_SOURCE).body
    if isinstance(node, ast.Assign) and len(node.targets) == 1
    and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'REGRASP_HEM_TASK')


def action():
    return {'tool': 'finish_episode', 'action': [[0.]*9 for _ in range(2)], 'steps': 1,
            'stage': 'preparation', 'visual_assessment': 'uncertain', 'reason': 'CPU fixture.'}


def interface():
    matrix = [[200., 0., 128.], [0., 200., 128.], [0., 0., 1.]]
    return {'camera_intrinsics': {c: deepcopy(matrix) for c in dq.CAMERAS},
            'camera_calibration': [{'id': c, 'resolution_wh': [256, 256], 'intrinsics': deepcopy(matrix)}
                                   for c in dq.CAMERAS], 'private_scene_canary': 'NEVER_ACTOR'}


def observation():
    depth = np.full((5, 256, 256, 1), .75, np.float32)
    valid = np.ones(depth.shape, bool)
    valid[:, 0, 0, 0] = False
    return {'simulation_time_s': 2., 'depth': depth, 'depth_valid': valid,
            'rgb': np.full((5, 256, 256, 3), 50, np.uint8), 'private_scene_canary': 'NEVER_ACTOR'}


class QueryTests(unittest.TestCase):
    def run_client(self, *, module=client, enabled=True, scenario='query', image_change=False, depth_panel=False, history=False, strategy='general'):
        calls, requests, order, handlers, commands = [], [], [], {}, []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collection = root/'output/collections/cpu-query'
            class Simulator:
                def __init__(self, command, *args):
                    commands.append(command)
                    self.process = mock.Mock(pid=123); self.process.poll.return_value = None
                    self.obs = observation(); self.steps = 0
                    collection.mkdir(parents=True)
                def receive(self):
                    return {'ready': True, 'observation': self.obs, 'public_interface': interface()}
                def dispatch(self, tool, args=None):
                    order.append(tool); requests.append((tool, deepcopy(args)))
                    if tool != 'finish_episode':
                        self.steps += 1 if tool == 'stop' else args['steps']
                        self.obs['simulation_time_s'] += (1 if tool == 'stop' else args['steps'])/20
                        self.obs['rgb'][:] = 50 + self.steps
                    else:
                        (collection/'capture.json').write_text(json.dumps({'complete': True, 'steps': self.steps}))
                    return {'active': tool != 'finish_episode', 'observation': self.obs}
                def close(self): return 0
            def prepare(obs, folder):
                folder.mkdir(parents=True)
                payload = {'public_robot_observation': {'simulation_time_s': obs['simulation_time_s']},
                           'rgb_image_order': list(dq.CAMERAS)}
                (folder/'observation.json').write_text(json.dumps(payload))
                np.savez_compressed(folder/'public_depth.npz', depth=obs['depth'], depth_valid=obs['depth_valid'])
                images = []
                for i,camera in enumerate(dq.CAMERAS):
                    path=folder/(camera+'.png');Image.fromarray(obs['rgb'][i]).save(path);images.append(path)
                return payload, images
            class Actor:
                last_call_timing = {'process_wall_s': .1, 'completed': False}
                def __init__(self, *args, **kwargs):
                    self.timeout_s=kwargs['timeout_s']
                def invoke(self, prompt, images, schema):
                    n=len(calls)
                    order.append('call'+str(n))
                    calls.append({'prompt': prompt, 'images': [p.read_bytes() for p in images],
                                  'schema': deepcopy(schema), 'timeout': self.timeout_s})
                    if scenario == 'timeout_first' or (scenario == 'timeout_second' and n==1):
                        raise TimeoutError('CPU timeout')
                    value=action()
                    initial_extended='depth_query' in schema['properties']
                    if initial_extended:
                        value['depth_query']=None
                    if enabled and scenario != 'direct' and (n==0 or scenario=='repeat_query'
                                                            or (scenario=='two_queries' and n==2)):
                        context=json.loads(next(line.split(': ',1)[1] for line in prompt.splitlines()
                                                if line.startswith('frozen_public_depth_query_context: ')))
                        request={'kind':'depth_query','observation_id':context['frozen_observation_id'],
                                 'camera':'robot_1_wrist','pixels_uv':[[128,128],[0,0]],'include_camera_geometry':True}
                        if scenario=='stale':request['observation_id']='0'*64
                        if scenario=='over_budget':request['pixels_uv']=[[128,128]]*9
                        if scenario=='bool_pixel':request['pixels_uv']=[[True,128]]
                        value.update(tool='depth_query',depth_query=request)
                        if scenario=='nonzero_placeholder':value['action'][0][3]=.01
                    if scenario=='two_queries' and n==1:
                        value=action();value.update(tool='act',steps=2)
                        value['action'][0][3]=.03
                    if scenario=='mixed_action':value.update(tool='act')
                    if scenario=='invalid_second' and n==1:value['tool']='depth_query'
                    if image_change and n==0:images[0].write_bytes(b'changed')
                    if scenario=='interrupt_first' and n==0:handlers[signal.SIGTERM](signal.SIGTERM,None)
                    if scenario=='interrupt_second' and n==1:handlers[signal.SIGTERM](signal.SIGTERM,None)
                    usage={key:0 for key in module.USAGE_FIELDS}
                    usage.update(input_tokens=100+60*n, output_tokens=10*(n+1))
                    return {'decision':value,'session_id':'PRIVATE_SESSION_CANARY','usage':usage,
                            'wall_s':.25,'model':'gpt-6-astra','effort':'ultra','cli_version':'CPU-fixture'}
                def close(self): pass
            argv=['client','--run-id','cpu-query','--decisions','2' if scenario=='two_queries' else '1','--model-timeout','180']
            if enabled:argv+=['--pixel-depth-query']
            if history or strategy != 'general':
                argv += ['--mode', 'dressing', '--strategy', strategy]
            prefix=SimpleNamespace(actions=np.zeros((3,2,9),np.float32),
                trusted_metadata={'reset_seed':123987},
                public_lineage={'source_group':'PRIVATE_LINEAGE', 'replay_steps':3},
                initial_public_state={'simulation_time_s':np.asarray(2.)},
                final_public_state={'simulation_time_s':np.asarray(2.15)})
            if history:
                argv += ['--replay-prefix-run','private-parent','--replay-prefix-steps','3',
                         '--replay-observe-steps','1','2']
            if depth_panel:argv+=['--wrist-depth-panel']
            original_lookup=dq.lookup
            def lookup(*args):
                result=original_lookup(*args)
                if scenario=='interrupt_after_query':handlers[signal.SIGTERM](signal.SIGTERM,None)
                return result
            caught=None
            with mock.patch.object(module,'__file__',str(root/'participant/collection/codex_client.py')), \
                 mock.patch.object(module,'Simulator',Simulator), mock.patch.object(module,'prepare_observation',prepare), \
                 mock.patch.object(module,'source_snapshot',return_value={}), mock.patch.object(codex_actor,'Actor',Actor), \
                 mock.patch.object(module.signal,'signal',side_effect=lambda sig,fn:handlers.__setitem__(sig,fn)), \
                 mock.patch.object(sys,'argv',argv),mock.patch('builtins.print'),mock.patch.object(dq,'lookup',lookup), \
                 mock.patch('participant.collection.continuation.load_replay_prefix',return_value=prefix), \
                 mock.patch('participant.collection.milestones.write_index'), \
                 mock.patch.object(module,'official_review_points',return_value=0):
                try:module.main()
                except BaseException as error:caught=error
            trace=root/'output/operator-traces/cpu-query'
            attempt=json.loads((trace/'attempt.json').read_text())
            events=[json.loads(row) for row in (trace/'decisions.jsonl').read_text().splitlines()]
            public,skipped=exporter.public_events(trace/'decisions.jsonl')
            return dict(attempt=attempt,events=events,public=public,skipped=skipped,calls=calls,
                        requests=requests,order=order,commands=commands,error=caught)

    def test_default_schema_prompt_image_commands_and_calls_identical(self):
        old=self.run_client(module=baseline,enabled=False,scenario='direct')
        new=self.run_client(enabled=False,scenario='direct')
        self.assertIsNone(old['error']);self.assertIsNone(new['error'])
        for key in ('calls','requests','order','commands'):self.assertEqual(old[key],new[key])
        self.assertEqual(client.SCHEMA,baseline.SCHEMA)
        self.assertNotIn('pixel_depth_query',new['attempt'])

    def test_direct_action_uses_one_model_call_and_original_action(self):
        r=self.run_client(scenario='direct')
        self.assertIsNone(r['error']);self.assertEqual(r['order'],['call0','finish_episode'])
        self.assertEqual(r['attempt']['actor_calls_attempted'],1)
        self.assertEqual(r['attempt']['decisions_completed'],1)
        self.assertEqual(r['attempt']['pixel_depth_query']['queries_completed'],0)

    def test_query_followup_frozen_inputs_original_schema_and_separate_usage(self):
        r=self.run_client();self.assertIsNone(r['error'])
        self.assertEqual(r['order'],['call0','call1','finish_episode'])
        self.assertEqual(r['calls'][1]['schema'],baseline.SCHEMA)
        self.assertEqual(r['calls'][0]['images'],r['calls'][1]['images'])
        self.assertTrue(r['calls'][1]['prompt'].startswith(r['calls'][0]['prompt']))
        self.assertEqual([c['timeout'] for c in r['calls']],[180,180])
        command=r['commands'][0]
        self.assertEqual(command[command.index('--input-timeout')+1],'480.0')
        a=r['attempt'];self.assertEqual(a['actor_calls_attempted'],2);self.assertEqual(a['decisions_completed'],1)
        self.assertEqual(a['actor_usage']['input_tokens'],160)
        self.assertEqual(a['actor_usage_accounting']['calls_recorded'],2)
        call_events=[e for e in r['events'] if e['type']=='model_call']
        self.assertEqual([e['usage_accounting']['incremental_usage']['input_tokens'] for e in call_events],[100,60])
        self.assertEqual(call_events[0]['frozen_observation_id'],call_events[1]['frozen_observation_id'])
        self.assertNotEqual(call_events[0]['input_sha256'],call_events[1]['input_sha256'])
        decision=next(e for e in r['events'] if e['type']=='decision')
        self.assertEqual(decision['input_sha256'],call_events[1]['input_sha256'])
        self.assertEqual(decision['model_call_index'],1)
        query=next(e for e in r['public'] if e['type']=='depth_query_result')
        self.assertEqual(query['response']['results'][0]['optical_z_m'],.75)
        self.assertIsNone(query['response']['results'][1]['optical_z_m'])
        self.assertFalse(query['executed'])
        self.assertEqual(query['response_sha256'],dq.sha(query['response']))
        for event,call in zip(call_events,r['calls']):
            self.assertEqual(event['schema_sha256'],hashlib.sha256(json.dumps(call['schema'],allow_nan=False).encode()).hexdigest())
        self.assertNotIn('PRIVATE_SESSION_CANARY',json.dumps(r['public']))
        self.assertNotIn('NEVER_ACTOR',json.dumps(r['calls'],default=lambda b:'image-bytes'))

    def test_invalid_initial_queries_fail_closed_with_usage_preserved(self):
        for scenario in ('stale','over_budget','bool_pixel','nonzero_placeholder','mixed_action'):
            with self.subTest(scenario=scenario):
                r=self.run_client(scenario=scenario)
                self.assertIsInstance(r['error'],ValueError)
                self.assertEqual(len(r['calls']),1);self.assertEqual(r['attempt']['decisions_completed'],0)
                self.assertEqual(r['attempt']['actor_usage']['input_tokens'],100)
                self.assertEqual(r['requests'],[('stop',None),('finish_episode',None)])

    def test_followup_query_or_invalid_action_never_executes(self):
        for scenario in ('repeat_query','invalid_second'):
            with self.subTest(scenario=scenario):
                r=self.run_client(scenario=scenario);self.assertIsInstance(r['error'],ValueError)
                self.assertEqual(r['attempt']['actor_usage']['input_tokens'],160)
                self.assertEqual(r['attempt']['decisions_completed'],0)
                self.assertEqual(r['requests'],[('stop',None),('finish_episode',None)])

    def test_timeout_records_unknown_call_without_losing_prior_usage(self):
        for scenario,count,known in [('timeout_first',1,0),('timeout_second',2,100)]:
            with self.subTest(scenario=scenario):
                r=self.run_client(scenario=scenario);self.assertIsInstance(r['error'],TimeoutError)
                a=r['attempt'];self.assertEqual(a['actor_calls_attempted'],count)
                self.assertEqual(a['actor_usage'].get('input_tokens',0),known)
                self.assertEqual(a['actor_usage_accounting']['calls_recorded'],count)
                self.assertFalse(a['actor_usage_accounting']['fully_known'])
                self.assertEqual(a['actor_usage_accounting']['unknown_call_indices'],[count-1])

    def test_interrupt_after_query_before_action_preserves_all_completed_calls(self):
        for scenario,calls,queries,tokens in [('interrupt_first',1,0,100),('interrupt_after_query',1,1,100),
                                             ('interrupt_second',2,1,160)]:
            with self.subTest(scenario=scenario):
                r=self.run_client(scenario=scenario);self.assertIsInstance(r['error'],KeyboardInterrupt)
                a=r['attempt'];self.assertEqual(a['status'],'interrupted')
                self.assertEqual(a['actor_calls_attempted'],calls);self.assertEqual(a['actor_usage']['input_tokens'],tokens)
                self.assertEqual(a['pixel_depth_query']['queries_completed'],queries)
                self.assertEqual(a['decisions_completed'],0)
                self.assertEqual(r['requests'],[('stop',None),('finish_episode',None)])

    def test_changed_image_rejected_before_followup(self):
        r=self.run_client(image_change=True)
        self.assertIsInstance(r['error'],ValueError);self.assertEqual(len(r['calls']),1)
        self.assertEqual(r['attempt']['actor_calls_attempted'],1)

    def test_six_images_with_existing_depth_panel_are_reused_and_recorded_per_call(self):
        r=self.run_client(depth_panel=True);self.assertIsNone(r['error'])
        self.assertEqual([len(c['images']) for c in r['calls']],[6,6])
        self.assertEqual(r['calls'][0]['images'],r['calls'][1]['images'])
        records=r['attempt']['wrist_depth_panel']['model_inputs']
        self.assertEqual([v['model_call_index'] for v in records],[0,1])
        self.assertEqual(records[0]['ordered_images'],records[1]['ordered_images'])

    def test_sixteen_images_keep_current_history_and_depth_order_in_both_calls(self):
        r=self.run_client(depth_panel=True,history=True)
        self.assertIsNone(r['error'])
        self.assertEqual([len(c['images']) for c in r['calls']],[16,16])
        self.assertEqual(r['calls'][0]['images'],r['calls'][1]['images'])
        history=r['attempt']['replay_visual_history']
        self.assertEqual(history['delivery'],'first_observation_query_cycle')
        groups=history['first_model_input']['image_context']['groups']
        self.assertEqual([g['kind'] for g in groups],
                         ['current','historical_same_episode','historical_same_episode'])
        self.assertEqual([g['image_indices'] for g in groups],
                         [list(range(5)),list(range(5,10)),list(range(10,15))])
        for call in r['calls']:
            for forbidden in ('PRIVATE_LINEAGE','123987','private-parent','raw_points'):
                self.assertNotIn(forbidden,call['prompt'])
        call0,call1=r['order'].index('call0'),r['order'].index('call1')
        self.assertEqual(r['order'][call0:call1+1],['call0','call1'])
        records=r['attempt']['wrist_depth_panel']['model_inputs']
        self.assertEqual([x['panel']['image_index'] for x in records],[15,15])
        self.assertEqual(records[0]['ordered_images'],records[1]['ordered_images'])
        self.assertEqual(r['attempt']['simulation_steps'],3)  # only the fake replay

    def test_three_new_strategies_keep_their_tasks_and_query_dispatch_separate(self):
        for strategy,task in [('coordinated-support-diagnostic',client.SUPPORT_DIAGNOSTIC_TASK),
                              ('coordinated-regrasp-hem',client.REGRASP_HEM_TASK),
                              ('coordinated-support-guide',client.SUPPORT_GUIDE_TASK)]:
            with self.subTest(strategy=strategy):
                r=self.run_client(strategy=strategy)
                self.assertIsNone(r['error'])
                self.assertEqual(r['attempt']['strategy'],strategy)
                self.assertIn(task,r['calls'][0]['prompt'])
                self.assertEqual(r['order'],['call0','call1','finish_episode'])
                self.assertEqual(r['attempt']['simulation_steps'],0)

    def test_opt_out_is_unchanged_for_all_new_strategies_and_sixteen_images(self):
        for strategy in ('coordinated-support-diagnostic','coordinated-regrasp-hem',
                         'coordinated-support-guide'):
            with self.subTest(strategy=strategy):
                flags=dict(enabled=False,scenario='direct',strategy=strategy,history=True,depth_panel=True)
                with mock.patch.object(baseline, 'REGRASP_HEM_TASK', PUBLIC_A_TASK):
                    old=self.run_client(module=baseline,**flags)
                new=self.run_client(**flags)
                self.assertIsNone(old['error']);self.assertIsNone(new['error'])
                for key in ('calls','requests','order','commands'):
                    self.assertEqual(old[key],new[key])

    def test_lookup_preserves_exact_optical_z_invalids_and_bounds(self):
        obs=observation()
        obs['depth'][0,10,10,0]=np.float32(2.1234567)
        obs['depth'][0,20,20,0]=np.nan
        obs['depth'][0,21,21,0]=0
        sources={k:'a'*64 for k in ['observation_json','public_depth_npz',*[c+'_rgb' for c in dq.CAMERAS]]}
        frame=dq.freeze_public_frame(obs,interface(),sources,'cpu',0)
        req=dict(kind='depth_query',observation_id=frame.observation_id,camera='overview',
                 pixels_uv=[[10,10],[20,20],[21,21],[0,0],[255,255],[256,0],[-1,0]],
                 include_camera_geometry=True)
        result=dq.lookup(frame,req)['results']
        self.assertEqual(result[0]['optical_z_m'],float(obs['depth'][0,10,10,0]))
        self.assertNotEqual(result[0]['camera_range_m'],result[0]['optical_z_m'])
        self.assertEqual([r['status'] for r in result],
                         ['valid','invalid','invalid','invalid','valid','out_of_bounds','out_of_bounds'])
        self.assertTrue(all(result[i]['optical_z_m'] is None for i in [1,2,3,5,6]))

    def test_budget_resets_only_after_a_real_action_and_new_observation(self):
        r=self.run_client(scenario='two_queries');self.assertIsNone(r['error'])
        self.assertEqual(r['order'],['call0','call1','act','call2','call3','finish_episode'])
        self.assertEqual(r['attempt']['actor_calls_attempted'],4)
        self.assertEqual(r['attempt']['decisions_completed'],2)
        self.assertEqual(r['attempt']['pixel_depth_query']['queries_completed'],2)
        calls=[v for v in r['events'] if v['type']=='model_call']
        self.assertEqual(calls[0]['frozen_observation_id'],calls[1]['frozen_observation_id'])
        self.assertEqual(calls[2]['frozen_observation_id'],calls[3]['frozen_observation_id'])
        self.assertNotEqual(calls[0]['frozen_observation_id'],calls[2]['frozen_observation_id'])

    def test_incompatible_flags_reject_before_start(self):
        for flags in (['--actor-backend','app-server'],['--plan-size','2'],['--model-timeout','181']):
            with mock.patch.object(sys,'argv',['client','--run-id','reject','--pixel-depth-query',*flags]), \
                 mock.patch.object(client.signal,'signal'),mock.patch.object(client,'Simulator') as sim, \
                 mock.patch('sys.stderr'),self.assertRaises(SystemExit):
                client.main()
            sim.assert_not_called()

    def test_frame_copies_public_arrays_and_ignores_extra_input_fields(self):
        obs=observation();sources={k:'a'*64 for k in ['observation_json','public_depth_npz',*[c+'_rgb' for c in dq.CAMERAS]]}
        frame=dq.freeze_public_frame(obs,interface(),sources,'cpu',0)
        old=frame.observation_id;obs['depth'][:]=99;sources['public_depth_npz']='b'*64
        self.assertEqual(float(frame.depth[0,128,128,0]),.75)
        self.assertEqual(frame.observation_id,old);self.assertFalse(frame.depth.flags.writeable)
        request={'kind':'depth_query','observation_id':old,'camera':'robot_0_wrist',
                 'pixels_uv':[[128,128],[-1,128]],'include_camera_geometry':True}
        result=dq.lookup(frame,request)
        self.assertEqual(result['results'][0]['camera_xyz_m'],[0.,0.,.75])
        self.assertIsNone(result['results'][1]['optical_z_m'])
        self.assertNotIn('NEVER_ACTOR',json.dumps(result))


if __name__=='__main__':unittest.main(verbosity=2)
