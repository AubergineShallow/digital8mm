# judge 3: insert bosses + hood hole ligaments vs the release hood STEP (final + hood_on drop), read-only
import os, sys, json
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L
V = cq.Vector
hood = cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', 'hood.step')).val()
def cylx(r, x0, x1, y, z):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))
b = None
for (y, z) in [(11.0, 90.5), (-11.0, 90.5), (24.5, 36.0)]:
    c = cylx(4.0, -7.6, -5.2, y, z); b = c if b is None else b.fuse(c)
worst = 0.0
for k in range(0, 31):
    v = hood.translate(V(0, 0, 60 - 2 * k)).intersect(b).Volume(); worst = max(worst, v)
res = dict(hood_drop_max_mm3=round(worst, 3), final_gap=round(hood.distance(b), 3))
# hood plate material left round 4 holes dia 8.6 (x -2.5..0): min distance hole surface -> plate boundary features
holes = {'TL': (11.0, 90.5), 'TR': (-11.0, 90.5), 'LL': (24.5, 36.0), 'LR': (-19.0, 44.0)}
for k, (y, z) in holes.items():
    h = cylx(4.3, -2.6, 0.1, y, z)
    plate = hood.intersect(cq.Solid.makeBox(2.5, 70, 100, V(-2.5, -35, 0.3)))
    rest = plate.cut(h)
    # ligament proxy: volume of plate inside a ring r 4.3..5.5 round the hole (full ring = 2.5*pi*(5.5^2-4.3^2))
    ring = cylx(5.5, -2.5, 0.0, y, z).cut(cylx(4.3, -2.6, 0.1, y, z))
    full = ring.Volume(); have = rest.intersect(ring).Volume()
    res['ring1.2_%s' % k] = round(have / full, 3)
print(json.dumps(res))
json.dump(res, open(os.path.join(os.path.dirname(__file__), 'p_hood.json'), 'w'))
