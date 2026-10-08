# SPDX-License-Identifier: MIT
"""r3 regression cases for the 2026-10-05 audit (REVIEW.md s2/s3, check_evidence_logic.py). The evidence cases are pure
Python; evidence fixtures live in a TemporaryDirectory, critical-feature probes use a synthetic chord
function (they test the checker's logic, not the camera's geometry). Each case asserts the CORRECTED behaviour.
r5: the J7-R cases use small synthetic CadQuery solids, the real camera/lens proxies, and a cached current-source
lens collar. Planted geometry faults from research/r5-lens-support/verify/p_integrity.py use positive controls and
assert the intended failure channel. No exported STEP/STL or physical evidence is reused. Run through run_locked.py.

Run (repo root): python3 cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r3_regressions.py
  --against-r2   also run the comparable cases against the r2 code in candidate-fr1/_base/ and show they fail there
"""
import json
import os
import sys
import tempfile
from functools import lru_cache
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402

H = {k: (c * 64) for k, c in (('panel', 'a'), ('cap1', 'b'), ('cap2', 'c'), ('old', '0'), ('cpanel', 'd'))}
CUR = {'stl/panel.stl': H['panel'], 'stl/coupons/cap_retention_grip.stl': H['cap1'],
       'stl/coupons/cap_retention_cap.stl': H['cap2'], 'stl/coupons/base_edge_panel.stl': H['cpanel']}
CMAP = {'G-CAP-1': ['stl/coupons/cap_retention_cap.stl', 'stl/coupons/cap_retention_grip.stl']}


def rec(item, state, artifacts, verdict='pass', **kw):
    return dict(dict(item=item, state=state, artifacts=artifacts, profile='test profile', verdict=verdict,
                     date='2026-10-05', by='test'), **kw)


