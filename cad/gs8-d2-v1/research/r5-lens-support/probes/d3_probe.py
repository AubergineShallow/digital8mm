"""Designer 3 read-only probe: build the proposed LCB (lens collar bearing), S1 tub boss, S2/S3 panel bosses and the
corrected Kowa proxy in the D2 assembly frame; check overlaps against the release STEP parts, COTS proxies, keep-outs
and the existing insertion sweeps; report LCB volume/mass. No repo file is written."""
import os, sys, json, math
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L
import cots
import d2_common as dc
V = cq.Vector
XF = float(sys.argv[1]) if len(sys.argv) > 1 else L.C_FLANGE_X     # C flange x (D2 10.6; real ~2.5)
ZA = 60.0
parts = {p: cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', p + '.step')).val()
         for p in ('tub', 'hood', 'panel', 'base_grip', 'pi_keeper', 'plunger')}
C = cots.build_all(L, only={'gs_camera', 'c_cs_adapter', 'pi5', 'cooler', 'microsd'})
cot = {k: r['shape'].val() for k, r in C.items()}

def cylx(r, x0, x1, y=0.0, z=ZA):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))

def prism_yz(pts, x0, x1):
    w = cq.Workplane('YZ', origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)
    return w.val()

# ---- corrected Kowa LM6HC proxy (Kowa drawing, dossier_external s7.1), x from the C flange
KOWA = [(12.7, -6.7, 0.0), (15.75, 0.0, 2.2), (21.0, 2.2, 7.6), (19.5, 7.6, 10.6), (20.85, 10.6, 22.4),
        (19.3, 22.4, 30.9), (19.25, 30.9, 36.6), (19.0, 36.6, 37.6), (20.75, 37.6, 41.7), (27.0, 41.7, 50.5),
        (23.0, 50.5, 56.2)]
lens = None
for r, a, b in KOWA:
    s = cylx(r, XF + a, XF + b)
    lens = s if lens is None else lens.fuse(s)
for xs in (14.4, 33.0):   # M2 thumb screws, head d 3.8 to r 24, drawn on the right (-Y) like D2
    lens = lens.fuse(cq.Solid.makeCylinder(1.9, 4.0, V(XF + xs, -20.0, ZA), V(0, -1, 0)))

# ---- LCB (lens collar bearing), Kowa build
BAND = (2.2, 7.6); TRAVEL = 1.5; R_BAND = 21.0; CLR = 0.15
xs0, xs1 = XF + BAND[0] - TRAVEL, XF + BAND[1] + TRAVEL          # sleeve bore extent
X_REAR = L.XT1                                                    # -2.7, bears on the tub wall front face
R_RING, Z_FLAT = 28.5, 33.0
t45 = R_RING * math.sqrt(0.5)
yflat = t45 - ((ZA - t45) - Z_FLAT)                               # 45 deg flank meets the flat
def outline(r=R_RING, zf=Z_FLAT, off=0.0):
    pts = []
    n = 48
    a0, a1 = math.radians(-45.0), math.radians(225.0)             # arc from lower right over the top to lower left
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        pts.append(((r + off) * math.cos(a), ZA + (r + off) * math.sin(a)))
    yl = yflat + off * (math.sqrt(2) - 1)
    pts += [(-yl, zf - off), (yl, zf - off)]
    return pts
ring = prism_yz(outline(), X_REAR, xs0)
sleeve = cylx(R_BAND + CLR + 3.0, xs0 - 0.01, xs1)
S = {'S1': (0.0, 88.5), 'S2': (27.5, 74.0), 'S3': (27.5, 46.0)}
ears = None
for nm, (y, z) in S.items():
    e = cylx(4.7, X_REAR, 0.3, y, z)
    # web from the ear toward the axis
    ang = math.atan2(z - ZA, y); L0 = math.hypot(y, z - ZA)
    w = cq.Workplane('YZ', origin=(X_REAR, 0, 0)).center(y - 0.5 * (L0 - 20) * math.cos(ang), z - 0.5 * (L0 - 20) * math.sin(ang)) \
        .transformed(rotate=(0, 0, math.degrees(ang))).rect(L0 - 20, 9.4).extrude(3.0).val()
    ears = e.fuse(w) if ears is None else ears.fuse(e).fuse(w)
lug = cq.Workplane('XY').box(xs1 - xs0, 12.5, 7.5, centered=False).translate((xs0, -3.75, ZA + 23.5)).val()
lcb = ring.fuse(sleeve).fuse(ears).fuse(lug)
bore = cylx(18.75, X_REAR - 1, xs0 + 0.01).fuse(cylx(R_BAND + CLR, xs0, xs1 + 1))
cuts = [bore, cq.Workplane('XY').box(xs1 - xs0 + 2, 1.5, 12.0, centered=False).translate((xs0 - 1, -0.75, ZA + 18)).val()]
for nm, (y, z) in S.items():
    cuts.append(cylx(1.7, X_REAR - 1, 1.0, y, z))
    cuts.append(cylx(3.5, -0.35, 40.0, y, z))
