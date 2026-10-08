# r5 step 1 (geometry) probe, 2026-10-06. Run through the lock from the repo root:
#   .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/research/r5-lens-support/probes/r5s1/p_geom.py
# Builds tub, hood, panel, the lens collars and the COTS proxies from the current layout and writes p_geom.json:
#  1. the 3 tub insert bosses (standalone) vs the pi_in sweep (real pi5/cooler/x1203/x1203_kit proxies, 2 mm steps +
#     1.0/0.5 before final, judge 3 p_pidrop_j3 method), vs the 4 Pi COTS boxes, vs the hood_on and camera_in sweeps;
#  2. hood foot-hole rings (point-in-solid rays in the plate at x -0.1 / -1.25 / -2.4, 72 directions);
#  3. collar vs the lens thumb-screw keep-outs; 4. camera float gaps at s 0 / nom / max (body, bfar) and the adapter
#     and lens against every printed part and the Pi COTS; 5. the C flange stack (BFAR face + 5.0) and the cone seat.
import json
import math
import os
import sys
import time

D2 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, D2)
import cadquery as cq  # noqa: E402
import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402
import cots  # noqa: E402
import printed_tub as PT  # noqa: E402
import printed_hood as PH  # noqa: E402
import printed_panel as PP  # noqa: E402
import printed_collar as PC  # noqa: E402

V = cq.Vector
t0 = time.time()
res = dict(revision='r5 step 1', s=dict(nom=L.CAM['s_nom'], range=L.CAM['s_range']))


def vol(a, b):
    try:
        return round(a.intersect(b).Volume(), 3)
    except Exception as e:  # noqa: BLE001
        return 'err %s' % e


def dist(a, b):
    try:
        return round(a.distance(b), 3)
    except Exception as e:  # noqa: BLE001
        return 'err %s' % e


def pts(path, step=2.0):
    out = []
    for a, b in zip(path[:-1], path[1:]):
        n = max(1, int(math.ceil(math.dist(a, b) / step)))
        out += [tuple(a[i] + (b[i] - a[i]) * k / n for i in range(3)) for k in range(n)]
    last, d = path[-2], math.dist(path[-2], path[-1])
    out += [tuple(path[-1][i] + (last[i] - path[-1][i]) * e / d for i in range(3)) for e in (1.0, 0.5) if d > e]
    return out


def sweep(moving, path, target):
    worst = (0.0, None)
    for p in pts(path):
        v = moving.translate(V(*p)).intersect(target).Volume()
        if v > worst[0]:
            worst = (round(v, 3), [round(x, 2) for x in p])
    return dict(max_mm3=worst[0], at=worst[1])


ins = {i['id']: i for i in L.INSERTIONS}
# ---------------------------------------------------------------- 1. insert bosses
bosses = {k: PT._insert_boss(L, b)[0] for k, b in L.TUB_INSERT_BOSSES.items()}
boss_all = dc.fuse_all(list(bosses.values()))
C = cots.build_all(L, only={'pi5', 'cooler', 'x1203', 'x1203_kit', 'c_cs_adapter', 'lens'})
stack = dc.fuse_all([C[k]['shape'].val() for k in ('pi5', 'cooler', 'x1203', 'x1203_kit')])
r1 = dict(pi_in_sweep=sweep(stack, ins['pi_in']['path'], boss_all),
          cots_boxes={k: {b: vol(s, dc.box_solid(L.COTS[k]['box'])) for b, s in bosses.items()}
                      for k in ('pi5', 'cooler', 'x1203', 'x1203_kit')},
          cots_box_gap={k: {b: dist(s, dc.box_solid(L.COTS[k]['box'])) for b, s in bosses.items()}
                        for k in ('pi5', 'cooler', 'x1203', 'x1203_kit')})
print('bosses', json.dumps(r1), round(time.time() - t0, 1), flush=True)
hood = PH.build_part(L, 'hood').val()
r1['hood_on_sweep'] = sweep(hood, ins['hood_on']['path'], boss_all)
r1['hood_gap_final'] = dist(hood, boss_all)
camp = {s: cots.gs_camera_parts(L, s) for s in (0.0, L.CAM['s_nom'], L.CAM['s_range'][1])}
adapter = C['c_cs_adapter']['shape'].val()
r1['camera_in_sweep'] = {str(s): sweep(dc.fuse_all([p['body'], p['bfar'], adapter]), ins['camera_in']['path'], boss_all)
                         for s, p in camp.items()}
