# SPDX-License-Identifier: MIT
"""GS8 D2: purchased-part (COTS) proxies, built from layout.COTS / layout sections 3-6 (assembly frame, mm).

build_all(layout) -> {cots_id: dict(shape=cq.Workplane, mass=g, src=str, box=B, name, step, com=(x, y, z) or None)}
plus one solid per layout.SCREWS row (MODULE CONTRACT): kind PT from layout.PT; r5 kind M3 (lens collar s_c1..s_c4)
from layout.M3 with its washer and heat-set insert. r5: gs_camera_parts(L, s) gives the real GS stack sub-solids.

Every shape stays inside its layout COTS box. Sources are the layout tags (datasheet / listing / repo / estimate);
every proxy is a proxy: nothing here was bought or measured. Connector and plug keep-outs are layout.KEEPOUTS
(checked by checks.py); the plug-in features that matter for fit are modelled here (Pi jacks, button, HDMI and
USB-C ports, camera holes and FPC connector, eyepiece eye-end dia 36.7 for the cup grip, encoder and switch bushings
with D shafts, switch anti-rotation tab, nut, stick plug).
LENS: chosen by layout.LENS at call time (build_d2.py --lens sets it); lens_proxy(layout, name) builds either one.
"""
import math

import cadquery as cq

import d2_common as dc

V = cq.Vector


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _cyl(axis, c0, c1, r, a0, a1):
    return dc.cyl_solid(dict(axis=axis, c=(c0, c1), r=r, a=(a0, a1)))


def _tube(axis, c0, c1, ro, ri, a0, a1):
    return _cyl(axis, c0, c1, ro, a0, a1).cut(_cyl(axis, c0, c1, ri, a0 - 0.1, a1 + 0.1))


def _hex_z(af, x, y, z0, z1, flats_y=True):
    """Hex prism along +Z; flats_y: flats face +-Y (corners on +-X)."""
    r = af / math.sqrt(3.0)
    a0 = 0.0 if flats_y else 30.0
    pts = [(x + r * math.cos(math.radians(a0 + 60 * i)), y + r * math.sin(math.radians(a0 + 60 * i))) for i in range(6)]
    return cq.Workplane('XY').workplane(offset=z0).polyline(pts).close().extrude(z1 - z0).val()


def _hex_y(af, x, z, y0, y1):
    """Hex prism along +Y (flats up/down)."""
    r = af / math.sqrt(3.0)
    pts = [(x + r * math.cos(math.radians(60 * i)), z + r * math.sin(math.radians(60 * i))) for i in range(6)]
    return _prism_y([(px, pz) for px, pz in pts], y0, y1)


def _prism_y(pts_xz, y0, y1):
    """Closed (x, z) polygon extruded along +Y from y0 to y1. Plane(xDir +X, normal +Y) has local v = -Z."""
    wp = cq.Workplane(cq.Plane(origin=V(0, y0, 0), xDir=V(1, 0, 0), normal=V(0, 1, 0)))
    return wp.polyline([(px, -pz) for px, pz in pts_xz]).close().extrude(y1 - y0).val()


def _band_y(pts_xz, t, y0, y1):
    """Strap-like band of thickness t along an (x, z) polyline, extruded y0..y1."""
    segs = []
    for (ax, az), (bx, bz) in zip(pts_xz[:-1], pts_xz[1:]):
        n = math.hypot(bx - ax, bz - az)
        nx, nz = -(bz - az) / n * t / 2, (bx - ax) / n * t / 2
        segs.append(_prism_y([(ax + nx, az + nz), (bx + nx, bz + nz), (bx - nx, bz - nz), (ax - nx, az - nz)], y0, y1))
    return _fuse(*segs)


def _d_shaft_y(x, z, r, flat_w, y0, y1):
    """D shaft along +Y: cylinder r with a flat leaving flat_w across (flat on the +z side)."""
    s = _cyl('y', x, z, r, y0, y1)
    cut = _box(x - r - 0.1, x + r + 0.1, y0 - 0.1, y1 + 0.1, z - r + flat_w, z + r + 0.1)
    return s.cut(cut)


def _fuse(*s):
    return dc.fuse_all([x for x in s if x is not None])


def _clip(shape, b):
    """Keep the proxy inside its COTS box (exact)."""
    return shape.intersect(dc.box_solid(b))


