import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from participant.collection.continuation import iter_action_chunks
from participant.collection.replay_checkpoints import ReplayCheckpoints


class SaveRejected(ValueError):
    pass


class Simulator:
    def __init__(self, step, reject_save=False):
        self.observation_step = step
        self.time = step / 20
        self.reject_save = reject_save
        self.calls = []

    def dispatch(self, tool, arguments):
        self.calls.append((tool, arguments))
        if tool == 'save_checkpoint':
            if self.reject_save:
                raise SaveRejected('checkpoint_rejected')
            return {'checkpoint': {'key': arguments['key'],
                                   'observation_step': self.observation_step,
                                   'simulation_time_s': self.time}}
        return {'active': True, 'held': tool == 'hold', 'hold_id': arguments['hold_id'],
                'observation': {'simulation_time_s': self.time}}


class ReplayCheckpointsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.trace = Path(temporary.name)
        self.control = ReplayCheckpoints(self.trace)

    def test_live_request_splits_only_unsent_actions_and_saves_at_prefix_end(self):
        self.control.initialize(12, [12])
        actions = np.zeros((12, 2, 9), dtype=np.float32)
        actions[7:, 0, 0] = .5
        chunks = self.control.chunks(iter_action_chunks(actions, cut_boundaries=(4,)))
        sent = [next(chunks)]
        requester = ReplayCheckpoints(self.trace)
        with self.assertRaisesRegex(ValueError, 'after 4'):
            requester.request('4')
        self.assertEqual(requester.request('next')[0], 5)
        self.assertEqual(requester.request('5'), (5, {'status': 'pending'}))
        saved = []
        for chunk in chunks:
            sent.append(chunk)
            sim = Simulator(chunk.end_step)
            result = self.control.save_due(sim, chunk.end_step, {'simulation_time_s': sim.time},
                                           rejected=SaveRejected)
            if result is not None:
                saved.append(result['receipt']['observation_step'])
                self.assertEqual([call[0] for call in sim.calls], ['hold', 'save_checkpoint', 'resume'])
                self.assertIs(sim.calls[-1][1]['human_feedback'], False)
        np.testing.assert_array_equal(np.concatenate([
            np.repeat(chunk.action[None], chunk.steps, axis=0) for chunk in sent]), actions)
        self.assertEqual(saved, [5, 12])
        self.control.close()
        self.assertEqual(json.loads(requester.path.read_text())['status'], 'closed')
        with self.assertRaisesRegex(ValueError, 'closed'):
            requester.request('next')

    def test_acknowledged_save_rejection_resumes_replay(self):
        self.control.initialize(10, [1, 10])
        actions = np.zeros((10, 2, 9), dtype=np.float32)
        chunk = next(self.control.chunks(iter_action_chunks(actions)))
        sim = Simulator(chunk.end_step, reject_save=True)
        result = self.control.save_due(sim, chunk.end_step, {'simulation_time_s': sim.time},
                                       rejected=SaveRejected)
        self.assertEqual(result, {'status': 'failed', 'error': 'checkpoint_rejected'})
        self.assertEqual(sim.calls[-1], ('resume', {'hold_id': 'replay-000001', 'human_feedback': False}))
        self.control.close()
        state = json.loads(self.control.path.read_text())
        self.assertEqual(state['requests']['10']['status'], 'unreached')