def ev(files, state, items):
    """Write {relpath: content} under a temp evidence dir; evaluate one state against CUR / CMAP."""
    with tempfile.TemporaryDirectory(prefix='d2-r3-evidence-') as td:
        for rel, body in files.items():
            p = os.path.join(td, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(body if isinstance(body, str) else json.dumps(body))
        recs, ignored, _ = B.load_records(td)
    req = (lambda it: ['stl/%s.stl' % it]) if state == 'slicer_review' else (lambda it: CMAP.get(it, []))
    st = B.evidence_state(state, 'x', 'test', items, recs, CUR, req)
    return st, ignored


CAP_OK = {'stl/coupons/cap_retention_cap.stl': H['cap2'], 'stl/coupons/cap_retention_grip.stl': H['cap1']}


# ------------------------------------------------------------------------------------------- evidence (audit s2)
def test_failed_verdict_stays_open():
    st, _ = ev({'coupons/g-cap-1.json': rec('G-CAP-1', 'coupon_validation', CAP_OK, 'fail')},
               'coupon_validation', ['G-CAP-1'])
    assert st['failed'] == ['G-CAP-1'] and st['open'] and st['items']['G-CAP-1']['evidence_complete']
    assert B.open_evidence_list(dict(coupon_validation=st)) == ['coupon_validation (fail: G-CAP-1)']


def test_stale_r1_record_is_stale():
    st, _ = ev({'coupons/G-CAP-1-r1.json': rec('G-CAP-1', 'coupon_validation', dict(CAP_OK, **{
        'stl/coupons/cap_retention_cap.stl': H['old']}), revision='r1')}, 'coupon_validation', ['G-CAP-1'])
    assert st['stale'] == ['G-CAP-1'] and st['open'] and not st['items']['G-CAP-1']['evidence_complete']
    assert 'stale: G-CAP-1' in B.open_evidence_list(dict(coupon_validation=st))[0]


def test_coupon_record_cannot_cover_production_part():
    st, _ = ev({'slicer/base_edge_panel.json': rec('panel', 'slicer_review',
                                                  {'stl/coupons/base_edge_panel.stl': H['cpanel']})},
               'slicer_review', ['panel'])
    it = st['items']['panel']
    assert it['outcome'] == 'rejected' and it['rejected'] and 'coupon artifact' in it['rejected'][0]['why']
    assert st['open'] and st['items_pass'] == 0


def test_file_names_are_not_evidence():
    st, ignored = ev({'slicer/panel.md': 'verdict: pass\n', 'slicer/old-panel-r1.md': 'verdict: pass\n'},
                     'slicer_review', ['panel'])
    assert sorted(ignored) == ['slicer/old-panel-r1.md', 'slicer/panel.md'] and st['status'] == 'not run'


def test_old_revision_production_record_is_stale():
    st, _ = ev({'slicer/old-panel-r1.json': rec('panel', 'slicer_review', {'stl/panel.stl': H['old']})},
               'slicer_review', ['panel'])
    assert st['stale'] == ['panel'] and st['open']


def test_conflicting_records():
    st, _ = ev({'coupons/a.json': rec('G-CAP-1', 'coupon_validation', CAP_OK, 'pass'),
                'coupons/b.json': rec('G-CAP-1', 'coupon_validation', CAP_OK, 'fail')},
               'coupon_validation', ['G-CAP-1'])
    assert st['conflict'] == ['G-CAP-1'] and st['open']


def test_missing_required_coupon_artifact_rejected():
    st, _ = ev({'coupons/a.json': rec('G-CAP-1', 'coupon_validation',
                                      {'stl/coupons/cap_retention_cap.stl': H['cap2']})},
               'coupon_validation', ['G-CAP-1'])
    assert st['items']['G-CAP-1']['outcome'] == 'rejected' and 'cap_retention_grip' in \
        st['items']['G-CAP-1']['rejected'][0]['why']


def test_current_pass_closes_only_when_all_items_pass():
    files = {'slicer/p.json': rec('panel', 'slicer_review', {'stl/panel.stl': H['panel']})}
    st, _ = ev(files, 'slicer_review', ['panel'])
    assert not st['open'] and st['status'].startswith('all 1 items') and B.open_evidence_list(
        dict(slicer_review=st)) == []
    st, _ = ev(files, 'slicer_review', ['panel', 'tub'])
    assert st['open'] and st['not_run'] == ['tub']


def test_calibration_items_registered():
    si = B.state_items(dict(gates={}))
    assert {'G-KNOB-1', 'G-COMB-1', 'G-J4-1'} <= set(si['coupon_validation'])
    _, cmap, _ = B.coupon_artifacts(os.path.join(HERE, 'out'))
    assert cmap['G-KNOB-1'] and cmap['G-COMB-1'] and cmap['G-J4-1'] == ['stl/coupons/keyhole_slot.stl',
                                                                        'stl/coupons/tongue.stl']


def test_unknown_status_rejected():
    for s in ('not run', 'error', None):
        for neutral in (True, False):
            r = B.summarize('critical_features', [dict(status='pass'), dict(status=s)], info_neutral=neutral)
            assert r['status'] == 'fail' and r['unknown_statuses'], (s, neutral, r)


def test_info_only_category_does_not_pass():
    assert B.summarize('removals', [dict(status='info')] * 2, info_neutral=True)['status'] == 'fail'
    assert B.summarize('removals', [dict(status='info'), dict(status='pass')], info_neutral=True)['status'] == 'pass'
    assert B.summarize('removals', [dict(status='info'), dict(status='stub'), dict(status='pass')],
                       info_neutral=True)['status'] == 'stub'


def test_root_is_found_from_a_deeper_folder():
    with tempfile.TemporaryDirectory() as td:
        for d in ('cad/gs8-d2-v1/candidate-fr1', 'electronics'):
            os.makedirs(os.path.join(td, d))
        assert os.path.samefile(B.find_root(os.path.join(td, 'cad', 'gs8-d2-v1', 'candidate-fr1')), td)


# ------------------------------------------------------------------------------------------- critical features (s3)
def _layout(feats, joints=None, lb=('hood',), parts=('hood',), gates=None):
    return SimpleNamespace(PARTS={p: {} for p in parts}, CRITICAL_FEATURES=list(feats), LOAD_BEARING_PARTS=list(lb),
                           FEATURE_CLASS_MIN={'lip': 1.6, 'flexure': 1.2}, FEATURE_CLASS_GATED=('flexure',),
                           FEATURE_GATES=gates or {}, FDM={'MIN_WALL_LOADED': 1.6}, REQUIRED_JOINT_IDS=(),
                           CRITICAL_JOINTS=[dict(id='J', parts=list(parts), required=[f['id'] for f in feats])]
                           if joints is None else joints)


def _run(lay, chord, parts=('hood',)):
    calls = []
    keep = CK.chord

    def fake(shape, p, d):
        calls.append(tuple(round(x, 6) for x in p))
        return chord(p)
    CK.chord = fake
    try:
        rows = CK.check_critical_features(lay, {p: dict(shape=object(), stub=False) for p in parts})
    finally:
        CK.chord = keep
    return rows, calls


LIP = dict(id='hood_groove_lower_lip', part='hood', structural=True, origin=(0.0, 0.0, 0.0), direction=(0, 0, 1),
           span=(4, 12.0, (1, 0, 0)), min_mm=1.6, cls='lip')
OK = (2.0, -1.0, 1.0, None)
MISS = (None, None, None, 'synthetic: outside the material')


def _feat(rows, fid):
    return next(r for r in rows if r.get('kind') == 'feature' and r['id'] == fid)


def test_even_span_measures_origin_and_stale_origin_fails():
    rows, calls = _run(_layout([LIP]), lambda p: MISS if all(abs(x) < 1e-12 for x in p) else OK)
    assert (0.0, 0.0, 0.0) in calls
    r = _feat(rows, LIP['id'])
    assert r['status'] == 'fail' and r['error'].startswith('stale origin')
    assert CK.feature_offsets(LIP)[0][0] == 0.0 and len(CK.feature_offsets(LIP)[0]) == 5


def test_unexpected_missing_ray_fails_and_expect_outside_allows_it():
    miss6 = lambda p: MISS if abs(p[0] - 6.0) < 1e-9 else OK  # noqa: E731
    r = _feat(_run(_layout([LIP]), miss6)[0], LIP['id'])
    assert r['status'] == 'fail' and 'unexpected missing ray' in r['error']
    f = dict(LIP, expect_outside=dict(offsets=[6.0], why='synthetic relief'))
    r = _feat(_run(_layout([f]), miss6)[0], LIP['id'])
    assert r['status'] == 'pass' and r['expected_outside'] == [6.0]
    r = _feat(_run(_layout([f]), lambda p: OK)[0], LIP['id'])          # declared miss is in material: stale declaration
    assert r['status'] == 'fail' and 'stale declaration' in r['error']
    f2 = dict(LIP, expect_outside=dict(offsets=[6.0]))                   # no reason given
    assert _feat(_run(_layout([f2]), miss6)[0], LIP['id'])['status'] == 'fail'


def test_deleted_joint_entries_fail():
    keep = dict(LIP, id='remaining_feature', span=None)
    lay = _layout([keep], joints=[dict(id='J4', parts=['hood'], required=['remaining_feature', 'base_keyhole_lip_f_l'])])
    rows = _run(lay, lambda p: OK)[0]
    j = next(r for r in rows if r.get('kind') == 'joint' and r['id'] == 'J4')
    assert j['status'] == 'fail' and 'base_keyhole_lip_f_l: missing entry' in j['error']
    part_rows = [r for r in rows if r.get('kind') == 'coverage']
    assert part_rows and all(r['status'] == 'pass' for r in part_rows)     # the old per-part rule alone stays green


def test_joint_registry_required():
    rows = _run(_layout([dict(LIP, span=None)], joints=[]), lambda p: OK)[0]
    assert any(r.get('kind') == 'joint' and r['status'] == 'fail' for r in rows)
    lay = _layout([dict(LIP, span=None)], joints=[dict(id='J', parts=['hood'], required=[LIP['id']])],
                  lb=('hood', 'tub'), parts=('hood', 'tub'))
    rows = _run(lay, lambda p: OK, parts=('hood', 'tub'))[0]
    assert any(r.get('id') == 'part:tub' and r['status'] == 'fail' for r in rows)


def test_flexure_is_gated_exception_not_ordinary_pass():
    flex = dict(id='grip_cap_detent_arm', part='hood', structural=True, origin=(1, 0, 0), direction=(0, 1, 0),
                min_mm=1.2, cls='flexure')
    thin = lambda p: (1.5, -0.75, 0.75, None)  # noqa: E731
    rows = _run(_layout([flex], gates={'grip_cap_detent_arm': 'G-CAP-1'}), thin)[0]
    r, j = _feat(rows, flex['id']), next(r for r in rows if r.get('kind') == 'joint')
    assert r['status'] == 'info' and 'G-CAP-1' in r['exception'] and j['gated_exceptions']
    assert j['status'] == 'info' and 'G-CAP-1' in j['exception']     # fix-baseline V-L1: not counted as a pass
    rows = _run(_layout([flex]), thin)[0]                                    # no gate: FAIL
    assert _feat(rows, flex['id'])['status'] == 'fail'


def test_baseline_registry_joints_complete():
    import layout as L
    ids = {f['id']: f for f in CK.registry(L, 'CRITICAL_FEATURES')}
    req = [r for j in CK.registry(L, 'CRITICAL_JOINTS') for r in j['required']]
    assert not [r for r in req if r not in ids], 'joint names a missing feature'
    assert all(any(p in j['parts'] for j in L.CRITICAL_JOINTS) for p in CK.registry(L, 'LOAD_BEARING_PARTS'))
    assert {'grip_cap_detent_arm', 'grip_cap_detent_dimple_wall', 'grip_cap_groove_corner'} <= set(L.FEATURE_GATES)


# ------------------------------------------------------------------------------------------- r3 fix-baseline cases
# (verifier findings 2026-10-05: V-H1, V-M1..M4, V-L1, V-L2; fixtures E7-E12 / C4 / C7 / C8 of that review)
PANEL_OK = {'stl/panel.stl': H['panel']}


def test_unknown_state_fail_record_stays_open():                 # V-H1 / E7
    st, _ = ev({'slicer/x.json': rec('panel', 'slicer', PANEL_OK, 'fail'),
                'slicer/p.json': rec('panel', 'slicer_review', PANEL_OK)}, 'slicer_review', ['panel'])
    assert st['open'] and st['items']['panel']['outcome'] == 'rejected' and st['rejected'] == ['panel']
    assert 'unknown state' in st['items']['panel']['rejected'][0]['why']
    assert 'rejected: panel' in B.open_evidence_list(dict(slicer_review=st))[0]


def test_unreadable_record_is_listed_and_open():                 # V-H1 / E8
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, 'slicer'))
        with open(os.path.join(td, 'slicer', 'bad.json'), 'w') as f:
            f.write('{"item": "panel", "state": "slicer_review", "verdict": "fail", ')
        with open(os.path.join(td, 'slicer', 'ok.json'), 'w') as f:
            json.dump(rec('panel', 'slicer_review', PANEL_OK), f)
        recs, _, _ = B.load_records(td)
    un = B.unassigned_records(recs, {'slicer_review': ['panel']})
    assert len(un) == 1 and 'unreadable JSON' in un[0]
    st = B.evidence_state('slicer_review', 'x', 't', ['panel'], recs, CUR, lambda it: ['stl/panel.stl'])
    oe = B.open_evidence_list(dict(slicer_review=st), un)
    assert any(x.startswith('evidence (1 unassigned/unreadable') for x in oe)