# ------------------------------------------------------------------------------------------- power stack
def pi5(L, c):
    f = c['features']
    x0, x1 = L.PI['x']
    y0, y1 = L.PI['y']
    pcb = dc.box_solid(f['pcb'])
    for hx, hy in f['holes']:
        pcb = pcb.cut(_cyl('z', hx, hy, 1.35, 18.0, 21.0))                     # M2.5 holes dia 2.7
    under = _box(x0 + 6.5, x1 - 6.5, y0 + 6.5, y1 - 6.5, 16.0, 18.5)           # underside parts (pogo field)
    jacks = _fuse(_box(x0 - 3.0, x0 + 18.0, y0 + 1.5, y0 + 17.0, 20.1, 36.1),   # RJ45
                  _box(x0 - 3.0, x0 + 14.5, y0 + 20.0, y0 + 35.0, 20.1, 36.1),  # USB 2 (upper) + USB 3 pair
                  _box(x0 - 3.0, x0 + 14.5, y0 + 38.0, y0 + 53.0, 20.1, 36.1))
    g = f['gpio']
    pl = L.STICK['plug']
    jacks = jacks.cut(_box(pl['x'][0] - 0.1, pl['x'][1] + 0.05, pl['y'][0] - 0.05, pl['y'][1] + 0.05, pl['z'][0] - 0.05,
                           pl['z'][1] + 0.05))                                 # USB 3 receptacle cavity (stick plug)
    gpio = _box(g['x'][0], g['x'][1], g['y'][0], g['y'][1], 20.1, g['z'][1])
    btn = _box(x1 - 2.5, f['button']['x_face'], f['button']['y'] - 1.5, f['button']['y'] + 1.5, 20.1, 22.4)
    hdmi = [_box(hx - 3.75, hx + 3.75, y1 - 6.7, y1, 20.1, 23.6) for hx in (f['hdmi0']['x'], f['hdmi0']['x'] + 13.5)]
    usbc = _box(f['usbc']['x'] - 4.5, f['usbc']['x'] + 4.5, y1 - 6.7, y1, 20.1, 23.3)
    cams = _box(f['cam1']['x'][0], f['cam1']['x'][1], y1 - 6.7, y1 - 2.0, 20.1, 25.6)   # clear of the cooler
    soc = _box(x1 - 45.0, x1 - 28.0, y0 + 20.0, y0 + 37.0, 20.1, 21.4)
    return _fuse(pcb, under, jacks, gpio, btn, *hdmi, usbc, cams, soc)


def cooler(L, c):
    b = c['box']
    x0, x1 = b['x']
    y0, y1 = b['y']
    fb = c['features']['blower']
    plate = _box(x0, x1, y0, y1, 21.6, 23.4)          # base plate over the SoC thermal pad (SoC top z 21.4)
    feet = [_cyl('z', fx, fy, 1.5, b['z'][0], 21.6) for fx in (x0 + 3.0, x1 - 3.0) for fy in (y0 + 3.0, y1 - 3.0)]
    fins = [_box(fb['x'][1], x1, y, y + 1.0, 23.4, 30.5) for y in [y0 + 1.0 + 2.5 * i for i in range(int((y1 - y0 - 2) / 2.5))]]
    blower = _box(fb['x'][0], fb['x'][1], fb['y'][0], fb['y'][1], 23.4, b['z'][1])
    hub = _cyl('z', (fb['x'][0] + fb['x'][1]) / 2, (fb['y'][0] + fb['y'][1]) / 2, 9.0, b['z'][1] - 0.6, b['z'][1])
    return _fuse(plate, blower.cut(hub), *fins, *feet)   # 4 push-pin feet (estimate positions)


def x1203(L, c):
    x0, x1 = L.PI['x']
    y0, y1 = L.PI['y']
    pcb = dc.box_solid(c['features']['pcb'])
    for hx, hy in L.PI['holes']:
        pcb = pcb.cut(_cyl('z', hx, hy, 1.35, 5.0, 9.0))
    pogo = _box(x1 - 58.0, x1 - 7.0, y0 + 0.5, y0 + 5.0, 7.6, 16.0)            # pogo pins under the GPIO pads
    parts = _box(x0 + 12.0, x0 + 40.0, y0 + 12.0, y1 - 12.0, 7.6, 11.0)        # charger + converter field (estimate)
    xh = _box(x0 + 2.0, x0 + 10.0, y0 + 10.0, y0 + 16.0, 7.6, 13.5)            # battery XH header (estimate)
    return _fuse(pcb, pogo, parts, xh)


