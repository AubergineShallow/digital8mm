# read-only probe for design_2 (ring-clamp designer -> housing clamp): real-camera proxy + cam_cradle + cam_clip
# boxes in the D2 frame, checked against the release STEP parts, COTS proxies and keep-outs. No repo file is written.
import os, sys, json
D2 = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1'
sys.path.insert(0, D2)
import cadquery as cq
import layout as L
import cots
import d2_common as dc
V = cq.Vector
B = L.B
parts = {p: cq.importers.importStep(os.path.join(D2, 'out', 'step', 'parts', p + '.step')).val()
         for p in ('tub', 'hood', 'panel', 'base_grip', 'pi_keeper', 'plunger')}
want = {'pi5', 'cooler', 'microsd', 'x1203', 'x1203_kit', 'hmx039', 'evf_board', 'eyepiece', 'foam_pad'}
C = cots.build_all(L, only={k for k in want if k in L.COTS})
for k, r in C.items():
    parts['cots:' + k] = r['shape'].val()

def box(b):
    return dc.box_solid(b)

def cylx(r, x0, x1, y=0.0, z=60.0):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))

HF = -5.2; T_BF = 1.25
cam = (box(B(HF - 18.24, HF - 11.75, -19.75, 19.75, 40.25, 79.75))          # rear cover 39.5 sq x 6.49
       .fuse(box(B(HF - 11.75, HF - 10.35, -19.0, 19.0, 41.0, 79.0)))       # PCB 38 sq x 1.4
       .fuse(cylx(17.5, HF - 10.35, HF))                                    # housing body dia 35
       .fuse(box(B(HF - 5.02, HF, -5.08, 5.08, 76.0, 81.6)))                # top tab
       .fuse(box(B(HF - 4.1, HF - 1.1, 5.08, 7.5, 77.9, 80.9)))             # lock screw head (+Y assumed)
       .fuse(cylx(18.0, HF + T_BF, HF + T_BF + 1.2)))                       # BFAR head dia 36 x 1.2
cradle = box(B(-13.5, -5.2, -18.0, 18.0, 36.75, 50.0)).cut(cylx(17.75, -14.0, -4.0))
clip = box(B(-13.5, -5.2, -8.0, 8.0, 81.85, 89.1)).fuse(box(B(-12.32, -10.32, -6.0, 6.0, 77.8, 81.85)))
movers = {'cam': cam, 'cradle': cradle, 'clip': clip}

def hits(solid, obst, kos, tag):
    bb = solid.BoundingBox(); res = []
    for p, s in obst.items():
        ob = s.BoundingBox()
        if ob.xmin > bb.xmax or ob.xmax < bb.xmin or ob.ymin > bb.ymax or ob.ymax < bb.ymin or ob.zmin > bb.zmax or ob.zmax < bb.zmin:
            continue
        v = solid.intersect(s).Volume()
        if v > 0.05:
            ib = solid.intersect(s).BoundingBox()
            res.append((tag, p, round(v, 2), [round(a, 2) for a in (ib.xmin, ib.xmax, ib.ymin, ib.ymax, ib.zmin, ib.zmax)]))
    sb = B(bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
    for k, kb in kos.items():
        if L.boxes_overlap(sb, kb):
            v = solid.intersect(box(kb)).Volume()
            if v > 0.05:
                res.append((tag, k, round(v, 2), 'keepout'))
    return res

kos = {k: v for k, v in L.KEEPOUTS.items() if k not in ('ko_fpc_cam', 'ko_fpc_loop')}
out = {}
fin = {p: s for p, s in parts.items() if p != 'panel'}
r = []
for nm, s in movers.items():
    r += hits(s, parts, kos, 'final:' + nm)
out['final'] = r
print('FINAL', json.dumps(r))

def path_pts(wps, step=1.0):
    pts = []
    for a, b in zip(wps[:-1], wps[1:]):
        d = max(abs(b[i] - a[i]) for i in range(3)); n = max(1, int(d / step))
        pts += [tuple(a[i] + (b[i] - a[i]) * k / n for i in range(3)) for k in range(n)]
    return pts + [wps[-1]]

obst7 = {p: s for p, s in parts.items() if p not in ('panel',)}
for nm, mv, wps in (('camera_in', cam.fuse(cradle), [(-7.2, 60, 4.5), (-7.2, 0, 4.5), (-7.2, 0, 0), (0, 0, 0)]),
                    ('clip_in', clip, [(-2.9, 40, 0.0), (-2.9, 0, 0.0), (0, 0, 0)])):
    extra = {} if nm == 'camera_in' else {'cam': cam, 'cradle': cradle}
    worst = {}
    for pt in path_pts(wps):
        for h in hits(mv.translate(V(*pt)), {**obst7, **extra}, kos, nm):
            k = h[1]
            if h[2] > worst.get(k, (0,))[0]:
                worst[k] = (h[2], pt)
    out[nm] = worst
    print(nm, json.dumps(worst))

hood_noturret = parts['hood'].cut(box(B(0.0, 10.0, -40, 40, 0, 101)))
for sid, (y, z) in (('s_cam_l', (13.5, 40.5)), ('s_cam_r', (-13.5, 40.5)), ('s_cam_t', (0.0, 85.6))):
    bit = cq.Solid.makeCylinder(3.25, 40.0, V(-0.5, y, z), V(1, 0, 0))
    hnd = cq.Solid.makeCylinder(15.0, 100.0, V(39.5, y, z), V(1, 0, 0))
    drv = bit.fuse(hnd)
    rr = hits(drv, {'hood_noturret': hood_noturret, 'base_grip': parts['base_grip'], 'plunger': parts['plunger'],
                    'tub': parts['tub']}, {}, sid)
    out[sid] = rr
    print(sid, json.dumps(rr))
json.dump(out, open(os.path.join(os.path.dirname(__file__), 'probe_d2.json'), 'w'), indent=1, default=str)
