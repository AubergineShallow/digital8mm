# read-only probe: load release STEP parts (assembly frame?) and COTS proxies; measure J7 surroundings
import os, sys, json, math
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L
import cots
V = cq.Vector
parts = {}
for p in ('tub', 'hood', 'panel', 'base_grip', 'pi_keeper', 'plunger'):
    s = cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', p + '.step')).val()
    parts[p] = s
    bb = s.BoundingBox()
    print(p, 'bbox', [round(v, 2) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)], 'vol', round(s.Volume(), 0))
C = cots.build_all(L, only={'gs_camera', 'c_cs_adapter', 'lens', 'pi5', 'cooler', 'microsd'})
for k, r in C.items():
    bb = r['shape'].val().BoundingBox()
    print('cots', k, [round(v, 2) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
cam = C['gs_camera']['shape'].val()
ring = cq.Solid.makeCylinder(18.0, 5.8, V(-5.2, 0, 60), V(1, 0, 0))
# radial gap ring -> tub / hood in 8 directions: translate ring until contact (coarse 0.01)
def first_contact(sol, part, d, tmax=2.0, step=0.01):
    t = 0.0
    while t <= tmax:
        m = sol.translate(V(*(c * t for c in d)))
        try:
            v = m.intersect(part).Volume()
        except Exception:
            v = 0
        if v > 1e-4:
            return round(t, 2)
        t += step
    return None
res = {}
for nm, d in (('+Y', (0, 1, 0)), ('-Y', (0, -1, 0)), ('+Z', (0, 0, 1)), ('-Z', (0, 0, -1)),
              ('-Y-Z', (0, -0.7071, -0.7071)), ('+Y-Z', (0, 0.7071, -0.7071))):
    res[nm] = dict(tub=first_contact(ring, parts['tub'], d), hood=first_contact(ring, parts['hood'], d))
print('ring first contact (mm) by direction', json.dumps(res))
print('ring-tub dist', round(ring.distance(parts['tub']), 3), 'ring-hood dist', round(ring.distance(parts['hood']), 3))
print('cam-tub dist', round(cam.distance(parts['tub']), 3), 'cam-hood', round(cam.distance(parts['hood']), 3),
      'cam-panel', round(cam.distance(parts['panel']), 3))
ad = C['c_cs_adapter']['shape'].val(); ln = C['lens']['shape'].val()
print('adapter-hood', round(ad.distance(parts['hood']), 3), 'lens-hood', round(ln.distance(parts['hood']), 3))
