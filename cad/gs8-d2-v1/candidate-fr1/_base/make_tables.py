# SPDX-License-Identifier: MIT
"""GS8 D2: refresh the generated tables in the D2 documents from layout.py (plain Python, no CadQuery).

    python cad/gs8-d2-v1/make_tables.py            # rewrite every <!-- BEGIN:x --> ... <!-- END:x --> block
    python cad/gs8-d2-v1/make_tables.py --check    # exit 1 if a block is stale (no write)

Blocks: WIRING.md cables, plugs, header (+ harness-schedule.csv, pi5-header.csv); PRINT-GUIDE.md print, beds, engrave; ASSEMBLY.md steps, screws; DESIGN.md parts, cots, checks.
Printed volumes and masses come from the build's print manifest when one exists (MANIFEST_CANDIDATES), otherwise from
the layout estimates in `estimate_volume()` (shell area x wall x feature factor; marked "layout estimate").
make_bom.py (electronics/gs8-d2-v1) imports printed_rows() from here, so both documents use the same numbers.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as L  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
DOCS = {'wiring': os.path.join(ROOT, 'electronics', 'gs8-d2-v1', 'WIRING.md'),
        'print': os.path.join(HERE, 'PRINT-GUIDE.md'), 'assembly': os.path.join(HERE, 'ASSEMBLY.md'),
        'design': os.path.join(HERE, 'DESIGN.md')}
MANIFEST_CANDIDATES = ['exports/print-manifest.json', 'exports/print/print-manifest.json', 'out/print-manifest.json']
CHECKS_CANDIDATES = ['exports/build-receipt.json', 'out/build-receipt.json']

# --------------------------------------------------------------------------- cable data owned by the docs layer
CABLE_INFO = {
    'fpc': ('Raspberry Pi camera cable "Standard-Mini" 22-to-15 pin, 200 mm (official)',
            'up from CAM/DISP 1 beside the HDMI plug, forward over the cooler at z 30-39, S-fold of 9 layers over the '
            'fin end (bend r >= 1), down the camera rear face to its 15-pin connector'),
    'hdmi': ('micro-HDMI D-D, 200 mm (+10/-0), shielded thin coax OD 3.0; Pi end 90 deg up plug (<= 8.5 mm off the '
             'board, Q2), board end right-angle with the cable leaving -Y (EVF-SELECTION A3)',
             'up from HDMI0, back along the panel side under the dials (z 39.6-44), slack coil over the stick guide '
             '(ko_hdmi_coil, x -139..-113.5), '
             'down to the board lower edge through the slot gap y 4-17'),
    'usb_5v': ('USB-A male to 2-wire lead (24-26 AWG, 200 mm class) + 1N5817 in the + conductor + JST PH 2-pin '
               'wire-to-wire junction at the board end',
               'from the upper USB 2 port up the right-rear corner (y < -24) to z 64-70, across to the board 5 V '
               'pigtail; diode and splice under adhesive heat-shrink'),
    'oled_flex': ('Hicenda kit flex FM04112-MF1-A, 50 mm (with the panel)',
                  'from the OLED cell (open +Y) straight back to the board ZIF; mated outside the body, then the OLED '
                  'and the board go in together as a tethered pair (step 6); no fold beyond the kit form'),
    'qt': ('Adafruit 4397 STEMMA QT (JST SH 4) to female sockets, 150 mm',
           'header end plugged at step 4 on pins 1/3/5/6 (ko_qt_lead), up the right wall (ko_lead_wall, z 36.6-44), '
           'across behind the blower inlet (ko_lead_cross, x -84..-74) to the encoder lower edge; the JST-SH end '
           'plugs into the encoder at step 8'),
    'run_lead': ('pre-wired momentary button lead with female sockets (Squid Button class)',
                 'up from the grip cradle through the base opening and the floor run-lead hole, along the floor '
                 'channel under the X1203, up the port-side rise (ko_run_rise), over the cooler shroud under the camera '
                 '(ko_run_cross, x -27..-21, z 36.6-39.8), along the right wall (ko_lead_wall) down to pins 37/39 '
                 '(plugged at step 4)'),
    'fps_lead': ('2-way Dupont F to JST PH 2-pin lead, 200 mm (header side) + 50 mm JST PH pigtail soldered to the '
                 'switch lugs (2 joints); the PH pair is the step-8 inline junction',
                 'header end plugged at step 4 on pins 33/34, up the right wall (ko_lead_wall), across behind the '
                 'blower inlet (ko_lead_cross), back along the panel-side channel (ko_hdmi_run), up to the switch lugs '
                 '(ko_fps_up); PH junction mated at step 8'),
    'pigtail': ('18 AWG silicone pair, 180 mm, XT30U female; soldered to the X1203 battery pads (2 joints)',
                'from the X1203 pads round the port edge (ko_pig_wrap; pad position Q2), under the board (ko_pig_under, '
                'ko_pig_in), down the pigtail hole into the grip to the junction'),
    'pack_lead': ('18 AWG silicone pair, 60 mm, XT30U male (part of the pack)',
                  'from the pack BMS to the junction above the pack at the grip mouth'),
}

PLUG_ORDER = [   # (step, connector, action, caution): WIRING s7 and the "Harness" row of each ASSEMBLY step
    (1, 'pigtail -> X1203 battery pads', 'solder red to +, black to -; adhesive heat-shrink over both joints; strain-relief tie to a standoff', '**pack never connected** at the bench; meter + to - for no short before anything else'),
    (1, 'Active Cooler lead -> Pi FAN', 'plug the JST-SH 4', 'route it as the cooler ships'),
    (1, 'encoder A0', '1 solder blob on the A0 jumper', 'address 0x37'),
    (1, '18/24 switch pigtail', 'solder the 50 mm JST PH 2-pin pigtail to the common and position-2 lugs; heat-shrink', ''),
    (1, 'microSD', 'flash it (gate G-W3), then take it out of the Pi', 'the card must be out for steps 3-4 (it hits the front wall on the stack path)'),
    (1, 'EVF 5 V lead', 'solder the 1N5817 into the + conductor (band toward the board), the PH plug on the free end; adhesive heat-shrink', 'polarity: meter USB-A VBUS -> PH pin 1 through the diode (forward), GND -> pin 2'),
    (1, 'EVF board pigtail (Rev I)', 'solder the PH 2-pin pigtail to the traced EXT+ / GND pads; heat-shrink strain relief', 'photograph both board sides first (EVF gate G1)'),
    (3, 'run lead', 'after the base slide, fish its socket end up through the floor run-lead hole (x -34..-28, y 1.5..9) with tweezers', 'not before the slide: the base opening and the hole only overlap at the final pose'),
    (4, 'run lead', 'lay it in its floor channel before the stack goes down (`ko_run_floor`)', ''),
    (4, 'pigtail', 'feed the XT30 end down through the pigtail hole (x -45..-34, y -13..-4) into the grip', 'before the stack goes down'),
    (4, 'micro-HDMI -> Pi HDMI0', '90 deg plug, cable leaves upward', 'the EVF end stays loose'),
    (4, 'FPC -> Pi CAM/DISP 1', 'contacts as printed on the cable; latch closed', 'camera end loose'),
    (4, 'EVF 5 V lead -> Pi upper USB 2 port', 'USB-A', 'PH end loose'),
    (4, 'QT lead -> pins 1/3/5/6', 'red 1, blue 3, yellow 5, black 6; top open, header in sight', 'count from pin 1: an off-by-one plug puts 5 V (pin 2/4) on the 3V3 wire'),
    (4, '18/24 lead -> pins 33/34', 'GPIO13 on 33, GND on 34; PH end parked out of the left side', ''),
    (4, 'run lead -> pins 37/39', 'GPIO26 on 37, GND on 39', 'route over the cooler shroud (`ko_run_cross`)'),
    (5, 'microSD -> Pi slot', 'push home through the front slot (hood plate + tub wall) with tweezers, contacts up', 'after the hood is on'),
    (6, 'flex -> EVF board ZIF', 'outside the body, contacts per the kit', 'ESD: grounded mat'),
    (6, 'micro-HDMI -> EVF board', 'outside the body; right-angle plug, cable leaves -Y', '**only after gate G-W7 passed**'),
    (6, 'EVF 5 V lead PH -> board pigtail PH', 'outside the body, then the OLED + board pair slides in', '**never mate live** (pack unplugged)'),
    (7, 'FPC -> GS camera', '15-pin end, latch closed', 'fold the slack into `ko_fpc_loop`'),
    (8, 'QT lead -> encoder JST-SH', 'panel held beside the body', 'header end went on at step 4'),
    (8, '18/24 PH junction', 'mate the 2-pin PH pair', 'header end went on at step 4'),
    (9, 'USB stick -> Pi lower USB 3 port', 'from the rear scoop, sleeve fitted', ''),
    (10, 'pack XT30 -> pigtail XT30', 'at the grip mouth; push the junction and pack up', '**this powers the camera**: the X1203 may start the Pi'),
]

HEADER = [   # Pi 5 J8 pins used by D2: (pin, signal, connected to, cable id, bias / logic) -> WIRING s5, pi5-header.csv
    ('1', '3V3', 'encoder V+ (QT red)', '`qt`', '3.3 V supply'),
    ('2, 4', '5V', 'X1203 pogo pins (feed in)', 'none (pogo)', '5.1 V from the X1203'),
    ('3', 'GPIO2 / SDA1', 'encoder SDA (QT blue); X1203 gauge (pogo)', '`qt`', 'Pi 1.8 k pull-up'),
    ('5', 'GPIO3 / SCL1', 'encoder SCL (QT yellow); X1203 gauge (pogo)', '`qt`', 'Pi 1.8 k pull-up'),
    ('6', 'GND', 'encoder GND (QT black)', '`qt`', ''),
    ('33', 'GPIO13', '18/24 switch, common lug', '`fps_lead`', 'input, pull-up; low = 24 fps, high = 18 fps'),
    ('34', 'GND', '18/24 switch, position-2 lug', '`fps_lead`', ''),
    ('37', 'GPIO26', 'run button', '`run_lead`', 'input, pull-up; low = pressed (run toggles on press)'),
    ('39', 'GND', 'run button', '`run_lead`', ''),
    ('(pogo)', 'X1203 status lines', 'X1203', 'none', '**reserved**: Geekworm documents GPIO lines for power-loss detect and charge control on the X120x family (GPIO6 / GPIO16 on the X1200 wiki, recalled, not re-read). Do not use GPIO6 or GPIO16 until G-W2 confirms them'),
]


def fmt(v, nd=1):
    return ('%.*f' % (nd, v)).rstrip('0').rstrip('.') if isinstance(v, float) else str(v)


def box_txt(b):
    return ' / '.join('%s %s..%s' % (k, fmt(b[k][0]), fmt(b[k][1])) for k in 'xyz')


# --------------------------------------------------------------------------- printed parts: volumes and masses
def estimate_volume(pid):
    """Layout estimate of the solid volume (mm3): shell area x wall x feature factor. Replaced by the manifest."""
    T, pi = L.T, math.pi
    lx, w, h = L.XT1 - L.X_REAR, L.W, L.ZT1
    if pid == 'tub':
        return (lx * w + lx * h + 2 * w * h) * T * 1.15
    if pid == 'hood':
        band = (L.HOOD['band_x'][1] - L.HOOD['band_x'][0]) * (L.HOOD['y'][1] - L.HOOD['y'][0]) * (L.H - L.ZT1)
        plate = 2.5 * (L.HOOD['y'][1] - L.HOOD['y'][0]) * (L.H - L.HOOD['plate_z'][0])
        t1, t2 = L.HOOD['turret'], L.HOOD['turret_b']
        turret = sum(pi * (c['r'] ** 2 - c['r_in'] ** 2) * (c['a'][1] - c['a'][0]) for c in (t1, t2))
        hb = L.HOOD['housing']
        housing = 2 * ((hb['y'][1] - hb['y'][0]) + (hb['z'][1] - hb['z'][0])) * (hb['x'][1] - hb['x'][0]) * 1.6
        return (band + plate + turret + housing) * 1.1
    if pid == 'panel':
        b = L.PANEL['box']
        posts = sum(L.box_dims(p)[0] * L.box_dims(p)[1] * L.box_dims(p)[2] for p in L.PANEL_POSTS.values())
        return (lx * (b['z'][1] - b['z'][0]) * L.PANEL['t']) * 1.15 + posts * 0.7
    if pid == 'base_grip':
        bx, by, bz = L.box_dims(L.B(*L.BASE['x'], *L.BASE['y'], *L.BASE['z']))
        g = L.GRIP
        perim = 2 * ((g['x'][1] - g['x'][0]) + (g['y'][1] - g['y'][0])) - (8 - 2 * pi) * g['er']
        return bx * by * bz * 0.75 + perim * (g['z'][1] - g['z'][0]) * g['wall'] * 1.1
    if pid == 'eyecup':
        e = L.EYECUP
        return 2 * pi * (e['r_lip'] + e['r_base']) / 2 * 13.0 * 2.0 + 2 * pi * (e['sleeve']['r_in'] + 0.8) * 3.0 * 1.6
    if pid == 'stick_sleeve':
        dx, dy, dz = L.box_dims(L.STICK_SLEEVE['box'])
        return 2 * (dy + dz) * dx * L.STICK_SLEEVE['wall'] + dy * dz * 1.2
    if pid == 'plunger':
        return L.box_dims(L.PLUNGER['stem'])[0] * 11.0 * 6.0 + 0.8 * 13.6 * 7.8
    if pid in ('knob_exp', 'knob_fps'):
        k = L.KNOBS[pid]
        return pi * (k['d'] / 2) ** 2 * (k['y'][1] - k['y'][0]) * 0.7
    if pid == 'cap':
        dx, dy, dz = L.box_dims(L.CAP['box'])
        return dx * dy * dz * 0.7
    raise KeyError(pid)


def _find(cands):
    for c in cands:
        p = os.path.join(HERE, c)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                return c, json.load(f)
    return None, None


def manifest_entries():
    """{part_id: entry} from the build's print manifest (tolerant to list or dict layouts), or {}."""
    src, m = _find(MANIFEST_CANDIDATES)
    if not m:
        return None, {}
    parts = m.get('parts', m) if isinstance(m, dict) else m
    if isinstance(parts, dict):
        parts = [dict(v, id=k) if isinstance(v, dict) else {'id': k} for k, v in parts.items()]
    out = {}
    for e in parts:   # stub entries (envelope boxes written while a module is missing) are not used
        if isinstance(e, dict) and (e.get('id') or e.get('part')) in L.PARTS and not e.get('stub'):
            out[e.get('id') or e.get('part')] = e
    return src, out


