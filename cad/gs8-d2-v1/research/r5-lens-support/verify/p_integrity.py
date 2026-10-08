"""r5 integrity review: plant synthetic faults into the real r5 parts (out/step/parts) and confirm the new checks FAIL.
Read-only for the design: shapes are modified in memory; layout dicts are patched and restored. Run via run_locked.py."""
import copy
import json
import os
import sys
import time

D = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, D)
os.chdir(D)
import cadquery as cq          # noqa: E402
import layout as L             # noqa: E402
import checks as CK            # noqa: E402
import cots                    # noqa: E402

V = cq.Vector
T0 = time.time()
OUT = {}


def imp(p):
    w = cq.importers.importStep(os.path.join(D, 'out', 'step', 'parts', p + '.step'))
    s = w.val()
    return s


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cylx(r, x0, x1, y, z):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def st(rows):
    return [(r.get('mover') or r.get('item') or r.get('screw'), r.get('s', r.get('lens')), r['status'],
             (r.get('error') or r.get('warn') or '')[:150]) for r in rows]


def bad(rows):
    return [x for x in st(rows) if x[2] != 'pass']


base = {p: dict(shape=imp(p), kind='printed') for p in ('tub', 'hood', 'panel', 'lens_collar')}
OUT['bb'] = {p: [round(v, 2) for v in CK.bb_tuple(r['shape'])] for p, r in base.items()}
lens, _ = cots.lens_proxy(L, 'kowa_lm6hc')
base['lens'] = dict(shape=lens, kind='cots')
base['c_cs_adapter'] = dict(shape=cots.c_cs_adapter(L, None), kind='cots')
ly, lz = L.LENS_AXIS


def rows_with(**kw):
    r = {k: dict(v) for k, v in base.items()}
    for k, v in kw.items():
        r[k] = dict(r.get(k, {}), **v) if isinstance(v, dict) else dict(shape=v, kind='printed')
    return r


# ---------------------------------------------------------------- A. j7_float
A = {}
r0 = CK.check_j7_float(L, base)
A['baseline_bad'] = bad(r0)
A['baseline_min'] = {'%s@%s' % (r['mover'], r['s']): {k: (r.get(k) or {}).get('gap') for k in
                     ('min_overall', 'min_lateral', 'min_axial')} for r in r0 if r['mover'] in ('body', 'bfar', 'adapter')}
# A2 lateral: a hood bump 0.3 off the housing side (r 17.75) at x -12..-9
bump = box(-12.0, -9.0, ly - 17.75 - 0.3 - 0.5, ly - 17.75 - 0.3, lz - 1.0, lz + 1.0)
A['lateral_0.3'] = bad(CK.check_j7_float(L, rows_with(hood=base['hood']['shape'].fuse(bump))))
# A3 diagonal: a block ahead of and outside the BFAR head edge (dx 0.25, dy 0.25 -> 0.354 < floor 0.4)
diag = box(L.BFAR_FACE_X + 0.25, L.BFAR_FACE_X + 1.5, ly + 18.25, ly + 19.5, lz - 0.5, lz + 0.5)
A['diagonal_0.354'] = bad(CK.check_j7_float(L, rows_with(probe=diag)))
# A4 axial: the lip moved 0.2 back (a ring at x -4.2 inside the counterbore, r 16.2..18.5)
ring = cylx(18.5, L.BFAR_FACE_X + 0.2, L.CAM['lip_x'], ly, lz).cut(cylx(16.2, L.BFAR_FACE_X + 0.1, L.CAM['lip_x'] + 0.1, ly, lz))
A['axial_lip_0.2'] = bad(CK.check_j7_float(L, rows_with(tub=base['tub']['shape'].fuse(ring))))
# A5 stub masking: the hood fault with an unrelated obstacle (tub) flagged stub
A['stub_masks_hood_fault'] = bad(CK.check_j7_float(L, rows_with(hood=base['hood']['shape'].fuse(bump),
                                                                    tub=dict(stub=True))))
# A6 the lens hits the hood
A['lens_hits_hood'] = bad(CK.check_j7_float(L, rows_with(hood=base['hood']['shape'].fuse(
    box(20.0, 22.0, ly + 20.0, ly + 30.0, lz - 2, lz + 2)))))
OUT['A_j7_float'] = A
print('A done', round(time.time() - T0), flush=True)