def x1203_kit(L, c):
    k = c['kit']
    zs0, zs1 = k['standoff_z']
    hd, hh = k['head']
    out = []
    for hx, hy in L.PI['holes']:
        out.append(_hex_z(5.0, hx, hy, zs0, zs1))
        out.append(_cyl('z', hx, hy, hd / 2, zs0 - 1.6 - hh, zs0 - 1.6))       # screw head under the X1203
        out.append(_cyl('z', hx, hy, 1.2, zs0 - 1.6, zs0))                     # shank through the X1203
        out.append(_cyl('z', hx, hy, 1.2, zs1, zs1 + 1.6))                     # shank through the Pi
        out.append(_cyl('z', hx, hy, hd / 2, zs1 + 1.6, zs1 + 1.6 + hh))       # head on the Pi
    return _fuse(*out)


# ------------------------------------------------------------------------------------------- camera + lens
def gs_camera_parts(L, s=None, head_side='both'):
    """r5 (J7-R, judge 3 s6.8): the real GS stack at BFAR screw-out s (default CAM s_nom) as tagged sub-solids
    {'body': housing (front throat for the lens rear) + split lock tab + lock-screw head envelopes on BOTH sides +
    PCB (4 holes) + rear cover (FPC socket recess), 'bfar': BFAR head + its exposed fine thread (s > 0)}.
    The adapter is the separate COTS c_cs_adapter; the tripod block is removed at bench B0 (not modelled).
    r7 C4 (BX-4): also 'metal' (housing + tab + heads) and 'pcb_cover' (PCB + cover) for check_roll_catch; 'body' is
    still built as their union in the same order (j7_float and every caller see the same solid). head_side '+Y' /
    '-Y' builds the lock-screw head envelope on that side only (pre-G-CAM-1 variants); default 'both'."""
    cam = L.CAM
    ly, lz = L.LENS_AXIS
    s = cam['s_nom'] if s is None else s
    hf = L.cam_hf_x(s)
    H, P, Cv, T, B = cam['housing'], cam['pcb'], cam['cover'], cam['tab'], cam['bfar']
    hx0 = hf - H['depth']
    housing = _cyl('x', ly, lz, H['d'] / 2, hx0, hf).cut(
        _cyl('x', ly, lz, H['throat_d'] / 2, hf - H['throat_depth'], hf + 0.1))
    rt = H['d'] / 2
    tab = _box(hf - T['depth'], hf, ly - T['w'] / 2, ly + T['w'] / 2, lz + rt - 1.0, lz + T['top_r']).cut(
        _box(hf - T['depth'] - 0.1, hf + 0.1, ly - T['slot'] / 2, ly + T['slot'] / 2, lz + rt, lz + T['top_r'] + 0.1))
    xs = hf - T['screw_dx']
    if head_side not in ('both', '+Y', '-Y'):
        raise ValueError('gs_camera_parts head_side must be both, +Y or -Y (got %r)' % (head_side,))
    heads = [_cyl('y', xs, T['screw_z'], T['head_d'] / 2, a, b)
             for nm, (a, b) in (('+Y', (ly + T['w'] / 2 - 0.01, ly + T['w'] / 2 + T['head_h'])),
                                ('-Y', (ly - T['w'] / 2 - T['head_h'], ly - T['w'] / 2 + 0.01)))
             if head_side in ('both', nm)]
    hp, hc = P['sq'] / 2, Cv['sq'] / 2
    pcb = _box(hx0 - P['t'], hx0, ly - hp, ly + hp, lz - hp, lz + hp)
    for hy, hz in cam['holes']:
        pcb = pcb.cut(_cyl('x', hy, hz, cam['hole_d'] / 2, hx0 - P['t'] - 0.1, hx0 + 0.1))
    rear = hx0 - P['t'] - Cv['t']
    f = cam['fpc_socket']
    cover = _box(rear, hx0 - P['t'], ly - hc, ly + hc, lz - hc, lz + hc).cut(
        _box(rear - 0.1, rear + f['depth'], ly - f['w'] / 2, ly + f['w'] / 2, lz - hc + f['z_above_bottom'],
             lz - hc + f['z_above_bottom'] + f['h']))          # socket recess marks the FPC entry (FPC exits -X)
    body = _fuse(housing, tab, *heads, pcb, cover)
    head = _tube('x', ly, lz, B['d'] / 2, B['d_in'] / 2, L.BFAR_FACE_X - B['t'], L.BFAR_FACE_X)
    bfar = head if s < 0.01 else _fuse(head, _tube('x', ly, lz, B['thread_d'] / 2, B['d_in'] / 2, hf,
                                                   L.BFAR_FACE_X - B['t'] + 0.01))
    return dict(body=body, bfar=bfar, s=s, hf_x=hf, cover_rear_x=rear,
                metal=_fuse(housing, tab, *heads), pcb_cover=_fuse(pcb, cover), head_side=head_side)  # r7 C4


