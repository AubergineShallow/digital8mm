# Planted-fault probes for the D2 r5 verification logic (audit 2026-10-06, logic dimension).
# Read-only: imports cad/gs8-d2-v1 modules, feeds in-memory data, writes only logic-audit.json next to this file.
# Small CadQuery primitive solids only (no part module is built). Run with .venv-cad python -B.
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D2 = os.path.normpath(os.path.join(HERE, '..', '..', 'cad', 'gs8-d2-v1'))
sys.path.insert(0, D2)
sys.dont_write_bytecode = True

import cadquery as cq  # noqa: E402
import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402
import layout as L  # noqa: E402
import cots  # noqa: E402

RES = []


def probe(pid, fault, expect, got, caught, note=''):
    RES.append(dict(id=pid, fault=fault, expected=expect, observed=got, caught=bool(caught), note=note))
    print('%-4s %-7s %s -> %s' % (pid, 'CAUGHT' if caught else 'MISSED', fault, got))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


# ---------------------------------------------------------------- lens_support (F1-type faults)
def p_lens_support():
    base = copy.deepcopy(L.LENSES_DATA_ONLY['computar_h6z0812'])
    light = dict(base, name='synthetic 140 g lens', mass=140.0)
    light.pop('support')
    L.LENSES_DATA_ONLY['_t_light'] = light
    try:
        out = [r for r in CK.check_lens_support(L) if r['lens'] == '_t_light']
    finally:
        del L.LENSES_DATA_ONLY['_t_light']
    st = [r['status'] for r in out]
    probe('P1', '140 g lens with no support band / no collar under J7-R (camera floats, nothing holds it)',
          'fail', st, 'fail' in st, 'rule only fires above support_mass_g 150 g')

    # P2: the default lens's built collar is missing (rows without lens_collar, collars empty)
    out = [r for r in CK.check_lens_support(L, rows={}, collars={}) if r['lens'] == L.LENS]
    items = sorted({r['item'] for r in out})
    miss = {'lens_seated', 'bore_measured', 'seat_measured'} - set(items)
    probe('P2', 'default-lens collar solid absent from rows (lens_support only)', 'fail',
          dict(statuses=sorted({r['status'] for r in out}), measured_items_missing=sorted(miss)),
          any(r['status'] == 'fail' for r in out),
          'measured items silently skipped; J7 critical-feature probes on lens_collar would still FAIL in a build')

    # P3: band status 'measured' wrongly set while geometry unchanged -> WARN disappears (expected; just shows that the
    # only WARN gate is a status string)
    sp = L.LENSES[L.LENS]['support']
    keep = sp.get('status')
    sp['status'] = 'measured'
    try:
        out = [r for r in CK.check_lens_support(L) if r['lens'] == L.LENS and r['item'] == 'status']
    finally:
        sp['status'] = keep
    probe('P3', "support.status set to 'measured' with no evidence record", 'still WARN or bound to a G-LENS record',
          [r['status'] for r in out], any(r['status'] != 'pass' for r in out),
          'the WARN is cleared by a string in layout.py, not by a G-LENS evidence record')


# ---------------------------------------------------------------- j7_float
def cam_boxes(dx=0.0):
    """synthetic hanging unit: body box behind the wall, bfar box; parts_of(L, s) -> shifts with s."""
    ly, lz = L.LENS_AXIS

    def parts_of(_L, s):
        x = -20.0 + dx + s
        return {'body': box(x - 10, x, ly - 18, ly + 18, lz - 18, lz + 18),
                'bfar': box(x, x + 1.2, ly - 18, ly + 18, lz - 18, lz + 18)}
    ad = box(-18.0 + dx, -12.0 + dx, ly - 15, ly + 15, lz - 15, lz + 15)
    return parts_of, ad


def wall(x0, thick=3.0):
    ly, lz = L.LENS_AXIS
    return box(x0, x0 + thick, ly - 30, ly + 30, lz - 30, lz + 30)


def j7(rows, parts_of, s=(0.0, 1.25, 3.0)):
    return CK.check_j7_float(L, rows, s_values=s, parts_of=parts_of)


