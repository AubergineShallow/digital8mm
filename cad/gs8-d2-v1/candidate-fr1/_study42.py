"""integrate-fork helper: STUDY-base-cap s4.2 checks 1-4, 6, 7 from built checks.json files (no CAD)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
def rows(d):
    return json.load(open(os.path.join(HERE, 'out', d, 'checks.json')))['results']
def pick(R, cat, pred):
    return [r for r in R.get(cat, []) if pred(json.dumps(r, default=str))]
out = {}
for d in ['_none', '_int-panel', '.']:
    R = rows(d)
    sj = lambda s: '"s_j"' in s
    o = dict(driver=[(r.get('id') or r.get('screw'), r['status']) for r in pick(R, 'driver', sj)],
             boss=[(r.get('id') or r.get('screw'), r['status']) for r in pick(R, 'boss_geometry', sj)],
             interf=[(r.get('pair') or r.get('id'), r['status']) for r in pick(R, 'interference', sj)],
             clear=[(r.get('id') or r.get('name'), r.get('gap_mm', r.get('min_gap')), r['status']) for r in pick(R, 'clearance', lambda s: 'J4' in s)],
             base_on=[(r.get('id'), r['status']) for r in pick(R, 'sweeps', lambda s: 'base_on' in s)],
             j4=[(r.get('id'), r.get('values'), r['status']) for r in R['critical_features']
                 if str(r.get('id', '')).startswith(('tub_tongue_', 'base_keyhole_lip_', 'tub_j4_lock_boss', 'base_sj', 'J4_'))],
             lock=[(r.get('id'), r.get('off')) for r in []])
    out[d] = o
    print(d, json.dumps(o, default=str)[:1500])
sys.path.insert(0, HERE)
vals = {d: {x[0]: x[1] for x in o['j4']} for d, o in out.items()}
print('item 7: J4 probe values identical none/panel/all:', vals['_none'] == vals['_int-panel'] == vals['.'])
