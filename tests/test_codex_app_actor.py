"""CPU-only stdio protocol and isolation regressions; no Docker/model/GPU calls."""
from pathlib import Path
import sys
import tempfile
import threading
import unittest

from PIL import Image

from participant.collection.codex_actor import Actor, ActorError, DISABLED_FEATURES, STARTUP_NOTICES
from participant.collection.codex_app_actor import AppActor, BUNDLED_BWRAP_NOTICE, TurnResult, validate_schema


THREAD = '00000000-0000-4000-8000-000000000001'
SCHEMA = {'type': 'object', 'additionalProperties': False,
          'properties': {'answer': {'type': 'integer', 'minimum': 1, 'maximum': 2}},
          'required': ['answer']}

FAKE_SERVER = r'''
import json,sys,time
scenario=sys.argv[1]
thread='00000000-0000-4000-8000-000000000001'
count=0
def send(value): print(json.dumps(value),flush=True)
def event(method,params): send({'method':method,'params':params})
for line in sys.stdin:
 r=json.loads(line);method=r['method']
 if method=='initialized': continue
 if method=='initialize':
  send({'id':r['id'],'result':{'userAgent':'synthetic-test'}})
 elif method=='thread/start':
  event('thread/started',{'thread':{'id':thread}})
  send({'id':r['id'],'result':{'thread':{'id':thread},'model':'gpt-6-astra',
    'reasoningEffort':'ultra' if scenario!='bad_config' else 'medium',
    'approvalPolicy':'never','sandbox':{'type':'readOnly'},'instructionSources':[]}})
 elif method=='turn/start':
  count+=1;turn=f'00000000-0000-4000-8000-{count+10:012d}'
  assert r['params']['threadId']==thread
  assert r['params']['model']=='gpt-6-astra' and r['params']['effort']=='ultra'
  assert 'outputSchema' in r['params']
  assert r['params']['input'][1]['type']=='localImage'
  assert f'/{count-1:06d}/camera-00.png' in r['params']['input'][1]['path']
  if scenario=='bad_rpc':
   send({'id':99999,'result':{}});continue
  event('turn/started',{'threadId':thread,'turn':{'id':turn,'status':'inProgress','items':[]}})
  send({'id':r['id'],'result':{'turn':{'id':turn,'status':'inProgress','items':[]}}})
  if scenario=='timeout':time.sleep(1);continue
  if scenario=='eof':sys.exit(0)
  if scenario=='tool_request':
   send({'id':99,'method':'item/commandExecution/requestApproval','params':{'threadId':thread,'turnId':turn}})
   denied=json.loads(sys.stdin.readline());assert 'error' in denied;continue
  thread_arg=thread if scenario!='bad_thread' else '00000000-0000-4000-8000-000000000002'
  item={'type':'commandExecution','id':'tool'} if scenario=='tool_item' else {
   'type':'agentMessage','id':f'message-{count}','phase':'final_answer',
   'text':json.dumps({'answer':count if scenario!='bad_schema' else 9})}
  event('item/completed',{'threadId':thread_arg,'turnId':turn,'item':item})
  usage={'inputTokens':10*count,'cachedInputTokens':2*count,'outputTokens':3*count,
         'reasoningOutputTokens':count,'totalTokens':13*count}
  event('thread/tokenUsage/updated',{'threadId':thread,'turnId':turn,
   'tokenUsage':{'total':usage,'last':dict(usage,inputTokens=10,outputTokens=3)}})
  event('turn/moderationMetadata',{'threadId':thread,'turnId':turn,
   'metadata':{'prompt':{'is_blocked':scenario=='blocked_metadata'},'tool_call':{},'tool_response':{}}})
  if scenario=='unknown':event('item/newTool/delta',{'threadId':thread,'turnId':turn})
  elif scenario=='duplicate_final':event('item/completed',{'threadId':thread,'turnId':turn,
   'item':dict(item,id='extra-final')})
  status='failed' if scenario=='failed' else 'completed'
  event('turn/completed',{'threadId':thread,'turn':{'id':turn,'status':status,'items':[item]}})
'''


class FakeAppActor(AppActor):
    """Exercises the real adapter while replacing Docker with a local fixture."""
    def __init__(self, root, scenario='ok'):
        self.root = root
        self.model, self.effort = 'gpt-6-astra', 'ultra'
        self.timeout_s = .15 if scenario == 'timeout' else 3
        self.cli_version = 'codex-cli 0.166.0'
        self.session_id = None
        self.calls = 0
        self._closed = self._failed = self._network_created = self._proxy_created = False
        self._active_container = None
        self.network = 'fake-actor'
        self.binary = Path('/not-mounted-codex')
        self.public, self.codex_home, self.events = [root / x for x in ('public', 'home', 'events')]
        for directory in (self.public, self.codex_home, self.events): directory.mkdir()
        self._process = self._rpc_log = self._stderr_log = None
        self._lock = threading.Lock()
        self._buffer = bytearray()
        self._event_bytes = self._request_id = 0
        self._turn = self._announced_thread = None
        self._usage_total = {}
        self.provision_wall_s = 0
        self.fixture = root / 'fake_server.py'
        self.fixture.write_text(FAKE_SERVER)
        self.scenario = scenario
        try: self._start_server()
        except BaseException:
            self.close()
            raise

    def _container_command(self, name, directory, cli):
        return [sys.executable, '-u', str(self.fixture), self.scenario]

    def _remove_container(self, name):
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            self._process.wait(timeout=3)


class AppActorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.image = self.root / 'public-source.png'
        Image.new('RGB', (4, 4), (1, 2, 3)).save(self.image)
        self.actor = None

    def tearDown(self):
        if self.actor: self.actor.close()
        self.temp.cleanup()

    def test_two_turns_preserve_process_thread_images_schema_and_cumulative_usage(self):
        self.actor = FakeAppActor(self.root)
        pid = self.actor._process.pid
        a = self.actor.invoke('First public input', [self.image], SCHEMA)
        b = self.actor.invoke('Second public input', [self.image], SCHEMA)
        self.assertEqual(self.actor._process.pid, pid)
        self.assertIsNone(self.actor._process.poll())
        self.assertEqual(a['session_id'], b['session_id'])
        self.assertNotEqual(a['turn_id'], b['turn_id'])
        self.assertEqual(a['decision'], {'answer': 1})
        self.assertEqual(b['decision'], {'answer': 2})
        self.assertEqual(b['usage_scope'], 'thread_total')
        self.assertEqual(b['usage']['input_tokens'], 20)
        self.assertEqual(b['turn_usage_delta']['input_tokens'], 10)
        self.assertTrue((self.actor.public / '000000/camera-00.png').is_file())
        self.assertTrue((self.actor.public / '000001/camera-00.png').is_file())
        for k in ('staging_wall_s', 'process_wall_s', 'result_parse_wall_s', 'server_startup_wall_s'):
            self.assertGreaterEqual(b[k], 0)

    def test_failure_poisoning_and_process_cleanup(self):
        for scenario in ('bad_rpc', 'bad_thread', 'tool_item', 'tool_request',
                         'failed', 'unknown', 'duplicate_final', 'bad_schema', 'eof', 'timeout', 'blocked_metadata'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as d:
                actor = FakeAppActor(Path(d), scenario)
                with self.assertRaises(ActorError): actor.invoke('test', [self.image], SCHEMA)
                self.assertIsNotNone(actor._process.poll())
                self.assertTrue(actor._failed)
                with self.assertRaises(ActorError): actor.invoke('no reuse', [self.image], SCHEMA)
                actor.close()

    def test_configuration_mismatch_is_not_silently_accepted(self):
        with self.assertRaises(ActorError): FakeAppActor(self.root, 'bad_config')

    def test_only_exact_bundled_helper_notice_is_accepted_before_turn(self):
        actor = object.__new__(AppActor)
        actor._turn = None
        event = {'method':'configWarning','params':{'summary':BUNDLED_BWRAP_NOTICE,'details':None}}
        actor._notification(event,0)
        for params in ({'summary':'User namespace creation failed'},
                       {'summary':BUNDLED_BWRAP_NOTICE,'details':'fallback failed'}):
            with self.assertRaises(ActorError):actor._notification({'method':'configWarning','params':params},0)

    def test_remote_control_must_remain_disabled(self):
        actor = object.__new__(AppActor)
        actor._turn = None
        actor._notification({'method':'remoteControl/status/changed','params':{'status':'disabled'}},0)
        for status in ('connecting','connected','errored'):
            with self.assertRaises(ActorError):
                actor._notification({'method':'remoteControl/status/changed','params':{'status':status}},0)

    def test_known_cli_startup_notice_only_before_turn_started(self):
        actor=object.__new__(AppActor)
        actor.session_id=THREAD
        actor._turn=TurnResult(THREAD)
        event={'method':'warning','params':{'threadId':THREAD,'message':next(iter(STARTUP_NOTICES))}}
        actor._notification(event,0)
        actor._turn.started=True
        with self.assertRaises(ActorError):actor._notification(event,0)

    def test_app_command_reuses_isolation_settings_without_exec_only_flags(self):
        actor = object.__new__(AppActor)
        actor.model, actor.effort, actor.session_id = 'gpt-6-astra', 'ultra', None
        args = actor._app_command()
        self.assertEqual(args[:5], ['codex', 'app-server', '--listen', 'stdio://', '--strict-config'])
        self.assertNotIn('--ignore-user-config', args)  # not an app-server flag
        self.assertIn('forced_login_method="chatgpt"', args)
        self.assertIn('project_doc_max_bytes=0', args)
        self.assertIn('sandbox_mode="read-only"', args)
        self.assertIn('model_reasoning_effort="ultra"', args)
        disabled = [args[i+1] for i,x in enumerate(args[:-1]) if x=='--disable']
        self.assertEqual(tuple(disabled), DISABLED_FEATURES)
        actor.network='isolated';actor.binary=self.image
        actor.codex_home=self.root/'private-home';actor.public=self.root/'public'
        cmd=Actor._container_command(actor,'probe',actor.public,args)
        self.assertIn('--read-only', cmd)
        self.assertIn('--cap-drop=ALL', cmd)
        self.assertIn('HTTPS_PROXY=http://model-egress:8080',cmd)
        self.assertFalse(any('/project' in v or '/output/collections' in v or 'docker.sock' in v for v in cmd))

    def test_schema_rejects_unknown_constraints_boolean_numbers_and_extra_fields(self):
        with self.assertRaises(ActorError):validate_schema(None, {'type':'object','oneOf':[]},check_only=True)
        with self.assertRaises(ActorError):validate_schema(None, {'type':'string','minimum':1},check_only=True)
        for value in ({'answer':True},{'answer':3},{'answer':1,'other':2},{}):
            with self.subTest(value=value),self.assertRaises(ActorError):validate_schema(value,SCHEMA)

    def test_collector_action_schema_is_supported_and_range_checked(self):
        from participant.collection.codex_client import SCHEMA as action_schema
        validate_schema(None,action_schema,check_only=True)
        value=dict(tool='act',action=[[0.]*9]*2,steps=1,stage='preparation',
                   visual_assessment='uncertain',reason='public observation')
        validate_schema(value,action_schema)
        value['action'][0][0]=float('nan')
        with self.assertRaises(ActorError):validate_schema(value,action_schema)


if __name__ == '__main__': unittest.main()
