"""Accept trusted checkpoint requests during autonomous collection."""

import argparse
from contextlib import contextmanager
from dataclasses import replace
import fcntl
import json
from pathlib import Path
import re


STATE_FILE = 'replay-checkpoints.json'


class ReplayCheckpoints:
    def __init__(self, trace):
        self.path = trace / STATE_FILE
        self.lock = trace / 'replay-checkpoints.lock'
        self.due = None

    @contextmanager
    def edit(self):
        with self.lock.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads(self.path.read_text())
            yield state
            self._write(state)

    def _write(self, state):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, indent=2, allow_nan=False) + '\n')
        temporary.replace(self.path)

    def initialize(self, end, steps, *, max_step=None):
        self._write({
            'status': 'open', 'phase': 'replay' if end else 'dressing',
            'prefix_end': end, 'max_step': max_step if max_step is not None else end,
            'finish_supported': max_step is not None, 'reserved_through': 0,
            'requests': {str(step): {'status': 'pending'} for step in steps},
        })

    def request(self, value):
        with self.edit() as state:
            if state['status'] != 'open':
                raise ValueError('checkpoint requests are closed')
            reserved = state['reserved_through']
            if value == 'next':
                step = reserved + 1
            elif value == 'finish':
                step = value
            else:
                step = int(value)
            if str(step) in state['requests']:
                return step, state['requests'][str(step)]
            if step == 'finish':
                if not state.get('finish_supported', False):
                    raise ValueError('this run does not support a final checkpoint')
            elif not reserved < step <= state.get('max_step', state['prefix_end']):
                raise ValueError(
                    f'choose a step after {reserved} and at most {state.get("max_step", state["prefix_end"])}')
            request = state['requests'][str(step)] = {'status': 'pending'}
            return step, request

    def start_dressing(self):
        with self.edit() as state:
            state['phase'] = 'dressing'

    def boundaries(self, start, end):
        """Reserve each next dispatch, cutting it at the first pending checkpoint."""
        while start < end:
            with self.edit() as state:
                target = min((int(step) for step, request in state['requests'].items()
                              if step != 'finish' and request['status'] == 'pending'
                              and start < int(step) <= end), default=end)
                self.due = target if str(target) in state['requests'] else None
                state['reserved_through'] = target
            yield target
            start = target

    def chunks(self, chunks):
        for chunk in chunks:
            start = chunk.start_step
            for end in self.boundaries(start, chunk.end_step):
                yield replace(chunk, start_step=start, end_step=end, steps=end - start)
                start = end

    def save_due(self, sim, step, obs, *, rejected, prefix='replay'):
        if step != self.due:
            return None
        key = f'{prefix}-{step:06d}'
        time_before = float(obs['simulation_time_s'])

        def check_boundary(result, held):
            if (result.get('held') is not held or result.get('hold_id') != key
                    or not result.get('active') or sim.observation_step != step
                    or float(result['observation']['simulation_time_s']) != time_before):
                raise RuntimeError('checkpoint hold or resume changed the replay boundary')

        check_boundary(sim.dispatch('hold', {'hold_id': key, 'reason': f'{prefix}_checkpoint'}), True)
        record = self.save_held(sim, step, obs, key, str(step), rejected=rejected)
        check_boundary(sim.dispatch('resume', {'hold_id': key, 'human_feedback': False}), False)
        return record

    def save_held(self, sim, step, obs, key, request, *, rejected):
        try:
            receipt = sim.dispatch('save_checkpoint', {'key': key})['checkpoint']
        except rejected as exc:
            record = {'status': 'failed', 'error': str(exc)}
        else:
            if (sim.observation_step != step or receipt['observation_step'] != step
                    or receipt['key'] != key
                    or float(receipt['simulation_time_s']) != float(obs['simulation_time_s'])):
                raise RuntimeError('saved checkpoint does not match the observed boundary')
            record = {'status': 'saved', 'receipt': receipt}
        with self.edit() as state:
            state['requests'][request] = record
        return record

    def begin_finish(self):
        with self.edit() as state:
            state['status'] = 'closing'
            return state['requests'].get('finish', {}).get('status') == 'pending'

    def reuse_saved(self, step, request):
        with self.edit() as state:
            record = state['requests'].get(str(step))
            if record and record['status'] == 'saved':
                state['requests'][request] = record
                return record
            return None

    def close(self):
        with self.edit() as state:
            state['status'] = 'closed'
            for request in state['requests'].values():
                if request['status'] == 'pending':
                    request['status'] = 'unreached'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, help='Active autonomous run ID')
    parser.add_argument('--step', help='Requested boundary, next or finish; omit to show status')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', args.run):
        parser.error('invalid run ID')
    root = Path(__file__).resolve().parents[2]
    control = ReplayCheckpoints(root / 'output/operator-traces' / args.run)
    if not control.path.is_file():
        parser.error('this run has no checkpoint control')
    try:
        if args.step is None:
            print(control.path.read_text(), end='')
        else:
            step, request = control.request(args.step)
            print(json.dumps({'step': step, **request}))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