def test_rejected_fail_beside_pass_stays_open():                 # V-M1 / E9
    bad = rec('panel', 'slicer_review', PANEL_OK, 'fail')
    del bad['by']
    st, _ = ev({'slicer/a.json': bad, 'slicer/b.json': rec('panel', 'slicer_review', PANEL_OK)},
               'slicer_review', ['panel'])
    assert st['open'] and st['items']['panel']['outcome'] == 'rejected'


def test_item_typo_keeps_state_open():                           # V-M1 / E12
    st, _ = ev({'slicer/a.json': rec('Panel', 'slicer_review', PANEL_OK, 'fail'),
                'slicer/b.json': rec('panel', 'slicer_review', PANEL_OK)}, 'slicer_review', ['panel'])
    assert st['open'] and st['unmatched_records'] and 'unmatched: 1' in B.open_evidence_list(
        dict(slicer_review=st))[0]


def test_measured_and_assembly_records_name_doc_and_stls():      # V-M2 / E10
    import layout as L
    fp = os.path.join(HERE, 'FASTENER-POLICY.md')
    only_doc = {'cad/gs8-d2-v1/FASTENER-POLICY.md': B.sha(fp)}
    for state, gate in (('assembly_operation', 'G-W6'), ('measured_fit', 'G-MP-PACK')):
        req = B.required_artifacts_of(state, {})
        need = req(gate)
        assert need and need[0] == B.gate_doc(gate)
        if state == 'assembly_operation':
            assert {'stl/%s.stl' % p for p in L.PARTS} <= set(need)
        st = B.evidence_state(state, 'x', 't', [gate], [dict(file='a.json', index=0, rec=rec(gate, state, only_doc),
                                                              errors=[])], {}, req)
        assert st['open'] and st['items'][gate]['outcome'] == 'rejected', (state, st['items'])


def test_empty_category_fails():                                 # V-M4 / C8
    assert B.summarize('sweeps', [])['status'] == 'fail'
    assert B.summarize('removals', [], info_neutral=True)['status'] == 'fail'


def test_deleted_joint_with_its_probes_fails():                  # V-M3 / C4
    f = dict(LIP, span=None)
    lay = _layout([f], joints=[dict(id='J1', parts=['hood'], required=[f['id']])])
    lay.REQUIRED_JOINT_IDS = ('J1', 'J4_base_tub')
    rows = _run(lay, lambda p: OK)[0]
    assert any(r.get('id') == 'J4_base_tub' and r['status'] == 'fail' for r in rows)
    fr = dict(id='FR_x', parts=['hood'], required=[f['id']], replaces=['J4_base_tub'])
    lay.FR_JOINTS = [fr]
    lay.CRITICAL_JOINTS = list(lay.CRITICAL_JOINTS) + [fr]        # r4: a replacement counts only once merged + validated
    rows = _run(lay, lambda p: OK)[0]
    assert not any(r.get('id') == 'J4_base_tub' for r in rows)
    del lay.REQUIRED_JOINT_IDS                                   # no registry at all: FAIL, never silent
    rows = _run(lay, lambda p: OK)[0]
    assert any(r.get('id') == 'REQUIRED_JOINT_IDS' and r['status'] == 'fail' for r in rows)


def test_joint_rejects_unknown_feature_status():                 # V-L2 / C7
    lay = _layout([], joints=[dict(id='J', parts=['hood'], required=['a'])])
    rows = CK.check_joint_coverage(lay, [dict(kind='feature', id='a', part='hood', status='not run', measured_mm=2.0)])
    assert rows[0]['status'] == 'fail' and "status 'not run'" in rows[0]['error']


def test_baseline_joint_ids_fixed():                             # V-M3: the real registry equals the fixed list
    import layout as L
    assert {j['id'] for j in L.CRITICAL_JOINTS} == set(L.REQUIRED_JOINT_IDS) and len(L.REQUIRED_JOINT_IDS) == 12


# ------------------------------------------------------------------------------------------- r4 (audit 2026-10-05-r3)
def test_malformed_field_types_are_rejected_not_crashing():      # r3 audit logic issue 2
    base = rec('panel', 'slicer_review', {'stl/panel.stl': H['panel']}, 'fail')
    for change in (dict(state=['slicer_review']), dict(item={'part': 'panel'}), dict(profile=['x']), dict(by=3)):
        st, _ = ev({'slicer/bad.json': dict(base, **change)}, 'slicer_review', ['panel'])     # must not raise
        assert st['open'], change
        if 'item' in change:
            assert st['unmatched_records'], change                 # kept visible as an unmatched record
        else:
            assert st['rejected'] == ['panel'] and st['items']['panel']['rejected'], change
        errs = B.validate_record(dict(base, **change))
        assert errs, change
    assert B.unassigned_records([dict(file='a.json', index=0, rec=dict(base, state=['x'], item={'p': 1}),
                                      errors=['x'])], {'slicer_review': ['panel']})


