# SPDX-License-Identifier: MIT
"""Pi commissioning CLI with continuous multi-take preview; GPIO/audio remain separate."""
from pathlib import Path
import json
import math
import signal
import time

from .controller import Controller, State
from .controls import ControlSelection
from .evf import EvfPolicy, PicameraEvfBackend
from .models import TakeSettings
from .storage import ClipStore
from .writer import AsyncClipWriter
from .power import BatteryGuard, Ina260Hwmon, request_os_poweroff, step_with_battery


def add_arguments(parser):
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fps', type=int, choices=(18, 24), default=24)
    parser.add_argument('--source-fps', type=int, choices=(48, 54, 60), default=None,
                        help='default 48 for 24 recording / 54 for 18; noninteger ratios have uneven sample spacing')
    parser.add_argument('--shutter-angle', type=int, choices=(90, 144, 180, 216), default=90,
                        help='explicit hardware default 90 degrees; impossible exposures are rejected')
    parser.add_argument('--gain', type=float, choices=(1, 2, 4, 8), default=1)
    parser.add_argument('--wb-gains', type=float, nargs=2, metavar=('RED', 'BLUE'), required=True,
                        help='measured positive calibrated gains; there is no assumed colour calibration')
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--takes', type=int, default=1, help='automatically record this many bench takes with continuous idle preview')
    parser.add_argument('--pause-seconds', type=float, default=2)
    parser.add_argument('--reserve-mib', type=int, default=1024)
    parser.add_argument('--preview-width', type=int, default=728)
    parser.add_argument('--preview-height', type=int, default=544)
    parser.add_argument('--display-size', type=int, nargs=2, default=(1024, 768), metavar=('WIDTH', 'HEIGHT'),
                        help='active HDMI canvas from kmsprint; whole-sensor image is letterboxed within it')
    parser.add_argument('--preview-only', action='store_true')
    parser.add_argument('--battery-hwmon', type=Path,
                        help='explicit Linux ina260 hwmon path; enables low-battery drained stop')
    parser.add_argument('--battery-poweroff', action='store_true',
                        help='request systemctl poweroff after a battery-triggered safe stop; requires --battery-hwmon')


def run(args):
    if getattr(args, 'battery_poweroff', False) and not getattr(args, 'battery_hwmon', None):
        raise ValueError('--battery-poweroff requires --battery-hwmon')
    battery = None
    if getattr(args, 'battery_hwmon', None):
        path = args.battery_hwmon.resolve(strict=True)
        if not path.is_relative_to(Path('/sys/devices')):
            raise ValueError('--battery-hwmon must resolve to a real /sys/devices hwmon device')
        battery = BatteryGuard(Ina260Hwmon(path))
    try:
        code, safe = _run(args, battery)
    finally:
        if battery is not None:
            battery.close()
    # _run has returned only after ClipStore exit and backend.close succeeded.
    if battery is not None and battery.policy.shutdown_reason:
        print(json.dumps({'battery_stop': battery.policy.shutdown_reason,
                          'safe_to_request_poweroff': safe,
                          'os_poweroff_requested': bool(args.battery_poweroff and safe)}))
        if args.battery_poweroff:
            request_os_poweroff(safe_to_poweroff=safe)
        return 2 if code == 0 else code
    return code


