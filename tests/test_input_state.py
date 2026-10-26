import unittest
from participant.streaming.input_state import BufferedKeys

class BufferedKeysTests(unittest.TestCase):
    def test_short_tap_survives_until_a_policy_boundary(self):
        keys=BufferedKeys({'I'})
        self.assertEqual(keys.update([('press','I'),('release','I')]),[('press','I')])
        self.assertEqual(keys.update([]),[])
        self.assertEqual(keys.update([]),[])
        self.assertEqual(keys.update([]),[('release','I')])
        self.assertFalse(keys.pressed)
    def test_long_hold_releases_without_extra_tail(self):
        keys=BufferedKeys({'I'})
        keys.update([('press','I')])
        for _ in range(5):keys.update([])
        self.assertEqual(keys.update([('release','I')]),[('release','I')])
    def test_blur_watchdog_overrides_minimum_hold(self):
        keys=BufferedKeys({'I'})
        keys.update([('press','I')])
        self.assertEqual(keys.update([],force_release=True),[('release','I')])
        self.assertFalse(keys.pressed)
        self.assertEqual(keys.update([]),[])
    def test_repress_cancels_pending_release(self):
        keys=BufferedKeys({'I'})
        keys.update([('press','I'),('release','I')])
        keys.update([('press','I')])
        for _ in range(5):self.assertEqual(keys.update([]),[])
        self.assertEqual(keys.update([('release','I')]),[('release','I')])
    def test_discrete_gripper_and_exit_are_not_stretched(self):
        keys=BufferedKeys({'I'})
        events=[('press','SPACE'),('release','SPACE'),('press','ESCAPE'),('release','ESCAPE')]
        self.assertEqual(keys.update(events),events)

if __name__=='__main__':unittest.main()
