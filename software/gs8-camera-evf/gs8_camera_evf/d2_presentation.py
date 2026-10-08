# SPDX-License-Identifier: MIT
"""Host-only D2 status presentation for the selected 1024 x 768 EVF-A.

No display, camera, input, OS, timing or shutdown actions live here. The returned
straight-alpha RGBA overlay has a transparent, full-sensor-aspect preview window.
A future commissioned display adapter must place the *entire* preview in that
window; placing this overlay over the existing full-canvas preview would crop it.

The built-in 5 x 7 glyphs make pixel bounds deterministic without a font/package
or hardware dependency. Host rendering is not optical/eyepiece qualification.
"""
from dataclasses import dataclass
from math import gcd, isfinite
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .d2_runtime import D2Status


CANVAS_SIZE = (1024, 768)
HEADER_HEIGHT = 48
FOOTER_HEIGHT = 40
FULL_SENSOR_SIZE = (1456, 1088)
DEFAULT_PREVIEW_SIZE = (728, 544)

WHITE = (240, 242, 244, 255)
MUTED = (174, 181, 188, 255)
AMBER = (255, 207, 102, 255)
RED = (255, 112, 112, 255)
BLACK = (0, 0, 0, 255)
RGBA = tuple[int, int, int, int]

# Original, deliberately small uppercase raster alphabet. Each row is five bits.
_FONT_ROWS = {
    ' ': ('00000',) * 7,
    'A': ('01110','10001','10001','11111','10001','10001','10001'),
    'B': ('11110','10001','10001','11110','10001','10001','11110'),
    'C': ('01111','10000','10000','10000','10000','10000','01111'),
    'D': ('11110','10001','10001','10001','10001','10001','11110'),
    'E': ('11111','10000','10000','11110','10000','10000','11111'),
    'F': ('11111','10000','10000','11110','10000','10000','10000'),
    'G': ('01111','10000','10000','10111','10001','10001','01111'),
    'H': ('10001','10001','10001','11111','10001','10001','10001'),
    'I': ('11111','00100','00100','00100','00100','00100','11111'),
    'J': ('00111','00010','00010','00010','10010','10010','01100'),
    'K': ('10001','10010','10100','11000','10100','10010','10001'),
    'L': ('10000','10000','10000','10000','10000','10000','11111'),
    'M': ('10001','11011','10101','10101','10001','10001','10001'),
    'N': ('10001','11001','10101','10011','10001','10001','10001'),
    'O': ('01110','10001','10001','10001','10001','10001','01110'),
    'P': ('11110','10001','10001','11110','10000','10000','10000'),
    'Q': ('01110','10001','10001','10001','10101','10010','01101'),
    'R': ('11110','10001','10001','11110','10100','10010','10001'),
    'S': ('01111','10000','10000','01110','00001','00001','11110'),
    'T': ('11111','00100','00100','00100','00100','00100','00100'),
    'U': ('10001','10001','10001','10001','10001','10001','01110'),
    'V': ('10001','10001','10001','10001','10001','01010','00100'),
    'W': ('10001','10001','10001','10101','10101','10101','01010'),
    'X': ('10001','10001','01010','00100','01010','10001','10001'),
    'Y': ('10001','10001','01010','00100','00100','00100','00100'),
    'Z': ('11111','00001','00010','00100','01000','10000','11111'),
    '0': ('01110','10001','10011','10101','11001','10001','01110'),
    '1': ('00100','01100','00100','00100','00100','00100','01110'),
    '2': ('01110','10001','00001','00010','00100','01000','11111'),
    '3': ('11110','00001','00001','01110','00001','00001','11110'),
    '4': ('00010','00110','01010','10010','11111','00010','00010'),
    '5': ('11111','10000','10000','11110','00001','00001','11110'),
    '6': ('01110','10000','10000','11110','10001','10001','01110'),
    '7': ('11111','00001','00010','00100','01000','01000','01000'),
    '8': ('01110','10001','10001','01110','10001','10001','01110'),
    '9': ('01110','10001','10001','01111','00001','00001','01110'),
    '-': ('00000','00000','00000','11111','00000','00000','00000'),
    '+': ('00000','00100','00100','11111','00100','00100','00000'),
    '.': ('00000','00000','00000','00000','00000','00110','00110'),
    ':': ('00000','00110','00110','00000','00110','00110','00000'),
    '/': ('00001','00001','00010','00100','01000','10000','10000'),
    '%': ('11001','11001','00010','00100','01000','10011','10011'),
    '|': ('00100',) * 7,
    '?': ('01110','10001','00001','00010','00100','00000','00100'),
}
FONT = {char: tuple(int(row, 2) for row in rows) for char, rows in _FONT_ROWS.items()}


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def intersects(self, other):
        return (self.x < other.right and other.x < self.right
                and self.y < other.bottom and other.y < self.bottom)