def test_unvalidated_replacement_cannot_waive_required_joint():  # r3 audit logic issue 3
    f = dict(LIP, span=None)
    lay = _layout([f], joints=[dict(id='J1', parts=['hood'], required=[f['id']])])
    lay.REQUIRED_JOINT_IDS = ('J1', 'J4')
    lay.FR_JOINTS = [dict(id='FR_phantom', parts=['hood'], required=[], replaces=['J4'])]   # never merged
    rows = _run(lay, lambda p: OK)[0]
    j4 = [r for r in rows if r.get('id') == 'J4']
    assert j4 and j4[0]['status'] == 'fail' and 'FR_phantom' in j4[0]['error']
    bad = dict(id='FR_empty', parts=['hood'], required=[], replaces=['J4'])                 # merged, nothing covered
    lay.FR_JOINTS, lay.CRITICAL_JOINTS = [bad], list(lay.CRITICAL_JOINTS) + [bad]
    rows = _run(lay, lambda p: OK)[0]
    assert any(r.get('id') == 'J4' and r['status'] == 'fail' for r in rows)


def test_cable_routes_real_layout_and_synthetic_faults():        # r4 wiring: route continuity / ends / length
    import copy
    import layout as L
    rows = CK.check_cable_routes(L)
    assert {r['cable'] for r in rows} == {c['id'] for c in L.CABLES}
    assert all(r['status'] in ('pass', 'info') for r in rows), [r.get('error') for r in rows if r['status'] == 'fail']
    assert B.summarize('cable_routes', rows, info_neutral=True)['status'] == 'pass'
    lay = SimpleNamespace(KEEPOUTS=dict(L.KEEPOUTS), COTS=L.COTS, CABLES=copy.deepcopy(L.CABLES))
    qt = next(c for c in lay.CABLES if c['id'] == 'qt')
    qt['via'].remove('ko_lead_link')                         # the r3 10 mm gap comes back
    r = next(x for x in CK.check_cable_routes(lay) if x['cable'] == 'qt')
    assert r['status'] == 'fail' and 'gap 10.00' in r['error']
    qt['via'].insert(2, 'ko_lead_link')
    qt['length'] = 100                                        # shorter than the route + allowance
    r = next(x for x in CK.check_cable_routes(lay) if x['cable'] == 'qt')
    assert r['status'] == 'fail' and 'cable length 100' in r['error']
    run = next(c for c in lay.CABLES if c['id'] == 'run_lead')
    run['via'].remove('ko_run_link')                          # the r3 edge-only touch (4 x 0.4 window)
    r = next(x for x in CK.check_cable_routes(lay) if x['cable'] == 'run_lead')
    assert r['status'] == 'fail' and 'passage only' in r['error']


def test_whole_part_test_is_split_and_goes_stale():              # r3 audit logic issue 1
    import layout as L
    hg = B.hardware_gates()
    assert 'G-SNAP-2/whole' in hg['gates'] and 'G-PANEL-1/whole' in hg['gates'] and 'G-KEEP-1/whole' in hg['gates']
    si = B.state_items(hg)
    assert 'G-SNAP-2/whole' in si['assembly_operation'] and 'G-SNAP-2' in si['coupon_validation']
    req = B.required_artifacts_of('assembly_operation', {})('G-SNAP-2/whole')
    assert req[0] == B.gate_doc('G-SNAP-2') and 'stl/hood.stl' in req and 'stl/tub.stl' in req
    art = {k: 'e' * 64 for k in req[1:]}
    art[req[0]] = B.resolve_artifact(req[0], {})[1]
    r = [dict(file='w.json', index=0, rec=rec('G-SNAP-2/whole', 'assembly_operation', art), errors=[])]
    cur = {k: v for k, v in art.items() if k.startswith('stl/')}
    ok = B.evaluate_item('assembly_operation', 'G-SNAP-2/whole', r, cur, req)
    assert ok['outcome'] == 'pass', ok
    changed = dict(cur, **{'stl/hood.stl': '0' * 64})
    assert B.evaluate_item('assembly_operation', 'G-SNAP-2/whole', r, changed, req)['outcome'] == 'stale'
    # the gate passes only when both halves pass
    hg2 = dict(source_docs={}, gates={'G-SNAP-2': 'open (no record)', 'G-SNAP-2/whole': 'open (no record)'})
    states = dict(coupon_validation=dict(items={'G-SNAP-2': dict(outcome='pass', rejected=[])}),
                  assembly_operation=dict(items={}))
    B.apply_gate_outcomes(hg2, states)
    assert hg2['gates']['G-SNAP-2'].startswith('open') and 'G-SNAP-2/whole' in hg2['gates']['G-SNAP-2']
    states['assembly_operation']['items']['G-SNAP-2/whole'] = dict(outcome='pass', rejected=[])
    hg3 = dict(source_docs={}, gates={'G-SNAP-2': 'open (no record)', 'G-SNAP-2/whole': 'open (no record)'})
    B.apply_gate_outcomes(hg3, states)
    assert hg3['gates']['G-SNAP-2'].startswith('recorded pass')
    assert set(L.PARTS) >= {'hood', 'tub', 'panel', 'pi_keeper'}


# ------------------------------------------------------------------------------------------- r5 (J7-R) lens support
# r5 (judge 3 s6.10; integrity review F1-F3): synthetic FAILs for the J7-R checks. Small CadQuery solids stand in for
# the tub lip and panel keeper; camera/lens proxies and the cached collar come from current source.
def _j7_rows(lip_gap=None, keeper_gap=None):
    import cadquery as cq
    import layout as L
    C, (ly, lz) = L.CAM, L.LENS_AXIS
    gap = C['lip_gap'] if lip_gap is None else lip_gap
    x0 = L.BFAR_FACE_X + gap
    lip = (cq.Solid.makeCylinder(C['cb_d'] / 2 + 2.0, L.XT1 - x0, cq.Vector(x0, ly, lz), cq.Vector(1, 0, 0))
           .cut(cq.Solid.makeCylinder(C['lip_d'] / 2, L.XT1 - x0, cq.Vector(x0, ly, lz), cq.Vector(1, 0, 0))))
    cb = L.X_FW_IN              # + the counterbore wall (dia cb_d) from the wall inner face up to the lip land
    lip = lip.fuse(cq.Solid.makeCylinder(C['cb_d'] / 2 + 2.0, x0 - cb, cq.Vector(cb, ly, lz), cq.Vector(1, 0, 0))
                   .cut(cq.Solid.makeCylinder(C['cb_d'] / 2, x0 - cb, cq.Vector(cb, ly, lz), cq.Vector(1, 0, 0))))
    k = C['keeper']
    x1 = k['x'][1] if keeper_gap is None else L.cam_cover_rear(L.S_MAX) - keeper_gap
    keeper = cq.Solid.makeBox(3.33, k['y'][1] - k['y'][0], k['z'][1] - k['z'][0], cq.Vector(x1 - 3.33, k['y'][0], k['z'][0]))
    return L, {'tub': dict(shape=lip, kind='printed'), 'panel': dict(shape=keeper, kind='printed')}


def _bad(rows):
    return [(r['mover'], r['s'], r.get('error')) for r in rows if r['status'] != 'pass']