def gs_camera(L, c):
    """r5: the GS camera at the nominal s (body + bfar sub-solids fused); gs_camera_parts(L, s) for the float check."""
    p = gs_camera_parts(L)
    return _fuse(p['body'], p['bfar'])


def c_cs_adapter(L, c):
    """r5: C-CS adapter tube dia 30.75 / 25.5 (C thread), x CS_FLANGE_X..C_FLANGE_X (spigot inside the BFAR: not modelled)."""
    a = L.CAM['adapter_cyl']
    return _tube('x', *a['c'], a['r'], a['r_in'], *a['a'])


def _rev_x(pts_xr, ly, lz):
    """Closed (x, r) profile revolved about the lens axis (y ly, z lz)."""
    wp = cq.Workplane('XY').polyline(pts_xr).close().revolve(360.0, (0, 0, 0), (1, 0, 0))
    return wp.val().translate(V(0, ly, lz))


def lens_proxy(L, name=None):
    """Revolved C-mount lens from lens_spec segments (absolute x). r5: the support band's rear outer edge carries its
    45 deg edge_chamfer (it seats on the collar cone); the thumb screws are a swept keep-out (KEEPOUTS ko_lens_thumb_*),
    not proxy solids (r4 modelled the lock screws at one clock)."""
    d = L.lens_spec(name)
    ly, lz = L.LENS_AXIS
    sp = d.get('support_abs')
    segs = []
    for r, x0, x1, _ in d['segments_abs']:
        ch = sp.get('edge_chamfer', 0.0) if sp else 0.0
        if sp and ch > 0 and abs(x0 - sp['x0']) < 1e-6 and abs(r - sp['d'] / 2) < 1e-6:
            segs.append(_rev_x([(x0, 0.0), (x0, r - ch), (x0 + ch, r), (x1, r), (x1, 0.0)], ly, lz))
        else:
            segs.append(_cyl('x', ly, lz, r, x0, x1))
    shape = _fuse(*segs)
    front = d['segments_abs'][-1][2]
    shape = shape.cut(_cyl('x', ly, lz, d['segments_abs'][-1][0] - 3.0, front - 2.0, front + 0.1))   # front recess
    return shape, d


# ------------------------------------------------------------------------------------------- EVF
def eyepiece(L, c):
    """0PE039-16X: eye end dia 36.7 (F-20.3..F-17.3, the cup sleeve grips it), knurl barrel dia 38.5 to F, M29 spigot
    4.5 long behind F; clear aperture dia 23 (estimate)."""
    e = L.EVF
    ay, az = e['axis']
    F = e['F']
    x_eye = e['barrel']['a'][0]
    s = _fuse(_cyl('x', ay, az, 18.35, x_eye, x_eye + 3.0), _cyl('x', ay, az, e['barrel']['r'], x_eye + 3.0, F),
              _cyl('x', ay, az, e['spigot']['r'], F, F + e['spigot']['a'][1] - e['spigot']['a'][0]))
    return s.cut(_cyl('x', ay, az, 11.5, x_eye - 0.1, F - 3.0))


def hmx039(L, c):
    b = c['box']
    glass = dc.box_solid(b)
    return glass.cut(_box(b['x'][0] - 0.01, b['x'][0] + 0.3, b['y'][0] + 0.8, b['y'][1] - 0.8, b['z'][0] + 1.4,
                          b['z'][1] - 1.4))   # active-area step


