# SPDX-License-Identifier: MIT
"""GS8 D2: refresh the generated tables in the D2 documents from layout.py (plain Python, no CadQuery).

    python cad/gs8-d2-v1/make_tables.py            # rewrite every <!-- BEGIN:x --> ... <!-- END:x --> block
    python cad/gs8-d2-v1/make_tables.py --check    # exit 1 if a block is stale or a handwritten count disagrees
    python cad/gs8-d2-v1/make_tables.py --docs design,print,assembly   # refresh only these docs (no WIRING, CSV, SVG)
    python cad/gs8-d2-v1/make_tables.py --lint     # only the handwritten-count lint (+ its selftest)

Blocks: WIRING.md cables, plugs, header (+ harness-schedule.csv, pi5-header.csv); PRINT-GUIDE.md print, beds, engrave; ASSEMBLY.md steps, screws; DESIGN.md parts, cots, checks, counts (r3: the authoritative shared counts).
Count lint (r3, audit 2026-10-05 correction 1D): "<n> PT screws", "<n> screws", "<n> measured-part records",
"<n> coupon STLs", "<n> STLs", "<n> prints" (digits or words) in cad/gs8-d2-v1/*.md and electronics/gs8-d2-v1/*.md
(NOTES and the briefs excluded as history) must match counts() or a subgroup it derives (per step / per head part).
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
             'down to the board lower edge through the slot gap y 4-17; r7 (BX-1): the board end is plugged in the '
             'body after the pair is home, upward (+Z) through the bottom-rail gap from the open left side'),
    'usb_5v': ('USB-A male to 2-wire lead (24-26 AWG, 200 mm class) + 1N5817 in the + conductor + JST PH 2-pin '
               'wire-to-wire junction at the board end',
               'from the upper USB 2 port up the right-rear corner (y < -24) to z 64-70, across to the board 5 V '
               'pigtail; diode and splice under adhesive heat-shrink; r7 (BX-9): PH junction mated outside (pair '
               'held about 60 mm out), rides in above the bottom rail beside the board, pushed into ko_5v_end once '
               'the board is home'),
    'oled_flex': ('Hicenda kit flex FM04112-MF1-A, 50 mm (with the panel)',
                  'from the OLED cell (open +Y) straight back to the board ZIF; mated outside the body (foam pad stuck '
                  'to the OLED back first, r7 BX-7), then the OLED and the board go in together as a tethered pair '
                  '(step 6); no fold beyond the kit form'),
    'qt': ('QT lead 250 mm (240-270): Adafruit 4397 STEMMA QT female sockets (D2-24) spliced to Pololu 5521 JST-SH '
           '4-pin (D2-24B), splice W-QT; or a one-piece 240-270 mm lead of the same ends (MP-QT buy-check)',
           'header end plugged at step 4 on pins 1/3/5/6 (ko_qt_lead; single 1-pin housings, seated with tweezer '
           'tips), up the right wall (ko_lead_wall, z 36.6-44), across behind the blower inlet (ko_lead_cross, x '
           '-84..-74; splice in its straight run, y -29..17, joints 91-115 mm from the socket tip), up the tail '
           '(ko_qt_tail) to the plug at the encoder -X socket (ko_qt_plug); r7 (BX-2): the JST-SH end is plugged at '
           'step 8 with the panel held 60 mm off (mating pose qt_enc); the spare folds into ko_lead_stow at +30 mm'),
    'run_lead': ('pre-wired momentary button lead with female sockets (Squid Button class)',
                 'up from the grip cradle through the base opening and the floor run-lead hole, along the floor '
                 'channel under the X1203, up the port-side rise (ko_run_rise), over the cooler shroud under the camera '
                 '(ko_run_cross, x -27..-21, z 36.6-39.8), along the right wall (ko_lead_wall) down to pins 37/39 '
                 '(plugged at step 4)'),
    'fps_lead': ('2-way Dupont F to JST PH 2-pin lead, 200 mm (header side) + 50 mm JST PH pigtail soldered to the '
                 'switch lugs (2 joints); the PH pair is the step-8 inline junction',
                 'header end plugged at step 4 on pins 33/34, up the right wall (ko_lead_wall), across behind the '
                 'blower inlet (ko_lead_cross), back along the panel-side channel (ko_hdmi_run), up to the switch lugs '
                 '(ko_fps_up); PH junction mated first at step 8, both hands, with the panel propped 60 mm off '
                 '(mating pose fps_ph); r7 (BX-2): the spare and the PH junction fold into ko_lead_stow at +30 mm'),
    # r7 C3 (BX-3, BX-11): cut-to-length pigtail, U at W, RTV at the pads, taped leg (layout PIGTAIL, lead_access)
    'pigtail': ('18 AWG silicone pair, cut to L_cut = 200 mm + d_board (set at G-W2; 200-225 mm: d_board over 25 mm '
                'stops step 1, G-W5 drop, `lead_access` pigtail_drop), XT30U female; '
                'soldered to the X1203 battery pads (2 joints), RTV strain relief at the pads (neutral cure, not '
                'acetoxy; no standoff tie); r4: inline 15 A fuse (Littelfuse 0251015.MXL) in the + conductor within '
                'about 25 mm of the XT30 female (2 joints, inside L_cut)',
                'from the X1203 pads on the top face, straight in from inside the board (y < 23), to the W mark on the '
                'port edge (x -37.5, 31.5 mm from the button-end edge; pad position Q2); round the edge in a U over '
                'Kapton (ko_pig_wrap), the leg taped flat under the board (ko_pig_under, ko_pig_in), down the pigtail '
                'hole into the grip to the junction; 136-141 mm stored folded above the pack with the pack lead '
                '(ko_xt30); the sleeved fuse (about 20 x dia 5) lies along X beside the XT30 pair, both flat on the pack top under the run button (r7 fix-up); '
                'L_cut = 200 + d_board, rounded up to 5 mm'),
    'pack_lead': ('18 AWG silicone pair, 60 mm, XT30U male (part of the pack)',
                  'from the pack BMS to the junction above the pack at the grip mouth'),
}

PLUG_ORDER = [   # (step, connector, action, caution): WIRING s7 and the "Harness" row of each ASSEMBLY step
    (1, 'pigtail fuse (r4)', 'splice the 15 A fuse (Littelfuse 0251015.MXL) into the red conductor about 20-25 mm from the XT30 female: trim each fuse lead to 6.5 mm (a 1.5 mm stub at the body + a 5 mm lap joint on the stripped conductor), adhesive 3:1 heat-shrink over the whole splice (about 28 mm)', 'hand-solder at 350 C for 5 s max per lead (datasheet); never re-solder the XT30 female with the fuse fitted; meter the red path end to end (< 0.1 ohm)'),
    (1, 'pigtail -> X1203 battery pads', 'cut to L_cut (`PIGTAIL`); solder red to +, black to -; adhesive heat-shrink over both joints; on the bare X1203 lead the pair to the W mark, Kapton over the edge, form the U and tape the leg flat under the X1203 to the hole point; then RTV strain relief at the pads (neutral cure) over the joints and 8-10 mm of the pair (before the Pi covers top-face pads); stack when tack-free, full cure before step 4', '**pack never connected** at the bench; meter + to - for no short before anything else; r7 (BX-3): no tie to a standoff'),
    (1, 'Active Cooler lead -> Pi FAN', 'plug the JST-SH 4', 'route it as the cooler ships'),
    (1, 'encoder A0', '1 solder blob on the A0 jumper', 'address 0x37'),
    (1, 'QT lead splice (W-QT, r7)', 'join Adafruit 4397 to Pololu 5521 by SH pin number: joints 91-115 mm from the '
     'socket tip, 8 mm apart, one thin sleeve each, one adhesive 3:1 sleeve about 35 mm over all; finished 250 +/- 10 '
     'mm', 'map continuity first; never join by colour alone; meter end to end, no short'),
    (1, '18/24 switch pigtail', 'solder the 50 mm JST PH 2-pin pigtail to the common and position-2 lugs; heat-shrink', ''),
    (1, 'microSD', 'flash it (gate G-W3), then take it out of the Pi', 'the card must be out for steps 3-4 (it hits the front wall on the stack path)'),
    (1, 'EVF 5 V lead', 'solder the 1N5817 into the + conductor (band toward the board), the PH plug on the free end; adhesive heat-shrink', 'polarity: meter USB-A VBUS -> PH pin 1 through the diode (forward), GND -> pin 2'),
    (1, 'EVF board pigtail (Rev I)', 'solder the PH 2-pin pigtail to the traced EXT+ / GND pads; heat-shrink strain relief', 'photograph both board sides first (EVF gate G1)'),
    (3, 'run lead', 'before the tub is lowered, push its sockets up through the base passage and the rear (-X) end of the floor run-lead hole (x -41.5..-28, y 1.5..9); lower the tub, slide the base; tape the lead flat in its floor lane (`ko_run_floor`)', 'r7 (BX-16): threaded before the tub goes down (`lead_access` run_lead_window)'),
    (4, 'run lead', 'check it is still taped flat in its floor lane (`ko_run_floor`), socket end out over the open +Y side', 'before the stack goes down'),
    (4, 'pigtail', 'feed the XT30 end down through the pigtail hole (x -45..-34, y -13..-4) into the grip, long side front to back; the taped leg comes down with the stack', 'before the stack goes down; port edge > 10 mm from the W mark'),
    (4, 'micro-HDMI -> Pi HDMI0', '90 deg plug, cable leaves upward', 'the EVF end stays loose'),
    (4, 'FPC -> Pi CAM/DISP 1', 'contacts as printed on the cable; latch closed', 'camera end loose'),
    (4, 'EVF 5 V lead -> Pi upper USB 2 port', 'USB-A', 'PH end loose'),
    (4, 'QT lead -> pins 1/3/5/6', 'red 1, blue 3, yellow 5, black 6; top open, header in sight; one 1-pin housing at a time, seated straight down with open tweezer tips straddling the wire, each wire tugged; splice sleeve in the straight cross run', 'count from pin 1: an off-by-one plug puts 5 V (pin 2/4) on the 3V3 wire; never a 1x3 or 2x3 shell'),
    (4, '18/24 lead -> pins 33/34', 'GPIO13 on 33, GND on 34 (1x2 or two 1-pin housings; seat with tweezer tips, tug-test); PH end parked out of the left side', ''),
    (4, 'run lead -> pins 37/39', 'GPIO26 on 37, GND on 39 (1-pin housings, or one 1x2; seat with tweezer tips, tug-test)', 'route over the cooler shroud (`ko_run_cross`)'),
    (5, 'microSD -> Pi slot', 'push home through the front slot (hood plate + tub wall) with tweezers, contacts up', 'after the hood is on'),
    # r7 C1 (BX-1, BX-7, BX-9; SPEC-C1 3.3 + P1-4): pad on the OLED first, PH junction outside, HDMI in situ last
    (6, 'flex -> EVF board ZIF', 'on the bench, contacts per the kit; foam pad stuck to the OLED back first',
     'ESD: grounded mat'),
    (6, 'EVF 5 V lead PH -> board pigtail PH', 'outside the body, with the pair held about 60 mm out of the open left '
     'side, before the slide; the junction rides in above the bottom rail and is pushed into ko_5v_end with the '
     'tweezers once the board is home', '**never mate live** (pack unplugged)'),
    (6, 'micro-HDMI -> EVF board', 'in the body, AFTER the pair is home: plug fed in low under the rail end, lifted to '
     'the receptacle, pushed up (+Z) through the bottom-rail gap with a fingertip (guide top, or up from the open well); right-angle '
     'plug, cable leaves -Y', '**only after gate G-W7 passed**'),
    (7, 'FPC -> GS camera', '15-pin end, latch closed', 'fold the slack into `ko_fpc_loop`'),
    # r7 C2 (BX-2; SPEC-C2 s5): mated with the panel 60 mm off, spares folded into ko_lead_stow before the last 30 mm
    # r7 fix-up (VERIFY-C2): helper holds the body, panel propped on a ~110 mm block; PH first with both hands, then QT
    (8, '18/24 PH junction', 'first: a helper holds the body upright, the panel stands 60 mm off on a block about '
     '110 mm tall; mate the 2-pin PH pair with both hands, one on each housing (mating pose `fps_ph`)',
     'header end went on at step 4'),
    (8, 'QT lead -> encoder JST-SH', 'then: hold the plug by its rear end and push it into the rear-side (-X) socket, '
     'finishing with a fingernail on its back face, thumb behind the encoder +X edge (mating pose `qt_enc`); home '
     'when it stops (friction lock, no click)', 'header end went on at step 4'),
    (8, 'QT spare, 18/24 spare, PH junction -> `ko_lead_stow`', 'at about 30 mm off: flat fold between encoder and '
     'switch on the HDMI run; body upright until the panel is home', 'nothing over the blower inlet'),
    (9, 'USB stick -> Pi lower USB 3 port', 'from the rear scoop, sleeve fitted', ''),
    (10, 'pack XT30 -> pigtail XT30', 'camera on its right side, pack held in the palm; at the grip mouth, the whole pigtail XT30 housing + 15 mm of wire out (estimate about 28 mm), never mated inside the bay; push the junction and the folded pigtail in ahead of the pack, then the pack; the pair ends flat on the pack top, female end to the rear (G-MP-PACK)', '**this powers the camera**: the X1203 may start the Pi'),
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
        turret = 0.0   # r5 step 1 (J7-R): HOOD turret deleted (the lens collar is its own part); minimum fix
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
    if pid == 'lens_collar':    # r5 (J7-R): ring body r 30 round the default lens's bore + 4 feet + pinch lugs (~15 cm3)
        C, cs = L.COLLAR, L.collar_spec(L.LENS)
        body = pi * (C['body_r'] ** 2 - cs['bore_r'] ** 2) * (cs['front_x'] - C['flange_x'][0])
        feet = len(C['feet']) * pi * (C['foot_d'] / 2) ** 2 * (C['foot_x'][1] - C['foot_x'][0])
        lg = C['lug']
        lugs = (cs['front_x'] - lg['x'][0]) * (lg['bit_relief_y'] - lg['y_out']) * (lg['upper_z'][1] - lg['lower_z'][0])
        return (body + feet + lugs) * 1.15
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
SETTINGS = {'shell': '4 / 5 / 25 % gyroid', 'base_grip': '4 / 5 / 25 % gyroid',
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
    if s and s.get('kind', 'PT') != 'PT':      # r5: M3 (lens collar) rows carry their own spec
        return '%s%s into %s' % (s['spec'].split(' ISO')[0] + ' ' + L.M3['drive'], ' + washer' if s.get('washer') else '',
                                 s['into'])
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
    ('pack', 'xt30', 'pack_lead 18 AWG 60'), ('xt30', 'x1203', 'pigtail 18 AWG L_cut'),
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


def settings_of(r):
    """r4: the class setting plus the part's modifier meshes (layout.print_modifiers, exported by build_d2.py)."""
    mods = L.print_modifiers(r['id']) if r['id'] in L.PARTS else []
    if not mods:
        return SETTINGS[r['infill']]
    return '%s + %d %% modifier meshes x %d (`stl/modifiers/%s__mod_*.stl`: %s)' % (
        SETTINGS[r['infill']], L.MOD_INFILL, len(mods), r['id'], ', '.join(m['id'] for m in mods))


