import os, sys, json
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L, cots, d2_common as dc
parts = {p: cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', p + '.step')).val()
         for p in ('tub', 'hood', 'panel', 'base_grip', 'pi_keeper', 'plunger')}
for k, r in cots.build_all(L, only={'gs_camera', 'c_cs_adapter', 'lens', 'pi5', 'cooler', 'microsd'}).items():
    parts['cots:' + k] = r['shape'].val()
B = L.B
cand = {'F2b_right_of_cam': B(-24.0, -5.2, -27.3, -19.75, 44.0, 80.0),
        'F8a_below_lens_ahead_of_turret': B(8.5, 67.2, -32.0, 32.0, 0.3, 33.0),
        'F8b_below_turret_front_of_plate': B(1.0, 8.5, -32.0, 32.0, 0.3, 29.9),
        'F8c_ahead_of_base_below_plate': B(-0.5, 67.2, -35.2, 35.2, -8.0, 0.3),
        'F13_wall_to_plate_gap': B(-2.7, -2.5, -32.0, 32.0, 0.3, 97.0),
        'F14_bore_drop_region_hood': B(-2.5, 8.5, -6.5, 6.5, 40.76, 41.74)}
for nm, b in cand.items():
    bs = dc.box_solid(b); occ = {}
    for p, s in parts.items():
        v = s.intersect(bs).Volume()
        if v > 0.01:
            ib = s.intersect(bs).BoundingBox()
            occ[p] = dict(vol=round(v, 1), bb=[round(x, 2) for x in (ib.xmin, ib.xmax, ib.ymin, ib.ymax, ib.zmin, ib.zmax)])
    print(nm, json.dumps(dict(occ=occ, ko=[k for k, kb in L.KEEPOUTS.items() if L.boxes_overlap(b, kb)])))