def p_j7():
    parts_of, ad = cam_boxes()
    ly, lz = L.LENS_AXIS
    # obstacle: a plate 0.5 behind the body rear at s=0 (body rear x = -30): fine at axial 0.4
    rear = box(-33.5, -30.5, ly - 30, ly + 30, lz - 30, lz + 30)     # 0.5 behind body at s 0
    ring = box(-30, -5, ly + 18.8, ly + 25, lz - 25, lz + 25)          # 0.8 lateral above body
    rows = {'tub': dict(shape=rear), 'hood': dict(shape=ring), 'c_cs_adapter': dict(shape=ad)}
    base = [r['status'] for r in j7(rows, parts_of, s=(0.0,))]
    probe('P4', 'control: synthetic unit with 0.5 axial / 0.8 lateral gaps', 'pass', base, all(x == 'pass' for x in base))

    rows_t = dict(rows, tub=dict(shape=box(-33.0, -30.0, ly - 30, ly + 30, lz - 30, lz + 30)))   # touching
    st = [(r['mover'], r['status']) for r in j7(rows_t, parts_of, s=(0.0,))]
    probe('P5', 'camera body touching the tub (0 gap, 0 overlap)', 'fail', st, any(x == 'fail' for _, x in st))

    rows_g = dict(rows, tub=dict(shape=box(-33.0, -30.39, ly - 30, ly + 30, lz - 30, lz + 30)))   # 0.39 < 0.4
    st = [(r['mover'], r['status']) for r in j7(rows_g, parts_of, s=(0.0,))]
    probe('P6', 'axial gap 0.39 (rule 0.40)', 'fail', st, any(x == 'fail' for _, x in st))

    # P7: fault only at an intermediate s (obstacle a thin fin that the BFAR passes between s 1.25 and 3.0):
    # body moves +x with s; put a fin ahead of the bfar front at x where s=2.0 touches it but s=1.25 and 3.0 ...
    # monotone translation -> a fin ahead always closes at s_max; instead use a lateral bump only level with s=2.0.
    bump = box(-17.5, -17.05, ly + 18.55, ly + 20, lz - 5, lz + 5)   # 0.55 lateral (bfar rule 0.6) only at s~2
    rows_b = dict(rows, panel=dict(shape=bump))
    st = [(r['mover'], r['s'], r['status']) for r in j7(rows_b, parts_of)]
    st2 = [(r['mover'], r['s'], r['status']) for r in j7(rows_b, parts_of, s=(0.0, 1.25, 2.0, 3.0))]
    probe('P7', 'clash only at an intermediate screw-out s = 2.0 (fin level with the BFAR there)', 'fail',
          dict(default_s=[x for x in st if x[2] != 'pass'], with_s2=[x for x in st2 if x[2] != 'pass']),
          any(x[2] == 'fail' for x in st), 'j7_float samples s 0 / 1.25 / 3.0 only')

    # P8: a real clash beside a stub obstacle -> downgraded to stub (F2)
    rows_s = dict(rows_t, hood=dict(shape=ring, stub=True))
    st = [(r['mover'], r['status']) for r in j7(rows_s, parts_of, s=(0.0,))]
    probe('P8', 'body touches tub (real) while an unrelated obstacle (hood) is a stub', 'fail (stub only if the '
          'offender is a stub)', st, any(x == 'fail' for _, x in st),
          'stub blocks cad_release_candidate anyway (stubs list), so masking only hides which part is at fault')

    # P9: no obstacle within reach -> fail
    st = [r['status'] for r in j7({'c_cs_adapter': dict(shape=ad)}, parts_of, s=(0.0,))]
    probe('P9', 'nothing within 6 mm of the hanging unit (float unmeasured)', 'fail', st, all(x == 'fail' for x in st))

    # P10: lens row missing -> lens checks silently absent
    out = j7(rows, parts_of, s=(0.0,))
    probe('P10', "no 'lens' row in rows (lens-overlap and lens-vs-camera rows)", 'fail or explicit not-run',
          sorted({r['mover'] for r in out}), any(r['mover'] == 'lens' for r in out) and False,
          'lens rows are skipped without a row; the category still passes')

    # P11: lens touching the hood (0 gap) and lens overlapping the hood
    lens = box(-12.0, 40.0, ly - 21, ly + 21, lz - 21, lz + 21)
    h_touch = box(-5.0, 0.0, ly + 21.0, ly + 30, lz - 30, lz + 30)
    st = [r['status'] for r in j7(dict(rows, lens=dict(shape=lens), hood=dict(shape=h_touch)), parts_of, s=(0.0,))
          if r['mover'] == 'lens']
    probe('P11', 'lens barrel touching the hood plate (0 gap): a second, unintended support path', 'fail',
          st, 'fail' in st, 'lens row is overlap-only (<= 0.05 mm3); no minimum gap to chassis parts')
    h_over = box(-5.0, 0.0, ly + 20.5, ly + 30, lz - 30, lz + 30)
    st = [r['status'] for r in j7(dict(rows, lens=dict(shape=lens), hood=dict(shape=h_over)), parts_of, s=(0.0,))
          if r['mover'] == 'lens']
    probe('P12', 'lens barrel overlapping the hood', 'fail', st, 'fail' in st)