def evf_board(L, c):
    b = c['box']
    px0, px1 = c['features']['pcb_x']
    pcb = _box(px0, px1, b['y'][0], b['y'][1], b['z'][0], b['z'][1])
    comp = _box(b['x'][0] + 1.6, px0, b['y'][0] + 2.0, b['y'][1] - 2.0, b['z'][0] + 5.0, b['z'][1] - 2.0)
    hdmi = _box(b['x'][0], px0, 4.0, 17.0, b['z'][0], b['z'][0] + 4.0)       # micro-HDMI receptacle, lower edge
    zif = _box(px0 - 2.0, px0, b['y'][0] + 6.0, b['y'][0] + 19.0, b['z'][1] - 5.6, b['z'][1] - 1.6)   # below the rail
    return _fuse(pcb, comp, hdmi, zif)


def usb_stick(L, c):
    s = L.STICK
    bd, pl = s['body'], s['plug']
    body = dc.safe_chamfer(cq.Workplane().add(dc.box_solid(bd)), '|X', 1.0).val()
    plug = dc.box_solid(pl).cut(_box(pl['x'][0] + 0.5, pl['x'][1] + 0.1, pl['y'][0] + 0.4, pl['y'][1] - 0.4,
                                     pl['z'][0] + 0.4, pl['z'][1] - 0.4))
    return _fuse(body, plug)


# ------------------------------------------------------------------------------------------- panel controls
def encoder(L, c):
    """Adafruit 5880: PCB 25.3 x 25.6, encoder body, bushing dia 7, D shaft dia 6 (4.5 flat), 2 STEMMA QT sockets
    and parts on the back (estimate)."""
    e = L.ENCODER
    ex, ez = e['c']
    pcb = dc.box_solid(e['pcb'])
    body = dc.box_solid(e['body'])
    bush = dc.cyl_solid(e['bushing'])
    shaft = _d_shaft_y(ex, ez, e['shaft']['r'], e['shaft_flat'], *e['shaft']['a'])
    q = e['qt_socket']   # r7 C2: one source with checks._plug_point (same geometry as r6: dx +-9.5, w 4.3, y0 19.6, h 6)
    qts = [_box(ex + sx - q['w'] / 2, ex + sx + q['w'] / 2, q['y0'], e['pcb']['y'][0], ez - q['h'] / 2, ez + q['h'] / 2)
           for sx in q['dx']]
    back = _box(ex - 6.0, ex + 6.0, 22.6, e['pcb']['y'][0], ez - 6.0, ez + 6.0)
    return _fuse(pcb, body, bush, shaft, back, *qts)


def switch_1824(L, c):
    s = L.SWITCH_1824
    sx, sz = s['c']
    body = dc.cyl_solid(s['body'])
    bush = dc.cyl_solid(s['bushing'])
    shaft = _d_shaft_y(sx, sz, s['shaft']['r'], 4.8, *s['shaft']['a'])
    # The knob and its moving shaft depict one selected state. Fixed body/tab stay put.
    # layout.pol uses clockwise seen from +Y, hence the negative right-hand rotation.
    # This is a proxy pose, not a measured detent angle or permission to change the real switch.
    shaft = shaft.rotate((sx, 0, sz), (sx, 1, sz), -L.KNOBS['knob_fps']['index_deg'])
    nut = _hex_y(s['nut']['af'], sx, sz, *s['nut']['y']).cut(_cyl('y', sx, sz, s['bushing']['r'], s['nut']['y'][0] - 0.1,
                                                                    s['nut']['y'][1] + 0.1))
    tw, th, tp = s['anti_rot']['tab']
    tx, tz = L.pol((sx, sz), s['anti_rot']['r'], s['anti_rot']['angle_deg'])
    tab = _box(tx - tw / 2, tx + tw / 2, L.SPLIT, L.SPLIT + tp, tz - th / 2, tz + th / 2)
    return _fuse(body, bush, shaft, nut, tab)


# ------------------------------------------------------------------------------------------- grip and power
def run_button(L, c):
    rb = L.RUN_BTN
    body = dc.box_solid(rb['body'])
    cap = dc.cyl_solid(rb['cap'])
    return _fuse(body, cap)


