import sys, os, time, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grill as g
PF = g.nodes_in(-35.5, -27.5, 81.5, 89.5); PR = g.nodes_in(-147.5, -139.5, 43.5, 51.5)
KB1 = g.nodes_in(-95, -87, 8.2, 12.6); KB2 = g.nodes_in(-109, -101, 8.2, 12.6)
BR = g.nodes_in(-144, -136, 8.2, 14.6)
FLANGE = ((-150.0, 10.4), (-87.0, 10.4), 4.4, 7.8)
DIAG = ((-107.5, 11.0), (-143.5, 47.5), 3.0, 7.0)
REAR = ((-148.65, 8.2), (-148.65, 58.5), 3.0, 7.0)
FRONT = ((-19.75, 8.2), (-19.75, 85.5), 3.0, 7.0)
LINK = ((-19.75, 85.5), (-31.5, 85.5), 3.0, 7.0)
DIAG10 = ((-107.5, 11.0), (-141.5, 45.5), 3.0, 10.0)
OPTS = {
    'r2 (4 screws)': (PF + PR + KB1 + KB2, []),
    'A (keys, s_r1+s_r2)': (PF + PR, []),
    '1a A+flange': (PF + PR, [FLANGE]),
    '1b A+flange+diag': (PF + PR, [FLANGE, DIAG]),
    '1c A+flange+diag+rear': (PF + PR, [FLANGE, DIAG, REAR]),
    '1d A+diag only': (PF + PR, [DIAG]),
    '1e 1c+front rib': (PF + PR, [FLANGE, DIAG, REAR, FRONT, LINK]),
    '1f 1e diag d10': (PF + PR, [FLANGE, DIAG10, REAR, FRONT, LINK]),
    '1g A+front rib only': (PF + PR, [FRONT, LINK]),
    '2 s_r1+rear-bottom screw': (PF + BR, []),
    '2b 2+flange+rear rib': (PF + BR, [FLANGE, REAR]),
    '3 s_r1+s_b2': (PF + KB2, []),
}
LOADS = {'L1 seam x-98': (-98, 8.2), 'L3 EVF cap': (-148, 78), 'L4 EVF stop': (-137.6, 78),
         'L5 encoder': (-63, 57), 'L6 switch': (-123, 57), 'L7 cam keeper': (-26, 71)}
sel = sys.argv[1:] or list(OPTS)
res = {}
for name in OPTS:
    if not any(name.startswith(s) for s in sel): continue
    t0 = time.time(); pins, ribs = OPTS[name]; K = g.build(ribs); r = {}
    for ln, p in LOADS.items():
        r[ln] = round(float(g.solve(K, pins, p)[g.near(p)]), 3)
    bot = [k for k in range(g.N) if abs(g.P[k, 1] - g.Z0) < 1e-6][::2]
    worst = max((float(g.solve(K, pins, tuple(g.P[k]))[k]), float(g.P[k, 0])) for k in bot)
    r['L2 worst bottom'] = (round(worst[0], 3), round(worst[1], 1))
    res[name] = r
    print(name, r, '%.0fs' % (time.time() - t0), flush=True)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res_%s.json' % '_'.join(sel)[:20].replace(' ', '')), 'w'), indent=1)