# ---------------------------------------------------------------- lens_clamp / joint checks / summarize
def p_clamp_joint():
    rows = CK.check_lens_clamp(L)
    pol = rows[0]
    probe('P13', 'anchor polygon with the LR foot only in compression (bolted-only polygon misses the axis)',
          'fail or WARN', dict(status=pol['status'], margin=pol['margin_mm'], bolted_only=pol['bolted_only_margin_mm']),
          pol['status'] != 'pass' or pol.get('warn'), 'bolted_only_margin is reported, never gated (G5)')
    R = dict(j7_float=[dict(status='pass')], lens_support=[dict(status='pass')],
             lens_clamp=[dict(status='pass'), dict(status='info', warn='M_sep < 5 g')] * 1, inserts=[dict(status='pass')])
    R2 = dict(R, lens_clamp=[dict(status='pass')] + [dict(status='info', warn='w') for _ in range(3)])
    j = next(r for r in CK.check_joint_checks(L, R2) if r['id'] == 'J7_camera')
    probe('P14', 'every per-lens clamp row WARN; only the anchor-polygon row passes', 'not a plain pass',
          j['status'], j['status'] != 'pass', 'one pass row anywhere satisfies ">= 1 pass"')
    s = B.summarize('lens_clamp', [dict(status='info')], info_neutral=True)
    probe('P15', 'lens_clamp with info rows only', 'fail', s['status'], s['status'] == 'fail')
    s = B.summarize('j7_float', [])
    probe('P16', 'j7_float empty', 'fail', s['status'], s['status'] == 'fail')
    s = B.summarize('inserts', [dict(status='n/a')])
    probe('P17', "unknown row status 'n/a'", 'fail', s['status'], s['status'] == 'fail')
    out = CK.check_inserts(L, {})
    probe('P18', 'inserts with no part solids', 'fail', sorted({r['status'] for r in out}),
          all(r['status'] == 'fail' for r in out) and len(out) == 4)


# ---------------------------------------------------------------- evidence / gate registry
def rec(item, state, art, verdict='pass', **kw):
    return dict(dict(item=item, state=state, artifacts=art, profile='p', verdict=verdict, date='2026-10-06', by='a'),
                **kw)


def ev_item(state, item, r, cur, req):
    errs = B.validate_record(r)
    recs = [dict(file='x.json', index=0, rec=r, errors=errs)]
    return B.evaluate_item(state, item, recs, cur, req)