def test_j7_float_real_datums_pass():
    L, rows = _j7_rows()
    out = CK.check_j7_float(L, rows)
    assert not _bad(out), _bad(out)
    bf = next(r for r in out if r['mover'] == 'bfar' and r['s'] == 0.0)
    assert abs(bf['min_axial']['gap'] - L.CAM['lip_gap']) < 1e-3 and abs(bf['min_lateral']['gap'] - 0.75) < 1e-3
    bd = next(r for r in out if r['mover'] == 'body' and r['s'] == L.S_MAX)
    assert abs(bd['min_axial']['gap'] - 0.5) < 1e-3 and bd['min_axial']['to'] == 'panel'


def test_j7_float_lip_gap_zero_fails():
    L, rows = _j7_rows(lip_gap=0.0)
    bad = _bad(CK.check_j7_float(L, rows))
    assert bad and all(m == 'bfar' for m, _, _ in bad) and 'axial gap 0.000 to tub' in bad[0][2], bad


def test_j7_float_keeper_02_at_s_max_fails():
    L, rows = _j7_rows(keeper_gap=0.2)
    bad = _bad(CK.check_j7_float(L, rows))
    assert bad == [('body', L.S_MAX, bad[0][2])] and 'axial gap 0.200 to panel' in bad[0][2], bad


def test_lens_support_every_mass_without_support_fails():
    import layout as L
    # J7-R has no independent camera mount, even for a light M12 lens or the old threshold's exact boundary.
    entries = []
    for group, table in (('production', L.LENSES), ('data_only', L.LENSES_DATA_ONLY)):
        for mass in (20.0, 120.0, L.LOAD_MODEL['support_mass_g'], 300.0):
            name = '_t_no_support_%s_%g' % (group, mass)
            d = dict(L.LENSES_DATA_ONLY['computar_h6z0812'], name='synthetic unsupported lens', mass=mass)
            d.pop('support')
            table[name] = d
            entries.append((table, name))
    try:
        out = CK.check_lens_support(L)
    finally:
        for table, name in entries:
            del table[name]
    for _, name in entries:
        failed = [r for r in out if r['lens'] == name]
        assert len(failed) == 1 and failed[0]['item'] == 'support' and failed[0]['status'] == 'fail', failed
        assert 'no J7-R anchor' in failed[0]['error'], failed
    real = [r for r in out if not r['lens'].startswith('_t_')]          # the real table: no fail, WARNs only
    assert all(r['status'] in ('pass', 'info') for r in real) and any(r.get('warn') for r in real)
    assert B.summarize('lens_support', real, info_neutral=True)['status'] == 'pass'


def _box(x0, x1, y0, y1, z0, z1):
    import cadquery as cq
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _cylx(r, x0, x1, y, z):
    import cadquery as cq
    return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def _lateral_bump(L, gap=0.3, side=-1):
    ly, lz = L.LENS_AXIS
    edge = ly + side * (L.CAM['housing']['d'] / 2 + gap)
    y0, y1 = sorted((edge, edge + side * 0.5))
    return _box(-12.0, -9.0, y0, y1, lz - 1.0, lz + 1.0)


def _body_at_nominal(L, rows):
    return next(r for r in CK.check_j7_float(L, rows, s_values=(L.CAM['s_nom'],)) if r['mover'] == 'body')


def test_j7_float_lateral_03_fails():
    L, rows = _j7_rows()
    rows['hood'] = dict(shape=_lateral_bump(L), kind='printed')
    r = _body_at_nominal(L, rows)
    assert r['status'] == 'fail' and r['min_lateral'] == dict(gap=0.3, to='hood'), r
    assert r['offending_obstacles'] == ['hood'], r


def test_j7_float_diagonal_0354_fails():
    L, rows = _j7_rows()
    ly, lz = L.LENS_AXIS
    edge = ly + L.CAM['bfar']['d'] / 2
    rows['probe'] = dict(shape=_box(L.BFAR_FACE_X + 0.25, L.BFAR_FACE_X + 1.5,
                                    edge + 0.25, edge + 1.5, lz - 0.5, lz + 0.5), kind='printed')
    r = next(r for r in CK.check_j7_float(L, rows, s_values=(L.CAM['s_nom'],)) if r['mover'] == 'bfar')
    assert r['status'] == 'fail' and 'overall gap 0.354 to probe' in r['error'], r
    assert r['min_lateral']['gap'] >= r['rule']['lateral'] and r['min_axial']['gap'] >= r['rule']['axial'], r


def test_j7_float_axial_lip_02_fails():
    L, rows = _j7_rows(lip_gap=0.2)
    r = next(r for r in CK.check_j7_float(L, rows, s_values=(L.CAM['s_nom'],)) if r['mover'] == 'bfar')
    assert r['status'] == 'fail' and r['min_axial'] == dict(gap=0.2, to='tub'), r


def test_j7_float_real_fault_not_masked_by_unrelated_stub():
    L, rows = _j7_rows()
    rows['tub']['stub'] = True
    rows['hood'] = dict(shape=_lateral_bump(L), kind='printed')
    r = _body_at_nominal(L, rows)
    assert 'tub' in r['per_obstacle'] and r['status'] == 'fail', r
    assert r['offending_obstacles'] == ['hood'], r


def test_j7_float_only_offending_stub_is_stub():
    L, rows = _j7_rows()
    rows['hood'] = dict(shape=_lateral_bump(L), kind='printed', stub=True)
    r = _body_at_nominal(L, rows)
    assert r['status'] == 'stub' and r['offending_obstacles'] == ['hood'], r


def test_j7_float_closer_stub_cannot_mask_second_real_gap_fault():
    L, rows = _j7_rows()
    rows['stub_bump'] = dict(shape=_lateral_bump(L, 0.2), kind='printed', stub=True)
    rows['real_bump'] = dict(shape=_lateral_bump(L, 0.3, side=1), kind='printed')
    r = _body_at_nominal(L, rows)
    assert r['min_lateral']['to'] == 'stub_bump' and r['status'] == 'fail', r
    assert r['offending_obstacles'] == ['real_bump', 'stub_bump'], r


def test_j7_float_stub_overlap_cannot_mask_real_gap_fault():
    L, rows = _j7_rows()
    rows['stub_bump'] = dict(shape=_lateral_bump(L, -0.2), kind='printed', stub=True)
    rows['real_bump'] = dict(shape=_lateral_bump(L, 0.3, side=1), kind='printed')
    r = _body_at_nominal(L, rows)
    assert 'overlaps stub_bump' in r['error'] and r['status'] == 'fail', r
    assert r['offending_obstacles'] == ['real_bump', 'stub_bump'], r


def test_j7_float_no_obstacle_cannot_pass_or_be_stub():
    import layout as L
    rows = CK.check_j7_float(L, {}, s_values=(L.CAM['s_nom'],))
    assert rows and all(r['status'] == 'fail' and 'not measured' in r['error'] for r in rows), rows


