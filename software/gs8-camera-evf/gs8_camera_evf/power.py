# SPDX-License-Identifier: MIT
"""GNB 3S LiHV low-voltage stop policy and optional Linux INA260/OS adapters.

Thresholds are provisional commissioning settings, not cell protection ratings.
This module never drives a cutoff GPIO. A stalled reader must not stall capture.
"""
from dataclasses import dataclass
from pathlib import Path
import subprocess
from threading import Event, Lock, Thread
import time


@dataclass(frozen=True)
class BatterySample:
    acquired_ns: int
    millivolts: int
    milliamps: int


class BatteryPolicy:
    """Latch stop on undervoltage or lost telemetry; no automatic recovery/cutoff."""
    # Provisional 3S values: warn 3.6, stop 3.5, critical 3.4 V/cell average.
    # Pack voltage alone cannot detect an imbalanced cell; independent cell protection required.
    max_age_ns = 500_000_000
    start_dwell_ns = 1_000_000_000
    low_dwell_ns = 1_000_000_000

    def __init__(self, now_ns):
        self.started_ns = now_ns
        self.last_poll_ns = now_ns
        self.last_sample_ns = None
        self.healthy_since = None
        self.low_since = None
        self.ready = False
        self.warning = False
        self.shutdown_reason = None

    def stop(self, reason):
        self.shutdown_reason = self.shutdown_reason or reason
        self.ready = False

    def update(self, now_ns, sample=None, error=None):
        if self.shutdown_reason:
            return
        if type(now_ns) is not int or now_ns < self.last_poll_ns:
            self.stop('monitor_clock_regression')
            return
        self.last_poll_ns = now_ns
        if error:
            self.stop('battery_monitor_error')
            return
        if sample is None:
            if now_ns - self.started_ns > self.max_age_ns:
                self.stop('battery_monitor_missing')
            return
        if (type(sample.acquired_ns) is not int or sample.acquired_ns > now_ns
                or now_ns - sample.acquired_ns > self.max_age_ns
                or (self.last_sample_ns is not None and sample.acquired_ns < self.last_sample_ns)):
            self.stop('battery_monitor_stale_or_reordered')
            return
        if (type(sample.millivolts) is not int or not 6000 <= sample.millivolts <= 13350
                or type(sample.milliamps) is not int or not -100 <= sample.milliamps <= 15000):
            self.stop('battery_monitor_implausible')
            return
        if sample.acquired_ns == self.last_sample_ns:
            return  # repeated polling is not a new conversion/read
        if self.last_sample_ns is not None and sample.acquired_ns - self.last_sample_ns > self.max_age_ns:
            self.stop('battery_monitor_gap')
            return
        self.last_sample_ns = sample.acquired_ns
        voltage = sample.millivolts
        if voltage <= 10800:
            self.warning = True
        elif voltage >= 11100:
            self.warning = False
        if voltage <= 10200:
            self.stop('battery_critical_voltage')
        elif voltage <= 10500:
            if self.low_since is None:
                self.low_since = sample.acquired_ns
            if sample.acquired_ns - self.low_since >= self.low_dwell_ns:
                self.stop('battery_low_voltage')
        else:
            self.low_since = None
        if not self.ready:
            if voltage >= 11100 and not self.shutdown_reason:
                if self.healthy_since is None:
                    self.healthy_since = sample.acquired_ns
                self.ready = sample.acquired_ns - self.healthy_since >= self.start_dwell_ns
            else:
                self.healthy_since = None


class Ina260Hwmon:
    """Read an explicitly selected ina260 kernel hwmon device; no bus writes."""
    def __init__(self, directory):
        self.directory = Path(directory)

    def read(self):
        started = time.monotonic_ns()
        if (self.directory / 'name').read_text().strip() != 'ina260':
            raise ValueError('Selected hwmon device is not ina260')
        interval = int((self.directory / 'update_interval').read_text())
        if not 1 <= interval <= 100:
            raise ValueError('INA260 update_interval must be verified in 1..100 ms')
        voltage = int((self.directory / 'in1_input').read_text())
        current = int((self.directory / 'curr1_input').read_text())
        # Timestamp the beginning, so a delayed read cannot masquerade as fresh.
        return BatterySample(started, voltage, current)


class BatteryGuard:
    """One bounded latest-sample slot; a blocked I2C read cannot block the recorder."""
    def __init__(self, reader):
        self.reader = reader
        self.policy = BatteryPolicy(time.monotonic_ns())
        self._lock = Lock()
        self._stop = Event()
        self._sample = None
        self._error = None
        self._thread = Thread(target=self._read, name='battery-monitor', daemon=True)
        self._thread.start()

    def _read(self):
        while not self._stop.is_set():
            try:
                sample = self.reader.read()
                with self._lock:
                    self._sample = sample
            except Exception as exc:
                with self._lock:
                    self._error = type(exc).__name__
                return
            self._stop.wait(.1)

    def poll(self):
        with self._lock:
            sample, error = self._sample, self._error
        self.policy.update(time.monotonic_ns(), sample, error)
        return self.policy

    def close(self):
        self._stop.set()
        self._thread.join(timeout=.2)
        # A stuck read-only sysfs worker is a daemon; it never owns clip resources.


def request_os_poweroff(*, safe_to_poweroff, runner=subprocess.run):
    """Called only after recorder/preview/store cleanup; never force or cut power."""
    if safe_to_poweroff is not True:
        raise RuntimeError('Poweroff inhibited: recording drain/commit is not confirmed')
    try:
        runner(['systemctl', 'poweroff'], check=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError('OS poweroff request failed; no cutoff was requested') from exc


def step_with_battery(controller, now_ns, selection, *, trigger_pressed,
                      policy, shutdown_requested=False):
    """Both finder adapters use the recorder's existing drain/commit boundary.

    Policy must have been updated/polled on this tick. No poweroff or GPIO write.
    A held trigger during warmup must be released before a take can start.
    """
    return controller.step(now_ns, selection if policy.ready else None,
                           trigger_pressed=trigger_pressed,
                           shutdown_requested=shutdown_requested or bool(policy.shutdown_reason))
