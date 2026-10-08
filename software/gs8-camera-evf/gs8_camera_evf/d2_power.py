# SPDX-License-Identifier: MIT
"""D2 1S telemetry and ordered shutdown contracts, separate from GNB 3S.

3.3 V is the planning threshold in D2 WIRING s8/R-P8, subject to G-W5/G-W12.
These software checks are not battery protection or evidence of power margin.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable


@dataclass(frozen=True)
class D2BatterySample:
    acquired_ns: int
    millivolts: int
    percent: float


class D2BatteryPolicy:
    max_age_ns = 500_000_000
    start_dwell_ns = 1_000_000_000

    def __init__(self, now_ns, *, stop_millivolts=3300):
        if type(now_ns) is not int or now_ns < 0:
            raise ValueError('battery clock must be nonnegative integer nanoseconds')
        if type(stop_millivolts) is not int or not 3300 <= stop_millivolts <= 4000:
            raise ValueError('D2 stop threshold must be 3300..4000 mV; lowering the planning floor is not supported')
        self.stop_millivolts = stop_millivolts
        self.started_ns = self.last_poll_ns = now_ns
        self.last_sample = None
        self.healthy_since = None
        self.ready = self.warning = False
        self.shutdown_reason = None

    def stop(self, reason):
        self.shutdown_reason = self.shutdown_reason or reason
        self.ready = False

    def update(self, now_ns, sample=None, error=None):
        if self.shutdown_reason:
            return self
        if type(now_ns) is not int or now_ns < self.last_poll_ns:
            self.stop('battery_clock_regression')
            return self
        self.last_poll_ns = now_ns
        if error is not None:
            self.stop('battery_read_error')
            return self
        if sample is None:
            # Use the most recent *actual acquisition*, never the polling time.
            stamp = self.last_sample.acquired_ns if self.last_sample else self.started_ns
            if now_ns - stamp > self.max_age_ns:
                self.stop('battery_telemetry_missing')
            return self
        if (not isinstance(sample, D2BatterySample) or type(sample.acquired_ns) is not int
                or sample.acquired_ns < 0 or sample.acquired_ns > now_ns
                or now_ns - sample.acquired_ns > self.max_age_ns
                or (self.last_sample is not None and sample.acquired_ns < self.last_sample.acquired_ns)):
            self.stop('battery_telemetry_stale_or_reordered')
            return self
        if (type(sample.millivolts) is not int or not 2500 <= sample.millivolts <= 4350
                or type(sample.percent) not in (int, float) or not 0 <= sample.percent <= 100):
            self.stop('battery_telemetry_implausible')
            return self
        if self.last_sample is not None:
            if sample.acquired_ns == self.last_sample.acquired_ns:
                return self
            if sample.acquired_ns - self.last_sample.acquired_ns > self.max_age_ns:
                self.stop('battery_telemetry_gap')
                return self
        self.last_sample = sample
        if sample.millivolts <= self.stop_millivolts:
            self.stop('battery_low_voltage')
            return self
        if sample.millivolts <= self.stop_millivolts + 200:
            self.warning = True
        elif sample.millivolts >= self.stop_millivolts + 300:
            self.warning = False
        if self.healthy_since is None:
            self.healthy_since = sample.acquired_ns
        self.ready = sample.acquired_ns - self.healthy_since >= self.start_dwell_ns
        return self


class ShutdownPhase(str, Enum):
    IDLE = 'idle'
    DRAINING = 'draining'
    POWEROFF_REQUESTED = 'poweroff_requested'
    FAILED = 'failed'


@dataclass(frozen=True)
class ShutdownActions:
    """Commissioned adapters must supply all five operations explicitly.

    hold_screen must arrange display ownership independent of capture teardown,
    retaining SHUTTING DOWN until OS halt. sync/unmount must target the verified
    removable media, never an inferred path. Success is not a measured halt.
    """
    hold_screen: Callable[[], None]
    close_store: Callable[[], None]
    sync_media: Callable[[], None]
    unmount_media: Callable[[], None]
    request_poweroff: Callable[[], None]


class D2Shutdown:
    """Drain -> close -> sync -> unmount -> normal poweroff; never force.

    An action exception latches failure. There is no blind retry of a possibly
    completed unmount/poweroff. No actions are wired to the host by default.
    """
    def __init__(self, actions):
        if not isinstance(actions, ShutdownActions) or any(not callable(v) for v in vars(actions).values()):
            raise ValueError('all shutdown adapters must be explicit callables')
        self.actions = actions
        self.phase = ShutdownPhase.IDLE
        self.completed = []
        self.failure = None

    def _call(self, name):
        try:
            getattr(self.actions, name)()
            self.completed.append(name)
            return True
        except Exception as error:
            self.failure = f'{name}: {type(error).__name__}: {error}'
            self.phase = ShutdownPhase.FAILED
            return False

    def begin(self):
        if self.phase == ShutdownPhase.IDLE and self._call('hold_screen'):
            self.phase = ShutdownPhase.DRAINING
        return self.phase

    def advance(self, *, capture_safely_drained):
        if type(capture_safely_drained) is not bool:
            raise ValueError('capture drain acknowledgement must be boolean')
        if self.phase != ShutdownPhase.DRAINING or not capture_safely_drained:
            return self.phase
        for name in ('close_store', 'sync_media', 'unmount_media', 'request_poweroff'):
            if not self._call(name):
                return self.phase
        self.phase = ShutdownPhase.POWEROFF_REQUESTED
        return self.phase
