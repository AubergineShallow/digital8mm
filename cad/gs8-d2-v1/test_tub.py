# SPDX-License-Identifier: MIT
"""Stand-alone check of printed_tub.py (run through run_locked.py). Writes out/test_tub.json."""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402
import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402
import printed_tub as T  # noqa: E402

t0 = time.time()
wp = T.build(L)['tub']
s = wp.val()
tb = time.time() - t0
bb = s.BoundingBox()
env = L.PARTS['tub']['envelope']
vol = s.Volume()
res = dict(valid=s.isValid(), n_solids=len(wp.solids().vals()), volume_mm3=round(vol, 1),
           mass_g=round(L.mass_g(vol, 'tub'), 1), mass_100pct_g=round(vol * L.FDM['ASA_DENSITY'], 1),
           bbox=[round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)], build_s=round(tb, 1))
res['in_envelope'] = (bb.xmin >= env['x'][0] - 1e-3 and bb.xmax <= env['x'][1] + 1e-3 and bb.ymin >= env['y'][0] - 1e-3
                      and bb.ymax <= env['y'][1] + 1e-3 and bb.zmin >= env['z'][0] - 1e-3 and bb.zmax <= env['z'][1] + 1e-3)
pp = dc.to_print_pose(s, T.PRINT['tub']['face_down']).BoundingBox()
res['print_bbox'] = [round(pp.xlen, 2), round(pp.ylen, 2), round(pp.zlen, 2)]
res['beds'] = {k: (sorted([pp.xlen, pp.ylen])[1] <= max(v[:2]) and min(pp.xlen, pp.ylen) <= min(v[:2]) and pp.zlen <= v[2])
               for k, v in L.PRINT_BEDS.items()}


def ov(box):
    try:
        return round(s.intersect(dc.box_solid(box)).Volume(), 3)
    except Exception as e:  # noqa: BLE001
        return 'err %s' % e


res['keepouts'] = {k: ov(b) for k, b in L.KEEPOUTS.items()}
res['keepouts'] = {k: v for k, v in res['keepouts'].items() if v != 0}
mates = {frozenset((a, b)) for a, b, _ in L.MATES}
res['cots_box_overlaps'] = {}
for cid, c in L.COTS.items():
    if c.get('box') and frozenset(('tub', cid)) not in mates:
        v = ov(c['box'])
        if v:
            res['cots_box_overlaps'][cid] = v
res['pi_hooks'] = 'deleted (R1 r2): removable pi_keeper on s_k1/s_k2, see printed_keeper.py'
res['keeper_bosses'] = {k: dict(c=b['c'], r=b['r'], top=L.PI_KEEPER['boss_top']) for k, b in L.PI_KEEPER['bosses'].items()}
# ---- r5 step 1 (J7-R): lip + BFAR counterbore (radii, x), no pins, 3 M3 insert bosses: 0 mm3 against the pi_in sweep
#      (real pi5/cooler/x1203/x1203_kit proxies), the 4 Pi COTS boxes, the hood_on sweep and the camera_in sweep at
#      s 0 / nominal / max; insert bore dia, depth (insert + 0.2) and wall (>= 1.6). Each row has ok; exit 1 on a fail.
import math  # noqa: E402
import cots  # noqa: E402
import printed_hood as PH  # noqa: E402
V = cq.Vector
C, ly, lz = L.CAM, L.LENS_AXIS[0], L.LENS_AXIS[1]
loc = s.intersect(dc.box_solid(L.B(-8.2, -2.0, -36.0, 36.0, 20.0, 100.0)))      # front wall zone (fast point tests)


def inside(p):
    return loc.isInside(V(*p), 1e-4)


def first_hit(p0, d, t0, t1, want=True, step=0.01):
    """First t in [t0, t1] where p0 + t d is inside (want) / outside (not want) the tub."""
    t = t0
    while t <= t1 + 1e-9:
        if inside(tuple(p0[i] + d[i] * t for i in range(3))) == want:
            return round(t, 3)
        t += step
    return None


r5 = {}
dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in (60, 90, 135, 180, 225, 270, 315)]  # not the +Y roof
for nm, x, r_exp in (('lip', -3.3, C['lip_d'] / 2), ('counterbore', -4.6, C['cb_d'] / 2)):
    rs = [first_hit((x, ly, lz), (0, dy, dz), r_exp - 0.6, r_exp + 0.6) for dy, dz in dirs]
    r5['%s_radius' % nm] = dict(measured=rs, expected=r_exp, ok=all(v is not None and abs(v - r_exp) <= 0.03 for v in rs))
xl = first_hit((-2.0, ly, lz - 17.5), (-1, 0, 0), 0.0, 3.0)                  # outer face
xr = first_hit((-2.0 - xl, ly, lz - 17.5), (-1, 0, 0), 0.0, 3.0, want=False)  # lip rear face
r5['lip_land'] = dict(x=(round(-2.0 - xl, 3), round(-2.0 - xl - xr, 3)), expected=(L.XT1, C['lip_x']),
                      land=round(xr, 3), ok=abs(-2.0 - xl - L.XT1) <= 0.02 and abs(-2.0 - xl - xr - C['lip_x']) <= 0.02)