def test_j7_float_lens_hits_hood_and_only_fault_stubs_downgrade():
    import cots
    L, rows = _j7_rows()
    ly, lz = L.LENS_AXIS
    rows['lens'] = dict(shape=cots.lens_proxy(L, 'kowa_lm6hc')[0], kind='cots')
    rows['hood'] = dict(shape=_box(20.0, 22.0, ly + 20.0, ly + 30.0, lz - 2.0, lz + 2.0), kind='printed')
    rows['tub']['stub'] = True
    for stub, status in ((False, 'fail'), (True, 'stub')):
        rows['hood']['stub'] = stub
        r = next(r for r in CK.check_j7_float(L, rows, s_values=(L.CAM['s_nom'],)) if r['mover'] == 'lens')
        assert r['status'] == status and set(r['overlaps']) == {'hood'}, r


@lru_cache(maxsize=1)
def _collar_fixture():
    """Current-source geometry, computed once. A stale release export cannot make the positive control pass."""
    import layout as L
    import cots
    import printed_collar as PC
    col = PC.build_part(L, 'lens_collar', lens='kowa_lm6hc').val()
    lens = cots.lens_proxy(L, 'kowa_lm6hc')[0]
    assert col.isValid() and len(col.Solids()) == 1
    baseline = CK.check_lens_support(L, collars={'kowa_lm6hc': col}, lens_shapes={'kowa_lm6hc': lens})
    assert all(r['status'] in ('pass', 'info') for r in baseline), baseline
    return col, lens


def _support_rows(col=None):
    import layout as L
    baseline, lens = _collar_fixture()
    rows = CK.check_lens_support(L, collars={'kowa_lm6hc': baseline if col is None else col},
                                 lens_shapes={'kowa_lm6hc': lens})
    return {r['item']: r for r in rows if r['lens'] == 'kowa_lm6hc'}


def test_lens_support_current_collar_geometry_passes():
    rows = _support_rows()
    for item in ('lens_seated', 'bore_measured', 'seat_measured', 'thumb_keepouts'):
        assert rows[item]['status'] == 'pass', rows[item]


def test_lens_support_oversize_bore_fails():
    import layout as L
    col, _ = _collar_fixture()
    cs, (ly, lz) = L.collar_spec('kowa_lm6hc'), L.LENS_AXIS
    bad = col.cut(_cylx(cs['bore_r'] + 0.15, cs['cone_x1'] + 0.3, cs['front_x'] + 0.1, ly, lz))
    r = _support_rows(bad)['bore_measured']
    assert r['status'] == 'fail' and abs(r['diametral'] - 0.6) < 1e-3, r


def test_lens_support_axially_shifted_collar_fails_both_directions():
    import cadquery as cq
    col, _ = _collar_fixture()
    for dx in (-0.3, 0.3):
        rows = _support_rows(col.translate(cq.Vector(dx, 0, 0)))
        assert rows['lens_seated']['status'] == rows['seat_measured']['status'] == 'fail', (dx, rows)


def test_lens_support_thumb_keepout_bump_fails():
    import layout as L
    col, _ = _collar_fixture()
    ly, lz = L.LENS_AXIS
    bad = col.fuse(_box(14.0, 15.5, ly + 20.0, ly + 23.0, lz - 1.0, lz + 1.0))
    r = _support_rows(bad)['thumb_keepouts']
    assert r['status'] == 'fail' and any(v > CK.VOL_TOL for v in r['overlap_mm3'].values()), r


def test_lens_support_band_over_moving_ring_fails():
    import layout as L
    seg = L.LENSES['kowa_lm6hc']['segments']
    try:
        L.LENSES['kowa_lm6hc']['segments'] = [tuple(s[:4]) + ('rot' if 'knurl' in s[3].lower() else s[4],) for s in seg]
        r = next(r for r in CK.check_lens_support(L) if r['lens'] == 'kowa_lm6hc' and r['item'] == 'band_fixed')
    finally:
        L.LENSES['kowa_lm6hc']['segments'] = seg
    assert r['status'] == 'fail' and r['moving_over_band'], r


@lru_cache(maxsize=1)
def _insert_fixture():
    """Minimal real-datum s_c1 boss and the current collar; unrelated M3 rows are excluded, never ignored."""
    import layout as L
    col, _ = _collar_fixture()
    s = next(s for s in L.SCREWS if s['id'] == 's_c1')
    b = L.TUB_INSERT_BOSSES['TL']
    y, z = b['c']
    boss = _cylx(b['od'] / 2, b['x'][0], L.XT1, y, z)
    boss = boss.cut(_cylx(L.M3['insert']['bore_d'] / 2, min(b['bore_x']), L.XT1 + 0.1, y, z))
    boss = boss.cut(_cylx(L.M3['clear_d'] / 2, b['x'][0] - 0.1, L.XT1 + 0.1, y, z))
    scope = SimpleNamespace(SCREWS=[s], M3=L.M3, FDM=L.FDM)
    rows = dict(tub=dict(shape=boss, kind='printed'), lens_collar=dict(shape=col, kind='printed'))
    control = CK.check_inserts(scope, rows)
    assert len(control) == 1 and control[0]['status'] == 'pass', control
    return scope, s, boss, col


def _insert_row(boss=None, col=None):
    scope, _, base_boss, base_col = _insert_fixture()
    rows = dict(tub=dict(shape=base_boss if boss is None else boss, kind='printed'),
                lens_collar=dict(shape=base_col if col is None else col, kind='printed'))
    result = CK.check_inserts(scope, rows)
    assert len(result) == 1 and result[0]['screw'] == 's_c1', result
    return result[0]


def test_inserts_valid_fixture_passes():
    r = _insert_row()
    assert r['status'] == 'pass' and r['tip_in_void'] and abs(r['bore_dia'] - 4.0) < 1e-3, r


def test_inserts_oversize_bore_fails():
    _, s, boss, _ = _insert_fixture()
    y, z = s['head_point'][1:]
    r = _insert_row(boss=boss.cut(_cylx(2.2, -6.8, -2.6, y, z)))
    assert r['status'] == 'fail' and 'bore dia' in r['error'] and abs(r['bore_dia'] - 4.4) < 1e-3, r


def test_inserts_thin_wall_fails():
    _, s, boss, _ = _insert_fixture()
    y, z = s['head_point'][1:]
    r = _insert_row(boss=boss.cut(_box(-7.7, -5.25, y + 3.2, y + 6.0, z - 4.0, z + 4.0)))
    assert r['status'] == 'fail' and 'wall 1.200' in r['error'] and abs(r['wall_min'] - 1.2) < 1e-3, r


def test_inserts_tip_bottoming_fails():
    _, s, boss, _ = _insert_fixture()
    y, z = s['head_point'][1:]
    r = _insert_row(boss=boss.fuse(_cylx(1.7, -7.6, -6.85, y, z)))
    assert r['status'] == 'fail' and not r['tip_in_void'] and 'screw bottoms' in r['error'], r


