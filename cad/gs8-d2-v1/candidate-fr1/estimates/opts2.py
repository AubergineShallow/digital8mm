import sys, os, time, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grill as g
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'opts.py')).read().split('sel = sys.argv')[0].split('import grill as g')[1])
sel = sys.argv[1:] or list(OPTS)
bot = [k for k in range(g.N) if abs(g.P[k, 1] - g.Z0) < 1e-6]
lnodes = [g.near(p) for p in LOADS.values()] + bot
res = {}
for name in OPTS:
    if not any(name.startswith(s) for s in sel): continue
    t0 = time.time(); pins, ribs = OPTS[name]; K = g.build(ribs)
    bear = [k for k in g.BEAR if k not in set(pins)]
    ln = [k for k in lnodes if k not in set(pins)]
    C = g.flex(K, pins, bear + ln)
    r = {}
    for lname, p in LOADS.items():
        k = g.near(p)
        r[lname] = 0.0 if k in pins else round(g.contact_w(C, len(bear), ln.index(k)), 3)
    ws = [(g.contact_w(C, len(bear), ln.index(k)) if k in ln else 0.0, float(g.P[k, 0])) for k in bot]
    w98 = max(w for w, x in ws if -112 <= x <= -84)
    wmax = max(ws)
    r['L2 bottom max'] = (round(wmax[0], 3), round(wmax[1], 1)); r['L2 keys zone max'] = round(w98, 3)
    res[name] = r
    print(name, json.dumps(r), '%.0fs' % (time.time() - t0), flush=True)
    xs_want = [-150, -135, -120, -105, -98, -90, -75, -60, -45, -30, -15, -4.6]
    prof = []
    for xw in xs_want:
        k = min(bot, key=lambda k: abs(g.P[k, 0] - xw))
        prof.append(round(dict((x, w) for w, x in ws)[float(g.P[k, 0])], 2))
    print('   profile', prof)
