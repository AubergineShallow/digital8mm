"""integrate-fork helper: summarise a fork build dir (categories, rows, STL sha256 vs the r2 release out/stl)."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, '..', 'out', 'stl')
d = sys.argv[1]
c = json.load(open(os.path.join(d, 'checks.json')))
summ = c['summary']
bad = [s for s in summ if s.get('status') != 'pass']
cf = next((s for s in summ if s['check'] == 'critical_features'), {})
print('variant', c.get('variant'), 'rows', sum(s.get('n') or 0 for s in summ), 'categories %d, pass %d' % (
      len(summ), len(summ) - len(bad)), 'critical_features', {k: cf.get(k) for k in ('n', 'passed', 'info', 'failed')})
print('NOT PASS:', json.dumps(bad)[:800])
rc = json.load(open(os.path.join(d, 'build-receipt.json'))) if os.path.exists(os.path.join(d, 'build-receipt.json')) else {}
print('built_at', rc.get('built_at'), 'cad_release_candidate', rc.get('cad_release_candidate'), 'stubs', c.get('stubs'))
sd = os.path.join(d, 'stl')
for f in sorted(x for x in os.listdir(sd) if x.endswith('.stl')):
    h = hashlib.sha256(open(os.path.join(sd, f), 'rb').read()).hexdigest()
    r = os.path.join(REF, f)
    hr = hashlib.sha256(open(r, 'rb').read()).hexdigest() if os.path.exists(r) else None
    print('%-18s %s %s' % (f, h[:12], 'SAME as r2' if h == hr else 'differs from r2'))
