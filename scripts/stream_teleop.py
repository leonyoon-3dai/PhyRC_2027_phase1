#!/usr/bin/env python3
"""Run the unchanged official teleop loop with WebRTC + bounded keyboard bridge.

Host firewall must restrict 49100/TCP,47998/UDP,8210/TCP,8211/TCP before launch.
This is a human-only free-viewport streaming path, never an AI observation tool.
"""
import json
import importlib
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
sys.path.insert(0,'/project')
from participant.streaming.input_state import BufferedKeys
from participant.streaming import profiling
HOST=os.environ['STRETCH4_STREAM_HOST']
ORIGIN='http://'+HOST+':8210'
EVENTS=queue.Queue(maxsize=256)
KEYS=set()
LAST=0.0
SESSION=None
SEQ=-1
LOCK=threading.Lock()
GUIDANCE={'robots':[],'stream_size':[1280,720]}
RIGS=[]
APPLIED_KEYS=[]
FORCE_RELEASE=False
STREAM_SIZE=[int(os.environ.get('STRETCH4_STREAM_WIDTH','1280')),int(os.environ.get('STRETCH4_STREAM_HEIGHT','720'))]
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
        global KEYS,LAST,SESSION,SEQ,FORCE_RELEASE
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
                    if value.get('force_release') and not keys:FORCE_RELEASE=True
                    for key in KEYS-keys: EVENTS.put_nowait(('release',key))
                    for key in keys-KEYS: EVENTS.put_nowait(('press',key))
                    KEYS=keys;SEQ=value['seq'];LAST=time.monotonic()
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin',ORIGIN)
            self.end_headers()
            with LOCK:
                payload=dict(ok=True,guidance=GUIDANCE,server_keys=sorted(KEYS),applied_keys=APPLIED_KEYS)
            self.wfile.write(json.dumps(payload).encode())
        except (ValueError,TypeError,KeyError,queue.Full): self.send_error(400)