def bed_fit(dims):
    bx, by, h = dims
    return {bed: ((bx <= X and by <= Y) or (bx <= Y and by <= X)) and h <= Z for bed, (X, Y, Z) in L.PRINT_BEDS.items()}


def printed_rows():
    """One dict per printed part: geometry, print data, volume, mass (manifest first, else layout estimate)."""
    src, man = manifest_entries()
    rows = []
    for pid, p in L.PARTS.items():
        e = man.get(pid, {})
        vol = e.get('volume_mm3', e.get('volume'))
        mass = e.get('mass_est_g', e.get('mass_g', e.get('mass')))
        dims = e.get('print_bbox_mm') or e.get('print_dims') or e.get('bbox') or e.get('dims')
        basis = 'manifest (%s)' % src if vol is not None else 'layout estimate'
        if vol is None:
            vol = estimate_volume(pid)
        if mass is None:
            mass = L.mass_g(vol, pid)
        dims = tuple(round(float(v), 1) for v in dims) if dims else tuple(round(v, 1) for v in L.print_dims(pid))
        solid_g = vol * (L.TPU_DENSITY if p['material'].startswith('TPU') else L.FDM['ASA_DENSITY'])
        rows.append(dict(id=pid, module=p['module'], material=p['material'], colour=p['colour'],
                         face_down=p['face_down'], supports=e.get('supports', p['supports']), dims=dims,
                         fits=e.get('bed_fit') or bed_fit(dims), volume_mm3=vol, solid_g=solid_g, mass_g=mass,
                         time_h=e.get('print_time_est_h', e.get('time_h_est', round(0.25 + mass / 11.0, 1))),
                         filament_g=e.get('filament_g_est', round(mass * 1.05, 1)), basis=basis,
                         infill=p['infill']))
    return rows


