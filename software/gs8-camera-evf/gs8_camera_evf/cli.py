# SPDX-License-Identifier: MIT
"""GS8 EVF fork: explicit host simulation and Pi commissioning capture."""
import argparse
import json
from concurrent.futures import wait
from pathlib import Path

from .backends import SimulationBackend
from .controller import Controller, State
from .controls import ControlSelection
from .storage import ClipStore, StorageError, incomplete_clips


def main(argv=None):
    try:
        return _main(argv)
    except (StorageError, OSError, TimeoutError, ValueError, RuntimeError, ImportError) as error:
        import sys
        print(f'gs8-camera-evf: {error}', file=sys.stderr)
        return 1


def _main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    simulate = commands.add_parser('simulate', help='write explicitly labelled descriptor data, not footage')
    simulate.add_argument('--output', type=Path, required=True)
    simulate.add_argument('--fps', type=int, choices=(18, 24), default=18)
    simulate.add_argument('--frames', type=int, default=36)
    simulate.add_argument('--format', choices=('raw', 'encoded'), default='raw')
    simulate.add_argument('--audio', action='store_true', help='add simulated mono PCM silence')
    simulate.add_argument('--reserve-mib', type=int, default=256)
    inspect = commands.add_parser('inspect', help='inventory interrupted/failed takes without modifying them')
    inspect.add_argument('--output', type=Path, required=True)
    from .hardware_cli import add_arguments, run
    hardware = commands.add_parser('run', help='Pi-only DRM colour preview and silent DNG recording; bench commissioning required')
    add_arguments(hardware)
    from .d2_app import add_arguments as add_d2_arguments, run_demo, run_configured
    add_d2_arguments(commands)
    args = parser.parse_args(argv)
    if args.command == 'd2-demo':
        return run_demo(args)
    if args.command == 'd2-run':
        return run_configured(args)
    if args.command == 'run':
        return run(args)
    if args.command == 'inspect':
        if not args.output.is_dir():
            parser.error('inspect requires an existing storage directory')
        print(json.dumps({'incomplete_clips': incomplete_clips(args.output)}, indent=2))
        return 0
    if not 1 <= args.frames <= 2400 or args.reserve_mib < 0:
        parser.error('frames must be 1..2400 and reserve-mib must be nonnegative')
    selection = ControlSelection(args.fps, 180, 1.0, '5600', args.format, 'film', args.audio)
    with ClipStore(args.output, reserve_bytes=args.reserve_mib * 1024 * 1024) as store:
        controller = Controller(store, SimulationBackend())
        controller.step(0, selection, trigger_pressed=False)
        controller.step(20_000_000, selection, trigger_pressed=False)
        controller.step(30_000_000, selection, trigger_pressed=True)
        started = 50_000_000
        controller.step(started, selection, trigger_pressed=True)
        for index in range(args.frames):
            now = started + ((index + 1) * 1_000_000_000 + args.fps - 1) // args.fps
            controller.step(now, selection, trigger_pressed=True)
            # Virtual-time simulation has no real frame period for the OS to
            # schedule the writer. Waiting here is outside Controller.step().
            if controller._writer is not None:
                controller._writer.wait_idle()
        release = now + 1
        controller.step(release, selection, trigger_pressed=False)
        controller.step(release + 20_000_000, selection, trigger_pressed=False)
        controller.step(release + 120_000_000, selection, trigger_pressed=False, shutdown_requested=True)
        if controller._finish_future is not None:
            wait([controller._finish_future], timeout=10)
            controller.step(release + 120_000_000, selection, trigger_pressed=False)
        result = {'simulation_only': True, 'state': controller.state.value,
                  'safe_to_request_poweroff': controller.safe_to_request_poweroff,
                  'clip': str(controller.last_clip) if controller.last_clip else None,
                  'failure': controller.failure, 'events': list(controller.events)}
        print(json.dumps(result, indent=2))
        # Context teardown joins any remaining writer before abandoning files.
        return 0 if controller.state == State.SHUTDOWN and not controller.failure else 1