@dataclass(frozen=True)
class Label:
    key: str
    text: str
    x: int
    y: int
    scale: int
    colour: RGBA = WHITE

    @property
    def bounds(self):
        return Rect(self.x, self.y, text_width(self.text, self.scale), 7 * self.scale)


@dataclass(frozen=True)
class D2Presentation:
    """Immutable render plan. Coordinates are panel pixels, with half-open bounds.

    ``preview_rect=None`` means an opaque status screen, never a frozen image
    that could be mistaken for live view. ``notice_codes`` and ``diagnostics``
    preserve issue detail; all fixed issue categories are shown without scrolling.
    Neither this object nor its pixels establish display ownership or OS halt.
    """
    preview_rect: Rect | None
    labels: tuple[Label, ...]
    accent: RGBA
    notice_codes: tuple[str, ...]
    diagnostics: tuple[tuple[str, str], ...] = ()
    canvas_size: tuple[int, int] = CANVAS_SIZE

    @property
    def text(self):
        return '\n'.join(label.text for label in self.labels)


def text_width(text, scale):
    if type(scale) is not int or not 1 <= scale <= 6:
        raise ValueError('glyph scale must be an integer from 1 to 6')
    if not isinstance(text, str) or not text or any(char not in FONT for char in text):
        raise ValueError('label requires nonempty supported uppercase glyphs')
    return (6 * len(text) - 1) * scale


