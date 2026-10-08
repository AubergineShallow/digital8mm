# judge 3 read-only probe: pi_in sweep vs proposed tub bosses (d3 boss_l1+corbel, d1 nut bosses)
import os, sys, json
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L, cots, d2_common as dc
V = cq.Vector; B = L.B
C = cots.build_all(L, only={'pi5', 'cooler', 'x1203', 'x1203_kit'})
stack = None
for k, r in C.items():
    s = r['shape'].val()
    stack = s if stack is None else stack.fuse(s)
    bb = s.BoundingBox(); print(k, [round(a, 2) for a in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
def cylx(r, x0, x1, y, z):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))
# design 3 boss_l1: dia 8 along X at (0, 88.5), x -13.85..-5.2 + corbel triangle (xy) z 84.5..92.5
b3 = cylx(4.0, -13.85, -5.2, 0.0, 88.5)
cor = (cq.Workplane('XY').workplane(offset=84.5).polyline([(-5.2, -12.65), (-13.85, -4.0), (-5.2, -4.0)]).close()
       .extrude(8.0).val())
b3 = b3.fuse(cor)
# design 1 nut bosses OD 8.8 x -7.6..-5.2
b1 = None
for (y, z) in [(11.0, 90.5), (-11.0, 90.5), (24.5, 36.0)]:
    c = cylx(4.0, -7.6, -5.2, y, z); b1 = c if b1 is None else b1.fuse(c)
path = L.INSERTIONS[1]['path']; assert L.INSERTIONS[1]['id'] == 'pi_in'
def pts(path, step=2.0):
    out = []
    for a, b in zip(path[:-1], path[1:]):
        d = [b[i] - a[i] for i in range(3)]; n = max(1, int(max(abs(x) for x in d) / step))
        for k in range(n):
            out.append(tuple(a[i] + d[i] * k / n for i in range(3)))
    out.append(path[-1]); return out
res = {}
for nm, s in (('d3_boss_l1', b3), ('j3_insert_bosses', b1)):
    worst = (0, None)
    for p in pts(path):
        v = stack.translate(V(*p)).intersect(s).Volume()
        if v > worst[0]: worst = (v, p)
    res[nm] = dict(max_mm3=round(worst[0], 2), at=worst[1])
print(json.dumps(res))
json.dump(res, open(os.path.join(os.path.dirname(__file__), 'p_pidrop_j3.json'), 'w'))
