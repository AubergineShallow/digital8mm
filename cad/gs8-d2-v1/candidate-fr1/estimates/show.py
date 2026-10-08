import pickle, numpy as np, sys, os
d = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'depth.pkl'), 'rb'))
xs, zs, ym, src = d['xs'], d['zs'], d['ymax'], d['src']
dep = 32.2 - ym
x0, x1, z0, z1, sx, sz = [float(a) for a in sys.argv[1:7]]
def ch(v):
    return '#' if v < 1 else 'a' if v < 2.5 else 'b' if v < 4 else 'c' if v < 6 else 'd' if v < 8 else '.'
cols = np.arange(x0, x1, sx); rows = np.arange(z1, z0, -sz)
print('      ' + ''.join(('%d' % abs(c))[-2] if int(c) % 10 == 0 else ' ' for c in cols))
legend = {}
for r in rows:
    line = ''
    for c in cols:
        m = (xs >= c) & (xs < c + sx); n = (zs >= r - sz) & (zs < r)
        blk = dep[np.ix_(m, n)]; k = np.unravel_index(np.argmin(blk), blk.shape)
        v = blk[k]; line += ch(v)
        if v < 8: legend.setdefault(src[np.ix_(m, n)][k], set()).add((int(c), int(r)))
    print('%5.1f ' % r + line)
for k, v in legend.items():
    xx = [a for a, b in v]; zz = [b for a, b in v]
    print(k, 'x', min(xx), max(xx), 'z', min(zz), max(zz))