def preview_rect(source_size=DEFAULT_PREVIEW_SIZE):
    """Fit the full 91:68 source without crop or aspect-ratio distortion.

    The current backend's source dimensions must be positive, even integers
    with exactly the full IMX296 aspect ratio. Integer aspect multiples avoid
    rounding distortion. Both 728x544 and 1456x1088 map to 910x680 at (57, 48).
    This says nothing about actual HDMI scanout or optical field coverage.
    """
    if (not isinstance(source_size, (tuple, list)) or len(source_size) != 2
            or any(type(v) is not int or v <= 0 or v % 2 for v in source_size)
            or source_size[0] * FULL_SENSOR_SIZE[1] != source_size[1] * FULL_SENSOR_SIZE[0]):
        raise ValueError('preview source must have the full 1456:1088 sensor aspect ratio')
    divisor = gcd(*source_size)
    ratio_w, ratio_h = (v // divisor for v in source_size)
    available = CANVAS_SIZE[1] - HEADER_HEIGHT - FOOTER_HEIGHT
    multiple = min(CANVAS_SIZE[0] // ratio_w, available // ratio_h)
    width, height = ratio_w * multiple, ratio_h * multiple
    return Rect((CANVAS_SIZE[0] - width) // 2, HEADER_HEIGHT + (available - height) // 2, width, height)


_PHASES = {
    'checking': ('CHECKING', WHITE, 'WAIT FOR CHECKS / RELEASE RUN'),
    'ready': ('READY', WHITE, 'PRESS RUN TO RECORD'),
    'starting': ('STARTING', AMBER, 'START REQUESTED / WAIT'),
    'recording': ('REC', RED, 'PRESS RUN TO STOP'),
    'saving': ('SAVING', AMBER, 'KEEP POWER CONNECTED'),
    'applying_settings': ('APPLYING', AMBER, 'SETTINGS APPLY BETWEEN TAKES / WAIT'),
    'shutting_down': ('SHUTTING DOWN', AMBER, 'KEEP POWER CONNECTED'),
    'stopped': ('CAPTURE STOPPED', AMBER, 'KEEP POWER CONNECTED'),
    'fault_stopped': ('FAULT STOPPED', RED, 'KEEP POWER CONNECTED'),
}
_TERMINAL = ('shutting_down', 'stopped', 'fault_stopped')
_READINESS_GROUPS = (
    ('media', 'MEDIA'), ('free_bytes', 'STORAGE'), ('usb', 'USB'),
    ('soc_temperature', 'HEAT'), ('throttled', 'THROTTLE'),
    ('runtime_health', 'HEALTH DATA'), ('health_evidence', 'HEALTH DATA'),
    ('commissioning', 'BENCH CHECKS'), ('bench_', 'BENCH CHECKS'),
)


def _fps(value):
    return str(value) if type(value) is int and value in (18, 24) else '--'


def _gain(value):
    return f'{int(value)}X' if type(value) in (int, float) and value in (1, 2, 4, 8) else '--'


def _battery(status, *, lost):
    mv, percent = status.battery_millivolts, status.battery_percent
    voltage_ok = type(mv) is int and 2500 <= mv <= 4350 and not lost
    percent_ok = type(percent) in (int, float) and 0 <= percent <= 100 and isfinite(percent) and not lost
    voltage = f'{mv / 1000:.3f}V' if voltage_ok else '--V'
    soc = f'{percent:.0f}%' if percent_ok else '--%'
    return f'1S {voltage} {soc}', voltage_ok and percent_ok


def _right_label(key, text, y, scale, colour=WHITE):
    return Label(key, text, CANVAS_SIZE[0] - 24 - text_width(text, scale), y, scale, colour)


def _center_label(key, text, y, scale, colour=WHITE):
    return Label(key, text, (CANVAS_SIZE[0] - text_width(text, scale)) // 2, y, scale, colour)


def _qualification(simulation_only):
    return 'SIMULATION / UNQUALIFIED' if simulation_only is True else 'HARDWARE UNQUALIFIED'


def _layout(*, title, accent, qualifier, battery, primary, pending, notices,
            action, viewport, hero=None, subtitle=None, diagnostics=()):
    labels = [Label('phase', title, 24, 6, 3, accent),
              Label('qualification', qualifier, 24, 31, 2, MUTED),
              _right_label('battery', battery, 6, 3,
                           AMBER if any(code.startswith('battery') for code, _ in notices) else WHITE),
              Label('active_settings', primary, 24, 738, 3)]
    if pending is not None:
        labels.append(_right_label('pending_settings', pending, 738, 3, AMBER))
    if viewport is not None:
        # The only routine notice is LOW CELL. Other problems use a dedicated
        # page, keeping the complete reason list legible and the frame uncovered.
        hint = (' / '.join(text for _, text in notices) + ' / ' if notices else '') + action
        labels.append(_right_label('action', hint, 31, 2, AMBER if notices else WHITE))
    else:
        labels.append(_right_label('action', action, 31, 2))
        labels.append(_center_label('attention', hero or 'CHECK STATUS', 140, 4, accent))
        if subtitle:
            labels.append(_center_label('explanation', subtitle, 190, 3))
        # At most 16 fixed categories are produced. Two columns avoid tiny text,
        # scrolling, rotation, ellipses or a transient warning the eye can miss.
        columns = 2 if len(notices) > 8 else 1
        per_column = (len(notices) + columns - 1) // columns
        for index, (code, text) in enumerate(notices):
            column, row = divmod(index, per_column)
            center_x = 512 if columns == 1 else 268 + column * 488
            labels.append(Label('notice_' + code, text,
                                center_x - text_width(text, 3) // 2,
                                278 + row * 42, 3, accent))
    result = D2Presentation(viewport, tuple(labels), accent,
                            tuple(code for code, _ in notices), tuple(diagnostics))
    validate_layout(result)
    return result


def present_status(status: 'D2Status', *, source_size=DEFAULT_PREVIEW_SIZE):
    """Create a conservative presentation of one frozen runtime status.

    Only the runtime's actual phase can declare recording or capture stopped.
    Invalid/missing fields never turn into zero battery or a READY indication.
    Raw exceptions, paths and unknown readiness text are kept out of pixels;
    diagnostics preserve the exact supplied strings for a separate host log.
    """
    viewport = preview_rect(source_size)  # reject an incompatible compositor first
    phase = status.phase
    known_phase = isinstance(phase, str) and phase in _PHASES
    fallback = ('STATUS UNKNOWN', RED, 'CHECK STATUS / KEEP POWER CONNECTED')
    title, accent, action = _PHASES[phase] if known_phase else fallback
    reason = status.shutdown_reason if isinstance(status.shutdown_reason, str) else ''
    failure = status.failure if isinstance(status.failure, str) else ''
    raw_reasons = status.readiness_reasons
    valid_reasons = isinstance(raw_reasons, tuple) and all(isinstance(r, str) for r in raw_reasons)
    reasons = raw_reasons if valid_reasons else ('unknown_readiness',)
    battery_lost = reason.startswith('battery_') and reason != 'battery_low_voltage'
    battery_text, battery_known = _battery(status, lost=battery_lost)
    settings_known = (_fps(status.selected_fps) != '--' and _gain(status.selected_gain) != '--')
    active_known = (_fps(status.active_fps) != '--' and _gain(status.active_gain) != '--')
    # A physical FPS contact has a short qualification interval. During an
    # active take the runtime keeps its frozen settings while both selected
    # values temporarily become None. This is unresolved NEXT, not lost active
    # capture. All fault, battery and readiness checks below still apply.
    pending_unresolved = (phase in ('starting', 'recording', 'saving') and active_known
                          and status.settings_pending is True
                          and status.selected_fps is None and status.selected_gain is None)
    ready_state = (status.readiness_state == 'reported_limits_pass'
                   or (status.simulation_only is True and status.readiness_state == 'simulation_unqualified'))
    readiness_bad = not ready_state or bool(reasons)
    invalid_status = (any(type(v) is not bool for v in (status.simulation_only, status.settings_pending,
                                                       status.battery_warning, status.hardware_qualified))
                     or status.failure is not None and not isinstance(status.failure, str)
                     or status.shutdown_reason is not None and not isinstance(status.shutdown_reason, str)
                     or not valid_reasons)
    notices = []
    # Most consequential conditions always precede expandable readiness detail.
    if reason == 'controls_unavailable' or failure.startswith('controls_unavailable:'):
        notices.append(('input_lost', 'INPUT LOST'))
    if reason == 'battery_low_voltage':
        notices.append(('battery_low_voltage', 'LOW CELL'))
    elif battery_lost:
        notices.append(('battery_data_lost', 'BATTERY DATA LOST'))
    elif status.battery_warning is True:
        notices.append(('battery_warning', 'LOW CELL'))
    if failure:
        notices.append(('fault', 'FAULT'))
    if not known_phase or invalid_status:
        notices.append(('status_unknown', 'STATUS INVALID'))
    if not battery_known and not battery_lost:
        notices.append(('battery_unknown', 'BATTERY UNKNOWN'))
    if ((not settings_known and not pending_unresolved)
            or (phase in ('ready', 'starting', 'recording', 'saving') and not active_known)):
        notices.append(('settings_unknown', 'SETTINGS UNKNOWN'))
    if status.hardware_qualified is True:
        notices.append(('qualification_unverified', 'HARDWARE CLAIM UNVERIFIED'))
    if readiness_bad:
        notices.append(('not_ready', 'NOT READY'))
        seen = set()
        for detail in reasons:
            group = next((label for prefix, label in _READINESS_GROUPS if detail.startswith(prefix)), 'OTHER CHECK')
            if group not in seen:
                notices.append((f'readiness_{group.lower().replace(" ", "_")}', group))
                seen.add(group)
    if phase == 'ready' and (readiness_bad or not battery_known or not settings_known
                             or not active_known or failure or reason or invalid_status
                             or status.hardware_qualified is True):
        title, accent, action = 'NOT READY', RED if failure or invalid_status else AMBER, 'CHECK STATUS / RELEASE RUN'
    elif phase == 'checking' and readiness_bad:
        title, accent, action = 'NOT READY', AMBER, 'RECORD INHIBITED / CHECK STATUS'
    if invalid_status:
        title, accent, action = 'STATUS UNKNOWN', RED, 'CHECK STATUS / KEEP POWER CONNECTED'
    primary = f'ACTIVE {_fps(status.active_fps)} FPS  GAIN {_gain(status.active_gain)}'
    if status.active_fps is None and status.active_gain is None and phase not in ('starting', 'recording', 'saving'):
        primary = f'SELECT {_fps(status.selected_fps)} FPS  GAIN {_gain(status.selected_gain)}'
    pending = (f'NEXT {_fps(status.selected_fps)} FPS  GAIN {_gain(status.selected_gain)}'
               if status.settings_pending is True else None)
    hero = subtitle = None
    serious_notices = any(code != 'battery_warning' for code, _ in notices)
    if phase in _TERMINAL or reason or serious_notices:
        viewport = None
        if phase in _TERMINAL or reason or failure or not known_phase or invalid_status:
            hero, subtitle = 'KEEP POWER CONNECTED', 'OS HALT IS NOT CONFIRMED'
            action = 'KEEP POWER CONNECTED'
        else:
            hero, subtitle = 'CHECK READINESS', 'RELEASE RUN AFTER RECOVERY'
            action = 'CHECK STATUS'
    diagnostics = (('phase', str(phase)), ('shutdown_reason', str(status.shutdown_reason)),
                   ('failure', str(status.failure)), ('readiness_state', str(status.readiness_state)))
    diagnostics += tuple(('readiness_reason', detail) for detail in reasons)
    return _layout(title=title, accent=accent, qualifier=_qualification(status.simulation_only),
                   battery=battery_text, primary=primary, pending=pending, notices=notices,
                   action=action, viewport=viewport, hero=hero, subtitle=subtitle, diagnostics=diagnostics)


def present_shutdown(*, simulation_only):
    """Pre-renderable opaque image for a future ``hold_shutdown_screen`` adapter.

    The callback takes no status argument and can fire before a new snapshot is
    available. Do not reuse an old battery value, clip name or READY image. This
    function merely creates pixels; keeping them visible is the adapter's job.
    """
    if type(simulation_only) is not bool:
        raise ValueError('simulation_only must be explicitly boolean')
    return _layout(title='SHUTTING DOWN', accent=AMBER, qualifier=_qualification(simulation_only),
                   battery='1S --V --%', primary='STOP REQUESTED', pending=None,
                   notices=[('shutdown_requested', 'WAIT FOR SHUTDOWN')],
                   action='KEEP POWER CONNECTED', viewport=None,
                   hero='KEEP POWER CONNECTED', subtitle='OS HALT IS NOT CONFIRMED')


def validate_layout(presentation):
    """Reject clipping, unsupported glyphs, overlapping labels or preview cover."""
    if presentation.canvas_size != CANVAS_SIZE:
        raise ValueError('only the selected 1024x768 EVF-A canvas is supported')
    width, height = CANVAS_SIZE
    viewport = presentation.preview_rect
    if viewport is not None:
        if (viewport != preview_rect() or viewport.x < 0 or viewport.y < HEADER_HEIGHT
                or viewport.right > width or viewport.bottom > height - FOOTER_HEIGHT):
            raise ValueError('preview must preserve the full sensor within the reserved rails')
    bounds = []
    keys = set()
    for label in presentation.labels:
        if label.key in keys:
            raise ValueError('duplicate presentation label key')
        keys.add(label.key)
        rect = label.bounds
        if (type(label.x) is not int or type(label.y) is not int or label.x < 0 or label.y < 0
                or rect.right > width or rect.bottom > height):
            raise ValueError(f'label outside canvas: {label.key}')
        if viewport is not None and rect.intersects(viewport):
            raise ValueError(f'label obscures full sensor: {label.key}')
        if any(rect.intersects(previous) for previous in bounds):
            raise ValueError(f'overlapping label: {label.key}')
        bounds.append(rect)
    required = {'phase', 'qualification', 'battery', 'active_settings', 'action'}
    if not required <= keys:
        raise ValueError('presentation is missing required status labels')
    if viewport is None and any('notice_' + code not in keys for code in presentation.notice_codes):
        raise ValueError('attention page is missing a critical notice')
    for colour in (presentation.accent, *(label.colour for label in presentation.labels)):
        if len(colour) != 4 or any(type(channel) is not int or not 0 <= channel <= 255 for channel in colour):
            raise ValueError('RGBA colours require four byte channels')


def rasterize(presentation):
    """Return tightly packed 1024x768 straight-alpha RGBA bytes, top-left origin.

    Render only on changed presentation content and cache at the display adapter;
    do not put this Python rasterizer on the camera's per-frame callback path.
    No hardware frame or camera buffer is acquired, copied or retained here.
    """
    validate_layout(presentation)
    width, height = CANVAS_SIZE
    image = bytearray(bytes(BLACK) * (width * height))

    def fill(rect, colour):
        row = bytes(colour) * rect.width
        for y in range(rect.y, rect.bottom):
            start = (y * width + rect.x) * 4
            image[start:start + len(row)] = row

    if presentation.preview_rect is not None:
        fill(presentation.preview_rect, (0, 0, 0, 0))
    fill(Rect(0, 0, 6, HEADER_HEIGHT), presentation.accent)
    for label in presentation.labels:
        for index, char in enumerate(label.text):
            for row, mask in enumerate(FONT[char]):
                for column in range(5):
                    if mask & (1 << (4 - column)):
                        fill(Rect(label.x + (index * 6 + column) * label.scale,
                                  label.y + row * label.scale, label.scale, label.scale), label.colour)
    return bytes(image)
