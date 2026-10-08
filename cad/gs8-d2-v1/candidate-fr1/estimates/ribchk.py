import pickle, numpy as np, os
d = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'depth.pkl'), 'rb'))
xs, zs, ym, src = d['xs'], d['zs'], d['ymax'], d['src']
X, Z = np.meshgrid(xs, zs, indexing='ij'); dep = 32.2 - ym
def band(pa, pb, w):
    pa, pb = np.array(pa), np.array(pb); t = pb - pa; L = np.linalg.norm(t); t /= L; n = np.array([-t[1], t[0]])
    q = np.stack([X - pa[0], Z - pa[1]], -1)
    s = q @ t; o = q @ n
    return (s >= 0) & (s <= L) & (np.abs(o) <= w / 2 + 0.25)
def report(name, m):
    k = np.unravel_index(np.argmin(np.where(m, dep, 99)), dep.shape)
    print('%-28s min free depth %.2f at x %.1f z %.2f (%s)' % (name, dep[k], X[k], Z[k], src[k]))
report('flange x-150..-87 z8.2..12.6', (X >= -150.25) & (X <= -86.75) & (Z >= 8.2) & (Z <= 12.85))
report('flange rear x-150..-105 z..16', (X >= -150.25) & (X <= -105.5) & (Z >= 8.2) & (Z <= 16.25))
report('diag', band((-107.5, 11.0), (-141.5, 45.5), 3.0) & (Z >= 8.2))
report('rear rib', (X >= -150.4) & (X <= -146.9) & (Z >= 8.2) & (Z <= 58.75))
report('front rib x-20', (X >= -21.75) & (X <= -18.25) & (Z >= 8.2) & (Z <= 89.75))
report('front link z85.5', (X >= -27.75) & (X <= -18.25) & (Z >= 83.75) & (Z <= 87.25))
for xx in (-24, -23, -22, -21, -20, -19, -18, -17, -16, -15, -14):
    m = (np.abs(X - xx) < 0.01) & (Z >= 8.2) & (Z <= 89.5)
    k = np.unravel_index(np.argmin(np.where(m, dep, 99)), dep.shape)
    print('col x %d: min depth %.2f at z %.2f (%s)' % (xx, dep[k], Z[k], src[k]))
