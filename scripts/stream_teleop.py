#!/usr/bin/env python3
"""Run the unchanged official teleop loop with WebRTC + bounded keyboard bridge.

Host firewall must restrict 49100/TCP,47998/UDP,8210/TCP,8211/TCP before launch.
This is a human-only free-viewport streaming path, never an AI observation tool.
"""
import json
import os
from pathlib import Path
import queue
import runpy
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

sys.path.insert(0,'/workspace/PhyRC_Sim')
HOST=os.environ['STRETCH4_STREAM_HOST']
ORIGIN='http://'+HOST+':8210'
EVENTS=queue.Queue(maxsize=256)
KEYS=set()
LAST=0.0
SESSION=None
SEQ=-1
LOCK=threading.Lock()
ALLOWED=set('I K L J U O W S D A E Q V R C Z UP DOWN RIGHT LEFT NUMPAD_DIVIDE NUMPAD_MULTIPLY NUMPAD_8 NUMPAD_2 NUMPAD_6 NUMPAD_4 NUMPAD_9 NUMPAD_7 NUMPAD_ADD NUMPAD_SUBTRACT NUMPAD_3 NUMPAD_1 KEY_0 SPACE NUMPAD_0 NUMPAD_ENTER P ESCAPE'.split())


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_OPTIONS(self):
        if self.headers.get('Origin')!=ORIGIN:
            self.send_error(403);return
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin',ORIGIN)
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
    def do_POST(self):
        global KEYS,LAST,SESSION,SEQ
        if self.path!='/keys' or self.headers.get('Origin')!=ORIGIN:
            self.send_error(403);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<4096: raise ValueError('size')
            value=json.loads(self.rfile.read(size))
            keys=set(value['keys'])
            if not keys<=ALLOWED or len(keys)>32 or not isinstance(value['seq'],int): raise ValueError('keys/seq')
            with LOCK:
                if SESSION!=value['session']:
                    for key in KEYS: EVENTS.put_nowait(('release',key))
                    KEYS=set(); SEQ=-1; SESSION=value['session']
                if value['seq']>SEQ:
                    for key in KEYS-keys: EVENTS.put_nowait(('release',key))
                    for key in keys-KEYS: EVENTS.put_nowait(('press',key))
                    KEYS=keys;SEQ=value['seq'];LAST=time.monotonic()
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin',ORIGIN)
            self.end_headers();self.wfile.write(b'{"ok":true}')
        except (ValueError,TypeError,KeyError,queue.Full): self.send_error(400)


def main():
    import isaacsim
    original=isaacsim.SimulationApp
    def start(config,*args,**kwargs):
        config=dict(config,headless=True,hide_ui=False,width=1280,height=720)
        app=original(config,*args,**kwargs)
        app.set_setting('/exts/omni.kit.livestream.app/primaryStream/publicIp',HOST)
        app.set_setting('/exts/omni.kit.livestream.app/primaryStream/signalPort',49100)
        app.set_setting('/exts/omni.kit.livestream.app/primaryStream/streamPort',47998)
        from isaacsim.core.experimental.utils.app import enable_extension
        enable_extension('omni.kit.livestream.app')
        import carb.input
        import omni.kit.app
        original_acquire=carb.input.acquire_input_interface
        iface=original_acquire()
        callbacks=[]
        # Passive performance reporting only; never changes dt, actions or physics.
        metrics_path=os.environ.get('STRETCH4_PERF_LOG')
        metrics_file=None
        if metrics_path:
            try:
                path=Path(metrics_path)
                path.parent.mkdir(parents=True,exist_ok=True)
                metrics_file=path.open('x',buffering=1)
            except OSError as error:
                print(f'[Participant performance] logging unavailable: {error}',flush=True)
        metrics={'wall':time.monotonic(),'sim':None,'events':0,'stop_requested':False}
        max_rss_gib=float(os.environ.get('STRETCH4_MAX_RSS_GIB','0'))
        class Proxy:
            def subscribe_to_keyboard_events(self,keyboard,callback):
                if getattr(callback,'__name__','') != 'on_keyboard_event':
                    return iface.subscribe_to_keyboard_events(keyboard,callback)
                callbacks.append(callback)
                print('[Participant stream] keyboard bridge ready',flush=True)
                return -987
            def unsubscribe_to_keyboard_events(self,keyboard,sub):
                if sub == -987: callbacks.clear()
                else: iface.unsubscribe_to_keyboard_events(keyboard,sub)
            def __getattr__(self,name): return getattr(iface,name)
        carb.input.acquire_input_interface=lambda:Proxy()
        def update(event):
            global KEYS
            if metrics_file:
                metrics['events']+=1
                now=time.monotonic()
                if now-metrics['wall']>=5:
                    from isaacsim.core.api import World
                    world=World.instance()
                    sim=float(world.current_time) if world else None
                    wall_dt=now-metrics['wall']
                    sim_dt=sim-metrics['sim'] if sim is not None and metrics['sim'] is not None else None
                    status=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
                    meminfo=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line)
                    rss_gib=int(status['VmRSS'].split()[0])/1024**2
                    available_gib=int(meminfo['MemAvailable'].split()[0])/1024**2
                    row={'wall_monotonic_s':now,'window_wall_s':wall_dt,'simulation_time_s':sim,
                         'simulation_dt_s':sim_dt,'app_update_events':metrics['events'],
                         'app_updates_per_wall_s':metrics['events']/wall_dt,
                         'simulation_s_per_wall_s':sim_dt/wall_dt if sim_dt is not None and sim_dt>=0 else None,
                         'reset_detected':sim_dt is not None and sim_dt<0,
                         'process_rss_gib':rss_gib,'host_available_gib':available_gib,
                         'mode':'human_stream_no_policy_inference'}
                    metrics_file.write(json.dumps(row)+'\n')
                    metrics.update(wall=now,sim=sim,events=0)
                    if max_rss_gib>0 and callbacks and not metrics['stop_requested'] and (rss_gib>=max_rss_gib or available_gib<16):
                        metrics['stop_requested']=True
                        metrics_file.write(json.dumps({'event':'memory_guard_graceful_stop','process_rss_gib':rss_gib,'host_available_gib':available_gib})+'\n')
                        print('[Participant performance] RAM guard requested graceful capture stop',flush=True)
                        os.kill(os.getpid(),signal.SIGTERM)
            if not callbacks:return
            with LOCK:
                if KEYS and time.monotonic()-LAST>.75:
                    for key in KEYS: EVENTS.put_nowait(('release',key))
                    KEYS=set()
                    print('[Participant stream] watchdog released all keys',flush=True)
            while True:
                try:kind,key=EVENTS.get_nowait()
                except queue.Empty:break
                value=SimpleNamespace(input=key,type=carb.input.KeyboardEventType.KEY_PRESS if kind=='press' else carb.input.KeyboardEventType.KEY_RELEASE,modifiers=0)
                for callback in callbacks:callback(value)
        app._participant_update=omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(update)
        server=ThreadingHTTPServer(('0.0.0.0',8211),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        print('[Participant stream] WebRTC enabled; human viewport only',flush=True)
        return app
    isaacsim.SimulationApp=start
    runpy.run_module('Env_StandAlone.Teleop_TShirt_Stretch4_Env',run_name='__main__',alter_sys=True)

if __name__=='__main__':main()