def pack(L, c):
    """1S2P 18650: 2 cells dia 18.6 x 65.5 upright side by side in x, BMS + nickel on top (estimate)."""
    b = c['box']
    (x0, x1), (y0, y1), (z0, z1) = b['x'], b['y'], b['z']
    yc = (y0 + y1) / 2
    cells = [_cyl('z', xc, yc, 9.3, z0, z0 + 65.5) for xc in (x0 + 9.5, x1 - 9.5)]
    wrap = _box(x0 + 9.5, x1 - 9.5, yc - 9.3, yc + 9.3, z0, z0 + 65.5)
    bms = _box(x0 + 0.5, x1 - 0.5, y0 + 1.0, y1 - 1.0, z0 + 65.5, z1)
    return _fuse(*cells, wrap, bms)


def xt30_pair(L, c):
    b = c['box']
    (x0, x1), (y0, y1), (z0, z1) = b['x'], b['y'], b['z']
    xm = (x0 + x1) / 2
    f = getattr(L, 'PIGTAIL_FUSE', None)
    zt = z0 if f is None else f['z'] + f['sleeve_od'] / 2 + 1.0     # r4: the pair sits above the fuse sleeve
    if f is not None and f.get('beside'):    # r7 fix-up (VERIFY-C3): the sleeve lies beside the pair, both flat
        zt = z0
        r_ = f['sleeve_od'] / 2 + 0.2
        y0, y1 = (y0, f['y'] - r_) if f['y'] > (y0 + y1) / 2 else (f['y'] + r_, y1)
    pair = _fuse(_box(x0, xm, y0 + 0.3, y1 - 0.3, zt + 0.2, z1 - 0.2), _box(xm, x1, y0, y1, zt, z1))
    if f is None:
        return pair
    sleeve = _cyl('x', f['y'], f['z'], f['sleeve_od'] / 2, *f['x'])   # r4: sleeved inline fuse on the pigtail
    return _fuse(pair, sleeve)


def tripod_nut(L, c):
    t = L.TRIPOD
    return _hex_z(t['nut_af'], t['x'], t['y'], *t['nut_z']).cut(_cyl('z', t['x'], t['y'], 2.6, t['nut_z'][0] - 0.1,
                                                                    t['nut_z'][1] + 0.1))


def strap(L, c):
    """12 mm hand strap: a loop over the base-top recess through the 2 upper slots, then a band down behind the hand
    toward the grip foot (proxy; it is soft and folds aside)."""
    us = L.STRAP['upper_slots']
    y0, y1 = -33.5, -21.5
    xa = (us[0]['x'][0] + us[0]['x'][1]) / 2
    xb = (us[1]['x'][0] + us[1]['x'][1]) / 2
    loop = _band_y([(xb, -9.5), (xb, -0.9), (xa, -0.9), (xa, -9.5)], 1.4, y0, y1)
    band = _band_y([((xa + xb) / 2, -10.0), (-93.0, -52.0), (-73.0, -104.0)], 1.5, y0, y1)
    tie = _band_y([(xb, -9.5), ((xa + xb) / 2, -10.0), (xa, -9.5)], 1.4, y0, y1)
    return _fuse(loop, tie, band)


def foam_pad(L, c):
    return dc.box_solid(c['box'])


