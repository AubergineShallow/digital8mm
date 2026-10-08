# SPDX-License-Identifier: MIT
"""D2's two dials and two buttons, with no hardware or LED side effects.

Source: electronics/gs8-d2-v1/WIRING.md section 8. GPIO26 is active-low
run/toggle; GPIO13 high=18, low=24. The encoder is seesaw 0x37, push pin 24.
A pulled-up open wire is indistinguishable from a released contact or 18 FPS.
This decoder cannot certify a connected harness.
"""
from dataclasses import dataclass

from .controls import ControlSelection

RUN_GPIO = 26
FPS_GPIO = 13
ENCODER_ADDRESS = 0x37
ENCODER_PUSH_PIN = 24


@dataclass(frozen=True)
class D2InputSample:
    acquired_ns: int
    run_high: bool
    fps_high: bool
    encoder_position: int
    encoder_push_high: bool
    power_pressed: bool


@dataclass(frozen=True)
class D2ControlState:
    selection: ControlSelection | None
    run_pressed: bool | None
    run_edge: bool
    shutdown_requested: bool


class _Contact:
    def __init__(self, debounce_ns=10_000_000):
        self.debounce_ns = debounce_ns
        self.candidate = None
        self.since = None
        self.stable = None
        self.armed = False

    def update(self, high, now):
        if high != self.candidate:
            self.candidate, self.since = high, now
        if now - self.since < self.debounce_ns:
            return None, False
        edge = high is False and self.stable is not False and self.armed
        self.stable = high
        if high:
            self.armed = True
        elif edge:
            self.armed = False
        return high, edge


class D2Controls:
    """Qualify raw samples; never queue a press from an unready camera.

    Gain detents 1/2/4/8x and reset-to-1x are a conservative commissioning
    interaction, not a claim of measured encoder direction or live exposure.
    The runtime freezes the settings for a take and applies changes afterward.
    Power requires a release after startup, then an uninterrupted 2 s hold.
    """
    max_age_ns = 100_000_000
    gains = (1.0, 2.0, 4.0, 8.0)

    def __init__(self):
        self._run, self._fps, self._push = _Contact(), _Contact(), _Contact()
        self._last_now = None
        self._last_sample = None
        self._position = None
        self._gain_index = 0
        self._power_armed = False
        self._power_since = None
        self._shutdown = False
        self._state = D2ControlState(None, None, False, False)

    def requalify_after_idle_setup(self):
        """Drop button/time history after a blocking idle camera setup.

        Preserve the chosen gain, but never replay unseen encoder movement or
        held buttons. The runtime must never use this while a take is active.
        """
        self._run, self._fps, self._push = _Contact(), _Contact(), _Contact()
        self._last_now = self._last_sample = self._position = None
        self._power_armed, self._power_since = False, None
        self._state = D2ControlState(None, None, False, self._shutdown)

    def update(self, now_ns, sample):
        if type(now_ns) is not int or now_ns < 0 or (self._last_now is not None and now_ns < self._last_now):
            raise ValueError('D2 input clock must be monotonic integer nanoseconds')
        if not isinstance(sample, D2InputSample):
            raise ValueError('D2 controls require a complete input sample')
        if (type(sample.acquired_ns) is not int or sample.acquired_ns < 0 or sample.acquired_ns > now_ns
                or now_ns - sample.acquired_ns > self.max_age_ns
                or (self._last_sample is not None and sample.acquired_ns < self._last_sample)):
            raise ValueError('D2 control sample is stale, future-dated or reordered')
        if (self._last_sample is not None and sample.acquired_ns - self._last_sample > self.max_age_ns):
            raise ValueError('D2 control sampling gap; inputs cannot be qualified')
        if any(type(value) is not bool for value in (sample.run_high, sample.fps_high,
                                                     sample.encoder_push_high, sample.power_pressed)):
            raise ValueError('D2 contact levels must be explicit booleans')
        if type(sample.encoder_position) is not int or not -(2**31) <= sample.encoder_position < 2**31:
            raise ValueError('D2 encoder position must be a signed 32-bit integer')
        delta = 0 if self._position is None else ((sample.encoder_position - self._position + 2**31) % 2**32 - 2**31)
        if abs(delta) > 128:
            raise ValueError('D2 encoder jumped/reset; do not silently change exposure')
        self._last_now = now_ns
        if sample.acquired_ns == self._last_sample:
            # A repeatedly polled cached value cannot qualify a button or hold.
            return D2ControlState(self._state.selection, self._state.run_pressed, False, self._shutdown)
        self._last_sample = sample.acquired_ns
        self._position = sample.encoder_position
        self._gain_index = max(0, min(len(self.gains) - 1, self._gain_index + delta))
        run_high, edge = self._run.update(sample.run_high, sample.acquired_ns)
        fps_high, _ = self._fps.update(sample.fps_high, sample.acquired_ns)
        _, reset = self._push.update(sample.encoder_push_high, sample.acquired_ns)
        if reset:
            self._gain_index = 0
        if not sample.power_pressed:
            self._power_armed, self._power_since = True, None
        elif self._power_armed:
            if self._power_since is None:
                self._power_since = sample.acquired_ns
            if sample.acquired_ns - self._power_since >= 2_000_000_000:
                self._shutdown = True
        selection = None if fps_high is None else ControlSelection(
            18 if fps_high else 24, 90, self.gains[self._gain_index], 'custom', 'raw', 'clean', False)
        self._state = D2ControlState(selection, None if run_high is None else not run_high, edge, self._shutdown)
        return self._state