def test_inserts_shallow_bore_fails():
    _, s, boss, _ = _insert_fixture()
    y, z = s['head_point'][1:]
    r = _insert_row(boss=boss.fuse(_cylx(2.0, -6.95, -6.4, y, z)))
    assert r['status'] == 'fail' and 'bore depth' in r['error'] and abs(r['bore_depth'] - 3.7) < 1e-3, r


def test_inserts_undersize_collar_hole_fails():
    _, s, _, col = _insert_fixture()
    y, z = s['head_point'][1:]
    plug = _cylx(1.7, 0.0, 3.0, y, z).cut(_cylx(1.45, -0.1, 3.1, y, z))
    r = _insert_row(col=col.fuse(plug))
    assert r['status'] == 'fail' and 'clearance hole' in r['error'] and abs(r['head_clear_r'] - 1.45) < 1e-3, r


def test_lens_clamp_1500g_lens_fails():
    import layout as L
    name = '_t_overloaded'
    L.LENSES_DATA_ONLY[name] = dict(L.LENSES['kowa_lm6hc'], name='synthetic 1.5 kg lens', mass=1500.0)
    try:
        r = next(r for r in CK.check_lens_clamp(L) if r.get('lens') == name)
    finally:
        del L.LENSES_DATA_ONLY[name]
    assert r['status'] == 'fail' and 'M_sep' in r['error'] and r['ratio_static'] < L.LOAD_MODEL['sep_safety'], r


def test_lens_clamp_low_pinch_force_fails():
    import layout as L
    saved = L.LOAD_MODEL['pinch_N']
    try:
        L.LOAD_MODEL['pinch_N'] = 20.0
        r = next(r for r in CK.check_lens_clamp(L) if r.get('lens') == 'kowa_lm6hc')
    finally:
        L.LOAD_MODEL['pinch_N'] = saved
    assert r['status'] == 'fail' and 'M_sep' in r['error'] and r['ratio_static'] < L.LOAD_MODEL['sep_safety'], r


def _clamp_kowa(L):
    return next(r for r in CK.check_lens_clamp(L) if r.get('lens') == 'kowa_lm6hc')


def test_lens_clamp_anchor_model_solves_bolts_without_compression_foot():
    import layout as L
    import numpy as np
    rows = CK.check_lens_clamp(L)
    model = next(r for r in rows if r['item'] == 'anchor_model')
    assert model['status'] == 'pass' and not model['compression_foot_active'] and model['simultaneous_loads'], model
    assert set(model['reaction_coefficients']) == set(L.COLLAR['bolted']) and 'LR' not in model['reaction_coefficients']
    ly, lz = L.LENS_AXIS
    matrix = np.array([[1.0, (L.COLLAR['feet'][k][0] - ly) / 1000.0,
                        (L.COLLAR['feet'][k][1] - lz) / 1000.0] for k in L.COLLAR['bolted']]).T
    coefficients = np.array([[model['reaction_coefficients'][k]['axial_N_per_N'],
                              *model['reaction_coefficients'][k]['bending_N_per_Nm']] for k in L.COLLAR['bolted']])
    assert np.allclose(matrix @ coefficients, np.eye(3), atol=2e-6), (matrix, coefficients)
    # Axis is outside the bolt-only triangle: uniform sharing is not valid and one unit-axial reaction is negative.
    assert min(coefficients[:, 0]) < 0.0 and sum(abs(coefficients[:, 0])) > 1.0, coefficients
    r = next(r for r in rows if r.get('lens') == 'kowa_lm6hc')
    assert r['anchor_model_provisional'] and not r['anchor_compression_foot_active'], r
    assert r['anchor_tension_shock_N'] > r['anchor_tension_nominal_shock_N'], r
    assert r['anchor_bending_shock_bound_Nm'] >= abs(r['M_wall_static_Nm']) * L.LOAD_MODEL['shock_g'] - 1e-3, r
    assert abs(r['anchor_axial_shock_N'] - sum(r['masses'].values()) * L.LOAD_MODEL['g'] *
               L.LOAD_MODEL['shock_g'] / 1000.0) < 0.005, r


def test_lens_clamp_anchor_prying_factor_scales_each_reaction():
    import layout as L
    saved = L.LOAD_MODEL['anchor_prying_factor']
    try:
        L.LOAD_MODEL['anchor_prying_factor'] = 1.0
        unit = _clamp_kowa(L)
        L.LOAD_MODEL['anchor_prying_factor'] = 2.0
        double = _clamp_kowa(L)
    finally:
        L.LOAD_MODEL['anchor_prying_factor'] = saved
    for k, value in unit['anchor_reactions_shock_N'].items():
        assert abs(double['anchor_reactions_shock_N'][k] - 2 * value) <= 0.002, (unit, double)
    assert unit['anchor_tension_nominal_shock_N'] == double['anchor_tension_nominal_shock_N']
    assert unit['aim_shock_deg'] == double['aim_shock_deg'] and unit['M_sep_Nm'] == double['M_sep_Nm']


def test_lens_clamp_asymmetric_bolts_amplify_anchor_bound():
    import layout as L
    baseline = _clamp_kowa(L)
    saved = L.COLLAR['feet']['TR']
    try:
        # Bring TR within 1 mm of TL: bolt reaction amplification must be visible even before exact degeneracy.
        y, z = L.COLLAR['feet']['TL']
        L.COLLAR['feet']['TR'] = (y - 1.0, z)
        r = _clamp_kowa(L)
    finally:
        L.COLLAR['feet']['TR'] = saved
    assert r['anchor_tension_shock_N'] > 10 * baseline['anchor_tension_shock_N'], (baseline, r)
    assert 'bolted-anchor bound' in r['warn'] and r['anchor_tension_shock_N'] > L.LOAD_MODEL['anchor_N'], r


def test_lens_clamp_invalid_prying_factor_fails_closed():
    import layout as L
    saved = L.LOAD_MODEL['anchor_prying_factor']
    try:
        for factor in (None, 0.0, -1.0, 0.99, float('nan'), float('inf'), True, 'two'):
            L.LOAD_MODEL['anchor_prying_factor'] = factor
            rows = CK.check_lens_clamp(L)
            model = next(r for r in rows if r['item'] == 'anchor_model')
            assert model['status'] == 'fail' and 'anchor_prying_factor' in model['error'], (factor, rows)
            assert B.summarize('lens_clamp', rows, info_neutral=True)['status'] == 'fail', rows
            json.dumps(rows, allow_nan=False)     # fail rows must remain valid receipt data
        del L.LOAD_MODEL['anchor_prying_factor']
        rows = CK.check_lens_clamp(L)
        assert next(r for r in rows if r['item'] == 'anchor_model')['status'] == 'fail', rows
    finally:
        L.LOAD_MODEL['anchor_prying_factor'] = saved


