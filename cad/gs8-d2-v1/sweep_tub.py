# SPDX-License-Identifier: MIT
"""Insertion sweep screen against the tub alone (proxy boxes/cylinders from layout; run through run_locked.py).
Prints the worst overlap (mm3) per insertion; writes out/sweep_tub.json. Snap hooks are expected to show the
tooth overlap on 'pi_in' (they deflect)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402
import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402
import printed_tub as T  # noqa: E402

tub = T.build(L)['tub'].val()
import cots  # noqa: E402
C = L.CAM
_cp = cots.gs_camera_parts(L)       # r5 (J7-R): the real GS stack at s nom + the C-CS adapter (it rides with the camera)
cam = [_cp['body'], _cp['bfar'], cots.c_cs_adapter(L, None)]
E = L.EVF
sets = {
    'camera_in': (cam, [(-11.1, 60.0, 2.0), (-11.1, 0, 2.0), (-11.1, 0, 0), (0, 0, 0)]),
    'camera_slide_only': (cam, [(-11.1, 60.0, 2.0), (-11.1, 0, 2.0), (-11.1, 0, 0)]),
    'panel_on': ([dc.box_solid(b) for b in list(L.PANEL_BOSSES.values()) + list(L.PANEL_POSTS.values())
                  + L.PANEL_LOCATE_RIBS + [E['cap'], C['keeper'], L.PANEL_TONGUE]], [(0, 70.0, 0), (0, 0, 0)]),
    'board_in': ([dc.box_solid(L.B(*E['board_pcb_x'], *E['board']['y'], *E['board']['z']))], [(0, 45.0, 0), (0, 0, 0)]),
    'oled_in': ([dc.box_solid(E['oled'])], [(0, 40.0, 0), (0, 0, 0)]),
    'pi_in': ([dc.box_solid(L.COTS['x1203']['features']['pcb']), dc.box_solid(L.COTS['pi5']['features']['pcb'])],
              [(0, 0, 45.0), (0, 0, 0)]),
    'pi_in_proposed': ([dc.box_solid(L.COTS[k]['box']) for k in ('x1203', 'pi5', 'cooler', 'x1203_kit')],
                       [(-2.8, 2.1, 80.0), (-2.8, 2.1, 40.0), (-2.8, 0, 40.0), (-2.8, 0, 5.0), (0, 0, 5.0), (0, 0, 0)]),
    'pi_in_layout_boxes': ([dc.box_solid(L.COTS[k]['box']) for k in ('x1203', 'pi5', 'cooler', 'x1203_kit')],
                           [(0, 0, 80.0), (0, 0, 0)]),
    'eyepiece_in': ([dc.cyl_solid(E['spigot']), dc.cyl_solid(E['barrel'])], [(-30.0, 0, 0), (0, 0, 0)]),
    'stick_in': ([dc.box_solid(L.STICK['body']), dc.box_solid(L.STICK['plug'])], [(-70.0, 0, 0), (0, 0, 0)]),
}


def samples(path, step=1.0):
    out = []
    for a, b in zip(path[:-1], path[1:]):
        n = max(1, int(max(abs(b[i] - a[i]) for i in range(3)) / step))
        out += [tuple(a[i] + (b[i] - a[i]) * k / n for i in range(3)) for k in range(n)]
    return out + [path[-1]]


res = {}
only = [a for a in sys.argv[1:] if not a.startswith('-')]
for k, (shapes, path) in sets.items():
    if only and k not in only:
        continue
    worst, at, final, pre, pre_at = 0.0, None, 0.0, 0.0, None
    n_pre = len(samples(path[:-1])) - 1 if len(path) > 2 else 0      # positions before the last segment
    for j, d in enumerate(samples(path)):
        v = 0.0
        for s in shapes:
            try:
                v += tub.intersect(s.translate(cq.Vector(*d))).Volume()
            except Exception:  # noqa: BLE001
                v += -1
        if v > worst:
            worst, at = v, d
        if j < n_pre and v > pre:
            pre, pre_at = v, d
        final = v
    res[k] = dict(worst_mm3=round(worst, 3), at=[round(x, 2) for x in at] if at else None, final_mm3=round(final, 3),
                  worst_before_last_segment_mm3=round(pre, 3), pre_at=[round(x, 2) for x in pre_at] if pre_at else None)
    print(k, res[k])
with open(os.path.join(HERE, 'out', 'sweep_tub.json'), 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=1)
