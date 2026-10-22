import unittest
import numpy as np
from participant.pi05.preprocessing import inputs, pack_actions, restore_actions
from test_collection import observation

class PreprocessTest(unittest.TestCase):
    def test_runtime_disk_parity_and_robot_order(self):
        obs=observation()
        obs['rgb'][0]=10;obs['rgb'][1]=20;obs['rgb'][2]=30
        obs['joint_position'][1,:]=np.arange(13)+100
        obs['previous_action'][0,8]=1;obs['previous_action'][1,8]=-1
        disk={key:value.reshape(-1) for key,value in obs.items() if key not in ('rgb','depth','depth_valid')}
        disk.update(overview_rgb=obs['rgb'][0],robot_0_wrist_rgb=obs['rgb'][1],robot_1_wrist_rgb=obs['rgb'][2])
        first,second=inputs(obs),inputs(disk)
        np.testing.assert_array_equal(first['state'],second['state'])
        np.testing.assert_array_equal(first['state'][13:26],np.arange(13)+100)
        for key in first['image']:np.testing.assert_array_equal(first['image'][key],second['image'][key])
        np.testing.assert_array_equal(first['state'][-2:],[1,-1])
    def test_action_identity(self):
        action=np.linspace(-1,1,18,dtype=np.float32).reshape(1,18)
        out=restore_actions(pack_actions(action))
        np.testing.assert_array_equal(out.reshape(1,18),action)
        self.assertEqual(out.dtype,np.float32)
        with self.assertRaises(ValueError):restore_actions(np.full((10,32),np.nan))

if __name__=='__main__':unittest.main()