# --------------------------------------------------------------------------- block renderers
SETTINGS = {'shell': '4 / 5 / 25 % gyroid', 'base_grip': '4 / 5 / 25 % gyroid + 40 % modifiers (bosses, keyholes)',
            'small': '4 / 6 / 100 %', 'tpu': '3 / 4 / 100 % (TPU 95A, 20-25 mm/s)',
            'thin': '2 / 4 / 0 % (0.8 walls, declared MIN_WALL exception THIN_OK)'}   # FIXER P8/P9
AXIS_WORDS = {(0, 0, 1): '+Z (up, from below)', (0, 0, -1): '-Z (down, from above)',
              (0, 1, 0): '+Y (toward the panel, from the right side)', (0, -1, 0): '-Y (from the panel side)',
              (1, 0, 0): '+X (forward, from the rear)', (-1, 0, 0): '-X (rearward, from the front)'}


def name_of(i):
    if i in L.PARTS:
        p = L.PARTS[i]
        return 'printed, %s %s' % (p['material'].split(' (')[0], p['colour'])
    if i in L.COTS:
        return L.COTS[i]['name']
    s = next((s for s in L.SCREWS if s['id'] == i), None)
    return 'PT 3.0 x 12 PH1 into %s' % s['into'] if s else i


def legs(path):
    out = ['start at offset (%s)' % ', '.join(fmt(float(v)) for v in path[0])]
    for a, b in zip(path, path[1:]):
        d = [b[k] - a[k] for k in range(3)]
        out.append(' + '.join('%s%s %s' % ('+' if v > 0 else '-', 'XYZ'[k], fmt(abs(float(v))))
                              for k, v in enumerate(d) if abs(v) > 1e-9) or 'hold')
    return ', then '.join(out)


