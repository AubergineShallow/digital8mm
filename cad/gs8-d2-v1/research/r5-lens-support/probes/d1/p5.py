import os, sys
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq, layout as L, d2_common as dc
V = cq.Vector
hood = cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', 'hood.step')).val()
def cylx(y, z, r, x0, x1): return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))
for nm, (y, z) in dict(TL=(11.5, 91.5), TR=(-11.5, 91.5), LL=(24.5, 36.0)).items():
    b = cylx(y, z, 4.4, -7.6, -5.2)
    worst = 0; at = None
    for i in range(0, 61):
        v = hood.translate(V(0, 0, float(i))).intersect(b).Volume()
        if v > worst: worst, at = v, i
    print('hood_on sweep vs boss', nm, 'worst %.3f mm3 at dz %s' % (worst, at))
# what hood material lies at x -8..-5.2 above z 80 (where, by y)
for y0, y1 in ((-30, -16), (-16, -7), (-7, 7), (7, 16), (16, 30)):
    s = hood.intersect(dc.box_solid(L.B(-8.0, -5.2, y0, y1, 80, 100)))
    if s.Volume() > 0.01:
        bb = s.BoundingBox(); print('hood at x-8..-5.2 y %g..%g: z %.1f..%.1f x %.1f..%.1f vol %.1f' % (y0, y1, bb.zmin, bb.zmax, bb.xmin, bb.xmax, s.Volume()))
