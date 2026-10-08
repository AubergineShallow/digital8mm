# SPDX-License-Identifier: MIT
"""Explicit D2 application entrypoint, config and hardware-adapter contract.

There is no default live adapter, automatic service installation or poweroff.
An integrator supplies verified readers/display/media operations. Host demos
use the same recorder runtime with labelled simulated capture.
"""
from dataclasses import dataclass, fields, replace
from contextlib import ExitStack
from pathlib import Path
import importlib
import json
import math
import signal
import time

from .backends import SimulationBackend
from .d2_controls import D2InputSample
from .d2_io import LatestReader
from .d2_power import D2BatterySample, D2Shutdown, ShutdownPhase
from .d2_readiness import load_commissioning
from .d2_runtime import D2Runtime
from .models import TakeSettings
from .controls import ControlSelection
from .evf import MIN_COLOUR_GAIN, MAX_COLOUR_GAIN
from .storage import ClipStore
from .writer import AsyncClipWriter


@dataclass(frozen=True)
class D2Config:
    output: Path
    wb_gains: tuple[float, float]
    simulation_only: bool = False
    reserve_mib: int = 1024
    commissioning_manifest: Path | None = None
    shutdown_mode: str = 'drain_only'
    poll_interval_ms: int = 5
    drain_timeout_seconds: float = 15
    stop_millivolts: int = 3300

    def __post_init__(self):
        if not isinstance(self.output, Path):
            raise ValueError('output must be a Path')
        if type(self.simulation_only) is not bool or type(self.reserve_mib) is not int or self.reserve_mib < 0:
            raise ValueError('simulation_only must be boolean and reserve_mib a nonnegative integer')
        if self.shutdown_mode not in ('drain_only', 'poweroff'):
            raise ValueError('shutdown_mode must be drain_only or poweroff')
        if self.simulation_only and self.shutdown_mode != 'drain_only':
            raise ValueError('simulation can never request OS poweroff')
        if type(self.poll_interval_ms) is not int or not 1 <= self.poll_interval_ms <= 20:
            raise ValueError('poll_interval_ms must be 1..20')
        if (type(self.drain_timeout_seconds) not in (int, float) or not math.isfinite(self.drain_timeout_seconds)
                or not 5 <= self.drain_timeout_seconds <= 120):
            raise ValueError('drain_timeout_seconds must be finite and 5..120')
        calibrated = TakeSettings.from_selection(
            ControlSelection(24, 90, 1, 'custom', 'raw', 'clean', False), self.wb_gains).wb_gains
        if calibrated is None or any(not MIN_COLOUR_GAIN <= value <= MAX_COLOUR_GAIN for value in calibrated):
            raise ValueError('explicit calibrated white balance in 0.01..32 is required')
        object.__setattr__(self, 'wb_gains', calibrated)
        if not self.simulation_only and self.commissioning_manifest is None:
            raise ValueError('physical D2 requires a reviewed commissioning_manifest; use d2-demo for host simulation')
        if type(self.stop_millivolts) is not int or not 3300 <= self.stop_millivolts <= 4000:
            raise ValueError('stop_millivolts must be 3300..4000; G-W5/G-W12 determine the threshold')

    @classmethod
    def load(cls, path):
        path = Path(path).resolve(strict=True)
        if path.stat().st_size > 64 * 1024:
            raise ValueError('D2 configuration is too large')
        value = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value['schema_version'] != 1:
            raise ValueError('D2 configuration schema_version must be 1')
        value = dict(value)
        value.pop('schema_version')
        unknown = set(value) - {f.name for f in fields(cls)}
        if unknown or not {'output', 'wb_gains'} <= value.keys():
            raise ValueError(f'D2 config has unknown fields or missing output/wb_gains: {sorted(unknown)}')
        for key in ('output', 'commissioning_manifest'):
            if value.get(key) is not None:
                if not isinstance(value[key], str) or not value[key]:
                    raise ValueError(f'{key} must be a nonempty path')
                candidate = Path(value[key])
                value[key] = (path.parent / candidate).resolve() if not candidate.is_absolute() else candidate
        return cls(**value)