r5['bfar_face_to_lip'] = dict(gap=round(C['lip_x'] - L.BFAR_FACE_X, 3), ok=C['lip_x'] - L.BFAR_FACE_X >= 0.4)
r5['no_pins'] = dict(points=[(-6.5, -15.0, 75.0), (-6.5, 15.0, 45.0), (-7.9, -15.0, 75.0), (-7.9, 15.0, 45.0)],
                     ok=not any(inside(p) for p in [(-6.5, -15.0, 75.0), (-6.5, 15.0, 45.0), (-7.9, -15.0, 75.0),
                                                    (-7.9, 15.0, 45.0)]))
bm = {}
for k, b in L.TUB_INSERT_BOSSES.items():
    (y, z), ins = b['c'], L.M3['insert']
    bd = [first_hit((-4.5, y, z), (0, dy, dz), 1.5, 2.5) for dy, dz in dirs + [(1.0, 0.0)]]
    depth = first_hit((L.XT1 + 0.3, y + 1.85, z), (-1, 0, 0), 0.0, 6.0)
    walls = []
    for dy, dz in [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 30)]:
        t1 = first_hit((-6.5, y, z), (0, dy, dz), 2.01, 9.0, want=False, step=0.02)
        walls.append(None if t1 is None else round(t1 - ins['bore_d'] / 2, 2))
    clear = first_hit((-7.3, y, z), (0, 0, 1), 0.0, 3.0)
    wmin = min(w for w in walls if w is not None)
    bm[k] = dict(bore_r=bd, depth_from_face=None if depth is None else round(depth - 0.3, 3), walls=walls, wall_min=wmin,
                 clear_r_at_x7_3=clear,
                 ok=(all(v is not None and abs(v - ins['bore_d'] / 2) <= 0.03 for v in bd) and depth is not None and
                     depth - 0.3 >= ins['length'] + 0.2 - 0.02 and wmin >= 1.6 - 0.02 and clear is not None and
                     abs(clear - L.M3['clear_d'] / 2) <= 0.03))
r5['insert_bosses'] = bm
bosses = {k: T._insert_boss(L, b)[0] for k, b in L.TUB_INSERT_BOSSES.items()}
boss_all = dc.fuse_all(list(bosses.values()))


def path_pts(path, step=2.0):
    out = []
    for a, b in zip(path[:-1], path[1:]):
        n = max(1, int(math.ceil(math.dist(a, b) / step)))
        out += [tuple(a[i] + (b[i] - a[i]) * j / n for i in range(3)) for j in range(n)]
    last, dd = path[-2], math.dist(path[-2], path[-1])
    return out + [tuple(path[-1][i] + (last[i] - path[-1][i]) * e / dd for i in range(3)) for e in (1.0, 0.5) if dd > e]


def sweep_max(mv, path):
    return round(max(mv.translate(V(*p)).intersect(boss_all).Volume() for p in path_pts(path)), 3)


INS = {i['id']: i for i in L.INSERTIONS}
CB = cots.build_all(L, only={'pi5', 'cooler', 'x1203', 'x1203_kit', 'c_cs_adapter'})
stack = dc.fuse_all([CB[k]['shape'].val() for k in ('pi5', 'cooler', 'x1203', 'x1203_kit')])
r5['bosses_vs_pi_in_sweep_mm3'] = sweep_max(stack, INS['pi_in']['path'])
r5['bosses_vs_pi_cots_boxes_mm3'] = {k: round(boss_all.intersect(dc.box_solid(L.COTS[k]['box'])).Volume(), 3)
                                     for k in ('pi5', 'cooler', 'x1203', 'x1203_kit')}
r5['ll_to_pi5_box_mm'] = round(bosses['LL'].distance(dc.box_solid(L.COTS['pi5']['box'])), 3)
hood = PH.build_part(L, 'hood').val()
r5['bosses_vs_hood_on_sweep_mm3'] = sweep_max(hood, INS['hood_on']['path'])
r5['bosses_to_hood_final_mm'] = round(hood.distance(boss_all), 3)
cam = {}
for sv in (0.0, L.CAM['s_nom'], L.CAM['s_range'][1]):
    p = cots.gs_camera_parts(L, sv)
    cam[str(sv)] = sweep_max(dc.fuse_all([p['body'], p['bfar'], CB['c_cs_adapter']['shape'].val()]), INS['camera_in']['path'])
r5['bosses_vs_camera_in_sweep_mm3'] = cam
r5['sweeps_ok'] = (r5['bosses_vs_pi_in_sweep_mm3'] == 0 and not any(r5['bosses_vs_pi_cots_boxes_mm3'].values()) and
                   r5['bosses_vs_hood_on_sweep_mm3'] == 0 and not any(cam.values()) and r5['ll_to_pi5_box_mm'] >= 0.25)
r5['ok'] = all(v.get('ok', True) for v in r5.values() if isinstance(v, dict) and 'ok' in v) and \
    all(v['ok'] for v in bm.values()) and r5['sweeps_ok']
res['r5'] = r5
res['notes'] = dc.NOTES
with open(os.path.join(HERE, 'out', 'test_tub.json'), 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
print('R5 TUB', 'PASS' if r5['ok'] else 'FAIL')
if '--stl' in sys.argv:
    cq.exporters.export(cq.Workplane().add(dc.to_print_pose(s, '-Y')), os.path.join(HERE, 'out', 'tub_test.stl'))
sys.exit(0 if res['r5']['ok'] else 1)   # r5: exit 1 on an r5 geometry fail
