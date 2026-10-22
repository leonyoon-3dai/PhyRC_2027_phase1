"""Shared public HDF5/runtime mapping. No position/delta-action conversion."""
import numpy as np

CAMERAS = ('overview','robot_0_wrist','robot_1_wrist')
SLOTS = ('base_0_rgb','left_wrist_0_rgb','right_wrist_0_rgb')
PROMPT = 'Coordinate two Stretch robots to help a seated person put on a T-shirt.'
STATE_FIELDS = ('joint_position','fingertip_origin_distance','gripper_close_command')


def inputs(obs):
    if 'rgb' in obs:
        images = {slot:np.array(obs['rgb'][i],copy=True) for i,slot in enumerate(SLOTS)}
    else:
        images = {slot:np.array(obs[cam+'_rgb'],copy=True) for cam,slot in zip(CAMERAS,SLOTS)}
    for image in images.values():
        if image.dtype != np.uint8 or image.shape != (256,256,3):
            raise ValueError('expected uint8 256x256 RGB')
    parts = [np.asarray(obs[key],np.float32).reshape(-1) for key in STATE_FIELDS]
    parts.append(np.asarray(obs['previous_action'],np.float32).reshape(2,9)[:,8])
    state = np.concatenate(parts)  # 26 joints + 2 fingertip distances + 2 intents + 2 previous grip commands
    if state.shape != (32,) or not np.isfinite(state).all():
        raise ValueError('invalid 32D public robot state')
    return {'state':state,'image':images,'image_mask':{slot:np.True_ for slot in SLOTS},'prompt':PROMPT}


def pack_actions(actions):
    a = np.asarray(actions)
    if a.dtype != np.float32 or a.shape[-1] != 18 or not np.isfinite(a).all() or (abs(a)>1).any():
        raise ValueError('expected float32 normalized [...,18] actions')
    return np.pad(a,[(0,0)]*(a.ndim-1)+[(0,14)])


def restore_actions(prediction):
    a = np.asarray(prediction)
    if a.ndim != 2 or a.shape[1] != 32 or not len(a) or not np.isfinite(a).all():
        raise ValueError('invalid model action chunk')
    return np.clip(a[:,:18],-1,1).astype(np.float32).reshape(-1,2,9)
