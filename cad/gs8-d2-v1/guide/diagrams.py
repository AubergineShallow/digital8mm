# SPDX-License-Identifier: MIT
"""GS8 D2 assembly guide: wiring diagrams drawn with PIL (schematic, not to scale). Text follows WIRING.md s5-s7."""
from __future__ import annotations

import math

from PIL import ImageFont

from build_guide import BLUE, GREY, INK, OK, WARN, arrow, callout, font, text_block, tw, warn_icon

RED, BLK, YEL, BLU_W = (200, 40, 40), (30, 30, 30), (225, 185, 20), (40, 90, 200)


def wire(d, pts, col, w=9):
    d.line(pts, fill=(255, 255, 255), width=w + 6, joint='curve')
    d.line(pts, fill=col, width=w, joint='curve')


def box3(d, xy, wh, label, fill=(235, 235, 232), f=None, outline=INK, fg=INK):
    x, y = xy
    d.rounded_rectangle((x, y, x + wh[0], y + wh[1]), radius=8, fill=fill, outline=outline, width=3)
    if label:
        f = f or font(20, True)
        for k, ln in enumerate(label.split('\n')):
            d.text((x + wh[0] / 2 - tw(d, ln, f) / 2, y + 8 + k * (f.size + 4)), ln, font=f, fill=fg)


def dim(d, a, b, label, off=26, f=None):
    f = f or font(18, True)
    (x0, y0), (x1, y1) = a, b
    d.line((x0, y0 - off, x1, y1 - off), fill=BLUE, width=2)
    for x, y in (a, b):
        d.line((x, y - off - 8, x, y - off + 8), fill=BLUE, width=2)
    d.text(((x0 + x1) / 2 - tw(d, label, f) / 2, y0 - off - f.size - 6), label, font=f, fill=BLUE)


def note(d, xy, s, width=420, f=None, col=INK):
    return text_block(d, xy, s, f or font(20), width, fill=col)


def heat_shrink(d, x0, y0, x1, y1):
    d.rounded_rectangle((x0, y0, x1, y1), radius=10, outline=(90, 90, 90), width=3)
    for x in range(int(x0) + 8, int(x1) - 4, 14):
        d.line((x, y0 + 3, x + 6, y0 + 3), fill=(150, 150, 150), width=2)


def dg_fuse(d, b):
    x0, y0, x1, y1 = b
    cy = y0 + 260
    box3(d, (x0 + 40, cy - 70), (150, 140), 'XT30\nfemale', fill=(250, 220, 120))
    wire(d, [(x0 + 190, cy - 30), (x1 - 300, cy - 30)], RED)
    wire(d, [(x0 + 190, cy + 30), (x1 - 300, cy + 30)], BLK)
    fx = x0 + 330
    d.rounded_rectangle((fx, cy - 50, fx + 120, cy - 10), radius=14, fill=(245, 245, 240), outline=INK, width=3)
    d.text((fx + 22, cy - 44), '15 A', font=font(22, True), fill=INK)
    heat_shrink(d, fx - 60, cy - 62, fx + 180, cy + 2)
    box3(d, (x1 - 300, cy - 90), (240, 180), 'to X1203\nbattery pads\n(step W2)')
    dim(d, (x0 + 190, cy - 64), (fx, cy - 64), '20-25 mm')
    dim(d, (fx - 60, cy + 110), (fx + 180, cy + 110), 'adhesive 3:1 heat-shrink, about 28 mm', off=-40)
    d.text((fx - 6, cy - 150), 'Littelfuse 0251015.MXL in the RED wire', font=font(18), fill=GREY)
    y = cy + 190
    y = note(d, (x0 + 40, y), 'Fuse leads: trim each to 6.5 mm = 1.5 mm stub at the fuse body + 5 mm lap joint on the '
             'stripped red conductor.', width=x1 - x0 - 80)
    y = note(d, (x0 + 40, y + 10), 'Solder each lead by hand at 350 C for 5 s at most (datasheet). Never re-solder the XT30 '
             'with the fuse fitted.', width=x1 - x0 - 80, col=WARN)
    note(d, (x0 + 40, y + 10), 'Meter: XT30 (+) to the far end of the red wire: less than 0.1 ohm.',
         width=x1 - x0 - 80, col=OK)