res['insert_bosses'] = r1
print('bosses+', json.dumps(r1), round(time.time() - t0, 1), flush=True)
# ---------------------------------------------------------------- 2. hood foot-hole rings
xs = (-0.1, -1.25, -2.4)


def ring(y0, z0, r0):
    best = (99.0, None)
    loc = hood.intersect(dc.box_solid(L.B(-2.7, 0.2, y0 - 14.0, y0 + 14.0, z0 - 14.0, z0 + 14.0)))
    for x in xs:
        for k in range(48):
            a = 2 * math.pi * k / 48
            dy, dz = math.cos(a), math.sin(a)
            t, inside, start = r0 - 0.6, False, None
            while t < r0 + 8.0:
                p = V(x, y0 + dy * t, z0 + dz * t)
                isin = loc.isInside(p, 1e-4)
                if isin and not inside:
                    inside, start = True, t
                elif inside and not isin:
                    w = t - start
                    if w < best[0]:
                        best = (round(w, 2), [round(x, 2), round(math.degrees(a)), round(start, 2)])
                    break
                t += 0.05
    return best


res['hood_hole_rings'] = {k: dict(zip(('min_mm', 'at_x_deg_r'), ring(y, z, L.HOOD['foot_holes']['d'] / 2)))
                          for k, (y, z) in L.COLLAR['feet'].items()}
print('rings', res['hood_hole_rings'], round(time.time() - t0, 1), flush=True)
# ---------------------------------------------------------------- 3/4/5. collar, camera float, stack
tub = PT.build_part(L, 'tub').val()
panel = PP.build_part(L, 'panel').val()
printed = dict(tub=tub, hood=hood, panel=panel)
for n in L.LENSES:
    printed['collar_' + n] = PC.build_part(L, 'lens_collar', lens=n).val()
res['collar_vs_thumb_keepouts'] = {k: dict(overlap=vol(printed['collar_kowa_lm6hc'], dc.box_solid(b)),
                                           gap=dist(printed['collar_kowa_lm6hc'], dc.box_solid(b)))
                                   for k, b in L.KEEPOUTS.items() if k.startswith('ko_lens_thumb')}
others = dict(printed, pi5=C['pi5']['shape'].val(), cooler=C['cooler']['shape'].val())
fl = {}
for s, p in camp.items():
    row = {}
    for part in ('body', 'bfar'):
        row[part] = {k: dict(ov=vol(p[part], o), gap=dist(p[part], o)) for k, o in others.items()
                     if not k.startswith('collar_fujinon')}
    fl[str(s)] = row
res['camera_float'] = fl
lens = {n: cots.lens_proxy(L, n)[0] for n in L.LENSES}
res['adapter'] = {k: dict(ov=vol(adapter, o), gap=dist(adapter, o)) for k, o in others.items()}
res['lens'] = {n: {k: dict(ov=vol(lens[n], o), gap=dist(lens[n], o)) for k, o in others.items()
                   if not (k.startswith('collar_') and k != 'collar_' + n)} for n in L.LENSES}
res['lens_vs_camera_nom'] = {n: dict(ov=vol(lens[n], dc.fuse_all([camp[L.CAM['s_nom']]['body'],
                                                                   camp[L.CAM['s_nom']]['bfar']])))
                             for n in L.LENSES}
abb = adapter.BoundingBox()
res['stack'] = dict(bfar_face=L.BFAR_FACE_X, adapter_x=[round(abb.xmin, 3), round(abb.xmax, 3)],
                    c_flange=L.C_FLANGE_X, c_minus_bfar=round(L.C_FLANGE_X - L.BFAR_FACE_X, 3),
                    collars={n: L.collar_spec(n) for n in L.LENSES})
res['seconds'] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p_geom.json'), 'w', encoding='utf-8',
          newline='\n') as f:
    json.dump(res, f, indent=1)
for k in ('camera_float', 'adapter', 'lens', 'lens_vs_camera_nom', 'collar_vs_thumb_keepouts', 'stack'):
    print(k, json.dumps(res[k]))
print('total', res['seconds'])
