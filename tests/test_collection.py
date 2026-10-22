"""Boundary and transition tests with a fake environment; no GPU claims."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from participant.collection.boundary import CONTRACT, Operator, public_observation, validate_action
from Policy.training_dataset import DatasetWriter


def observation(t=0.0, previous=None):
    dims = CONTRACT['default_dimensions']
    out = {}
    for name, spec in CONTRACT['observations'].items():
        shape = tuple(dims.get(x,x) if isinstance(x,str) else x for x in spec['shape'])
        out[name] = np.zeros(shape,dtype=spec['dtype'])
    out['simulation_time_s'] = np.array(t,np.float64)
    if previous is not None:
        out['previous_action'] = previous.copy()
    return out


class Env:
    def reset(self,seed=None):
        self.obs = observation()
        return self.obs, {'episode_id':1, 'seed':123, 'cloth_world_positions':'forbidden'}
    def step(self,a):
        self.obs = observation(float(self.obs['simulation_time_s'])+.05,a)
        return self.obs, 0, False, False, {'raw':'forbidden'}


class BoundaryTest(unittest.TestCase):
    def test_allowlist_and_copies(self):
        obs = observation()
        obs.update(seed=123, info={'secret':True}, cloth_world_positions=np.ones((3,3)))
        result = public_observation(obs)
        self.assertEqual(set(result),set(CONTRACT['competition_access']['allowed_policy_observations']))
        result['joint_position'][0,0] = 4
        self.assertEqual(obs['joint_position'][0,0],0)

    def test_bad_commands(self):
        for value in (np.zeros((18,),np.float32), np.full((2,9),np.nan,np.float32), np.full((2,9),np.inf,np.float32), np.full((2,9),1.01,np.float32), np.zeros((2,9),np.float64), [[False]*9]*2):
            with self.assertRaises(ValueError): validate_action(value,1)
        for steps in (0,-1,21,1.0,True):
            with self.assertRaises(ValueError): validate_action(np.zeros((2,9),np.float32),steps)

    def test_recorded_transitions(self):
        import h5py
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'capture'
            writer = DatasetWriter(path, CONTRACT, {'source':'gpt','raw_archive':False})
            op = Operator(Env(), writer, source='gpt',source_group='layout-a', model_id='unit-test',prompt='test only')
            op.begin(seed=42)
            action = np.zeros((2,9),np.float32); action[:,8]=1
            op.act(action,2)
            op.stop()
            self.assertEqual(op.finish_episode(), {'steps':3,'complete':True})
            writer.close(complete=True)
            with h5py.File(path/'policy.hdf5') as f:
                d=f['data/demo_0']
                self.assertTrue(f.attrs['complete'])
                self.assertTrue(d.attrs['complete'])
                self.assertEqual(d['actions'].shape,(3,18))
                np.testing.assert_array_equal(d['actions'][:],d['next_obs/previous_action'][:])
                np.testing.assert_array_equal(d['obs/joint_position'][1:],d['next_obs/joint_position'][:-1])
                np.testing.assert_allclose(d['next_obs/simulation_time_s'][:]-d['obs/simulation_time_s'][:],.05)
                self.assertEqual(d['dones'][:].tolist(),[0,0,1])
            with h5py.File(path/'audit.hdf5') as f:
                np.testing.assert_array_equal(f['demo_0/end_tick'][:]-f['demo_0/start_tick'][:],12)

if __name__=='__main__': unittest.main()