# ------------------------------------------------------------------------------------------- screws
def screw(L, s):
    """PT 3.0 x 12 pan head PH1: shank dia 3.0 head_point -> tip, head dia 6.0 x 2.4 behind head_point.
    r5: kind 'M3' (lens collar): ISO 7045 M3 (head dia 5.6 x 2.4) of s['length'], plus the ISO 7089 washer (head_point
    .. head_point + t along the axis) and its heat-set insert (tube OD = insert bore, ID = M3) where the entry has one:
    one hardware solid per SCREWS row, exempt from interference with the parts it joins (id prefix s_)."""
    if s.get('kind', 'PT') == 'PT':
        pt = L.PT
        ax = s['axis']
        shank = dc.cyl_along(pt['d'] / 2, 0.0, pt['length'], s['head_point'], ax)
        head = dc.cyl_along(pt['head_d'] / 2, -pt['head_h'], 0.0, s['head_point'], ax)
        recess = dc.cyl_along(1.2, -pt['head_h'] - 0.1, -pt['head_h'] + 1.2, s['head_point'], ax)
        return _fuse(shank, head.cut(recess))
    M, ax, hp = L.M3, s['axis'], s['head_point']
    out = [dc.cyl_along(M['d'] / 2, 0.0, s['length'], hp, ax)]
    head = dc.cyl_along(M['head_d'] / 2, -M['head_h'], 0.0, hp, ax)
    out.append(head.cut(dc.cyl_along(1.2, -M['head_h'] - 0.1, -M['head_h'] + 1.2, hp, ax)))
    if s.get('washer'):
        W = M['washer']
        out.append(dc.cyl_along(W['d'] / 2, 0.0, W['t'], hp, ax).cut(dc.cyl_along(W['d_in'] / 2, -0.1, W['t'] + 0.1, hp, ax)))
    ins = s.get('insert')
    if ins:
        k = next(c for c in 'xyz' if c in ins)
        i = 'xyz'.index(k)
        t0, t1 = sorted((v - hp[i]) / ax[i] for v in ins[k])
        out.append(dc.cyl_along(ins['bore_d'] / 2, t0, t1, hp, ax).cut(dc.cyl_along(M['d'] / 2 - 0.01, t0 - 0.1, t1 + 0.1,
                                                                                   hp, ax)))
    return _fuse(*out)


BUILDERS = dict(pi5=pi5, cooler=cooler, x1203=x1203, x1203_kit=x1203_kit, gs_camera=gs_camera,
                c_cs_adapter=c_cs_adapter, eyepiece=eyepiece, hmx039=hmx039, evf_board=evf_board, usb_stick=usb_stick,
                encoder=encoder, switch_1824=switch_1824, run_button=run_button, pack=pack, xt30_pair=xt30_pair,
                tripod_nut=tripod_nut, strap=strap, foam_pad=foam_pad, microsd=foam_pad)   # FIXER A-F2: box proxy


def build_one(L, cid):
    c = L.COTS[cid]
    if cid == 'lens':
        shape, d = lens_proxy(L)
        return dict(shape=cq.Workplane().add(shape), mass=d['mass'], src=d['src'], box=c['box'], name=d['name'],
                    step=c['step'], com=d['com'], kind='cots', pn=c['pn'])
    if c.get('box') is None:   # pt_screws / r5 m3_hw: mass/BOM rows only; the screw solids are the s_* rows
        kind = 'M3' if cid == 'm3_hw' else 'PT'
        ids = [s['id'] for s in L.SCREWS if s.get('kind', 'PT') == kind]
        return dict(shape=None, mass=0.0, src=c['src'], box=None, name=c['name'], step=c['step'], com=None,
                    kind='hardware', pn=c['pn'], note='mass carried by %s (%.1f g total)' % (', '.join(ids), c['mass']))
    shape = BUILDERS[cid](L, c)
    return dict(shape=cq.Workplane().add(shape), mass=c['mass'], src=c['src'], box=c['box'], name=c['name'],
                step=c['step'], com=None, kind='cots', pn=c['pn'])


def build_all(layout, only=None):
    """{id: row} for every COTS id (+ the 4 screws). `only`: optional iterable of ids to build."""
    L = layout
    out = {}
    for cid in L.COTS:
        if only is None or cid in only:
            out[cid] = build_one(L, cid)
    n_pt = max(1, sum(1 for s in L.SCREWS if s.get('kind', 'PT') == 'PT'))
    for s in L.SCREWS:
        if only is None or s['id'] in only:
            pt = s.get('kind', 'PT') == 'PT'    # r5: PT mass = pt_screws / n PT (as r4); M3 rows: L.screw_mass (screw +
            #                                     washer + insert)
            out[s['id']] = dict(shape=cq.Workplane().add(screw(L, s)),
                                mass=L.COTS['pt_screws']['mass'] / n_pt if pt else L.screw_mass(s),
                                src='standard class (PT)' if pt else 'standard class (M3, r5)', box=None,
                                name=('PT 3.0 x 12 PH1 (%s)' if pt else s['spec'] + ' + washer + insert (%s)') % s['into'],
                                step=s['step'], com=None, kind='hardware', pn=L.PT['spec'] if pt else s['spec'])
    return out