def blk_header():
    rows = ['| Pin | Signal | Connected to | Cable | Bias / logic |', '|---|---|---|---|---|']
    rows += ['| %s | %s | %s | %s | %s |' % h for h in HEADER]
    return '\n'.join(rows)


def blk_engrave():
    rows = ['| id | Kind | Text / shape | Where on the panel face (x, z) | Size | Stroke |', '|---|---|---|---|---|---|']
    for e in L.ENGRAVE['items']:
        if e['kind'] == 'text':
            where, size, what = '(%s, %s)' % tuple(fmt(float(v)) for v in e['at']), 'h %s' % fmt(e['h']), '"%s"' % e['text']
        else:
            r = e['r'] if not isinstance(e['r'], tuple) else '%s..%s' % e['r']
            where = 'centre (%s, %s), r %s' % (fmt(float(e['c'][0])), fmt(float(e['c'][1])), r)
            deg = e['deg'] if isinstance(e['deg'], list) else list(e['deg'])
            size = 'at %s deg' % ', '.join(fmt(float(d)) for d in deg) + (' (size %s x %s)' % e['size'] if 'size' in e else '')
            what = e['kind']
        rows.append('| `%s` | %s | %s | %s | %s | %s |' % (e['id'], e['kind'], what, where, size, e.get('stroke', '')))
    return '\n'.join(rows)


