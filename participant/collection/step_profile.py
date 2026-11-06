"""Opt-in wall timing of existing calls in one synchronous collector step.

Only numeric timing metrics are returned. Wrappers do not render, synchronize, step physics,
or start threads. Elapsed host times include waits charged to these call sites;
they are not GPU kernel timings. The collector owns one step thread per env.
"""
from functools import wraps
import threading
import time


class StepProfiler:
    def __init__(self, env, *, clock=None):
        self.env = env
        self.clock = time.perf_counter if clock is None else clock
        self.owner = None
        self.observe_depth = 0
        self.observe_s = self.capture_s = self.capture_in_observe_s = 0.0
        self.observe_calls = self.capture_calls = self.capture_outside_calls = 0
        self.restore = []

    def _wrap(self, obj, name, kind):
        original = getattr(obj, name)
        if getattr(original, '_phyrc_step_profile', False):
            raise RuntimeError('overlapping profiling of one environment is unsupported')
        present, previous = name in vars(obj), vars(obj).get(name)

        @wraps(original)
        def measured(*args, **kwargs):
            if threading.get_ident() != self.owner:
                return original(*args, **kwargs)
            outer_observe = kind == 'observe' and self.observe_depth == 0
            in_observe = self.observe_depth > 0
            if kind == 'observe':
                self.observe_calls += 1
                self.observe_depth += 1
            else:
                self.capture_calls += 1
                self.capture_outside_calls += int(not in_observe)
            started = self.clock()
            try:
                return original(*args, **kwargs)
            finally:
                elapsed = self.clock() - started
                if kind == 'observe':
                    self.observe_depth -= 1
                    if outer_observe:
                        self.observe_s += elapsed
                else:
                    self.capture_s += elapsed
                    if in_observe:
                        self.capture_in_observe_s += elapsed

        measured._phyrc_step_profile = True
        setattr(obj, name, measured)
        self.restore.append((obj, name, present, previous))

    def __enter__(self):
        self.owner = threading.get_ident()
        try:
            self._wrap(self.env, '_observe', 'observe')
            sensors = getattr(self.env, 'sensors', None)
            if sensors is not None:
                self._wrap(sensors, 'capture', 'capture')
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *_):
        while self.restore:
            obj, name, present, previous = self.restore.pop()
            if present:
                setattr(obj, name, previous)
            else:
                delattr(obj, name)
        return False

    def metrics(self, total_s):
        return {
            'step_observe_wall_s': self.observe_s,
            'step_capture_wall_s': self.capture_s,
            'step_observe_without_capture_wall_s': self.observe_s - self.capture_in_observe_s,
            'step_without_observe_wall_s': total_s - self.observe_s,
            'step_observe_calls': self.observe_calls,
            'step_capture_calls': self.capture_calls,
            'step_capture_outside_observe_calls': self.capture_outside_calls,
        }
