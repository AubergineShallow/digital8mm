import os, sys
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq, layout as L, d2_common as dc
V = cq.Vector; B = L.B
hood = cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', 'hood.step')).val()
# swept envelope of the clip during the -Y slide (x offset -2.9, z +2): x -16.4..-8.1, z 79.45..92.0, y -8..48
for nm, b in (('slide_env', B(-16.4, -8.1, -8.0, 48.0, 79.45, 92.0)), ('slide_env_lowtop', B(-16.4, -8.1, -8.0, 48.0, 79.45, 86.0))):
    s = hood.intersect(dc.box_solid(b))
    bb = s.BoundingBox()
    print(nm, round(s.Volume(), 2), [round(a, 2) for a in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
# what hood solid is in x -16.4..-8.1, y 16..40, z 79..95 : slice by y
for y0 in (16, 20, 24, 28, 32, 36):
    s = hood.intersect(dc.box_solid(B(-16.4, -8.1, y0, y0 + 4, 75.0, 97.0)))
    if s.Volume() > 0.01:
        bb = s.BoundingBox(); print('y', y0, round(s.Volume(), 1), [round(a, 2) for a in (bb.xmin, bb.xmax, bb.zmin, bb.zmax)])
# housing top clearance used by the hook
print('HOOD_HOOKS', [ (h['id'], h.get('x'), h.get('y')) for h in L.HOOD_HOOKS])
