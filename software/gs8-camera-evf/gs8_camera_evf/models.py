# SPDX-License-Identifier: MIT
"""Take settings and backend messages. No sensor calibration is assumed."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from fractions import Fraction
import math
from pathlib import Path

from .controls import ControlSelection


@dataclass(frozen=True, slots=True)
class TakeSettings:
    fps: int
    shutter_angle: int
    exposure_us: int
    analogue_gain: float
    wb: str
    capture_format: str
    look: str
    audio: bool
    wb_gains: tuple[float, float] | None = None

    @classmethod
    def from_selection(cls, selection: ControlSelection, wb_gains=None):
        if not isinstance(selection, ControlSelection):
            raise ValueError('a valid physical control selection is required')
        if type(selection.fps) is not int or selection.fps not in (18, 24):
            raise ValueError('FPS must be 18 or 24')
        if type(selection.shutter_angle) is not int or selection.shutter_angle not in (90, 144, 180, 216):
            raise ValueError('unsupported shutter angle')
        if type(selection.analogue_gain) not in (int, float) or selection.analogue_gain not in (1, 2, 4, 8):
            raise ValueError('unsupported analogue gain')
        if selection.wb not in ('3200', '4300', '5600', 'custom'):
            raise ValueError('unsupported white balance')
        if selection.capture_format not in ('raw', 'encoded') or selection.look not in ('film', 'clean', 'pxl'):
            raise ValueError('unsupported format or look')
        if type(selection.audio) is not bool:
            raise ValueError('audio must be boolean')
        if wb_gains is not None:
            if (not isinstance(wb_gains, (list, tuple)) or len(wb_gains) != 2
                    or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in wb_gains)):
                raise ValueError('white balance requires two positive finite calibrated gains')
            wb_gains = tuple(float(v) for v in wb_gains)
        return cls(selection.fps, selection.shutter_angle,
                   round(Fraction(selection.shutter_angle * 1_000_000, 360 * selection.fps)),
                   float(selection.analogue_gain), selection.wb, selection.capture_format,
                   selection.look, selection.audio, wb_gains)

    def to_dict(self):
        values = asdict(self)
        if self.wb_gains is None:
            values.pop('wb_gains')
        return values


@dataclass(frozen=True, slots=True)
class Frame:
    """Source sequence (zero-based per take), timestamp and immutable pixels.

    FilePayload avoids materializing a DNG in Python memory. Applied metadata
    is the backend's measured result, never a copy of requested settings.
    """
    index: int
    sensor_timestamp_ns: int
    payload: bytes | bytearray | memoryview | FilePayload
    applied_metadata: dict | None = None


@dataclass(frozen=True, slots=True)
class FilePayload:
    """Closed, immutable regular file; backend retains it until close()."""
    path: Path


@dataclass(frozen=True, slots=True)
class DroppedFrames:
    first_sequence: int
    count: int
    reason: str


@dataclass(frozen=True, slots=True)
class AudioInfo:
    sample_rate: int
    channels: int
    sample_frames: int
    sensor_timestamp_ns: int

    def to_dict(self):
        values = asdict(self)
        for name, value in values.items():
            if type(value) is not int or value < (0 if name == 'sensor_timestamp_ns' else 1):
                raise ValueError('invalid audio timing metadata')
        return values


@dataclass(frozen=True, slots=True)
class Artifact:
    filename: str
    payload: bytes | FilePayload
    kind: str
    audio_info: AudioInfo | None = None
