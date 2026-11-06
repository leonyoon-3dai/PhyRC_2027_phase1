#!/usr/bin/env python3
"""Benchmark-only collector entry point: match the app viewport in ON and OFF.

Public camera resolution, capture rate, physics and collector protocol are kept.
This removes the startup app-config difference, not the idle-render difference.
No GPU work is performed on importing this module.
"""
import sys
from pathlib import Path

ROOT = Path('/project') if Path('/project/config').is_dir() else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def viewport_config(config):
    return dict(config, headless=True, hide_ui=False, width=1280, height=720)


def main():
    import collect_operator
    # Parse/sanitize before importing Kit, including this wrapper's arguments.
    args = collect_operator.parse_arguments()
    collect_operator.isolate_simulator_arguments()
    # collect_operator will duplicate fd 1 itself. Avoid Isaac import before it.
    original_parse = collect_operator.parse_arguments
    def parse_once():
        import isaacsim
        original = isaacsim.SimulationApp
        def start(config, *a, **kw):
            return original(viewport_config(config), *a, **kw)
        isaacsim.SimulationApp = start
        return args
    # isaacsim import may emit native logs; establish fd redirection first.
    protocol = collect_operator.open_protocol_stream()
    collect_operator.open_protocol_stream = lambda: protocol
    collect_operator.parse_arguments = parse_once
    try:
        return collect_operator.main()
    finally:
        collect_operator.parse_arguments = original_parse


if __name__ == '__main__':
    raise SystemExit(main())