def _run(args, battery=None):
    last_battery_state = None

    def poll_battery():
        nonlocal last_battery_state
        status = battery.poll()
        report = (status.warning, status.shutdown_reason)
        if report != last_battery_state:
            print(json.dumps({'battery_warning': status.warning,
                              'battery_stop': status.shutdown_reason}))
            last_battery_state = report
        return status

    if (not 0 < args.seconds <= 3600 or args.reserve_mib < 0 or not 1 <= args.takes <= 100
            or not math.isfinite(args.pause_seconds) or not .1 <= args.pause_seconds <= 3600):
        raise ValueError('seconds must be in (0, 3600], takes in 1..100, pause-seconds in [0.1, 3600], and reserve nonnegative')
    selection = ControlSelection(args.fps, args.shutter_angle, args.gain, 'custom', 'raw', 'clean', False)
    settings = TakeSettings.from_selection(selection, args.wb_gains)
    policy = EvfPolicy(args.fps, args.source_fps, (args.preview_width, args.preview_height), display_size=tuple(args.display_size))
    policy.validate_settings(settings)
    backend = PicameraEvfBackend(policy)
    stop_requested = False

    def interrupt(signum, frame):
        nonlocal stop_requested
        stop_requested = True

    old_handlers = {sig: signal.signal(sig, interrupt) for sig in (signal.SIGINT, signal.SIGTERM)}
    controller = None
    try:
        sensor = backend.preflight(settings)
        print(json.dumps({'hardware_uncommissioned': True, 'sensor': sensor, 'settings': settings.to_dict()}, indent=2))
        deadline = time.monotonic() + 10
        while not backend.warmed_up or (battery is not None and not battery.policy.ready):
            if battery is not None and poll_battery().shutdown_reason:
                return 2, True  # no take opened; finally must still close preview
            backend.check_health()
            backend.poll(time.monotonic_ns())
            if stop_requested:
                return 130, True
            if time.monotonic() >= deadline:
                raise TimeoutError('sensor controls/cadence did not settle during ten-second warmup')
            time.sleep(.005)
        if args.preview_only:
            deadline = time.monotonic() + args.seconds
            while not stop_requested and time.monotonic() < deadline:
                if battery is not None and poll_battery().shutdown_reason:
                    break
                backend.check_health()
                backend.poll(time.monotonic_ns())
                time.sleep(.005)
            return 0, True
        with ClipStore(args.output, reserve_bytes=args.reserve_mib * 1024 * 1024) as store:
            controller = Controller(store, backend, wb_gains=args.wb_gains,
                                    writer_factory=lambda transaction: AsyncClipWriter(transaction, capacity=4))
            # Qualify released trigger then a rising edge using real, never fabricated, time.
            controller.step(time.monotonic_ns(), selection, trigger_pressed=False)
            time.sleep(.025)
            controller.step(time.monotonic_ns(), selection, trigger_pressed=False)
            pressed_at = time.monotonic()
            stop_deadline = None
            take_number = 1
            pause_started = None
            last_clip = None
            while True:
                now = time.monotonic()
                if battery is not None:
                    if poll_battery().shutdown_reason:
                        stop_requested = True
                ending = (pause_started is not None or stop_requested
                          or now - pressed_at >= args.seconds + .025 or controller.failure is not None)
                shutdown = stop_requested or controller.failure is not None or (ending and take_number == args.takes)
                if battery is None:
                    controller.step(time.monotonic_ns(), selection, trigger_pressed=not ending,
                                    shutdown_requested=shutdown)
                else:
                    step_with_battery(controller, time.monotonic_ns(), selection,
                                      trigger_pressed=not ending, policy=battery.policy,
                                      shutdown_requested=shutdown)
                if controller.last_clip is not None and controller.last_clip != last_clip:
                    last_clip = controller.last_clip
                    pause_started = now
                    stop_deadline = None
                if (pause_started is not None and not shutdown and now - pause_started >= args.pause_seconds
                        and controller.state == State.READY):
                    take_number += 1
                    pressed_at = now
                    pause_started = None
                    ending = False
                if ending and pause_started is None and stop_deadline is None:
                    stop_deadline = now + 15
                if controller.state == State.SHUTDOWN:
                    break
                if stop_deadline is not None and now >= stop_deadline:
                    raise TimeoutError('recording or durable writer drain did not finish; inspect the incomplete take')
                time.sleep(.002)
            print(json.dumps({'state': controller.state.value, 'failure': controller.failure,
                              'safe_to_request_poweroff': controller.safe_to_request_poweroff,
                              'clip': str(controller.last_clip) if controller.last_clip else None}, indent=2))
            return (1 if controller.failure else 0), controller.safe_to_request_poweroff
    finally:
        # No OS poweroff or OS_HALTED GPIO assertion. Stop joins event processing,
        # releases retained camera buffers, and joins worker ownership explicitly.
        try:
            backend.close()
        finally:
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