def p_evidence():
    h = lambda c: c * 64  # noqa: E731
    cmap = {'G-COL-1': ['stl/coupons/collar_hood_plate.stl', 'stl/coupons/collar_part.stl',
                        'stl/coupons/collar_tub_front.stl']}
    cur = {k: h('a') for k in cmap['G-COL-1']}
    ok = {k: h('a') for k in cmap['G-COL-1']}
    o = ev_item('coupon_validation', 'G-COL-1', rec('G-COL-1', 'coupon_validation', ok), cur, cmap['G-COL-1'])
    probe('P19', 'control: G-COL-1 record on current coupon hashes', 'pass', o['outcome'], o['outcome'] == 'pass')
    cur2 = dict(cur, **{'stl/coupons/collar_part.stl': h('b')})
    o = ev_item('coupon_validation', 'G-COL-1', rec('G-COL-1', 'coupon_validation', ok), cur2, cmap['G-COL-1'])
    probe('P20', 'collar coupon re-cut (hash change) after a G-COL-1 pass', 'stale', o['outcome'], o['outcome'] == 'stale')
    # P21: coupon gate whose coupons are not in the manifest -> required [] -> any current artifact closes it
    req = B.required_artifacts_of('coupon_validation', {})('G-COL-1')
    spec = os.path.relpath(os.path.join(D2, 'SPEC.md'), B.ROOT).replace(os.sep, '/')
    o = ev_item('coupon_validation', 'G-COL-1', rec('G-COL-1', 'coupon_validation', {spec: B.sha(os.path.join(D2, 'SPEC.md'))}),
                {}, req)
    probe('P21', 'coupon gate missing from coupons-manifest (cmap empty); record names only SPEC.md', 'rejected',
          dict(required=req, outcome=o['outcome']), o['outcome'] != 'pass',
          'evaluate_item: required [] = "any current artifact"')
    # P22: G-CAM-2 required artifacts
    r_cam2 = B.required_artifacts_of('assembly_operation', {})('G-CAM-2')
    need = {'stl/lens_collar.stl', 'stl/tub.stl', 'stl/hood.stl', 'stl/panel.stl'}
    probe('P22', 'G-CAM-2 binding (assembled sag test) includes collar/tub/hood/panel STLs + gate doc', 'bound',
          dict(n=len(r_cam2), doc=[x for x in r_cam2 if x.endswith('.md')], has=sorted(need & set(r_cam2)),
               modifiers=any('modifiers' in x for x in r_cam2)),
          need <= set(r_cam2) and any(x.endswith('.md') for x in r_cam2),
          'modifier meshes (insert-boss perimeters) are not bound to assembly items')
    for g in ('G-CAM-1', 'G-LENS'):
        r = B.required_artifacts_of('measured_fit', {})(g)
        probe('P23' if g == 'G-CAM-1' else 'P24', '%s binding' % g, 'gate doc', r, bool(r),
              'measured-part gate: bound to its acceptance doc only (correct: it measures purchased parts)')
    # P25: malformed records
    bad = [rec('G-COL-1', 'coupon_validation', [['a', h('a')]]),
           rec('G-COL-1', 'coupon_validation', {k: h('A') for k in ok}),
           rec(['G-COL-1'], 'coupon_validation', ok),
           rec('G-COL-1', 'coupon_validation', ok, verdict='PASS?'),
           rec('G-COL-1', 'coupon_validation', ok, date='not a date', by='x')]
    errs = [bool(B.validate_record(r)) for r in bad]
    probe('P25', 'malformed records: list artifacts / upper-case hex / list item / bad verdict / bad date',
          'all rejected', errs, all(errs[:4]), 'date is not validated (free text) -- last entry')
    # P26: registry: which coupon gates in the live receipt map to no coupon STL
    hg = B.hardware_gates()
    si = B.state_items(hg)
    _, cm, _ = B.coupon_artifacts(B.OUT)
    empty = [g for g in si['coupon_validation'] if not cm.get(g)]
    probe('P26', 'live coupon_validation items with no coupon STL bound (would accept any artifact)', 'none',
          dict(items=si['coupon_validation'], unbound=empty), not empty)
    reg = {g: st for st, items in si.items() for g in items if g in ('G-CAM-1', 'G-CAM-2', 'G-COL-1', 'G-LENS')}
    probe('P27', 'state of G-CAM-1 (MP-CAM) / G-LENS / G-COL-1 / G-CAM-2', 'measured/measured/coupon/assembly',
          reg, reg == {'G-CAM-1': 'measured_fit', 'G-LENS': 'measured_fit', 'G-COL-1': 'coupon_validation',
                       'G-CAM-2': 'assembly_operation'})
    probe('P28', "'MP-CAM' as a gate id", 'registered or aliased', 'MP-CAM' in hg['gates'] or
          any('MP-CAM' in g for g in hg['gates']), 'MP-CAM' in hg['gates'],
          'hardware_gates() only harvests G-*; a record with item "MP-CAM" would be unmatched (keeps state open)')


# ---------------------------------------------------------------- registry de-dup / mass_com
def p_registry():
    from types import SimpleNamespace
    a = dict(id='tub_front_wall_seat', part='tub', origin=(-3.95, -20.0, 30.0))
    b = dict(id='tub_front_wall_seat', part='tub', origin=(-3.95, 11.0, 86.0))
    got = CK.registry(SimpleNamespace(CRITICAL_FEATURES=[a, b]), 'CRITICAL_FEATURES')
    probe('P29', 'two CRITICAL_FEATURES entries share an id (r5 re-uses tub_front_wall_seat, layout.py 1049 vs 1589)',
          'fail (duplicate id)', [g['origin'] for g in got], len(got) == 2,
          'registry() de-duplicates last-wins silently: the r4 plain-wall probe is dropped without a row')
    import inspect
    src = inspect.getsource(B.run_full)
    probe('P30', 'mass_com category: CoM far outside any balance rule', 'fail', "status = 'pass' if total_g > 0",
          "total_g'] > 0" not in src, 'mass_com counts as one of the 27 passing categories with no rule')


if __name__ == '__main__':
    for f in (p_lens_support, p_j7, p_clamp_joint, p_evidence, p_registry):
        try:
            f()
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            RES.append(dict(id=f.__name__, error='%s: %s' % (type(e).__name__, e)))
    with open(os.path.join(HERE, 'logic-audit.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(date='2026-10-06', script='logic_planted.py', probes=RES), fh, indent=1, default=str)
    print('%d probes, %d missed' % (len(RES), sum(1 for r in RES if not r.get('caught', False))))