@dataclass(frozen=True)
class D2Adapters:
    """Readers implement read()/close(); display methods must be nonblocking.

    Readers are acquired explicitly by the integrator, then owned/closed by
    LatestReader workers. show_status receives D2Status and must not paint over
    the retained shutdown screen. hold_shutdown_screen must survive camera/DRM
    session close. No screenshot or host callback proves that it does so.
    """
    input_reader: object
    battery_reader: object
    backend_factory: object
    show_status: object
    hold_shutdown_screen: object
    health_reader: object | None = None
    shutdown_actions: object | None = None


def run_application(config, adapters, *, clock_ns=time.monotonic_ns, sleep=time.sleep, manage_signals=True,
                    reader_factory=LatestReader):
    """Own supplied readers immediately, then run until a drained stop.

    SIGINT/SIGTERM request draining. Missing readiness drains a take and leaves
    the application unready. Capture and reader cleanup precede any opt-in OS
    request; no uncertain poweroff is retried. Readers own no clip resources.
    """
    if not isinstance(adapters, D2Adapters):
        raise ValueError('explicit D2Adapters are required')
    sources = (adapters.input_reader, adapters.battery_reader, adapters.health_reader)
    unwrapped = {id(source): source for source in sources if source is not None}
    readers = []
    old_handlers = {}
    interrupted = False
    result = None
    cleanup_errors = []
    cleanup_pending = []

    def close_sources():
        # Remove before calling: a failed/uncertain cleanup is not retried.
        while readers:
            reader = readers.pop()
            if reader is None:
                continue
            try:
                if reader.close() is False:
                    cleanup_pending.append('read-only peripheral worker still owns its device')
            except Exception as error:
                cleanup_errors.append(f'reader: {type(error).__name__}: {error}')
        while unwrapped:
            _, source = unwrapped.popitem()
            try:
                source.close()
            except Exception as error:
                cleanup_errors.append(f'unstarted reader: {type(error).__name__}: {error}')

    def restore_signals():
        while old_handlers:
            sig, handler = old_handlers.popitem()
            try:
                signal.signal(sig, handler)
            except Exception as error:
                cleanup_errors.append(f'signal handler: {type(error).__name__}: {error}')

    def interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True

    try:
        if not isinstance(config, D2Config):
            raise ValueError('explicit D2Config is required')
        if (sources[0] is None or sources[1] is None
                or len(unwrapped) != sum(source is not None for source in sources)
                or any(not callable(getattr(source, method, None)) for source in unwrapped.values()
                       for method in ('read', 'close'))):
            raise ValueError('D2 requires separate owned input/battery readers with read()/close()')
        if not all(callable(v) for v in (adapters.backend_factory, adapters.show_status, adapters.hold_shutdown_screen)):
            raise ValueError('D2 backend and display adapters must be callable')
        if config.shutdown_mode == 'poweroff' and adapters.shutdown_actions is None:
            raise ValueError('poweroff requires explicit commissioned screen/media/OS shutdown actions')
        commissioning = load_commissioning(config.commissioning_manifest) if config.commissioning_manifest else None
        if commissioning is not None and not commissioning.limits_passed:
            raise ValueError('commissioning limits failed: ' + ', '.join(commissioning.reasons))
        if manage_signals:
            for sig in (signal.SIGINT, signal.SIGTERM):
                old_handlers[sig] = signal.signal(sig, interrupt)
        with ExitStack() as resources:
            store = resources.enter_context(ClipStore(config.output, reserve_bytes=config.reserve_mib * 1024 * 1024))
            coordinator = None
            if config.shutdown_mode == 'poweroff':
                coordinator = D2Shutdown(replace(adapters.shutdown_actions, close_store=store.close,
                                                  hold_screen=adapters.hold_shutdown_screen))
            observer = coordinator.begin if coordinator else adapters.hold_shutdown_screen
            runtime = D2Runtime(store, adapters.backend_factory, now_ns=clock_ns(), wb_gains=config.wb_gains,
                                stop_millivolts=config.stop_millivolts, simulation_only=config.simulation_only,
                                commissioning=commissioning, shutdown_observer=observer,
                                writer_factory=lambda transaction: AsyncClipWriter(transaction, capacity=4))
            capture_closed = False
            def close_capture():
                nonlocal capture_closed
                if capture_closed:
                    return
                # A FilePayload can still be read by a queued disk write even
                # after capture stops. Join writer ownership before closing any
                # backend which might unlink its staging files. On exceptional
                # teardown ClipStore then preserves the incomplete transaction.
                if store.active is not None:
                    writer = getattr(store.active, '_writer', None)
                    if writer is not None:
                        writer.close(wait=True)
                seen, errors = set(), []
                for backend in (runtime.backend, runtime._orphan_backend):
                    if backend is not None and id(backend) not in seen:
                        seen.add(id(backend))
                        try:
                            backend.close()
                        except Exception as error:
                            errors.append(f'{type(error).__name__}: {error}')
                if errors:
                    raise RuntimeError('D2 capture cleanup failed: ' + '; '.join(errors))
                capture_closed = True
            resources.callback(close_capture)
            for source, interval, name in ((sources[0], config.poll_interval_ms / 1000, 'd2-controls'),
                                          (sources[1], .1, 'd2-battery'), (sources[2], .1, 'd2-health')):
                if source is None:
                    readers.append(None)
                else:
                    reader = reader_factory(source, interval_seconds=interval, name=name)
                    readers.append(reader)
                    unwrapped.pop(id(source))  # ownership transfers only after construction succeeds
            last_report = None
            stop_at = None
            while True:
                now = clock_ns()
                inputs, input_error = readers[0].poll()
                battery, battery_error = readers[1].poll()
                health, health_error = readers[2].poll() if readers[2] else (None, None)
                status = runtime.step(now, inputs, battery, input_error=input_error, battery_error=battery_error,
                                      health_sample=None if health_error else health, shutdown_requested=interrupted)
                if not runtime.shutdown_reason and status != last_report:
                    try:
                        adapters.show_status(status)
                        last_report = status
                    except Exception as error:
                        runtime.report_fault('status_display_failed', error)
                if runtime.shutdown_reason:
                    if stop_at is None:
                        stop_at = now
                    if runtime.capture_safely_drained:
                        # All potentially failing recorder/peripheral cleanup runs
                        # before the external OS request. Store.close is idempotent.
                        close_capture()
                        close_sources()
                        restore_signals()
                        if coordinator:
                            if cleanup_errors or cleanup_pending:
                                raise RuntimeError('poweroff inhibited by incomplete cleanup: ' +
                                                   '; '.join(cleanup_errors + cleanup_pending))
                            coordinator.advance(capture_safely_drained=True)
                            if coordinator.phase != ShutdownPhase.POWEROFF_REQUESTED:
                                raise RuntimeError(coordinator.failure or 'shutdown actions were not completed')
                        result = {'status': runtime.status().to_dict(), 'capture_safely_drained': True,
                                  'os_poweroff_requested': bool(coordinator), 'os_halt_verified': False,
                                  'cleanup_errors': cleanup_errors, 'cleanup_pending': cleanup_pending}
                        return result
                    if now - stop_at >= config.drain_timeout_seconds * 1_000_000_000:
                        raise TimeoutError('D2 capture/commit did not drain; poweroff inhibited, inspect incomplete takes')
                sleep(config.poll_interval_ms / 1000)
    finally:
        close_sources()
        restore_signals()
        # On ordinary drained completion the result carries cleanup diagnostics.
        # On an exception retain its cause, and disclose additional close errors.
        if result is None and cleanup_errors:
            import sys
            cause = sys.exc_info()[1]
            raise RuntimeError('D2 cleanup errors: ' + '; '.join(cleanup_errors)) from cause