def write_csvs():
    """Side files in electronics/gs8-d2-v1: harness-schedule.csv (cables) and pi5-header.csv (pins)."""
    import csv
    edir = os.path.dirname(DOCS['wiring'])
    with open(os.path.join(edir, 'harness-schedule.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['id', 'name', 'class', 'from', 'to', 'length_mm', 'steps', 'keepouts', 'routing_note'])
        for c in L.CABLES:
            pn, note = CABLE_INFO.get(c['id'], (c['name'], ''))
            w.writerow([c['id'], c['name'], pn, c['frm'], c['to'], c['length'], ' '.join(str(s) for s in c['steps']),
                        ' '.join(c['via']), note])
    with open(os.path.join(edir, 'pi5-header.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['pin', 'signal', 'connected_to', 'cable', 'bias_logic'])
        for h in HEADER:
            w.writerow([x.replace('`', '') for x in h])


SVG_BOXES = {   # block diagram: id -> (x, y, w, h, label lines)
    'pack': (20, 400, 150, 60, ['1S2P 18650 pack', 'BMS >= 10 A (grip)']),
    'xt30': (20, 300, 150, 40, ['XT30U junction', '(grip mouth)']),
    'x1203': (300, 300, 200, 60, ['Geekworm X1203', '1S -> 5.1 V 5 A, gauge 0x36']),
    'pi5': (300, 60, 200, 200, ['Raspberry Pi 5', 'EEPROM PSU_MAX_CURRENT=5000', 'POWER_OFF_ON_HALT=1']),
    'plunger': (20, 120, 150, 50, ['printed plunger', '-> Pi power button']),
    'cooler': (20, 40, 150, 40, ['Active Cooler']),
    'camera': (660, 20, 180, 44, ['GS camera (IMX296)']),
    'evf': (660, 90, 180, 44, ['EVF board (Rev I)']),
    'oled': (880, 90, 120, 44, ['HMX039 OLED']),
    'stick': (660, 160, 180, 44, ['SDCZ880 USB stick']),
    'encoder': (660, 230, 180, 44, ['5880 encoder 0x37']),
    'fps': (660, 300, 180, 44, ['18/24 rotary']),
    'run': (660, 370, 180, 44, ['run button (grip)']),
}
SVG_LINKS = [   # (from box, to box, label)
    ('pack', 'xt30', 'pack_lead 18 AWG 60'), ('xt30', 'x1203', 'pigtail 18 AWG 180'),
    ('x1203', 'pi5', 'pogo: 5V, GND, I2C'), ('plunger', 'pi5', 'button (mech.)'), ('cooler', 'pi5', 'FAN JST-SH'),
    ('pi5', 'camera', 'fpc 200: CAM/DISP 1'), ('pi5', 'evf', 'hdmi 200 + usb_5v (1N5817)'),
    ('evf', 'oled', 'flex 50'), ('pi5', 'stick', 'USB 3 lower'), ('pi5', 'encoder', 'qt 150: pins 1/3/5/6'),
    ('pi5', 'fps', 'fps_lead: 33/34, GPIO13'), ('pi5', 'run', 'run_lead: 37/39, GPIO26'),
]


def write_svg():
    """electronics/gs8-d2-v1/wiring-d2.svg: block diagram of the D2 harness (generated, theme-neutral)."""
    def esc(t):
        return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1020 480" font-family="DejaVu Sans, Arial, sans-serif" '
         'font-size="11">', '<rect width="1020" height="480" fill="#ffffff"/>',
         '<text x="20" y="18" font-size="13" font-weight="bold">GS8 D2 harness (generated by make_tables.py from '
         'layout.py; proxies, not verified)</text>']
    for a, b, lab in SVG_LINKS:
        xa, ya, wa, ha, _ = SVG_BOXES[a]
        xb, yb, wb, hb, _ = SVG_BOXES[b]
        if xb > xa + wa:
            x1, y1, x2, y2 = xa + wa, ya + ha / 2, xb, yb + hb / 2
        elif xa > xb + wb:
            x1, y1, x2, y2 = xa, ya + ha / 2, xb + wb, yb + hb / 2
        else:
            x1, y1 = xa + wa / 2, ya + (0 if yb < ya else ha)
            x2, y2 = xb + wb / 2, yb + (hb if yb < ya else 0)
        o.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#444" stroke-width="1.4"/>' % (x1, y1, x2, y2))
        o.append('<text x="%.0f" y="%.0f" fill="#1a4f8a" font-size="10" text-anchor="middle">%s</text>' % (
            (x1 + x2) / 2, (y1 + y2) / 2 - 4, esc(lab)))
    for k, (x, y, w, h, lines) in SVG_BOXES.items():
        o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="#f4f4f2" stroke="#222"/>' % (x, y, w, h))
        for i, t in enumerate(lines):
            o.append('<text x="%d" y="%d" text-anchor="middle"%s>%s</text>' % (
                x + w / 2, y + 16 + 14 * i, ' font-weight="bold"' if i == 0 else '', esc(t)))
    o.append('</svg>')
    with open(os.path.join(os.path.dirname(DOCS['wiring']), 'wiring-d2.svg'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(o) + '\n')


def blk_plugs():
    rows = ['| Step | Connector | Action | Caution |', '|---|---|---|---|']
    for st, con, act, cau in PLUG_ORDER:
        bench = ' (bench)' if not next(x for x in L.STEPS if x['step'] == st).get('in_body', True) else ''
        rows.append('| %d%s | %s | %s | %s |' % (st, bench, con, act, cau))
    return '\n'.join(rows)


def blk_cables():
    rows = ['| id | Cable (class) | From | To | Length (mm) | Plugged at step | Route (keep-out chain) | Routing note |',
            '|---|---|---|---|---|---|---|---|']
    for c in L.CABLES:
        pn, note = CABLE_INFO.get(c['id'], (c['name'], ''))
        chain = '; '.join('`%s` %s' % (k, box_txt(L.KEEPOUTS[k])) for k in c['via'] if k in L.KEEPOUTS) or 'direct'
        rows.append('| `%s` | %s | %s | %s | %s | %s | %s | %s |' % (
            c['id'], pn, c['frm'], c['to'], c['length'], ', '.join(str(s) for s in c['steps']), chain, note))
    return '\n'.join(rows)


def blk_print():
    rows = ['| # | Part | Material, colour | Face down | Build X x Y x Z (mm) | Perim. / top-bottom / infill | Supports | '
            'Volume (cm3) | Mass at 100 % (g) | Mass as printed (g) | Filament [est] (g) | Time [est] (h) | Basis |',
            '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    tot = [0.0, 0.0, 0.0, 0.0]
    for n, r in enumerate(printed_rows(), 1):
        rows.append('| %d | `%s` | %s, %s | %s | %s | %s | %s | %.1f | %.1f | %.1f | %.1f | %.1f | %s |' % (
            n, r['id'], r['material'], r['colour'], r['face_down'], ' x '.join(fmt(v) for v in r['dims']),
            SETTINGS[r['infill']], r['supports'], r['volume_mm3'] / 1000, r['solid_g'], r['mass_g'], r['filament_g'],
            r['time_h'], r['basis']))
        for k, key in enumerate(('solid_g', 'mass_g', 'filament_g', 'time_h')):
            tot[k] += r[key]
    rows.append('| | **total** | | | | | | | **%.0f** | **%.0f** | **%.0f** | **%.1f** | |' % tuple(tot))
    return '\n'.join(rows)


def blk_beds():
    beds = list(L.PRINT_BEDS)
    rows = ['| Part | Build X x Y x Z (mm) | ' + ' | '.join(beds) + ' |', '|---|---|' + '---|' * len(beds)]
    for r in printed_rows():
        cells = ' | '.join('fits (%s)' % ('STL' if r['basis'].startswith('manifest') else 'envelope')
                           if r['fits'].get(b) else '**no**' for b in beds)
        rows.append('| `%s` | %s | %s |' % (r['id'], ' x '.join(fmt(v) for v in r['dims']), cells))
    return '\n'.join(rows)


def blk_screws():
    rows = ['| Screw | Joins | Into | Head point (x, y, z) | Travels | Engagement (mm) | Counterbore | Step | Driver | '
            'Torque (N m) |', '|---|---|---|---|---|---|---|---|---|---|']
    for s in L.SCREWS:
        cb = s['cbore']
        rng = ', '.join('%s %s..%s' % (k, fmt(cb[k][0]), fmt(cb[k][1])) for k in 'xyz' if k in cb)
        cbt = 'dia %s in `%s`, %s' % (fmt(cb['d']), cb['part'], rng)
        tq = tuple(fmt(v, 2) for v in L.PT['torque_Nm'])   # FIXER A-F7: 0.35 printed as 0.3
        rows.append('| `%s` | %s | %s | (%s) | %s | %s | %s | %d | %s, bit dia <= %s x %s+ | %s-%s, stop at head '
                    'contact |' % (s['id'], ' + '.join(s['joins']), s['into'],
                                   ', '.join(fmt(float(v)) for v in s['head_point']),
                                   AXIS_WORDS.get(tuple(s['axis']), str(s['axis'])), fmt(s['engage']), cbt,
                                   s['step'], L.PT['drive'], fmt(L.DRIVER['bit_d']), fmt(L.DRIVER['bit_len']), *tq))
    return '\n'.join(rows)


def blk_steps():
    out = []
    for st in L.STEPS:
        n = st['step']
        out.append('### Step %d. %s%s\n' % (n, st['name'], '' if st.get('in_body', True) else ' (bench)'))
        out.append(st['action'] + '\n')
        out.append('| Item | Detail |\n|---|---|')
        if st.get('bench'):
            out.append('| Bench sub-assembly | %s |' % '; '.join('`%s` (%s)' % (i, name_of(i)) for i in st['bench']))
        parts = [i for i in st['adds'] if not i.startswith('s_')]
        txt = '; '.join('`%s` (%s)' % (i, name_of(i)) for i in parts) or 'none (bench step)'
        out.append('| Parts added to the body | %s |' % txt)
        screws = [s for s in L.SCREWS if s['id'] in st['adds']]
        if screws:
            out.append('| Fasteners | %d x %s |' % (len(screws), L.PT['spec']))
            out.append('| Driving | %s |' % '; '.join('`%s` travels %s, %s mm engagement into %s' % (
                s['id'], AXIS_WORDS.get(tuple(s['axis'])), fmt(s['engage']), s['into']) for s in screws))
            out.append('| Torque | %s-%s N m by hand, stop at head contact (FASTENER-POLICY C; provisional until '
                       'G-PT-1); no threadlocker |' % tuple(fmt(v, 2) for v in L.PT['torque_Nm']))
        else:
            out.append('| Fasteners | none |')
        out.append('| Tool | %s |' % st['tool'])
        ins = [i for i in L.INSERTIONS if i['step'] == n]
        if ins:
            out.append('| Motion | %s |' % '; '.join('`%s` (%s): %s%s' % (
                i['id'], ', '.join(i['moving']), legs(i['path']),
                ' (snaps: %s)' % ', '.join(i['snaps']) if i.get('snaps') else '') for i in ins))
        hp = [p for p in PLUG_ORDER if p[0] == n]
        if hp:
            out.append('| Harness (WIRING s7) | %s |' % '; '.join('%s: %s%s' % (
                con, act, (' (**%s**)' % cau.replace('**', '')) if cau else '') for _, con, act, cau in hp))
        cab = [c for c in L.CABLES if n in c['steps']]
        if cab:
            out.append('| Cables | %s |' % '; '.join('`%s` %s -> %s' % (c['id'], c['frm'], c['to']) for c in cab))
        if st.get('in_body', True):
            out.append('| In the body after this step | %d ids (`layout.present_at(%d)`) |' % (len(L.present_at(n)), n))
        out.append('')
    return '\n'.join(out).rstrip()


def blk_parts():
    rows = ['| id | Module | Owner | Material, colour | Face down | Envelope (assembly frame) | Mass as printed (g) | '
            'Basis |', '|---|---|---|---|---|---|---|---|']
    for r in printed_rows():
        p = L.PARTS[r['id']]
        rows.append('| `%s` | `%s` | %s | %s, %s | %s | %s | %.1f | %s |' % (
            r['id'], p['module'], p['owner'], p['material'], p['colour'], p['face_down'], box_txt(p['envelope']),
            r['mass_g'], r['basis']))
    return '\n'.join(rows)


def blk_cots():
    rows = ['| id | Part | P/N or class | Source | Mass (g) | Step |', '|---|---|---|---|---|---|']
    for k, c in L.COTS.items():
        m = c['mass'] if c['mass'] is not None else L.LENSES[L.LENS]['mass']
        pn = c['pn'] if len(str(c['pn'])) < 60 else 'see FASTENER-POLICY'
        rows.append('| `%s` | %s | %s | %s | %s | %s |' % (k, c['name'], pn, c['src'], fmt(float(m)), c['step']))
    return '\n'.join(rows)


def blk_checks():
    src, d = _find(CHECKS_CANDIDATES)
    if not d:
        return '_No build results yet: build_d2.py has not written %s._' % ' or '.join(CHECKS_CANDIDATES[:2])
    if isinstance(d.get('summary'), list):     # build_d2.py receipt
        crc = d.get('cad_release_candidate', d.get('release_candidate'))
        rows = ['Source: `%s`, built %s (%s). CAD release candidate (computed checks only, not a hardware or '
                'finished-camera claim): **%s**. Stub parts: %s.' % (
            src, d.get('built_at'), ' '.join(d.get('argv', [])) or 'full', crc,
            ', '.join(d.get('stubs', [])) or 'none'), '']
        st = d.get('status_states') or {}
        if st:
            rows += ['| Evidence state | Status |', '|---|---|']
            for k, v in st.items():
                v = v if isinstance(v, dict) else {'status': v}
                extra = (' (%s of %s checks, %s rows)' % (v.get('checks_passed'), (v.get('checks_passed') or 0) +
                         (v.get('checks_not_passed') or 0), v.get('rows_passed'))) if 'checks_passed' in v else ''
                rows.append('| `%s` | %s%s |' % (k, v.get('status'), extra))
            rows.append('')
        oe = d.get('open_evidence')
        if oe:
            rows += ['Open evidence: %s.' % (', '.join(oe) if isinstance(oe, list) else oe), '']
        rows += ['| Check | n | passed | failed | stub | info | status |', '|---|---|---|---|---|---|---|']
        for c in d['summary']:
            rows.append('| %s | %s | %s | %s | %s | %s | %s |' % tuple(c.get(k, '') for k in (
                'check', 'n', 'passed', 'failed', 'stub', 'info', 'status')))
        mc = (d.get('totals') or {}).get('mass_com') or {}
        if mc:
            rows += ['', '| Lens | Total mass (g) | CoM (x, y, z) | CoM ahead of the grip axis (mm) | CoM above the grip '
                     'top (mm) |', '|---|---|---|---|---|']
            for lens, m in mc.items():
                rows.append('| %s | %.0f | (%s) | %+.1f | %.1f |' % (lens, m['total_g'], ', '.join(
                    '%.1f' % v for v in m['com']), m['ahead_of_grip_axis'], m['above_grip_top']))
        rows += ['', '_Only computed checks may say "pass"; purchased parts are proxies and nothing is hardware-verified._']
        return '\n'.join(rows)
    rows = ['Source: `%s`.' % src, '', '| Key | Value |', '|---|---|']
    for k, v in d.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            rows.append('| %s | %s |' % (k, v))
        elif isinstance(v, dict) and all(isinstance(x, (str, int, float, bool)) for x in v.values()):
            rows.append('| %s | %s |' % (k, ', '.join('%s %s' % kv for kv in v.items())[:400]))
        else:
            rows.append('| %s | (%s, %d entries) |' % (k, type(v).__name__, len(v)))
    return '\n'.join(rows)


BLOCKS = {'wiring': {'cables': blk_cables, 'plugs': blk_plugs, 'header': blk_header}, 'print': {'print': blk_print, 'beds': blk_beds, 'engrave': blk_engrave},
          'assembly': {'steps': blk_steps, 'screws': blk_screws},
          'design': {'parts': blk_parts, 'cots': blk_cots, 'checks': blk_checks}}


def refresh(check=False):
    stale = []
    for doc, blocks in BLOCKS.items():
        path = DOCS[doc]
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            text = f.read()
        new = text
        for name, fn in blocks.items():
            pat = re.compile(r'(<!-- BEGIN:%s -->\n).*?(\n<!-- END:%s -->)' % (name, name), re.S)
            if pat.search(new):
                body = fn()
                new = pat.sub(lambda m: m.group(1) + body + m.group(2), new)
        if new != text:
            stale.append(os.path.relpath(path, ROOT))
            if not check:
                with open(path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(new)
    return stale


if __name__ == '__main__':
    chk = '--check' in sys.argv
    s = refresh(check=chk)
    if not chk:
        write_csvs()
        write_svg()
    print(('stale: ' if chk else 'refreshed: ') + (', '.join(s) if s else 'none'))
    sys.exit(1 if chk and s else 0)