def dg_pads(d, b):
    x0, y0, x1, y1 = b
    box3(d, (x0 + 420, y0 + 80), (480, 330), 'Geekworm X1203\n(battery pads)', fill=(200, 225, 205))
    px = x0 + 480
    for k, (lab, col) in enumerate((('+', RED), ('-', BLK))):
        yy = y0 + 220 + k * 90
        d.rectangle((px, yy - 18, px + 60, yy + 18), fill=(212, 175, 55), outline=INK, width=2)
        d.text((px + 70, yy - 16), 'BAT ' + lab, font=font(24, True), fill=INK)
        wire(d, [(x0 + 150, yy), (px + 30, yy)], col)
        heat_shrink(d, px - 70, yy - 20, px + 40, yy + 20)
    box3(d, (x0 + 30, y0 + 190), (120, 150), 'pigtail\n(fused,\nstep W1)', fill=(250, 220, 120))
    d.rounded_rectangle((x0 + 455, y0 + 190, x0 + 600, y0 + 340), radius=18, outline=(90, 140, 200), width=3)
    d.text((x0 + 610, y0 + 425), 'RTV bead over both joints (strain relief); no tie', font=font(18), fill=INK)
    y = y0 + 480
    y = note(d, (x0 + 40, y), 'Red to +, black to -. Adhesive heat-shrink over both joints, then the neutral-cure RTV bead. The U at the W '
             'mark and the taped leg are on the next steps of this page.',
             width=x1 - x0 - 80)
    note(d, (x0 + 40, y + 10), 'The pack is NEVER connected at the bench. Meter + to - on the pigtail: no short, '
         'before anything else.', width=x1 - x0 - 80, col=WARN)


def dg_diode(d, b):
    x0, y0, x1, y1 = b
    cy = y0 + 230
    box3(d, (x0 + 30, cy - 60), (150, 120), 'USB-A\nmale', fill=(225, 225, 230))
    d.text((x0 + 190, cy - 70), 'VBUS', font=font(18, True), fill=RED)
    d.text((x0 + 190, cy + 42), 'GND', font=font(18, True), fill=INK)
    wire(d, [(x0 + 180, cy - 30), (x1 - 220, cy - 30)], RED, 7)
    wire(d, [(x0 + 180, cy + 30), (x1 - 220, cy + 30)], BLK, 7)
    dx = x1 - 470
    d.rectangle((dx, cy - 48, dx + 110, cy - 12), fill=(30, 30, 30))
    d.rectangle((dx + 84, cy - 48, dx + 100, cy - 12), fill=(235, 235, 235))
    d.text((dx - 10, cy - 104), '1N5817', font=font(20, True), fill=INK)
    arrow(d, [(dx + 92, cy + 130), (dx + 92, cy - 4)], width=4, head=16, fill=BLUE)
    d.text((dx - 40, cy + 136), 'band toward the board', font=font(18, True), fill=BLUE)
    heat_shrink(d, dx - 30, cy - 60, dx + 140, cy + 2)
    box3(d, (x1 - 220, cy - 70), (110, 140), 'JST PH\n2-pin', fill=(245, 245, 245))
    d.text((x1 - 102, cy - 46), 'pin 1 (+)', font=font(17, True), fill=RED)
    d.text((x1 - 102, cy + 20), 'pin 2 (GND)', font=font(17, True), fill=INK)
    y = cy + 200
    y = note(d, (x0 + 40, y), 'The diode goes in the + conductor, band (cathode) toward the PH plug, i.e. toward the EVF '
             'board. Adhesive heat-shrink over the diode and both joints.', width=x1 - x0 - 80)
    note(d, (x0 + 40, y + 10), 'Meter (diode test): USB-A VBUS (+ probe) to PH pin 1 reads a forward drop; reversed probes '
         'read open. USB-A GND to PH pin 2: continuity. No continuity between the two conductors.',
         width=x1 - x0 - 80, col=OK)


def dg_evfpig(d, b):
    x0, y0, x1, y1 = b
    box3(d, (x0 + 360, y0 + 70), (560, 330), 'Hicenda HDMI driver board Rev I', fill=(200, 225, 205))
    for k, (lab, col) in enumerate((('EXT+', RED), ('GND', BLK))):
        yy = y0 + 230 + k * 80
        d.rectangle((x0 + 420, yy - 16, x0 + 470, yy + 16), fill=(212, 175, 55), outline=INK, width=2)
        d.text((x0 + 490, yy - 14), lab + '  (traced pad)', font=font(20, True), fill=INK)
        wire(d, [(x0 + 120, yy), (x0 + 445, yy)], col, 7)
    box3(d, (x0 + 20, y0 + 200), (100, 130), 'PH\n2-pin', fill=(245, 245, 245))
    heat_shrink(d, x0 + 380, y0 + 200, x0 + 480, y0 + 340)
    y = y0 + 460
    y = note(d, (x0 + 40, y), 'First photograph both sides of the board (EVF gate G1). Then solder the PH 2-pin pigtail to '
             'the traced EXT+ and GND pads; heat-shrink as strain relief.', width=x1 - x0 - 80)
    note(d, (x0 + 40, y + 10), 'Keep the pin order of the EVF 5 V lead (step W3): + on PH pin 1, GND on pin 2, so the '
         'junction mates pin for pin.', width=x1 - x0 - 80, col=WARN)