cuts.append(cq.Solid.makeCylinder(1.25, 9.0, V(0.5 * (xs0 + xs1), 0.75, ZA + 28.0), V(0, 1, 0)))     # pinch pilot
cuts.append(cq.Solid.makeCylinder(1.7, 3.0, V(0.5 * (xs0 + xs1), -3.75, ZA + 28.0), V(0, 1, 0)))     # head-lug clearance
for c in cuts:
    lcb = lcb.cut(c)
vol = lcb.Volume()
bb = lcb.BoundingBox()
res = dict(XF=XF, lcb_bbox=[round(v, 2) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)],
           lcb_vol_mm3=round(vol, 0), lcb_mass_g_shell=round(vol * 1.07e-3 * 0.85, 1),
           lcb_com=[round(v, 2) for v in cq.Shape.centerOfMass(lcb).toTuple()], sleeve=(round(xs0, 2), round(xs1, 2)))
turret_vol = (math.pi * (30**2 - 18.25**2) * 6.5 + math.pi * (28.5**2 - 18.25**2) * 2.5)
res['turret_vol_mm3_approx'] = round(turret_vol, 0)

# ---- bosses
s1 = cylx(4.0, -12.7, -5.2 + 0.01, 0.0, 88.5)
corbel = cq.Workplane('XY').polyline([(-5.2, -4.0 - 7.5), (-12.7, -4.0), (-5.2, -4.0)]).close().extrude(8.0) \
    .translate((0, 0, 84.5)).val()
s1 = s1.fuse(corbel)
s2 = cq.Workplane('XY').box(8.0, 9.2, 8.0, centered=False).translate((-13.35, 23.5, 70.0)).val()
s3 = cq.Workplane('XY').box(8.0, 9.2, 8.0, centered=False).translate((-13.35, 23.5, 42.0)).val()
new = {'lcb': lcb, 's1_boss(tub)': s1, 's2_boss(panel)': s2, 's3_boss(panel)': s3, 'kowa_corrected': lens}

def ov(a, b):
    try:
        return round(a.intersect(b).Volume(), 3)
    except Exception as e:
        return 'err'
hits = {}
others = dict(parts); others.update({'cots:' + k: v for k, v in cot.items()})
for k, b in L.KEEPOUTS.items():
    others['ko:' + k] = dc.box_solid(b)
for nm, s in new.items():
    h = {}
    for on, o in others.items():
        if nm.startswith('s1') and on == 'tub': continue
        if nm.startswith(('s2', 's3')) and on == 'panel': continue
        v = ov(s, o)
        if v == 'err' or v > 0.05:
            h[on] = v
    hits[nm] = h
hits['lcb_vs_kowa_corrected'] = ov(lcb, lens)
res['overlaps'] = hits
# min distances that matter
res['dist'] = dict(lcb_kowa=round(lcb.distance(lens), 3), lcb_adapter=round(lcb.distance(cot['c_cs_adapter']), 3),
                   lcb_camera=round(lcb.distance(cot['gs_camera']), 3), s1_camera=round(s1.distance(cot['gs_camera']), 3),
                   s2_camera=round(s2.distance(cot['gs_camera']), 3), s3_camera=round(s3.distance(cot['gs_camera']), 3),
                   s1_hood=round(s1.distance(parts['hood']), 3), s3_tub=round(s3.distance(parts['tub']), 3),
                   s2_tub=round(s2.distance(parts['tub']), 3))
# camera_in sweep vs S1 boss: camera proxy at the path offsets
cam = cot['gs_camera']
sweep = []
for dy in range(60, -1, -2):
    sweep.append((-11.1, dy, 2.0))
for dz in (2.0, 1.0, 0.0):
    sweep.append((-11.1, 0.0, dz))
for dx in [-11.1 + 0.5 * k for k in range(23)]:
    sweep.append((dx, 0.0, 0.0))
worst = {}
for nm in ('s1_boss(tub)',):
    m = 0.0
    for d in sweep:
        v = ov(cam.translate(V(*d)), new[nm])
        if v != 'err':
            m = max(m, v)
    worst[nm] = m
res['camera_in_sweep_overlap'] = worst
# panel_on: panel bosses moving +Y offset 70..0 vs camera proxy and tub
pm = {}
for nm in ('s2_boss(panel)', 's3_boss(panel)'):
    m = {}
    for dy in range(70, -1, -2):
        for on in ('cots:gs_camera', 'tub', 'hood'):
            v = ov(new[nm].translate(V(0, dy, 0)), others[on])
            if v != 'err' and v > m.get(on, 0):
                m[on] = v
    pm[nm] = m
res['panel_on_sweep_overlap'] = pm
# hood drop (hood moves from +60 to 0 in z) vs S1 boss
hm = 0.0
for dz in range(60, -1, -2):
    v = ov(parts['hood'].translate(V(0, 0, dz)), s1)
    if v != 'err':
        hm = max(hm, v)
res['hood_drop_vs_s1'] = hm
json.dump(res, open(os.path.join(os.path.dirname(__file__), 'd3_probe_%s.json' % ('d2' if abs(XF - L.C_FLANGE_X) < 1e-6 else 'xf%.1f' % XF)), 'w'), indent=1)
print(json.dumps(res, indent=1))
