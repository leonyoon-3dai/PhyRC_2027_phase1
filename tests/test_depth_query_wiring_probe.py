"""CPU fake-collector coverage of the model-free GPU wiring driver."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from participant.collection import codex_actor, codex_client, depth_query as dq
from scripts.probe_depth_query_protocol import synthetic_observation
from scripts.probe_depth_query_wiring import MODEL_ID, WiringFixtureActor, run_probe


class DepthQueryWiringProbeTest(unittest.TestCase):
    def run_fixture(self, *, short_lift=False):
        requests, commands = [], []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collection = root / 'output/collections/cpu-depth-wiring'

            class Simulator:
                def __init__(self, command, *_):
                    commands.append(command)
                    self.process = mock.Mock(pid=123)
                    self.process.poll.return_value = None
                    self.steps = 0
                    collection.mkdir(parents=True)

                def obs(self):
                    return synthetic_observation(20 + self.steps)

                def receive(self):
                    matrix = [[200.,0.,128.],[0.,200.,128.],[0.,0.,1.]]
                    interface = {
                        'camera_intrinsics': {c: deepcopy(matrix) for c in dq.CAMERAS},
                        'camera_calibration': [{'id': c, 'resolution_wh': [256,256],
                                                'intrinsics': deepcopy(matrix)} for c in dq.CAMERAS]}
                    return {'ready': True, 'observation': self.obs(), 'public_interface': interface}

                def dispatch(self, tool, arguments=None):
                    requests.append((tool,deepcopy(arguments)))
                    if tool == 'finish_episode':
                        (collection/'capture.json').write_text(json.dumps({'complete':True,'steps':self.steps}))
                        return {'active': False}
                    self.steps += 1 if tool == 'stop' or short_lift else arguments['steps']
                    return {'active': True, 'observation': self.obs()}

                def close(self):
                    return 0

            with mock.patch.object(codex_client, '__file__', str(root/'participant/collection/client.py')), \
                 mock.patch.object(codex_client, 'Simulator', Simulator), \
                 mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                 mock.patch.object(codex_client.signal, 'signal'), \
                 mock.patch.object(codex_actor, '_native_binary', side_effect=AssertionError('real Actor forbidden')), \
                 mock.patch('builtins.print'):
                if short_lift:
                    with self.assertRaisesRegex(ValueError,'transition/provenance'):
                        run_probe('cpu-depth-wiring')
                    report=json.loads((root/'output/sessions/cpu-depth-wiring-probe.json').read_text())
                else:
                    report=run_probe('cpu-depth-wiring')
            attempt=json.loads((root/'output/operator-traces/cpu-depth-wiring/attempt.json').read_text())
            return report,requests,commands,attempt

    def test_query_does_not_dispatch_and_final_capture_has_three_steps(self):
        report,requests,commands,attempt=self.run_fixture()
        self.assertTrue(report['passed'])
        self.assertEqual([r[0] for r in requests],['act','stop','finish_episode'])
        self.assertEqual(requests[0][1]['steps'],2)
        self.assertEqual(requests[0][1]['action'],[[0.,0.,0.,.029999999329447746,0.,0.,0.,0.,-1.]]*2)
        self.assertEqual(report['real_model_calls'],0)
        self.assertEqual(report['actual_physics_transitions'],3)
        self.assertEqual(report['query_physics_transitions'],0)
        self.assertEqual(report['client_actor_invocations'],4)
        self.assertEqual(report['fixture_calls'][0]['public_clock_s'],report['fixture_calls'][1]['public_clock_s'])
        self.assertTrue(report['actor_cleanup_ok'])
        self.assertEqual(attempt['source'],'integration_test')
        self.assertEqual(attempt['model'],MODEL_ID)
        self.assertEqual(attempt['actor_usage']['input_tokens'],0)
        self.assertEqual(commands[0][commands[0].index('--source')+1],'integration_test')
        self.assertEqual(commands[0][commands[0].index('--max-steps')+1],'4')

    def test_short_actual_action_fails_three_transition_check(self):
        report,_,_,attempt=self.run_fixture(short_lift=True)
        self.assertFalse(report['passed'])
        self.assertEqual(report['error_type'],'ValueError')
        self.assertEqual(attempt['recorded_simulation_steps'],2)

    def test_fixture_rejects_advanced_clock_before_followup_action(self):
        actor=WiringFixtureActor(model=MODEL_ID,effort='none',timeout_s=180)
        context={'frozen_observation_id':'a'*64,'simulation_time_s':4.}
        first=json.dumps({'public_robot_observation':{'simulation_time_s':4.}})
        first+='\nfrozen_public_depth_query_context: '+json.dumps(context)
        response=actor.invoke(first,[],dq.response_schema(codex_client.SCHEMA))
        self.assertEqual(response['decision']['tool'],'depth_query')
        second=json.dumps({'public_robot_observation':{'simulation_time_s':4.05}})
        second+='\ndepth_query_result: '+json.dumps({'observation_id':'a'*64,'simulation_time_s':4.05,
            'camera':'robot_0_wrist','results':[{'pixel_uv':[128,128],'optical_z_m':None},
                                               {'pixel_uv':[0,0],'optical_z_m':None}]})
        with self.assertRaisesRegex(ValueError,'same public observation'):
            actor.invoke(second,[],codex_client.SCHEMA)
        self.assertEqual(len(actor.calls),1)

    def test_existing_report_rejects_before_simulator_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'report.json';report.write_text('{}')
            with mock.patch.object(codex_client,'Simulator') as simulator:
                with self.assertRaisesRegex(ValueError,'already exists'):
                    run_probe('unique',report)
            simulator.assert_not_called()
            self.assertEqual(report.read_text(),'{}')


if __name__ == '__main__':
    unittest.main()