def dg_switch(d, b):
    x0, y0, x1, y1 = b
    cx, cy = x0 + 560, y0 + 200
    d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), fill=(230, 230, 228), outline=INK, width=3)
    d.text((cx - 70, cy - 14), '18/24 switch', font=font(20, True), fill=INK)
    lugs = [('C', cx - 60, cy + 150), ('1', cx, cy + 165), ('2', cx + 60, cy + 150)]
    for lab, lx, ly in lugs:
        d.rectangle((lx - 10, ly - 30, lx + 10, ly + 10), fill=(212, 175, 55), outline=INK, width=2)
        d.text((lx - 6, ly + 14), lab, font=font(18, True), fill=INK)
    wire(d, [(x0 + 120, cy + 290), (cx - 60, cy + 290), (cx - 60, cy + 160)], RED, 6)
    wire(d, [(x0 + 120, cy + 320), (cx + 60, cy + 320), (cx + 60, cy + 160)], BLK, 6)
    box3(d, (x0 + 20, cy + 255), (100, 100), 'PH\n2-pin', fill=(245, 245, 245))
    dim(d, (x0 + 120, cy + 250), (cx - 60, cy + 250), '50 mm pigtail', off=8)
    d.text((cx + 140, cy + 120), 'C = common\n1 = position 1 (not used)\n2 = position 2', font=font(18), fill=INK)
    note(d, (x0 + 40, cy + 370), 'Solder the 50 mm JST PH pigtail to the common lug and the position-2 lug (not lug 1). '
         'Heat-shrink both joints. It is a plain contact, so either conductor may go on either lug. Position 2 closed = '
         'GPIO13 low = 24 fps; open = 18 fps.', width=x1 - x0 - 80)


def dg_a0(d, b):
    x0, y0, x1, y1 = b
    box3(d, (x0 + 300, y0 + 60), (520, 360), 'Adafruit 5880 I2C QT rotary encoder', fill=(205, 215, 240))
    jx, jy = x0 + 520, y0 + 260
    for k in range(2):
        d.rectangle((jx + k * 34, jy, jx + 24 + k * 34, jy + 30), fill=(212, 175, 55), outline=INK, width=2)
    d.ellipse((jx + 4, jy - 4, jx + 54, jy + 34), fill=(190, 190, 195), outline=INK, width=2)
    d.text((jx - 4, jy + 44), 'A0', font=font(24, True), fill=INK)
    callout(d, (jx + 160, jy - 130), '1 solder blob = bridged', (jx + 30, jy + 10))
    note(d, (x0 + 40, y0 + 470), 'Bridge the A0 jumper with one solder blob. The encoder then answers at I2C address 0x37. '
         'The default 0x36 would clash with the X1203 fuel gauge.', width=x1 - x0 - 80)


def dg_header(d, b):
    x0, y0, x1, y1 = b
    pitch = 44
    gx = x0 + 70
    gy = y0 + 150
    used = {1: RED, 3: BLU_W, 5: YEL, 6: BLK, 33: (150, 60, 160), 34: BLK, 37: (210, 110, 20), 39: BLK}
    danger = {2, 4}
    d.text((gx - 40, gy - 130), 'Pi 5 header J8 seen from above; board edge (even pins) at the top', font=font(20, True),
           fill=INK)
    d.line((gx - 20, gy - 40, gx + 19 * pitch + 20, gy - 40), fill=GREY, width=3)
    d.text((gx + 19 * pitch - 90, gy - 72), 'board edge', font=font(17), fill=GREY)
    for k in range(20):
        for row in range(2):
            pin = 2 * k + (2 if row == 0 else 1)
            x = gx + k * pitch
            y = gy + row * pitch
            if pin in used:
                d.ellipse((x - 15, y - 15, x + 15, y + 15), fill=used[pin], outline=INK, width=3)
            elif pin in danger:
                d.rectangle((x - 13, y - 13, x + 13, y + 13), fill=(255, 220, 210), outline=WARN, width=3)
            else:
                d.rectangle((x - 9, y - 9, x + 9, y + 9), fill=(215, 215, 215))
            if pin in (1, 2, 39, 40) or pin in used or pin in danger:
                s = str(pin)
                f = font(15, True)
                ty = y - 38 if row == 0 else y + 19
                d.text((x - tw(d, s, f) / 2, ty), s, font=f, fill=WARN if pin in danger else INK)
    d.rectangle((gx - 22, gy + pitch - 22, gx + 22, gy + pitch + 22), outline=INK, width=3)
    d.text((gx - 40, gy + pitch + 46), 'PIN 1: inner row, at the end farthest from the USB ports', font=font(18, True),
           fill=INK)
    yy = gy + pitch + 100
    rows = [('QT lead', 'red 1 (3V3), blue 3 (SDA), yellow 5 (SCL), black 6 (GND)', RED),
            ('18/24 lead', 'GPIO13 on 33, GND on 34', (150, 60, 160)),
            ('run lead', 'GPIO26 on 37, GND on 39', (210, 110, 20))]
    for t, s, c in rows:
        d.ellipse((gx - 40, yy + 4, gx - 18, yy + 26), fill=c)
        d.text((gx - 6, yy), t + ':', font=font(20, True), fill=INK)
        d.text((gx + 140, yy), s, font=font(20), fill=INK)
        yy += 38
    yy += 14
    warn_icon(d, gx - 40, yy)
    note(d, (gx + 10, yy), 'Count from pin 1. Pins 2 and 4 carry 5 V: one pin off and 5 V reaches the encoder 3V3 wire. '
         'Photograph the header before the body is closed.', width=x1 - gx - 60, col=WARN, f=font(20, True))


