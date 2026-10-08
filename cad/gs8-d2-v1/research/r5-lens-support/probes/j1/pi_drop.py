"""Judge 1 probe: sweep the Pi stack along INSERTIONS pi_in against the proposed tub-front-wall features of D1/D2/D3."""
import sys, json
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L
import cots
V = cq.Vector
C = cots.build_all(L, only={'x1203', 'x1203_kit', 'pi5', 'cooler'})
stack = None
for k, r in C.items():
    s = r['shape'].val()
    stack = s if stack is None else stack.fuse(s)
bb = stack.BoundingBox()
print('stack bbox', round(bb.xmin,2), round(bb.xmax,2), round(bb.ymin,2), round(bb.ymax,2), round(bb.zmin,2), round(bb.zmax,2))
def cylx(r, x0, x1, y, z):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))
feat = {}
b = cylx(4.0, -13.85, -5.2, 0.0, 88.5)
cor = cq.Workplane('XY', origin=(0, 0, 84.5)).polyline([(-5.2, -12.65), (-13.85, -4.0), (-5.2, -4.0)]).close().extrude(8.0).val()
feat['D3_boss_l1+corbel'] = b.fuse(cor)
feat['D1_TL'] = cylx(4.4, -7.6, -5.2, 11.0, 92.0)
feat['D1_TR'] = cylx(4.4, -7.6, -5.2, -11.0, 92.0)
feat['D1_LL'] = cylx(4.4, -7.6, -5.2, 24.5, 36.0)
feat['D2_pin_l'] = cylx(0.95, -8.2, -5.2, 16.5, 46.0)
feat['D2_pin_r'] = cylx(0.95, -8.2, -5.2, -16.5, 46.0)
path = [(-2.8, 2.1, 80.0), (-2.8, 2.1, 40.0), (-2.8, 0, 40.0), (-2.8, 0, 5.0), (0, 0, 5.0), (0, 0, 0)]
pts = []
for (a, b2) in zip(path[:-1], path[1:]):
    d = [b2[i] - a[i] for i in range(3)]
    n = max(1, int(max(abs(x) for x in d) / 2.0))
    for i in range(n):
        pts.append(tuple(a[j] + d[j] * i / n for j in range(3)))
pts.append(path[-1])
res = {}
for name, f in feat.items():
    worst = (0.0, None)
    fb = f.BoundingBox()
    for p in pts:
        s = stack.moved(cq.Location(V(*p)))
        sb = s.BoundingBox()
        if sb.xmax < fb.xmin or sb.xmin > fb.xmax or sb.ymax < fb.ymin or sb.ymin > fb.ymax or sb.zmax < fb.zmin or sb.zmin > fb.zmax:
            continue
        v = s.intersect(f).Volume()
        if v > worst[0]:
            worst = (round(v, 2), p)
    res[name] = worst
print(json.dumps(res, indent=1))