# ---------------------------------------------------------------- B. lens_support (Kowa, real collar)
B = {}
col = base['lens_collar']['shape']
cs = L.collar_spec('kowa_lm6hc')


def ls(c=None, lens_shape=None):
    out = CK.check_lens_support(L, {}, collars={'kowa_lm6hc': c if c is not None else col},
                                lens_shapes={'kowa_lm6hc': lens_shape if lens_shape is not None else lens})
    return [x for x in st(out) if x[1] == 'kowa_lm6hc' and x[2] != 'pass']


B['baseline_kowa_nonpass'] = ls()
big = cylx(cs['bore_r'] + 0.15, cs['cone_x1'] + 0.3, cs['front_x'] + 0.1, ly, lz)
B['bore_+0.3_diametral'] = ls(col.cut(big))
B['collar_+0.3x'] = ls(col.translate(V(0.3, 0, 0)))
B['collar_-0.3x'] = ls(col.translate(V(-0.3, 0, 0)))
B['thumb_ko_bump'] = ls(col.fuse(box(14.0, 15.5, ly + 20.0, ly + 23.0, lz - 1, lz + 1)))
seg = copy.deepcopy(L.LENSES['kowa_lm6hc']['segments'])
try:
    L.LENSES['kowa_lm6hc']['segments'] = [tuple(s[:4]) + (('rot',) if 'knurl' in str(s[3]).lower() or
                                          (abs(s[1] - 2.2) < 0.01) else (s[4],)) for s in seg]
    B['band_made_moving'] = ls()
finally:
    L.LENSES['kowa_lm6hc']['segments'] = seg
OUT['B_lens_support'] = B
print('B done', round(time.time() - T0), flush=True)

# ---------------------------------------------------------------- C. lens_clamp
C = {}
k = dict(L.LENSES['kowa_lm6hc'], name='synthetic 1.5 kg', mass=1500.0)
L.LENSES_DATA_ONLY['_t_heavy'] = k
try:
    C['heavy_1500g'] = [x for x in st(CK.check_lens_clamp(L, {}, collars={})) if x[1] == '_t_heavy']
finally:
    del L.LENSES_DATA_ONLY['_t_heavy']
p = L.LOAD_MODEL['pinch_N']
try:
    L.LOAD_MODEL['pinch_N'] = 20.0
    C['pinch_20N'] = [x for x in st(CK.check_lens_clamp(L, {}, collars={})) if x[1] == 'kowa_lm6hc']
finally:
    L.LOAD_MODEL['pinch_N'] = p
OUT['C_lens_clamp'] = C
print('C done', round(time.time() - T0), flush=True)

# ---------------------------------------------------------------- D. inserts (real tub + collar)
Dd = {}
s1 = next(s for s in L.SCREWS if s['id'] == 's_c1')
y1, z1 = s1['head_point'][1], s1['head_point'][2]


def ins(**kw):
    return [x for x in st(CK.check_inserts(L, rows_with(**kw)))]


Dd['baseline'] = ins()
tub = base['tub']['shape']
Dd['bore_4.4'] = [x for x in ins(tub=tub.cut(cylx(2.2, -6.8, -2.6, y1, z1))) if x[0] == 's_c1']
Dd['wall_1.2'] = [x for x in ins(tub=tub.cut(box(-7.7, -5.25, y1 + 3.2, y1 + 6.0, z1 - 4, z1 + 4))) if x[0] == 's_c1']
Dd['tip_bottoms'] = [x for x in ins(tub=tub.fuse(cylx(1.7, -7.6, -6.85, y1, z1))) if x[0] == 's_c1']
Dd['bore_shallow_3.7'] = [x for x in ins(tub=tub.fuse(cylx(2.0, -6.95, -6.4, y1, z1))) if x[0] == 's_c1']
hole = cylx(1.7, 0.0, 3.0, y1, z1).cut(cylx(1.45, -0.1, 3.1, y1, z1))
Dd['collar_hole_r1.45'] = [x for x in ins(lens_collar=col.fuse(hole)) if x[0] == 's_c1']
OUT['D_inserts'] = Dd
print('D done', round(time.time() - T0), flush=True)

OUT['seconds'] = round(time.time() - T0)
json.dump(OUT, open(os.path.join(os.path.dirname(__file__), 'p_integrity.json'), 'w'), indent=1, default=str)
for k_, v_ in OUT.items():
    print(k_, json.dumps(v_, default=str)[:1500])
