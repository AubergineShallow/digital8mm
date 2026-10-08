# SPDX-License-Identifier: MIT
"""Capture boundary and explicit simulation backend; no Pi device is accessed."""
from typing import Protocol
import io
import json
import wave
from copy import deepcopy

from .models import Artifact, AudioInfo, DroppedFrames, Frame, TakeSettings


SIMULATION_SENSOR = {'model': 'imx296', 'width': 1456, 'height': 1088, 'bit_depth': 10,
                     'mode': 'simulated_descriptor', 'crop': [0, 0, 1456, 1088],
                     'timestamp_clock': 'simulation_monotonic', 'simulated': True}


def validate_sensor_descriptor(sensor):
    if not isinstance(sensor, dict):
        raise ValueError('backend must report a sensor descriptor')
    for key in ('model', 'mode', 'timestamp_clock'):
        if not isinstance(sensor.get(key), str) or not sensor[key]:
            raise ValueError(f'backend sensor {key} must be a nonempty string')
    for key in ('width', 'height', 'bit_depth'):
        if type(sensor.get(key)) is not int or sensor[key] <= 0:
            raise ValueError(f'backend sensor {key} must be a positive integer')
    crop = sensor.get('crop')
    if (not isinstance(crop, (list, tuple)) or len(crop) != 4
            or any(type(v) is not int or v < (0 if i < 2 else 1) for i, v in enumerate(crop))):
        raise ValueError('backend sensor crop must be [x, y, width, height] in source pixels')
    json.dumps(sensor, allow_nan=False)
    return deepcopy(sensor)


def validate_final_summary(summary, *, stop_since_ns, now_ns):
    """Require producer evidence; storage-only fallback cannot close capture."""
    if not isinstance(summary, dict) or summary.get('evidence') != 'backend_counters':
        raise ValueError('backend final summary requires independent backend_counters evidence')
    for key in ('expected_frame_count', 'source_frame_count', 'stop_requested_ns'):
        if type(summary.get(key)) is not int or summary[key] < 0:
            raise ValueError(f'backend final summary {key} must be a nonnegative integer')
    if summary['source_frame_count'] < summary['expected_frame_count']:
        raise ValueError('backend source count cannot be smaller than delivered image count')
    if not stop_since_ns <= summary['stop_requested_ns'] <= now_ns:
        raise ValueError('backend stop timestamp lies outside the controller stop interval')
    json.dumps(summary, allow_nan=False)
    return deepcopy(summary)


class CaptureBackend(Protocol):
    """All methods run on one controller thread and must return promptly.

    Device callbacks/encoding run on backend-owned workers. poll transfers
    immutable messages out of a thread-safe queue; it never waits for capture
    or disk I/O. FilePayload files stay closed and immutable until close().
    preflight failure must release its own partially acquired resources.
    """
    simulated: bool

    def preflight(self, settings: TakeSettings) -> dict:
        """Return negotiated sensor model/mode/crop/dimensions/clock metadata."""

    def start(self, settings: TakeSettings, now_ns: int) -> None: ...
    def poll(self, now_ns: int) -> list[Frame | DroppedFrames]: ...
    def request_stop(self, now_ns: int) -> None:
        """Idempotent stop request; it is NOT a drained acknowledgement."""

    def drained(self, now_ns: int) -> bool:
        """True only after producers stop AND every queued frame has been delivered."""

    def artifacts(self) -> list[Artifact]:
        """Called once after drain. Audio must already be closed and complete."""

    def final_summary(self) -> dict:
        """After drain: expected_frame_count, source_frame_count, stop_requested_ns.

        Producer counters must include reported tail drops. Counts must not be
        reconstructed from the storage journal, which would hide queue loss.
        """

    def close(self) -> None:
        """Idempotently release devices/staging files after writer completion."""


class SimulationBackend:
    """Tiny descriptors, not images/video. Timing is virtual, not a benchmark.

    The simulated audio is silence with nominal frame-count duration. It proves
    packaging only, not real audio alignment, latency, drift or 24/32-bit I2S.
    """
    simulated = True

    def __init__(self, drain_delay_ns=100_000_000):
        if type(drain_delay_ns) is not int or drain_delay_ns < 0:
            raise ValueError('drain delay must be a nonnegative integer')
        self.drain_delay_ns = drain_delay_ns
        self.settings = None
        self.stopped_ns = None
        self.index = 0

    def preflight(self, settings):
        if self.settings is not None and self.stopped_ns is None:
            raise RuntimeError('simulation backend already running')
        return dict(SIMULATION_SENSOR)

    def start(self, settings, now_ns):
        self.settings = settings
        self.started_ns = now_ns
        self.stopped_ns = None
        self.index = 0

    def _timestamp(self, index):
        # Round upward so poll cannot return a frame before its due time.
        return self.started_ns + ((index + 1) * 1_000_000_000 + self.settings.fps - 1) // self.settings.fps

    def poll(self, now_ns):
        if self.settings is None:
            return []
        until = min(now_ns, self.stopped_ns) if self.stopped_ns is not None else now_ns
        count = max(0, (until - self.started_ns) * self.settings.fps // 1_000_000_000 - self.index)
        if count > 512:
            raise RuntimeError('simulation poll backlog exceeds 512 frames')
        frames = []
        while self._timestamp(self.index) <= until:
            timestamp = self._timestamp(self.index)
            payload = (json.dumps({'simulation_only': True, 'contains_pixels': False,
                                  'index': self.index, 'timestamp_ns': timestamp,
                                  'fps': self.settings.fps}, sort_keys=True) + '\n').encode()
            frames.append(Frame(self.index, timestamp, payload))
            self.index += 1
        return frames

    def request_stop(self, now_ns):
        if self.stopped_ns is None:
            self.stopped_ns = now_ns

    def drained(self, now_ns):
        return (self.stopped_ns is not None
                and now_ns >= self.stopped_ns + self.drain_delay_ns
                and (self.settings is None or self._timestamp(self.index) > self.stopped_ns))

    def artifacts(self):
        if not self.settings or not self.settings.audio:
            return []
        stream = io.BytesIO()
        with wave.open(stream, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48_000)
            wav.writeframes(b'\0\0' * (self.index * 48_000 // self.settings.fps))
        return [Artifact('audio.sim.wav', stream.getvalue(), 'simulated_audio',
                         AudioInfo(48_000, 1, self.index * 48_000 // self.settings.fps, self._timestamp(0)))]

    def final_summary(self):
        return {'expected_frame_count': self.index, 'source_frame_count': self.index,
                'stop_requested_ns': self.stopped_ns, 'evidence': 'backend_counters'}

    def close(self):
        self.settings = None
