"""Sensitivity: screw stations as ONE pinned node + rotational spring 3EI/L of an 8x8 x 62 post (29.7 N m/rad)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grill as g
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'opts.py')).read()
exec(src.split('sel = sys.argv')[0].split('import grill as g')[1])
KR = 3 * g.E * (8 ** 4 / 12) / 62.0
centre = {'PF': (-31.5, 85.5), 'PR': (-143.5, 47.5), 'KB1': (-91, 8.2), 'KB2': (-105, 8.2), 'BR': (-140, 8.2)}
groups = {'PF': PF, 'PR': PR, 'KB1': KB1, 'KB2': KB2, 'BR': BR}
bot = [k for k in range(g.N) if abs(g.P[k, 1] - g.Z0) < 1e-6]
for name in ('r2', 'A ', '1e', '2b', '3 '):
    key = next(k for k in OPTS if k.startswith(name)); pins_full, ribs = OPTS[key]
    K = g.build(ribs); pins = []
    for gn, nodes in groups.items():
        if set(nodes) <= set(pins_full):
            c = g.near(centre[gn]); pins.append(c); K[3 * c + 1, 3 * c + 1] += KR; K[3 * c + 2, 3 * c + 2] += KR
    bear = [k for k in g.BEAR if k not in pins]
    ln = [g.near(p) for p in LOADS.values()] + bot
    ln = [k for k in dict.fromkeys(ln) if k not in pins]
    C = g.flex(K, pins, bear + ln)
    w = lambda k: 0.0 if k in pins else g.contact_w(C, len(bear), ln.index(k))
    r = {l: round(w(g.near(p)), 3) for l, p in LOADS.items()}
    ws = [(w(k), float(g.P[k, 0])) for k in bot]
    r['keys zone max'] = round(max(v for v, x in ws if -112 <= x <= -84), 3); r['bottom max'] = round(max(ws)[0], 3)
    print(key, json.dumps(r))
