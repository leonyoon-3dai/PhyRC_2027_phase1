"""Passive inclusive timers for the unchanged teleoperation loop."""
from collections import defaultdict
from functools import wraps
import time
TOTAL=defaultdict(lambda:[0.0,0])
HANDLES=[]
def wrap(obj,name,label):
    original=getattr(obj,name)
    @wraps(original)
    def timed(*args,**kwargs):
        start=time.perf_counter()
        try:return original(*args,**kwargs)
        finally:
            TOTAL[label][0]+=time.perf_counter()-start;TOTAL[label][1]+=1
    setattr(obj,name,timed)
def snapshot():return {k:{'wall_s':v[0],'calls':v[1]} for k,v in TOTAL.items()}
def install(module):
    from Policy.teleop_recording import FullTeleopRecorder
    from Policy.training_deferred import DeferredTrainingTeleop
    for name,label in [('cloth_pre_step','cloth_pre'),('cloth_post_step','cloth_post'),('drive_robot','drive_robot')]:wrap(module,name,label)
    wrap(FullTeleopRecorder,'_physics_step','archive_physics_callback')
    wrap(DeferredTrainingTeleop,'_capture','policy_boundary_capture')
    original=module.initialize_manipulation
    def initialize(env):
        result=original(env)
        interface=env.world._physics_context._physics_sim_interface
        clock={'start':None}
        def pre(*args):clock['start']=time.perf_counter()
        def post(*args):
            if clock['start'] is not None:
                TOTAL['physics_event_interval'][0]+=time.perf_counter()-clock['start'];TOTAL['physics_event_interval'][1]+=1
                clock['start']=None
        HANDLES.extend([interface.subscribe_physics_on_step_events(pre_step=True,order=100000,on_update=pre),interface.subscribe_physics_on_step_events(pre_step=False,order=-100000,on_update=post)])
        return result
    module.initialize_manipulation=initialize
