# designer-1 probe 2 (read-only): candidate features vs release parts, proxies, keep-outs and sweeps
import os, sys
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq, layout as L, cots, d2_common as dc
V = cq.Vector
P = {p: cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', p + '.step')).val()
     for p in ('tub', 'hood', 'panel', 'base_grip', 'pi_keeper', 'plunger')}
C = cots.build_all(L, only={'pi5', 'cooler', 'x1203', 'x1203_kit', 'microsd'})
for k, r in C.items(): P['cots:' + k] = r['shape'].val()
def cylx(y, z, r, x0, x1): return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))
def box(*b): return dc.box_solid(L.B(*b))
def ext(s, d):  # swept solid of s translated along vector d (convex-ish hull by lofting bboxes is overkill: sample)
    out = s
    n = int(max(abs(c) for c in d) // 2) + 1
    for i in range(1, n + 1):
        out = out.fuse(s.translate(V(*(c * i / n for c in d))))
    return out
def hits(name, s, skip=()):
    res = []
    for p, sh in P.items():
        if p in skip: continue
        try: v = sh.intersect(s).Volume()
        except Exception: v = -1
        if abs(v) > 0.01: res.append('%s %.2f' % (p, v))
    bb = s.BoundingBox(); b = L.B(bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
    ko = [k for k, kb in L.KEEPOUTS.items() if L.boxes_overlap(b, kb) and dc.box_solid(kb).intersect(s).Volume() > 0.01]
    print('%-28s parts: %s | keepouts: %s' % (name, res or '-', ko or '-'))
S = dict(TL=(11.5, 91.5), TR=(-11.5, 91.5), LL=(24.5, 36.0))
for k, (y, z) in S.items():
    b = cylx(y, z, 4.4, -7.7, -5.2)
    hits('nutboss_' + k + ' final', b, skip=('tub',))
    hits('nutboss_' + k + ' vs panel sweep', ext(b, (0, -70, 0)), skip=[p for p in P if p != 'panel'])
    pis = [p for p in P if p.startswith('cots:') and p != 'cots:microsd']
    hits('nutboss_' + k + ' vs pi drop', ext(ext(b, (2.8, 0, 0)), (0, -2.1, -80)), skip=[p for p in P if p not in pis])
    hits('hoodhole_' + k + ' (plate)', cylx(y, z, 4.5, -2.5, 0.0), skip=('tub',))
hits('foot_LR (-19,44) thru plate', cylx(-19.0, 44.0, 4.5, -2.5, 0.0), skip=('tub',))
for k, (y, z) in list(S.items()) + [('LR', (-19.0, 44.0))]:
    hits('collar_foot_' + k + ' x-2.7..0.3', cylx(y, z, 4.0, -2.7, 0.3), skip=())
# collar envelope in front of the plate: dia 60 x 0.3..8.5 plus ears; pinch lug at +Y
col = cylx(0, 60, 30.0, 0.3, 8.5).fuse(box(0.3, 2.7, -16, 16, 86, 96)).fuse(box(0.3, 2.7, 19, 30, 30, 42)).fuse(box(2.7, 8.5, 29, 36.5, 54.5, 65.5))
hits('collar envelope', col)
fin = box(-23.5, -19.5, -22.5, -20.25, 41.0, 94.3).fuse(box(-23.5, -19.5, -27.7, -22.5, 41.0, 45.0)).fuse(box(-23.5, -19.5, -27.7, -22.5, 75.0, 79.0))
hits('hood roll fin final', fin, skip=('hood',))
hits('hood roll fin drop sweep', ext(fin, (0, 0, 60)), skip=('hood', 'panel'))
# tub lip and counterbore: material that the new bore would remove/keep
print('tub vol in dia37.5 x-5.2..-4.3 annulus r18.25..18.75:', round(P['tub'].intersect(cylx(0, 60, 18.75, -5.2, -4.3).cut(cylx(0, 60, 18.25, -5.2, -4.3))).Volume(), 1))
