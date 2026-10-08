# read-only probe 2: free-space candidate boxes vs built parts, COTS proxies, keep-outs; seat land area
import os, sys, json
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L
import cots
import d2_common as dc
V = cq.Vector
parts = {p: cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', p + '.step')).val()
         for p in ('tub', 'hood', 'panel', 'base_grip', 'pi_keeper', 'plunger')}
C = cots.build_all(L, only={'gs_camera', 'c_cs_adapter', 'lens', 'pi5', 'cooler', 'microsd', 'x1203', 'x1203_kit'})
for k, r in C.items():
    parts['cots:' + k] = r['shape'].val()
B = L.B
cand = {
    'F1_above_cam': B(-24.47, -5.2, -27.3, 16.5, 80.0, 94.0),
    'F2_right_of_cam': B(-24.0, -5.2, -27.3, -19.75, 40.25, 80.0),
    'F3_left_of_cam': B(-24.47, -6.6, 19.75, 32.2, 41.0, 79.75),
    'F4_under_cam': B(-21.0, -5.2, -25.5, 19.75, 36.5, 40.25),
    'F5_behind_cam': B(-27.5, -24.67, -19.75, 3.5, 47.5, 79.75),
    'F7_turret_to_lens': B(8.5, 10.6, -25.5, 25.5, 34.5, 85.5),
    'F8_below_lens_ext': B(0.0, 67.2, -32.0, 32.0, 0.3, 33.0),
    'F9_right_of_lens_ext': B(0.0, 67.2, -35.0, -27.0, 33.0, 87.0),
    'F11_left_of_lens_ext': B(0.0, 67.2, 27.0, 35.0, 33.0, 87.0),
    'F12_above_lens_ext': B(0.0, 67.2, -27.0, 27.0, 87.0, 100.0),
}
out = {}
for nm, b in cand.items():
    bs = dc.box_solid(b)
    occ = {}
    for p, s in parts.items():
        try:
            v = s.intersect(bs).Volume()
        except Exception as e:
            v = -1
        if v > 0.01:
            ib = s.intersect(bs).BoundingBox()
            occ[p] = dict(vol=round(v, 1), bb=[round(x, 2) for x in (ib.xmin, ib.xmax, ib.ymin, ib.ymax, ib.zmin, ib.zmax)])
    ko = [k for k, kb in L.KEEPOUTS.items() if L.boxes_overlap(b, kb)]
    out[nm] = dict(box=b, occupied=occ, keepouts=ko)
    print(nm, json.dumps(dict(occupied=occ, keepouts=ko)))
# annulus inside the turret bore around cs_ring/adapter: r 15.4..18.2, x 0.6..8.5
ann = cq.Solid.makeCylinder(18.2, 7.9, V(0.6, 0, 60), V(1, 0, 0)).cut(cq.Solid.makeCylinder(15.4, 7.9, V(0.6, 0, 60), V(1, 0, 0)))
print('annulus r15.4-18.2 x0.6-8.5 vs hood', round(ann.intersect(parts['hood']).Volume(), 2), 'vs cam',
      round(ann.intersect(parts['cots:gs_camera']).Volume(), 2), 'vs adapter', round(ann.intersect(parts['cots:c_cs_adapter']).Volume(), 2),
      'vs lens', round(ann.intersect(parts['cots:lens']).Volume(), 2))
# seat land: tub material in the first 0.1 mm in front of the seat inside the 39.5 square
sq = dc.box_solid(B(-5.2, -5.1, -19.75, 19.75, 40.25, 79.75))
a = parts['tub'].intersect(sq).Volume() / 0.1
print('seat land area mm2 (tub face inside 39.5 sq)', round(a, 1), 'of', round(39.5 ** 2, 1), '; bore circle', round(3.14159 * 18.25 ** 2, 1))
for half, nm in ((B(-5.2, -5.1, -19.75, 0, 40.25, 79.75), '-Y half'), (B(-5.2, -5.1, 0, 19.75, 40.25, 79.75), '+Y half'),
                 (B(-5.2, -5.1, -19.75, 19.75, 40.25, 60), 'lower half'), (B(-5.2, -5.1, -19.75, 19.75, 60, 79.75), 'upper half')):
    print('  land', nm, round(parts['tub'].intersect(dc.box_solid(half)).Volume() / 0.1, 1))
json.dump(out, open('probe2.json', 'w'), indent=1)