def add_arguments(commands):
    demo = commands.add_parser('d2-demo', help='D2 controls/lifecycle with labelled synthetic descriptors; never hardware')
    demo.add_argument('--output', type=Path, required=True)
    demo.add_argument('--scenario', choices=('two-takes', 'low-battery', 'lost-inputs'), default='two-takes')
    run = commands.add_parser('d2-run', help='explicit integrator adapter/config; no default live deployment')
    run.add_argument('--config', type=Path, required=True)
    run.add_argument('--adapter', required=True, help='trusted installed Python module:factory returning D2Adapters')


def run_configured(args):
    config = D2Config.load(args.config)
    # Validate commissioning before importing an adapter which might open devices.
    if config.commissioning_manifest:
        qualification = load_commissioning(config.commissioning_manifest)
        if not qualification.limits_passed:
            raise ValueError('commissioning bench measurements do not meet D2 limits')
    module, separator, factory_name = args.adapter.partition(':')
    if not separator or not module or not factory_name.isidentifier() or not all(p.isidentifier() for p in module.split('.')):
        raise ValueError('--adapter must be a trusted installed module:factory')
    factory = getattr(importlib.import_module(module), factory_name, None)
    if not callable(factory):
        raise ValueError('D2 adapter factory was not found or is not callable')
    result = run_application(config, factory(config))
    print(json.dumps(result, indent=2))
    return 1 if result['status']['failure'] or result['cleanup_errors'] else 0