def dg_evf_mate(d, b):
    x0, y0, x1, y1 = b
    box3(d, (x0 + 380, y0 + 120), (380, 260), 'EVF board\n(outside the body)', fill=(200, 225, 205))
    box3(d, (x0 + 40, y0 + 120), (190, 130), 'HMX039\nmicro-OLED', fill=(70, 70, 80), fg=(255, 255, 255))
    wire(d, [(x0 + 230, y0 + 185), (x0 + 380, y0 + 185)], (215, 160, 60), 14)
    d.text((x0 + 240, y0 + 136), 'flex -> ZIF', font=font(18, True), fill=INK)
    wire(d, [(x0 + 760, y0 + 300), (x1 - 60, y0 + 300)], BLK, 10)
    d.text((x0 + 780, y0 + 236), 'micro-HDMI from the Pi:\nplug AFTER the slide (6c)', font=font(18, True), fill=WARN)
    wire(d, [(x0 + 570, y0 + 380), (x0 + 570, y0 + 470), (x1 - 60, y0 + 470)], RED, 6)
    d.text((x0 + 590, y0 + 420), '5 V PH junction (lead from the Pi USB)', font=font(18, True), fill=INK)
    y = y0 + 540
    y = note(d, (x0 + 40, y), '1  Flex into the ZIF, contacts as the kit shows; close the latch.\n'
             '2  Mate the EVF 5 V lead PH plug with the board pigtail (pin 1 to pin 1).\n'
             '3  micro-HDMI: NOT here. It goes in after the slide, up through the rail gap (page 6c, BX-1).',
             width=x1 - x0 - 80)
    note(d, (x0 + 40, y + 12), 'Flex and 5 V PH are mated outside the body, on the ESD mat, with the pack out. The HDMI '
         'is plugged in place after the slide (page 6c).', width=x1 - x0 - 80, col=WARN)


def dg_xt30(d, b):
    x0, y0, x1, y1 = b
    cy = y0 + 230
    box3(d, (x0 + 80, cy - 70), (200, 140), 'pack XT30\nmale', fill=(250, 220, 120))
    box3(d, (x0 + 340, cy - 70), (200, 140), 'pigtail XT30\nfemale (fused)', fill=(250, 220, 120))
    arrow(d, [(x0 + 250, cy + 110), (x0 + 310, cy + 110)], width=5, head=16)
    arrow(d, [(x0 + 600, cy + 110), (x0 + 560, cy + 110)], width=5, head=16)
    wire(d, [(x0 + 540, cy - 20), (x1 - 80, cy - 20)], RED)
    wire(d, [(x0 + 540, cy + 20), (x1 - 80, cy + 20)], BLK)
    d.text((x1 - 300, cy - 74), 'to the X1203 (inside)', font=font(18), fill=GREY)
    note(d, (x0 + 40, cy + 170), 'Red to red. Push the housings together at the grip mouth; never push or pull by the wires. '
         'This connection powers the camera: the X1203 may start the Pi at once.', width=x1 - x0 - 80, col=WARN)


DIAGRAMS = dict(fuse=dg_fuse, pads=dg_pads, diode=dg_diode, evfpig=dg_evfpig, switch=dg_switch, a0=dg_a0,
                header=dg_header, evf_mate=dg_evf_mate, xt30=dg_xt30)