def blk_print():
    rows = ['| # | Part | Material, colour | Face down | Build X x Y x Z (mm) | Perim. / top-bottom / infill | Supports | '
            'Volume (cm3) | Mass at 100 % (g) | Mass as printed (g) | Filament [est] (g) | Time [est] (h) | Basis |',
            '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    tot = [0.0, 0.0, 0.0, 0.0]
    for n, r in enumerate(printed_rows(), 1):
        rows.append('| %d | `%s` | %s, %s | %s | %s | %s | %s | %.1f | %.1f | %.1f | %.1f | %.1f | %s |' % (
            n, r['id'], r['material'], r['colour'], r['face_down'], ' x '.join(fmt(v) for v in r['dims']),
            settings_of(r), r['supports'], r['volume_mm3'] / 1000, r['solid_g'], r['mass_g'], r['filament_g'],
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


CHECKSJSON_CANDIDATES = ['exports/checks.json', 'out/checks.json']


def blk_order():
    """r6 (audit 2026-10-06 M2): PRINT-GUIDE s7 from layout.PRINT_PREREQS / COUPON_PREREQS / PRINT_SEQUENCE and the
    build receipt's print_release (which parts the recorded evidence releases now)."""
    _, rec = _find(CHECKS_CANDIDATES)
    rel = (rec or {}).get('print_release') or {}
    prel, crel = rel.get('parts') or {}, rel.get('coupon_gates') or {}

    def state(v):
        if not v:
            return 'not built'
        return 'released' if v.get('status') == 'released' else 'blocked (%d of %d open)' % (
            len(v.get('missing') or []), len(v.get('print_after') or []))
    rows = ['| Order | What | Print only after a current recorded pass of | Now |', '|---|---|---|---|',
            '| 1 | Calibration and fit coupons (s6, all except the 3 G-COL-1 coupons) | nothing: print them first, in '
            'parallel with the bench measurements | released |',
            '| 2 | Bench measurements, no printing (ASSEMBLY B0, MEASURED-PARTS): MP-CAM with the lens (G-CAM-1, '
            'G-LENS), MP-PACK, MP-RUN, MP-X1203, MP-HDMI, MP-EVF, MP-ENC, MP-SW, MP-STICK, MP-FPC | update `layout.py` '
            'with any measured difference, rebuild and rerun the release sequence before order 3 | - |']
    for g, gates in L.COUPON_PREREQS.items():
        rows.append('| 3 | %s coupons (`collar_tub_front`, `collar_hood_plate`, `collar_part`) and the centring '
                    'gauge (`stl/tools/collar_gauge.stl`) | %s | %s |' % (g, ', '.join(gates), state(crel.get(g))))
    for n, pid in enumerate(L.PRINT_SEQUENCE, 4):
        rows.append('| %d | `%s` | %s | %s |' % (n, pid, ', '.join(L.PRINT_PREREQS.get(pid, ())) or 'nothing',
                                                state(prel.get(pid))))
    gates = sorted({g for v in list(L.PRINT_PREREQS.values()) + list(L.COUPON_PREREQS.values()) for g in v})
    rows += ['', '| Gate | What it fixes before printing |', '|---|---|']
    rows += ['| %s | %s |' % (g, L.PRINT_PREREQ_WHY.get(g, '')) for g in gates]
    return '\n'.join(rows)


def blk_orientation():
    """r6: PRINT-GUIDE s3 head: the settled orientation of every part (layout.PRINT_ORIENTATION_WHY) with the computed
    print_overhang result of the last build (checks.json)."""
    _, ck = _find(CHECKSJSON_CANDIDATES)
    res = {r.get('part'): r for r in ((ck or {}).get('results') or {}).get('print_overhang') or []}
    rows = ['| Part | Face down | Why this face | Computed (print_overhang) | Bridges: longest span (mm) | Declared supports |',
            '|---|---|---|---|---|---|']
    for pid in list(L.PARTS) + ['collar_gauge']:
        r = res.get(pid) or {}
        fd = L.PARTS[pid]['face_down'] if pid in L.PARTS else L.COLLAR['gauge']['face_down']
        why = L.PRINT_ORIENTATION_WHY.get(pid, 'assembly tool: rear end down, both cones widen upward at 45 deg')
        sup = ', '.join('`%s`' % z for z in sorted(r.get('supports_used') or {})) or 'none'
        span = r.get('longest_bridge_mm')
        hole = r.get('hole_edge_bridges')
        rows.append('| `%s` | %s | %s | %s | %s | %s |' % (
            pid, fd, why, r.get('status', 'not built'),
            '-' if not span else ('%.1f%s' % (span, ' (%d around a hole)' % hole if hole else '')), sup))
    return '\n'.join(rows)


def _kind_of(s):
    """r5: (kind label, drive, torque text) per SCREWS row: PT (thread-forming, FASTENER-POLICY C) or M3 (ISO 7045 into
    a heat-set insert, FASTENER-POLICY I, its own torque)."""
    if s.get('kind', 'PT') == 'PT':
        return 'PT 3.0 x 12', L.PT['drive'], '%s-%s, stop at head contact' % tuple(fmt(v, 2) for v in L.PT['torque_Nm'])
    return ('%s + washer' % s['spec'].split(' ISO')[0] if s.get('washer') else s['spec'].split(' ISO')[0],
            L.M3['drive'], '%s (machine thread in a brass insert)' % fmt(s['torque_Nm'], 2))


def blk_screws():
    # r5: Kind column; drive and torque per kind (PT torque was printed for every row); a zero-depth counterbore row
    #     (s_c4: washer on the lug top) prints as none
    rows = ['| Screw | Kind | Joins | Into | Head point (x, y, z) | Travels | Engagement (mm) | Counterbore | Step | '
            'Driver | Torque (N m) |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for s in L.SCREWS:
        cb = s['cbore']
        rng = ', '.join('%s %s..%s' % (k, fmt(cb[k][0]), fmt(cb[k][1])) for k in 'xyz' if k in cb)
        cbt = ('dia %s in `%s`, %s' % (fmt(cb['d']), cb['part'], rng) if cb['d'] > 0 else
               (cb.get('note') or 'none (spot face)'))
        kind, drive, tq = _kind_of(s)   # FIXER A-F7: 0.35 printed as 0.3 (fmt 2 places)
        rows.append('| `%s` | %s | %s | %s | (%s) | %s | %s | %s | %d | %s, bit dia <= %s x %s+ | %s |'
                    % (s['id'], kind, ' + '.join(s['joins']), s['into'],
                       ', '.join(fmt(float(v)) for v in s['head_point']),
                       AXIS_WORDS.get(tuple(s['axis']), str(s['axis'])), fmt(s['engage']), cbt,
                       s['step'], drive, fmt(L.DRIVER['bit_d']), fmt(L.DRIVER['bit_len']), tq))
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
            pts = [s for s in screws if s.get('kind', 'PT') == 'PT']
            m3s = [s for s in screws if s.get('kind', 'PT') != 'PT']      # r5: lens-collar M3 rows, own spec/torque
            fx = (['%d x %s' % (len(pts), L.PT['spec'])] if pts else []) + \
                 ['`%s` %s' % (s['id'], name_of(s['id']).split(' into ')[0]) for s in m3s]
            out.append('| Fasteners | %s |' % '; '.join(fx))
            out.append('| Driving | %s |' % '; '.join('`%s` travels %s, %s mm engagement into %s' % (
                s['id'], AXIS_WORDS.get(tuple(s['axis'])), fmt(s['engage']), s['into']) for s in screws))
            tqs = (['%s-%s N m by hand, stop at head contact (FASTENER-POLICY C; provisional until G-PT-1)'
                    % tuple(fmt(v, 2) for v in L.PT['torque_Nm'])] if pts else []) + \
                  ['`%s` %s N m (FASTENER-POLICY I, M3 into a heat-set insert)' % (s['id'], fmt(s['torque_Nm'], 2))
                   for s in m3s]
            out.append('| Torque | %s; no threadlocker |' % '; '.join(tqs))
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


# --------------------------------------------------------------------------- r3 docs: authoritative counts + count lint
# Audit 2026-10-05 correction 1D: the shared counts are computed here from source and written once, as the DESIGN.md
# `counts` block; the other docs point to it. `--check` also lints handwritten count phrases in the D2 docs.
COUPON_MANIFESTS = ['out/coupons-manifest.json', 'out/coupons-r1-manifest.json']
MEASURED_DOC = os.path.join(HERE, 'MEASURED-PARTS.md')
NUM_WORDS = {w: i for i, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen '
    'eighteen nineteen twenty'.split())}
NUM_WORDS.update({'twenty-%s' % w: 20 + i for w, i in list(NUM_WORDS.items())[1:10]})


def _lead_int(text):
    m = re.match(r'\s*(\d+)\s*x\b', text)
    return int(m.group(1)) if m else None


def coupon_counts():
    """[(manifest, n entries with an stl)], files in out/stl/coupons (or None)."""
    per = []
    for rel in COUPON_MANIFESTS:
        p = os.path.join(HERE, rel)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                m = json.load(f)
            cs = m.get('coupons', []) if isinstance(m, dict) else m
            per.append((rel, sum(1 for c in cs if isinstance(c, dict) and c.get('stl')),
                        sum(int(c.get('qty', 1)) for c in cs if isinstance(c, dict) and c.get('stl'))))
    d = os.path.join(HERE, 'out', 'stl', 'coupons')
    files = len([f for f in os.listdir(d) if f.lower().endswith('.stl')]) if os.path.isdir(d) else None
    return per, files


def mp_ids():
    if not os.path.exists(MEASURED_DOC):
        return []
    with open(MEASURED_DOC, encoding='utf-8') as f:
        ids = re.findall(r'^\| (MP-[A-Z0-9]+)\b', f.read(), re.M)
    return list(dict.fromkeys(ids))       # one record per id (sub-rows such as "MP-X1203 cooler line" share it)


def tool_rows():
    """Rows of the ASSEMBLY.md s1.1 toolset table (the tool categories)."""
    if not os.path.exists(DOCS['assembly']):
        return []
    with open(DOCS['assembly'], encoding='utf-8') as f:
        t = f.read()
    m = re.search(r'^### 1\.1 .*?$(.*?)^#', t, re.M | re.S)
    return re.findall(r'^\| (\d+) \| ([^|]+?) \|', m.group(1), re.M) if m else []


def counts():
    """Ordered {key: dict(label, value, detail, source)} of the shared D2 counts."""
    by_step, m3_step = {}, {}
    pt = set(L.pt_screw_ids())          # r5: the PT count and its sub-groups are kind PT only
    for s in L.SCREWS:
        (by_step if s['id'] in pt else m3_step).setdefault(s['step'], []).append(s['id'])
    per, files = coupon_counts()
    ncoup = sum(n for _, n, _ in per) if per else files   # None when no coupon build output exists
    mps = mp_ids()
    tools = tool_rows()
    C = {}
    C['printed'] = dict(label='Printed production parts', value=len(L.PARTS),
                        detail=', '.join('`%s`' % p for p in L.PARTS), source='`layout.PARTS`')
    C['pt'] = dict(label='PT 3.0 x 12 PH1 body screws', value=len(pt),
                   detail='; '.join('step %s: %s' % (k, ', '.join('`%s`' % i for i in v)) for k, v in sorted(by_step.items())),
                   source='`layout.SCREWS` kind PT (`layout.pt_screw_ids()`)')
    C['m3'] = dict(label='M3 lens-collar screws (ISO 7045 PH1 + washer, into heat-set inserts)',
                   value=sum(len(v) for v in m3_step.values()),
                   detail='; '.join('step %s: %s' % (k, ', '.join('`%s`' % i for i in v)) for k, v in sorted(m3_step.items())),
                   source='`layout.SCREWS` kind M3')
    C['kit_screws'] = dict(label='X1203 kit M2.5 screws (UPS kit, not body screws)', value=_lead_int(L.X1203_KIT['screws']),
                           detail=L.X1203_KIT['screws'], source="`layout.X1203_KIT['screws']`")
    C['kit_standoffs'] = dict(label='X1203 kit standoffs (UPS kit)', value=_lead_int(L.X1203_KIT['standoff']),
                              detail=L.X1203_KIT['standoff'], source="`layout.X1203_KIT['standoff']`")
    C['coupons'] = dict(label='Coupon STLs', value=ncoup,
                        detail=' + '.join('%d (`%s`, %d pieces by qty)' % (n, r, q) for r, n, q in per) +
                        ('; %s STL files in `out/stl/coupons/`%s' % (files, '' if files == ncoup else ' (**MISMATCH**)')),
                        source='coupon manifests')
    if ncoup is None:
        C['coupons'].update(value='n/a', detail='no coupon build output (coupon manifests and `out/stl/coupons/` missing)')
    C['mp'] = dict(label='Measured-part records', value=len(mps), detail=', '.join(mps), source='`MP-*` ids in MEASURED-PARTS.md')
    C['harnesses'] = dict(label='Harnesses (cables)', value=len(L.CABLES), detail=', '.join('`%s`' % c['id'] for c in L.CABLES),
                          source='`layout.CABLES`')
    C['tools'] = dict(label='Assembly tool categories', value=len(tools), detail='ASSEMBLY.md s1.1 rows 1-%d' % len(tools),
                      source='ASSEMBLY.md s1.1 table')
    C['steps'] = dict(label='Assembly steps', value=len(L.STEPS), detail='%d bench, %d in the body' % (
        sum(1 for s in L.STEPS if s.get('bench')), sum(1 for s in L.STEPS if not s.get('bench'))), source='`layout.STEPS`')
    C['_coupon_parts'] = [n for _, n, _ in per]
    C['_coupon_total'] = ncoup or 0
    C['_coupon_qty'] = sum(q for _, _, q in per)
    pts = [s for s in L.SCREWS if s['id'] in pt]
    C['_pt_groups'] = sorted({len(v) for v in by_step.values()} |
                             {sum(1 for s in pts if s['head_part'] == h) for h in {s['head_part'] for s in pts}})
    C['_m3_groups'] = sorted({len(v) for v in m3_step.values()} | {C['m3']['value']})
    C['_all_screws'] = len(L.SCREWS)
    return C


def blk_counts():
    C = counts()
    rows = ['Generated by `make_tables.py` from source; the other D2 docs point here instead of restating these totals. '
            '`make_tables.py --check` lints handwritten count phrases against this table.', '',
            '| Count | Value | Detail | Source |', '|---|---|---|---|']
    for k, v in C.items():
        if not k.startswith('_'):
            rows.append('| %s | **%s** | %s | %s |' % (v['label'], v['value'], v['detail'], v['source']))
    return '\n'.join(rows)


LINT_GLOBS = [(HERE, 'cad/gs8-d2-v1'), (os.path.dirname(DOCS['wiring']), 'electronics/gs8-d2-v1')]
LINT_SKIP = re.compile(r'(BRIEF|^NOTES)\.md$|-BRIEF\.md$')   # verbatim briefs and the working log are history
_N = r'(\d+|%s)' % '|'.join(sorted(NUM_WORDS, key=len, reverse=True))
COUNT_RE = re.compile(r'(?<![\w.-])(?<!x )%s((?:[ \t]+(?!%s\b)[^\s|,;:()\[\]+]+){0,5}?)[ \t]+'
                      r'(screws|prints|STLs|records|parts|pieces|coupons|harnesses|cables|tools|steps|standoffs)\b'
                      % (_N, '(?:' + _N[1:]), re.I)   # middle words never contain another count, a "+" or punctuation
# r3 fix-baseline (verifier VBD-4): more nouns (parts, pieces, coupons, harnesses, cables, tools, steps, standoffs),
# 'MP' = measured, PT sub-group sizes only when the phrase names the group, and paragraphs are linted joined (a phrase
# wrapped over two lines is still seen).
PT_GROUP_RE = re.compile(r'enclosure|keeper|panel|\bbase\b|\bgrip\b|\block\b|s_j|s_b|s_r|s_k|\bstep\b|\bJ4\b|\bPi\b',
                         re.I)
PT_TOTAL_RE = re.compile(r'whole body|in total|\btotal\b|all body|body screws', re.I)


def _num(t):
    return int(t) if t.isdigit() else NUM_WORDS[t.lower()]


def _paragraphs(lines):
    """[(text, [(offset, line no)])]: table rows and headings stand alone; other consecutive non-blank lines are joined
    with one space (so a count phrase wrapped over a line break is linted)."""
    out, cur = [], None
    for i, ln in enumerate(lines, 1):
        st = ln.strip()
        alone = st.startswith('|') or st.startswith('#') or st.startswith('<!--')
        item = re.match(r'([-*]|\d+\.)\s', st) is not None          # a list item starts a new paragraph
        if not st or alone or item:
            if cur:
                out.append(cur)
            cur = None
            if st and alone:
                out.append((ln, [(0, i)]))
            elif item:
                cur = (ln, [(0, i)])
            continue
        if cur is None:
            cur = (ln, [(0, i)])
        else:
            text, offs = cur
            cur = (text + ' ' + st, offs + [(len(text) + 1, i)])
    if cur:
        out.append(cur)
    return out


def lint_lines(lines, C=None):
    """[(line no, phrase, says, allowed, kind)] for the count phrases in `lines` that disagree with counts()."""
    C = C or counts()
    pt_ok = set(C['_pt_groups']) | {C['pt']['value']}
    kit_ok = {C['kit_screws']['value'], C['kit_screws']['value'] // 2}
    coup_ok = {C['_coupon_total']} | set(C['_coupon_parts'])
    out = []
    for ln, offs in _paragraphs([x.replace('PT 3.0 x 12', 'PT') for x in lines]):   # the screw spec is not a count
        for m in COUNT_RE.finditer(ln):
            n, mid, noun = _num(m.group(1)), m.group(2), m.group(3).lower()
            tail = ln[m.end():m.end() + 25]
            head = ln[max(0, m.start() - 40):m.start()]
            lno = max(l for o, l in offs if o <= m.start())
            if re.match(r'\s*x\s*\d', ln[m.end(1):m.end(1) + 6]) and 'PT' not in mid:
                continue                     # a dimension such as "5 x 5 screws"
            if re.search(r'\.(\s|$)', mid):
                continue                     # the phrase would run across a sentence end
            sent = re.split(r'\.\s', ln[:m.start()])[-1]
            if re.search(r'[+]\s*$|\b(saves?|adds?|removes?|fewer|more|extra|plus|minus)\b', sent, re.I):
                continue                     # a delta ("+2 printed parts", "saves ... 2 tools"), not a total
            if noun == 'records' and re.search(r'measured|\bMP\b', head + mid + tail, re.I):
                kind, ok = 'mp', {C['mp']['value']}
            elif noun == 'stls' and re.search(r'coupon', mid, re.I):
                kind, ok = 'coupons', coup_ok
            elif noun == 'stls':                # unqualified: production, coupon or both
                kind, ok = 'stls', coup_ok | {C['printed']['value'], C['printed']['value'] + C['_coupon_total']}
            elif noun == 'screws' and re.search(r'\bPT\b', mid):
                ctx = head[-25:] + mid + tail
                kind = 'pt'
                ok = ({C['pt']['value']} if PT_TOTAL_RE.search(mid + tail) or not PT_GROUP_RE.search(ctx)
                      else pt_ok)
            elif noun == 'screws' and re.search(r'M2\.5|kit', mid + tail, re.I):
                kind, ok = 'kit_screws', kit_ok
            elif noun == 'screws' and re.search(r'\bM3\b|collar', mid, re.I):     # r5: lens-collar M3 screws
                kind, ok = 'm3', set(C['_m3_groups'])
            elif noun == 'screws':
                kind, ok = 'screws', pt_ok | kit_ok | {C['_all_screws']}
            elif noun == 'prints':
                kind, ok = 'printed', {C['printed']['value'], C['_coupon_qty']} | coup_ok
            elif noun == 'parts' and len(mid.split()) <= 2 and re.search(r'(printed|production)\s*$', mid, re.I):
                kind, ok = 'printed', {C['printed']['value']}
            elif noun == 'parts' and len(mid.split()) <= 2 and re.search(r'measured\s*$', mid, re.I):
                kind, ok = 'mp', {C['mp']['value']}
            elif noun == 'pieces' and re.search(r'printed', mid, re.I):
                kind, ok = 'printed', {C['printed']['value'], C['_coupon_qty']}
            elif noun == 'coupons' and not mid.strip():
                kind, ok = 'coupons', coup_ok | {C['_coupon_qty']}
            elif noun in ('harnesses', 'cables') and not mid.strip():
                kind, ok = 'harnesses', {C['harnesses']['value']}
            elif noun == 'tools' and not mid.strip():
                kind, ok = 'tools', {C['tools']['value']}
            elif noun == 'steps' and re.search(r'assembly', head[-20:] + mid, re.I):
                kind, ok = 'steps', {C['steps']['value']}
            elif noun == 'standoffs':
                kind, ok = 'kit_standoffs', {C['kit_standoffs']['value']}
            else:
                continue
            if n not in ok:
                out.append((lno, m.group(0).strip(), n, sorted(ok), kind))
    return out


def lint_counts():
    """Handwritten count phrases that disagree with counts(): [(path, line, phrase, says, allowed, kind)]."""
    C = counts()
    out = []
    for d, rel in LINT_GLOBS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.md') or LINT_SKIP.search(fn):
                continue
            with open(os.path.join(d, fn), encoding='utf-8') as f:
                out += [('%s/%s' % (rel, fn),) + r for r in lint_lines(f.read().splitlines(), C)]
    return out


def lint_selftest():
    """The lint must flag the 2026-10-05 audit's handwritten mismatches (r2 wording) and pass the corrected ones."""
    C = counts()
    bad = ['r2 totals: 11 printed pieces, 6 PT screws, 10 harnesses', '| 9 records (MEASURED-PARTS) |',
           '## 6. Coupons to print first (about 3 h in total, r2: 21 STLs)', 'nine measured-part records',
           'six PT body screws', 'twenty-one coupon STLs',
           # r3 fix-baseline (verifier VBD-4): the planted phrases the r3 lint missed
           # r5: the two printed-count plants are derived (count + 1, the r3 off-by-one) since 12 is now correct
           'How to print the %d printed parts of D2.' % (C['printed']['value'] + 1), '21 coupons', 'nine measured parts',
           '11 harnesses', '13 tools', '11 assembly steps', '5 standoffs', '11 MP records',
           '%d printed pieces' % (C['printed']['value'] + 1), '3 PT screws',
           '4 PT screws in the whole body', 'the camera uses 6 PT 3.0 x 12\nPH1 screws',
           '5 M3 collar screws', '11 PT screws']        # r5: M3 count and an all-kinds total called PT
    bad = [t.split('\n') for t in bad]
    good = ['7 x PT 3.0 x 12 PH1 screws in the whole body', 'M2.5 x 5 screws', '8 M2.5 kit screws',
            '%d measured-part records' % C['mp']['value']]
    if C['_coupon_total']:
        good.append('%d coupon STLs' % C['coupons']['value'])
    good += ['the 2 keeper PT screws', '+2 printed parts', 'G-KEEP-1 coupons', 'Saves 1 part and 2\ntools',
             '4 M3 screws', 'the 3 collar screws', '11 screws in all']      # r5: kind M3 groups, all-kinds total
    good = [t.split('\n') for t in good]
    miss = [t for t in bad if not lint_lines(t, C)] + [t for t in good if lint_lines(t, C)]
    return miss


BLOCKS = {'wiring': {'cables': blk_cables, 'plugs': blk_plugs, 'header': blk_header},
          'print': {'print': blk_print, 'beds': blk_beds, 'engrave': blk_engrave, 'orientation': blk_orientation,
                    'order': blk_order},
          'assembly': {'steps': blk_steps, 'screws': blk_screws},
          'design': {'parts': blk_parts, 'cots': blk_cots, 'checks': blk_checks, 'counts': blk_counts}}


def refresh(check=False, docs=None):
    stale = []
    for doc, blocks in BLOCKS.items():
        if docs is not None and doc not in docs:
            continue
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
    # --check: report stale blocks of every doc (never writes) and lint handwritten counts; exit 1 on either.
    # --docs a,b: refresh only those docs (keys of DOCS: wiring, print, assembly, design). Without --docs every doc is
    # refreshed and the electronics side files (CSV, SVG) are rewritten; with --docs they are rewritten only if
    # "wiring" is listed. --lint: run only the count lint.
    args = sys.argv[1:]
    chk = '--check' in args
    sel = None
    if '--docs' in args:
        sel = [d.strip() for d in args[args.index('--docs') + 1].split(',') if d.strip()]
        bad = [d for d in sel if d not in DOCS]
        if bad:
            sys.exit('unknown --docs %s (choose from %s)' % (', '.join(bad), ', '.join(DOCS)))
    rc = 0
    if '--lint' not in args:
        s = refresh(check=chk, docs=None if chk else sel)
        if not chk and (sel is None or 'wiring' in sel):
            write_csvs()
            write_svg()
        print(('stale: ' if chk else 'refreshed: ') + (', '.join(s) if s else 'none'))
        rc = 1 if chk and s else 0
    if chk or '--lint' in args:
        miss = lint_selftest()
        for t in miss:
            print('count lint SELFTEST FAILED on: %r' % t)
        bad = lint_counts()
        rc = rc or (1 if miss else 0)
        for path, ln, phrase, n, ok, kind in bad:
            print('count lint: %s:%d: "%s" says %d; authoritative %s allows %s (DESIGN.md counts)' % (
                path, ln, phrase, n, kind, ok))
        print('count lint: %d disagreeing phrase(s); selftest %s' % (len(bad), 'FAILED' if miss else 'ok'))
        rc = rc or (1 if bad else 0)
    sys.exit(rc)
