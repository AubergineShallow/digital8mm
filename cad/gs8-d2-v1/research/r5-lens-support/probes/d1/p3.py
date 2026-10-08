# designer-1 probe 3: proper pi_in relative sweep vs new tub bosses; real-camera proxy camera_in sweep vs new features
import os, sys
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq, layout as L, cots, d2_common as dc
V = cq.Vector
C = cots.build_all(L, only={'pi5', 'cooler', 'x1203', 'x1203_kit'})
PI = None
for r in C.values():
    s = r['shape'].val(); PI = s if PI is None else PI.fuse(s)
def cylx(y, z, r, x0, x1): return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))
def box(*b): return dc.box_solid(L.B(*b))
def pathpts(wps, step=2.0):
    pts = []
    for a, b in zip(wps[:-1], wps[1:]):
        d = max(abs(b[i] - a[i]) for i in range(3)); n = max(1, int(d // step))
        pts += [tuple(a[i] + (b[i] - a[i]) * k / n for i in range(3)) for k in range(n)]
    return pts + [wps[-1]]
pi_path = [i for i in L.INSERTIONS if i['id'] == 'pi_in'][0]['path']
S = dict(TL=(11.5, 91.5), TR=(-11.5, 91.5), LL=(24.5, 36.0))
bosses = None
for k, (y, z) in S.items():
    b = cylx(y, z, 4.4, -7.7, -5.2); bosses = b if bosses is None else bosses.fuse(b)
worst = 0
for p in pathpts(pi_path):
    v = PI.translate(V(*p)).intersect(bosses).Volume()
    if v > worst: worst = v; wp = p
print('pi_in sweep vs 3 nut bosses: worst overlap %.3f mm3' % worst, ('at %s' % (wp,)) if worst > 0 else '')
# real GS camera proxy (s = 1.25, BFAR face on the lip at x -4.3, adapter pre-fitted)
s = 1.25; xf = -4.3; xh = xf - 1.2 - s
cam = (cylx(0, 60, 18.0, xf - 1.2, xf).fuse(cylx(0, 60, 15.4, xf, xf + 5.0))
       .fuse(cylx(0, 60, 17.75, xh - 10.35, xh)).fuse(box(xh - 5.02, xh, -5.08, 5.08, 60, 82.1))
       .fuse(box(xh - 11.75, xh - 10.35, -19, 19, 41, 79)).fuse(box(xh - 18.24, xh - 11.75, -19.75, 19.75, 40.25, 79.75)))
print('camera proxy bbox x %.2f..%.2f' % (cam.BoundingBox().xmin, cam.BoundingBox().xmax))
fin = box(-23.5, -19.5, -22.5, -20.25, 41.0, 94.3).fuse(box(-23.5, -19.5, -27.7, -22.5, 44.5, 48.5)).fuse(box(-23.5, -19.5, -27.7, -22.5, 75.0, 79.0))
tub = cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', 'tub.step')).val()
hood = cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', 'hood.step')).val()
# new tub: lip + counterbore replace the dia 36.5 bore locally (approx: add lip ring material, remove counterbore)
lip = cylx(0, 60, 18.25, -4.3, -2.7).cut(cylx(0, 60, 16.2, -4.3, -2.7))
cb = cylx(0, 60, 18.75, -5.3, -4.3)
obst = dict(tub=tub.cut(cb).fuse(lip), bosses=bosses, fin=fin, hood=hood)
cam_path = [i for i in L.INSERTIONS if i['id'] == 'camera_in'][0]['path']
for nm, o in obst.items():
    worst = 0; wp = None
    for p in pathpts(cam_path, 1.0):
        v = cam.translate(V(*p)).intersect(o).Volume()
        if v > worst: worst, wp = v, p
    print('camera_in (real proxy) vs %-7s worst %.3f mm3 %s' % (nm, worst, wp if worst > 0.05 else ''))
print('final: cam vs fin %.3f, vs bosses %.3f' % (cam.intersect(fin).Volume(), cam.intersect(bosses).Volume()))
print('fin vs ko_lead_wall %.3f' % fin.intersect(box(*[v for k in 'xyz' for v in L.KEEPOUTS['ko_lead_wall'][k]])).Volume())
