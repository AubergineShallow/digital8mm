import os, sys
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq, layout as L, cots, d2_common as dc
V = cq.Vector
P = {p: cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', p + '.step')).val() for p in ('tub', 'hood', 'panel')}
C = cots.build_all(L, only={'pi5', 'cooler', 'x1203', 'x1203_kit', 'gs_camera'})
def box(*b): return dc.box_solid(L.B(*b))
def cylx(y, z, r, x0, x1): return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))
top = box(-8.0, -5.2, -30.0, 16.0, 88.0, 97.3)
print('top flange zone vs hood final %.2f' % P['hood'].intersect(top).Volume())
sw = top
for i in range(1, 31): sw = sw.fuse(top.translate(V(0, 0, -2.0 * i)))
print('top flange zone vs hood drop sweep %.2f' % P['hood'].intersect(sw).Volume())
print('top flange zone vs tub (existing material) %.2f' % P['tub'].intersect(top).Volume())
bb = P['hood'].intersect(box(-12, -2.5, -35, 35, 80, 100)).BoundingBox()
print('hood material near the front-top inside: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
for nm, (y, z) in dict(TL=(11.5, 91.5), TR=(-11.5, 91.5), LL=(24.5, 36.0)).items():
    tip = cylx(y, z, 1.5, -9.7, -7.5)
    r = {p: round(s.intersect(tip).Volume(), 2) for p, s in P.items()}
    r.update({k: round(c['shape'].val().intersect(tip).Volume(), 2) for k, c in C.items()})
    print('screw tip', nm, {k: v for k, v in r.items() if v > 0})
print('wall-top z of tub front wall:', L.ZT1)
