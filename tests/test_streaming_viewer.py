"""CPU-only spectator privacy/protocol tests; no video client or TCP listener."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
from types import SimpleNamespace
import unittest

from participant.streaming.viewer_server import ProgressStore, completed_tail, make_handler


class SpectatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dist = self.root / 'dist'
        self.dist.mkdir()
        (self.dist / 'index.html').write_text('<h1>static viewer</h1>')
        self.store = ProgressStore(self.root)

    def fixture(self, name='new-run', started='2026-11-06T03:00:00Z', status='completed'):
        trace = self.root / 'output/operator-traces' / name
        capture = self.root / 'output/collections' / name
        trace.mkdir(parents=True); capture.mkdir(parents=True)
        (trace/'attempt.json').write_text(json.dumps({'run_id':name,'started_at_utc':started,
            'ended_at_utc':'2026-11-06T03:01:00Z','status':status,'source':'gpt','mode':'pickup',
            'model':'gpt-6-astra','reasoning_effort':'ultra','simulation_steps':20,'actor_calls_attempted':1,
            'wall_s':60,'actor_call_wall_s':30,'environment_dispatch_wall_s':20,'actor_usage':{},
            'auth':'PRIVATE_AUTH','session_id':'PRIVATE_SESSION','episode_seed':987654321}))
        (trace/'prompt.txt').write_text('Pick up using only public observations.')
        decision={'type':'decision','decision_index':0,'model_call_index':0,'model_invoked':True,
                  'plan_segment_index':0,'plan_segment_count':1,'wall_s':30,
                  'observation_simulation_time_s':1.5,'latest_observation_simulation_time_s':1.5,
                  'session_id':'PRIVATE_SESSION','reasoning':'PRIVATE_REASONING',
                  'decision':{'tool':'act','action':[[0.]*9]*2,'steps':20,'stage':'grasp',
                              'visual_assessment':'uncertain','reason':'Observe the public gripper view.',
                              'geometry':'PRIVATE_GEOMETRY'}}
        applied={'type':'applied_segment','decision_index':0,'start_step':0,'end_step':20,
                 'actual_steps':20,'simulation_start_s':1.5,'simulation_end_s':2.5,
                 'environment_dispatch_wall_s':20}
        (trace/'decisions.jsonl').write_text(json.dumps(decision)+'\n'+json.dumps(applied)+'\n')
        # Intentionally invalid HDF5: status may stat it, but must never open it.
        (capture/'policy.hdf5').write_bytes(b'PRIVATE_HDF5_NOT_A_VALID_FILE')
        (capture/'evaluation_summary.json').write_text(json.dumps({'report':{'valid':True,
            'metadata':{'geometry':'PRIVATE_GEOMETRY'},'result':{'raw_points':0,'success':False,
                'success_evaluated':True,'score_status':'no_contact','final_score':None}}}))
        return trace, capture

    def request(self, target, method='GET', body=b'', extra_headers=''):
        server, client = socket.socketpair()
        handler = make_handler(self.store, self.dist)
        def serve():
            try:
                handler(server, ('local-test', 0), SimpleNamespace())
            finally:
                server.close()
        thread=threading.Thread(target=serve);thread.start()
        request=(f'{method} {target} HTTP/1.0\r\nHost: viewer.test\r\n'
                 f'Content-Length: {len(body)}\r\n'+extra_headers+'\r\n').encode()+body
        client.sendall(request);client.shutdown(socket.SHUT_WR)
        response=b''
        while chunk:=client.recv(65536):response+=chunk
        client.close();thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        headers,payload=response.split(b'\r\n\r\n',1)
        return int(headers.split()[1]),headers.decode(),payload

    def test_latest_uses_start_time_and_status_not_modified_time(self):
        new,_=self.fixture(status='collecting')
        old,_=self.fixture('old-run','2026-11-05T23:59:00Z')
        os.utime(old/'attempt.json',(2000000000,2000000000))
        self.assertEqual(self.store.snapshot()['run_id'],'new-run')
        value=json.loads((new/'attempt.json').read_text());value['status']='unknown-state'
        (new/'attempt.json').write_text(json.dumps(value))
        self.assertEqual(self.store.snapshot(refresh=True)['run_id'],'old-run')

    def test_partial_jsonl_privacy_and_hdf5_stat_only(self):
        trace,_=self.fixture()
        with (trace/'decisions.jsonl').open('a') as stream:
            stream.write('{"type":"decision","decision_index":99')
        self.assertEqual(len(completed_tail(trace/'decisions.jsonl')),2)
        snapshot=self.store.snapshot()
        self.assertEqual(snapshot['recent_decisions'][0]['execution']['actual_steps'],20)
        self.assertEqual(len(snapshot['recent_decisions']),1)
        self.assertEqual(snapshot['evaluation']['raw_points'],0)
        self.assertIsNone(snapshot['evaluation']['final_score'])
        self.assertFalse(snapshot['same_as_video_run_verified'])
        self.assertEqual(snapshot['run_scope'],'latest_model_collection')
        serialized=json.dumps(snapshot)
        for secret in ('PRIVATE_',str(self.root),'episode_seed','session_id','reasoning'):
            # The requested effort key is allowed, hidden reasoning content is not.
            if secret=='reasoning':continue
            self.assertNotIn(secret,serialized)
        self.assertIn({'path':'capture/policy.hdf5','bytes':len(b'PRIVATE_HDF5_NOT_A_VALID_FILE')},snapshot['files'])

    def test_api_scope_no_store_and_static_traversal(self):
        self.fixture()
        status,headers,body=self.request('/api/progress')
        self.assertEqual(status,200);self.assertIn('Cache-Control: no-store',headers)
        self.assertEqual(json.loads(body)['control_mode'],'observer_only')
        self.assertEqual(self.request('/api/progress?path=/etc/passwd')[0],404)
        self.assertEqual(self.request('/api/files')[0],404)
        private=self.root/'secret.txt';private.write_text('PRIVATE_SECRET')
        (self.dist/'leak.txt').symlink_to(private)
        self.assertEqual(self.request('/leak.txt')[0],403)
        self.assertEqual(self.request('/../../secret.txt')[0],404)
        self.assertNotIn(b'PRIVATE_SECRET',self.request('/leak.txt')[2])
        self.assertEqual(self.request('/keys',method='POST',body=b'{}')[0],404)

    def test_metrics_are_bounded_client_reported_and_not_stream_identity(self):
        self.fixture()
        value={'run_id':'new-run','sdk_connected':True,'total_video_frames':10,
               'video_width':1280,'video_height':720,'page_visible':True}
        self.assertEqual(self.request('/api/viewer-metrics','POST',json.dumps(value).encode())[0],200)
        self.assertFalse(self.store.snapshot()['viewer_metrics']['frame_count_increased'])
        value['total_video_frames']=11
        self.assertEqual(self.request('/api/viewer-metrics','POST',json.dumps(value).encode())[0],200)
        metrics=self.store.snapshot()['viewer_metrics']
        self.assertTrue(metrics['frame_count_increased']);self.assertTrue(metrics['client_reported'])
        self.assertFalse(metrics['same_as_video_run_verified'])
        self.assertLess(metrics['last_seen_seconds'],2)
        for changed in [dict(value,video_width=99999),dict(value,total_video_frames=True),
                        dict(value,auth='PRIVATE_AUTH'),dict(value,run_id='../secret')]:
            self.assertEqual(self.request('/api/viewer-metrics','POST',json.dumps(changed).encode())[0],400)
        self.assertEqual(self.request('/api/viewer-metrics','POST',b'x'*2049)[0],400)
        self.assertEqual(self.request('/api/viewer-metrics','POST',json.dumps(value).encode(),
                                      'Origin: http://other.test\r\n')[0],403)
        stored=(self.root/'output/viewer-metrics/new-run.jsonl').read_text()
        self.assertNotIn('PRIVATE_',stored)

    def test_private_prompt_is_redacted_and_symlink_records_are_rejected(self):
        trace,_=self.fixture()
        (trace/'prompt.txt').write_text('Read /home/private/auth.json')
        self.assertIsNone(self.store.snapshot()['prompt'])
        self.assertTrue(self.store.snapshot()['prompt_redacted'])
        (trace/'attempt.json').unlink()
        private=self.root/'private.json';private.write_text('{"auth":"PRIVATE_AUTH"}')
        (trace/'attempt.json').symlink_to(private)
        self.assertFalse(self.store.snapshot(refresh=True)['available'])

    @unittest.skipUnless(shutil.which('node'),'node unavailable')
    def test_frontend_renders_untrusted_text_without_html_insertion(self):
        source=Path(__file__).resolve().parents[1]/'participant/streaming/spectator.js'
        harness=r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class El {
 constructor(tag){this.tag=tag;this.children=[];this._text='';this.open=false;}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
 set innerHTML(v){throw Error('Unsafe HTML insertion');}
 append(...x){this.children.push(...x);}
 replaceChildren(...x){this.children=x;this._text='';}
 setAttribute(){}
 querySelector(s){return this.children.find(c=>c.tag===s);}
 querySelectorAll(s){let all=this.children.flatMap(c=>[c,...c.querySelectorAll('*')]);return s==='*'?all:all.filter(c=>c.tag==='details'&&(s!=='details[open]'||c.open));}
}
const app=new El('app'),video={videoWidth:1280,videoHeight:720,getVideoPlaybackQuality:()=>({totalVideoFrames:4})};
global.document={head:new El('head'),hidden:false,createElement:tag=>new El(tag),getElementById:id=>id==='app'?app:video};
global.window={addEventListener(){}};global.setTimeout=()=>0;
const injection='<img src=x onerror="globalThis.PWNED=true">';
global.fetch=async()=>({ok:true,json:async()=>({available:true,run_id:'test-run',
 attempt:{status:'completed',simulation_steps:1,actor_calls_attempted:1},evaluation:{raw_points:0},files:[],
 prompt:injection,recent_decisions:[{decision_index:0,response:{stage:'grasp',tool:'stop',steps:1,reason:injection,visual_assessment:'uncertain'}}]})});
vm.runInThisContext(fs.readFileSync(process.argv[1],'utf8'));
setImmediate(()=>{assert(app.textContent.includes(injection));assert(!global.PWNED);
 assert(app.textContent.includes('최근 모델 수집 기록'));assert(app.textContent.includes('같은 실행인지 확인되지 않았습니다'));});
'''
        result=subprocess.run(['node','-e',harness,str(source)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':
    unittest.main()