def test_lens_clamp_degenerate_bolted_support_fails_closed():
    import layout as L
    saved = L.COLLAR['feet']['LL']
    try:
        # Collinear bolts cannot resist both bending components, even though LR still props up the full polygon.
        L.COLLAR['feet']['LL'] = (0.0, L.COLLAR['feet']['TL'][1])
        rows = CK.check_lens_clamp(L)
    finally:
        L.COLLAR['feet']['LL'] = saved
    model = next(r for r in rows if r['item'] == 'anchor_model')
    assert model['status'] == 'fail' and 'degenerate' in model['error'], rows
    assert B.summarize('lens_clamp', rows, info_neutral=True)['status'] == 'fail', rows


def test_lens_clamp_axis_outside_polygon_fails():
    import layout as L
    keep = L.COLLAR['feet']['LR']
    rows = CK.check_lens_clamp(L)
    assert rows[0]['item'] == 'anchor_polygon' and rows[0]['status'] == 'pass' and rows[0]['margin_mm'] >= 10.0
    kowa = next(r for r in rows if r.get('lens') == 'kowa_lm6hc')
    assert kowa['status'] == 'info' and 'M_sep' in kowa['warn'] and kowa['ratio_static'] >= 1.5
    L.COLLAR['feet']['LR'] = (-19.0, 75.0)     # the compression foot above the axis: polygon misses the lens axis
    try:
        p = CK.check_lens_clamp(L)[0]
    finally:
        L.COLLAR['feet']['LR'] = keep
    assert p['status'] == 'fail' and p['margin_mm'] < 10.0, p


def test_pt_count_ignores_m3():
    import layout as L
    import make_tables as MT
    pt = L.pt_screw_ids()
    m3 = [s['id'] for s in L.SCREWS if s.get('kind') == 'M3']
    assert len(pt) == 7 and m3 == ['s_c1', 's_c2', 's_c3', 's_c4'] and not set(pt) & set(m3)
    assert L.COTS['pt_screws']['name'].startswith('7 x PT') and abs(L.COTS['pt_screws']['mass'] - 5.6) < 1e-9
    assert MT.counts()['pt']['value'] == 7
    assert not {r['screw'] for r in CK.check_bosses(L, {})} & set(m3)      # boss rules: kind PT only
    assert {r['screw'] for r in CK.check_inserts(L, {})} == set(m3)         # inserts: kind M3 only


def test_j7_joint_requires_its_checks():
    import layout as L
    j7 = next(j for j in L.CRITICAL_JOINTS if j['id'] == 'J7_camera')
    assert set(j7['required_checks']) == {'j7_float', 'lens_support', 'lens_clamp', 'inserts'}
    ok = dict(j7_float=[dict(status='pass')], lens_support=[dict(status='pass'), dict(status='info', warn='w')],
              lens_clamp=[dict(status='pass')], inserts=[dict(status='pass')])
    row = next(r for r in CK.check_joint_checks(L, ok) if r['id'] == 'J7_camera')
    assert row['status'] == 'pass', row
    for bad in (dict(ok, j7_float=[dict(status='pass'), dict(status='fail')]), dict(ok, inserts=[]),
                dict(ok, lens_clamp=[dict(status='info', warn='w')])):
        assert next(r for r in CK.check_joint_checks(L, bad) if r['id'] == 'J7_camera')['status'] == 'fail'


def main(argv):
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_') and callable(f)]
    bad = 0
    for n, f in tests:
        try:
            f()
            print('PASS', n)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print('FAIL', n, '%s: %s' % (type(e).__name__, e))
    print('%d of %d cases pass' % (len(tests) - bad, len(tests)))
    if '--against-r2' in argv:
        against_r2()
    return 1 if bad else 0


def against_r2():
    """The same failure modes against the r2 code (candidate-fr1/_base/, the merge base copied from r2): each line
    says whether r2 still shows the defect the audit found (expected: yes for every case)."""
    import ast
    import hashlib
    import re
    import numpy as np
    base = os.path.join(HERE, 'candidate-fr1', '_base')

    def extract(fn, names, ns):
        tree = ast.parse(open(os.path.join(base, fn), encoding='utf-8').read())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), fn, 'exec'), ns)
        return ns
    vre = next(ast.literal_eval(n.value) for n in ast.parse(open(os.path.join(base, 'build_d2.py'),
               encoding='utf-8').read()).body if isinstance(n, ast.Assign) and
               any(getattr(t, 'id', '') == 'VERDICT_RE' for t in n.targets))
    sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()  # noqa: E731
    bns = extract('build_d2.py', {'_token_in', '_item_evidence', 'evidence_state', 'summarize'},
                  dict(os=os, re=re, sha=sha, VERDICT_RE=vre))
    out = []
    with tempfile.TemporaryDirectory(prefix='d2-r2-') as td:
        def case(sub, name, body, items):
            home = os.path.join(td, sub + name)
            os.makedirs(os.path.join(home, 'evidence', sub))
            open(os.path.join(home, 'evidence', sub, name), 'w').write(body)
            bns.update(HERE=home, EVIDENCE=os.path.join(home, 'evidence'))
            return bns['evidence_state'](sub, 'r2', items)['status']
        s = case('coupons', 'G-CAP-1-r1.md', 'verdict: fail\n', ['G-CAP-1'])
        out.append(('failed verdict leaves open_evidence', s.startswith('evidence with a recorded verdict for all')))
        s = case('coupons', 'G-CAP-1-old.md', 'verdict: pass\nsource_sha256: ' + '0' * 64 + '\n', ['G-CAP-1'])
        out.append(('stale record counts', s.startswith('evidence with a recorded verdict for all')))
        s = case('slicer', 'base_edge_panel.md', 'verdict: pass\n', ['panel'])
        out.append(('coupon file counts for production panel', s.startswith('evidence with a recorded verdict')))
    out.append(('unknown status passes', bns['summarize']('x', [dict(status='not run')], info_neutral=True)['status']
                == 'pass'))
    calls = []

    def chord(shape, p, d):
        calls.append(tuple(p))
        return MISS if all(abs(x) < 1e-12 for x in p) or abs(p[0] - 18.0) < 1e-9 else OK
    cns = extract('checks.py', {'registry', 'feature_class', 'check_critical_features'},
                  dict(np=np, chord=chord, _r=lambda x, n=3: round(x, n)))
    lay = _layout([LIP])
    rows = cns['check_critical_features'](lay, {'hood': dict(shape=object(), stub=False)})
    r = next(x for x in rows if x.get('id') == LIP['id'])
    out.append(('even span skips the origin', (0.0, 0.0, 0.0) not in calls))
    out.append(('unexpected missing ray passes', r['status'] == 'pass'))
    keep = dict(LIP, id='remaining_feature', span=None, origin=(1.0, 0.0, 0.0))
    lay = _layout([keep], joints=[dict(id='J4', parts=['hood'], required=['remaining_feature', 'base_keyhole_lip_f_l'])])
    rows = cns['check_critical_features'](lay, {'hood': dict(shape=object(), stub=False)})
    out.append(('deleted joint entry stays green', all(x['status'] == 'pass' for x in rows)))
    for name, shown in out:
        print('r2 %-45s %s' % (name, 'defect shown (fixed in r3)' if shown else 'NOT shown'))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