def run_demo(args):
    """Two takes or a fault, virtual clock plus real durable asynchronous writer.

    Hard-coded WB values/voltage/contact motion are TEST INPUTS. Not a capture,
    I/O latency, performance, hardware-readiness or shutdown qualification.
    """
    if Path(args.output).exists() and any(Path(args.output).iterdir()):
        raise ValueError('D2 demo requires a new or empty output directory; existing takes are not demo evidence')
    reports = []
    with ClipStore(args.output, reserve_bytes=0) as store:
        runtime = D2Runtime(store, lambda settings: SimulationBackend(), now_ns=0, wb_gains=(1.5, 1.25),
                            simulation_only=True,
                            writer_factory=lambda transaction: AsyncClipWriter(transaction, capacity=4))
        for ms in range(0, 6010, 10):
            run_high = not (1200 <= ms < 1240 or 2000 <= ms < 2040 or 2600 <= ms < 2640 or 3400 <= ms < 3440)
            inputs = D2InputSample(ms * 1_000_000, run_high, ms >= 1750, 1 if ms >= 1750 else 0, True, False)
            voltage = 3300 if args.scenario == 'low-battery' and ms >= 1800 else 3900
            error = 'simulated unplug' if args.scenario == 'lost-inputs' and ms >= 1800 else None
            state = runtime.step(ms * 1_000_000, inputs, D2BatterySample(ms * 1_000_000, voltage, 75),
                                 input_error=error, shutdown_requested=ms >= 4200)
            if not reports or state.to_dict() != reports[-1]['status']:
                reports.append({'virtual_ms': ms, 'status': state.to_dict()})
            if runtime.controller is not None and runtime.controller._writer is not None:
                runtime.controller._writer.wait_idle()
                if runtime.controller._finish_future is not None:
                    runtime.controller._finish_future.result(timeout=10)
            if runtime.capture_safely_drained:
                break
        if not runtime.capture_safely_drained:
            raise RuntimeError('D2 demo did not drain; inspect its labelled test takes')
        summary = {'simulation_only': True, 'contains_camera_footage': False, 'hardware_qualified': False,
                   'scenario': args.scenario, 'capture_safely_drained': runtime.capture_safely_drained,
                   'os_poweroff_requested': False, 'states': reports,
                   'clips': [str(p.parent) for p in sorted(Path(args.output).glob('*/manifest.json'))]}
        path = Path(args.output) / 'd2-demo-summary.json'
        path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'simulation_only': True, 'summary': str(path), 'clips': summary['clips'],
                          'capture_safely_drained': True, 'os_poweroff_requested': False}, indent=2))
        return 0
