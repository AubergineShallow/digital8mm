# designer-1 probe 1 (read-only): front extent of the Pi-stack proxies in the drop column, by y band
import sys
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq, layout as L, cots, d2_common as dc
mv = ['x1203', 'x1203_kit', 'pi5', 'cooler']
C = cots.build_all(L, only=set(mv))
for k in mv:
    s = C[k]['shape'].val(); bb = s.BoundingBox()
    print(k, 'bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
    # front-most x inside y bands (final pose)
    for y0, y1 in ((-32.5, -24), (-24, -14), (-14, 14), (14, 24), (24, 32.2)):
        sl = s.intersect(dc.box_solid(L.B(-30, 0, y0, y1, -10, 120)))
        v = sl.Volume()
        if v > 1e-3:
            b2 = sl.BoundingBox(); print('   y %6.1f..%6.1f  front x %.2f  (z %.1f..%.1f)' % (y0, y1, b2.xmax, b2.zmin, b2.zmax))
print('pi_in path', [i for i in L.INSERTIONS if i['id'] == 'pi_in'][0]['path'])
print('hood stack stop', getattr(L, 'STACK_STOP', None))
