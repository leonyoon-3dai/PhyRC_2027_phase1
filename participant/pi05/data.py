"""Reviewed-episode-only loader. Explicit source groups prevent split leakage."""
import hashlib
import json
from pathlib import Path
import h5py
import numpy as np
from participant.pi05.preprocessing import inputs, pack_actions


class Episodes:
    def __init__(self, manifest, split, horizon=10):
        self.manifest = Path(manifest).resolve()
        self.horizon = horizon
        spec = json.loads(self.manifest.read_text())
        groups = {}
        self.rows = []
        self.episodes = []
        for episode in spec['episodes']:
            group = episode['source_group']
            if group in groups and groups[group] != episode['split']:
                raise ValueError('source group crosses splits: '+group)
            groups[group] = episode['split']
            if episode['split'] != split:
                continue
            if episode.get('review') != 'approved_pipeline_test':
                raise ValueError('episode needs explicit review before SFT')
            path = (self.manifest.parent/episode['path']).resolve()
            if hashlib.sha256(path.read_bytes()).hexdigest() != episode['sha256']:
                raise ValueError('dataset checksum mismatch')
            with h5py.File(path,'r') as f:
                d = f['data'][episode['episode']]
                if not f.attrs['complete'] or not d.attrs['complete'] or d.attrs['num_samples'] < 1:
                    raise ValueError('incomplete episode')
                # Copy only allowed training observations through shared explicit mapping.
                n = int(d.attrs['num_samples'])
            self.episodes.append((path,episode['episode'],n))
            self.rows.extend((len(self.episodes)-1,i) for i in range(n))
        if not self.rows:
            raise ValueError('empty split')

    def __len__(self):
        return len(self.rows)

    def __getitem__(self,index):
        episode,i = self.rows[index]
        path,name,n = self.episodes[episode]
        with h5py.File(path,'r') as f:
            d = f['data'][name]
            keys = ('overview_rgb','robot_0_wrist_rgb','robot_1_wrist_rgb','joint_position',
                    'fingertip_origin_distance','gripper_close_command','previous_action')
            result = inputs({key:d['obs'][key][i] for key in keys})
            # Repeat last applied action only within this episode; never cross reset.
            indices = np.minimum(np.arange(i,i+self.horizon),n-1)
            action = d['actions'][i:min(i+self.horizon,n)]
            if len(action)<self.horizon:
                action = np.concatenate([action,np.repeat(action[-1:],self.horizon-len(action),axis=0)])
            result['actions'] = pack_actions(action)
        return result
