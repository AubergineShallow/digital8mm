import sys, math, json
sys.path.insert(0, r"C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1")
import cadquery as cq
import layout as L
import d2_common as dc
V = cq.Vector
def box(x0,x1,y0,y1,z0,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def bb(b): return box(b['x'][0],b['x'][1],b['y'][0],b['y'][1],b['z'][0],b['z'][1])
out = {}
# D1 LL nut boss: OD 8.8 at (y 24.5, z 36), x -7.6..-5.2, teardrop apex -Y
r = 4.4
cyl = cq.Solid.makeCylinder(r, 2.4, V(-7.6, 24.5, 36.0), V(1,0,0))
td = dc.teardrop(r, 0.0, 2.4, (-7.6, 24.5, 36.0), (1,0,0), up=(0,-1,0))
td = td.val() if hasattr(td,'val') else td
boss = cyl.fuse(td)
for cid in ('pi5','cooler','x1203_kit'):
    out['d1_LL_boss_vs_%s_box' % cid] = round(boss.intersect(bb(L.COTS[cid]['box'])).Volume(),2)
for k,b in L.KEEPOUTS.items():
    v = boss.intersect(bb(b)).Volume()
    if v>0.01: out['d1_LL_boss_vs_'+k]=round(v,2)
# pi5 proxy actual shape
import cots
sh = cots.pi5(L, L.COTS['pi5'])
sh = sh.val() if hasattr(sh,'val') else sh
out['d1_LL_boss_vs_pi5_proxy'] = round(boss.intersect(sh).Volume(),2)
# pi_in final +X slide phase: pi5 proxy at z+5, x from -2.8 to 0
hit=0
for dx in [-2.8,-2.0,-1.0,0.0]:
    hit=max(hit, boss.intersect(sh.translate(V(dx,0,5.0))).Volume())
out['d1_LL_boss_vs_pi5_proxy_slide_max'] = round(hit,2)
# D2 cradle pin hole outer wall: pin hole dia 2.2 at y 16.5, cradle side y 18
out['d2_pin_hole_outer_wall'] = round(18.0 - (16.5 + 1.1), 2)
# D1 TL/TR hood hole ligament to the front-top chamfer at the plate front face (x 0): chamfer starts z 97
out['d1_TL_hole_ligament_front_face'] = round(97.0 - (92.0 + 4.5), 2)
print(json.dumps(out, indent=1))
