# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GS8 contributors
"""Decode the GS8 release-v1 physical controls without accessing hardware.

The electrical source of truth is ``electronics/gs8-release-v1/netlist_source.py``
(``MCP_MAP``: MCP23017 0x20 GPA0-6/GPB0-6, unchanged from wiring-v1) and
``electronics/gs8-release-v1/pi5-header.csv`` (direct inputs BCM5/6/7/13). Contacts are active
low. GPA7 and GPB7 are unused outputs and never participate in decoding.
An invalid selector must inhibit starting a take, rather than select a default.

Read both MCP23017 ports on an interrupt and periodically. Those two reads do
not form an atomic snapshot, so pass invalid reads to ``Debouncer`` as ``None``.
The controller, not this module, freezes an accepted selection for each take.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeVar


class ControlError(ValueError):
    """A contact sample, selection, or debounce parameter is invalid."""


@dataclass(frozen=True, slots=True)
class ControlSelection:
    fps: int
    shutter_angle: int
    analogue_gain: float
    wb: str
    capture_format: str
    look: str
    audio: bool


_DIRECT_NAMES = ("ENC_N", "LOOK_FILM_N", "LOOK_PXL_N", "AUDIO_ON_N")
_Choice = TypeVar("_Choice")


def _one_low(name: str, contacts: tuple[tuple[_Choice, bool], ...]) -> _Choice:
    selected = [value for value, high in contacts if not high]
    if len(selected) != 1:
        raise ControlError(
            f"{name} requires exactly one low contact; got {len(selected)}"
        )
    return selected[0]


def decode_contacts(
    gpa: int, gpb: int, direct: Mapping[str, bool]
) -> ControlSelection:
    """Decode two unsigned MCP port bytes and direct GPIO electrical levels.

    Each required direct value must be a ``bool``: ``True`` means electrically
    high, not enabled. Extra keys (for example ``WB_SET_N``) are ignored.
    Missing keys, non-byte ports, non-boolean GPIO levels and invalid one-hot
    selectors raise ``ControlError``. The caller must treat errors as an
    invalid sample, not keep the last raw sample indefinitely.

    FORMAT and AUDIO each have one wired throw: an unplugged switch can look
    like RAW or AUDIO OFF. LOOK's open centre position is CLEAN. Consequently,
    successful decoding cannot prove every switch harness is connected.
    """
    for name, value in (("GPA", gpa), ("GPB", gpb)):
        if type(value) is not int or not 0 <= value <= 0xFF:
            raise ControlError(f"{name} must be an integer byte (0..255)")
    if not isinstance(direct, Mapping):
        raise ControlError("direct must be a mapping of electrical levels")
    for name in _DIRECT_NAMES:
        if name not in direct:
            raise ControlError(f"missing direct input {name}")
        if type(direct[name]) is not bool:
            raise ControlError(f"{name} must be bool: True=high, False=low")

    fps = _one_low("FPS", ((18, bool(gpa & 0x01)), (24, bool(gpa & 0x02))))
    shutter = _one_low(
        "SHUTTER",
        (
            (90, bool(gpa & 0x04)),
            (144, bool(gpa & 0x08)),
            (180, bool(gpa & 0x10)),
            (216, bool(gpa & 0x20)),
        ),
    )
    gain = _one_low(
        "GAIN",
        (
            (1.0, bool(gpa & 0x40)),
            (2.0, bool(gpb & 0x01)),
            (4.0, bool(gpb & 0x02)),
            (8.0, bool(gpb & 0x04)),
        ),
    )
    wb = _one_low(
        "WB",
        (
            ("3200", bool(gpb & 0x08)),
            ("4300", bool(gpb & 0x10)),
            ("5600", bool(gpb & 0x20)),
            ("custom", bool(gpb & 0x40)),
        ),
    )
    film = not direct["LOOK_FILM_N"]
    pxl = not direct["LOOK_PXL_N"]
    if film and pxl:
        raise ControlError("LOOK has both FILM and PXL contacts low")

    return ControlSelection(
        fps=fps,
        shutter_angle=shutter,
        analogue_gain=gain,
        wb=wb,
        capture_format="raw" if direct["ENC_N"] else "encoded",
        look="film" if film else "pxl" if pxl else "clean",
        audio=not direct["AUDIO_ON_N"],
    )


class Debouncer:
    """Require an unchanged, valid selection for ``stable_ms`` milliseconds.

    ``update`` returns ``None`` while settling; it never returns a stale
    selection after a dial change. Invalid input immediately forgets all prior
    settling, including a previously accepted selection. A subsequent valid
    sample must qualify for the full interval again.

    Timestamps are non-negative integer monotonic nanoseconds, typically from
    ``time.monotonic_ns()``. Equal timestamps are allowed but add no settling
    time. Decreasing timestamps raise ``ControlError`` without mutating state.
    The default 20 ms is a proposed starting value, not measured switch bounce.
    This class assumes regularly sampled inputs; elapsed time alone cannot
    reveal transitions or a disconnected device between samples.
    """

    def __init__(self, stable_ms: int = 20) -> None:
        if type(stable_ms) is not int or stable_ms < 0:
            raise ControlError("stable_ms must be a non-negative integer")
        self._stable_ns = stable_ms * 1_000_000
        self._candidate: ControlSelection | None = None
        self._candidate_since_ns: int | None = None
        self._last_ns: int | None = None

    def update(
        self, raw_selection: ControlSelection | None, now_ns: int
    ) -> ControlSelection | None:
        if type(now_ns) is not int or now_ns < 0:
            raise ControlError("now_ns must be a non-negative integer")
        if self._last_ns is not None and now_ns < self._last_ns:
            raise ControlError("now_ns must not move backwards")
        if raw_selection is not None and not isinstance(raw_selection, ControlSelection):
            raise ControlError("raw_selection must be ControlSelection or None")
        self._last_ns = now_ns

        if raw_selection is None:
            self._candidate = None
            self._candidate_since_ns = None
            return None
        if raw_selection != self._candidate:
            self._candidate = raw_selection
            self._candidate_since_ns = now_ns
        # A non-None candidate is always paired with its first sample time.
        assert self._candidate_since_ns is not None
        if now_ns - self._candidate_since_ns >= self._stable_ns:
            return self._candidate
        return None
