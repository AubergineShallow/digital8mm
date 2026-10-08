import os, sys
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq, layout as L, d2_common as dc
B = L.B
hood = cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', 'hood.step')).val()
def q(nm, b):
    s = hood.intersect(dc.box_solid(b)); v = s.Volume()
    if v < 0.01: print(nm, 0); return
    bb = s.BoundingBox(); print(nm, round(v, 1), [round(a, 2) for a in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
q('wide', B(-40, -6.3, 16, 35, 84, 97.3))
q('lowest_z_band', B(-40, -6.3, 0, 35, 84, 97.3))
for x0 in (-40, -30, -20, -12):
    q('x%d' % x0, B(x0, x0 + 8 if x0 < -12 else -6.3, 16, 35, 84, 97.3))
print([(h['id'], round(h.get('x', 0), 2), round(h.get('y', 0), 2)) for h in L.HOOD_HOOKS])