def main():
    import isaacsim
    original=isaacsim.SimulationApp
    def start(config,*args,**kwargs):
        config=dict(config,headless=True,hide_ui=False,width=STREAM_SIZE[0],height=STREAM_SIZE[1])
        app=original(config,*args,**kwargs)
        profiling.wrap(app,'update','app_update')
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
        buffered=BufferedKeys(ALLOWED-{'SPACE','NUMPAD_0','NUMPAD_ENTER','KEY_0','P','ESCAPE'})
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
        guidance_clock={'last':0.0,'warned':False}
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
            global KEYS,GUIDANCE,APPLIED_KEYS,FORCE_RELEASE
            now=time.monotonic()
            if callbacks and len(RIGS)==2 and now-guidance_clock['last']>.15:
                guidance_clock['last']=now
                try:
                    import numpy as np
                    import omni.ui
                    from pxr import Gf
                    from omni.kit.viewport.utility import get_active_viewport_window
                    from Policy.state import array,rotation
                    window=get_active_viewport_window()
                    viewport=window.viewport_api
                    widget=window.frame
                    dpi=omni.ui.Workspace.get_dpi_scale() or 1
                    tab=22*dpi if window.dock_tab_bar_visible or not (window.flags & omni.ui.WINDOW_FLAGS_NO_TITLE_BAR) else 0
                    rect=[widget.screen_position_x*dpi-4*dpi,widget.screen_position_y*dpi-tab-4*dpi,
                          widget.computed_width*dpi,widget.computed_height*dpi]
                    def project(p):
                        ndc=viewport.world_to_ndc.Transform(Gf.Vec3d(*map(float,p)))
                        if ndc[2]<0:return None
                        return [rect[0]+(ndc[0]+1)*rect[2]/2,rect[1]+(1-ndc[1])*rect[3]/2]
                    robots=[]
                    for index,rig in enumerate(RIGS):
                        position,quaternion=rig['robot'].get_world_pose()
                        position=array(position).reshape(3);basis=rotation(array(quaternion).reshape(4))
                        center=position+np.array([0,0,.10])
                        forward=basis[:,0].copy();forward[2]=0;forward/=np.linalg.norm(forward)
                        left=np.cross([0,0,1],forward)
                        keys=('I','K','J','L') if index==0 else ('UP','DOWN','LEFT','RIGHT')
                        labels=('전진','후진','왼쪽','오른쪽')
                        arrows=[]
                        for key,label,direction in zip(keys,labels,(forward,-forward,left,-left)):
                            arrows.append(dict(key=key,label=label,start=project(center+direction*.30),end=project(center+direction*.90)))
                        robots.append(dict(id=index,center=project(position+[0,0,.55]),arrows=arrows))
                    with LOCK:GUIDANCE=dict(robots=robots,stream_size=STREAM_SIZE,sample_monotonic_s=now)
                except Exception as error:
                    if not guidance_clock['warned']:
                        print(f'[Participant guidance] projection unavailable: {error}',flush=True)
                        guidance_clock['warned']=True
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
                         'component_cumulative_inclusive':profiling.snapshot(),
                         'mode':'human_stream_no_policy_inference'}
                    metrics_file.write(json.dumps(row)+'\n')
                    metrics.update(wall=now,sim=sim,events=0)
                    if max_rss_gib>0 and callbacks and not metrics['stop_requested'] and (rss_gib>=max_rss_gib or available_gib<16):
                        metrics['stop_requested']=True
                        metrics_file.write(json.dumps({'event':'memory_guard_graceful_stop','process_rss_gib':rss_gib,'host_available_gib':available_gib})+'\n')
                        print('[Participant performance] RAM guard requested graceful capture stop',flush=True)
                        os.kill(os.getpid(),signal.SIGTERM)
            if not callbacks:return
            force_release=False
            with LOCK:
                if FORCE_RELEASE:
                    force_release=True
                    FORCE_RELEASE=False
                if KEYS and time.monotonic()-LAST>.75:
                    KEYS=set()
                    force_release=True
                    print('[Participant stream] watchdog released all keys',flush=True)
            events=[]
            while True:
                try:kind,key=EVENTS.get_nowait()
                except queue.Empty:break
                events.append((kind,key))
            for kind,key in buffered.update(events,force_release):
                value=SimpleNamespace(input=key,type=carb.input.KeyboardEventType.KEY_PRESS if kind=='press' else carb.input.KeyboardEventType.KEY_RELEASE,modifiers=0)
                for callback in callbacks:callback(value)
            with LOCK:APPLIED_KEYS=sorted(buffered.pressed)
        app._participant_update=omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(update)
        server=ThreadingHTTPServer(('0.0.0.0',8211),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        print('[Participant stream] WebRTC enabled; human viewport only',flush=True)
        return app
    isaacsim.SimulationApp=start
    # Capture only public robot handles for human-view direction guidance.
    module=importlib.import_module('Env_StandAlone.Teleop_TShirt_Stretch4_Env')
    profiling.install(module)
    frame_limit=int(os.environ.get('STRETCH4_DIAGNOSTIC_CONTROL_FRAMES','0'))
    diagnostic_clock={'frames':0,'stopped':False}
    if frame_limit:
        original_running=module.simulation_app.is_running
        module.simulation_app.is_running=lambda:original_running() and diagnostic_clock['frames']<frame_limit
        original_drive=module.drive_robot
        def diagnostic_drive(rig,*args,**kwargs):
            if RIGS and rig is RIGS[0]:diagnostic_clock['frames']+=1
            return original_drive(rig,*args,**kwargs)
        module.drive_robot=diagnostic_drive
    configure=module.configure_stretch4
    def configured(*args,**kwargs):
        rig=configure(*args,**kwargs)
        RIGS.append(rig)
        return rig
    module.configure_stretch4=configured
    if os.environ.get('STRETCH4_PRACTICE_LAYOUT')=='garment_side':
        # Owner-requested training reset layout, never an evaluation setting.
        # Keep the four tables, all geometry/physics and designated cameras.
        if os.environ.get('STRETCH4_RANDOMIZE')!='0':
            raise ValueError('garment_side practice requires fixed original garment placement')
        table_x=float(module.BOX_POS[0]+module.GARMENT_X_OFFSETS[2])
        table_y=float(module.BOX_POS[1])
        half_pitch=float(module._BOX_PITCH)/2
        module.ROBOT1_SPAWN=(table_x-half_pitch,table_y,0.03)
        module.ROBOT2_SPAWN=(table_x+half_pitch,table_y,0.03)
        module.ROBOT1_YAW_DEG=0.0
        module.ROBOT2_YAW_DEG=180.0
        layout={'mode':'human_training_practice_only','randomization':False,
                'robot_0_spawn':module.ROBOT1_SPAWN,'robot_1_spawn':module.ROBOT2_SPAWN,
                'robot_yaw_deg':[0.0,180.0],'physics_and_designated_cameras_unchanged':True,
                'not_default_evaluation_layout':True}
        layout_path=os.environ.get('STRETCH4_PRACTICE_LAYOUT_LOG')
        if layout_path:
            Path(layout_path).write_text(json.dumps(layout,indent=2)+'\n')
        print('[Participant practice layout] '+json.dumps(layout),flush=True)
        module.main()
    else:
        module.main()

if __name__=='__main__':main()
