# SPDX-License-Identifier: MIT
"""r7 C5 (BX-5, BX-13, BX-14; SPEC-C5 s4): planted-fault regressions for checks.check_handling. Each case copies the
layout tables it plants a fault in (no module state is changed) and runs the check on the current geometry: the COTS
proxy solids (build_d2.build_cots) and the printed part solids from out/step/parts (no CAD build; a missing STEP is
built in-process). A positive control asserts the unplanted state passes with the SPEC-C5 s7 numbers.

Run (repo root): python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r7_c5_handling.py
"""
import copy
import os
import sys
from functools import lru_cache
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cadquery as cq  # noqa: E402

import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402
import layout as L  # noqa: E402

TABLES = ('STEPS', 'INSERTIONS', 'REMOVALS', 'MATES', 'PRESS_FITS', 'SNAP_TOOTH_ZONES', 'REST_POSES', 'REST_FORBIDDEN',
          'SCREWS', 'ENCODER')


class _NS(SimpleNamespace):
    """r7 fix-up: attributes not copied (DRIVER, PARTS, COTS, LENSES, mass_g: the rest_pose driver-plane and stability
    rules) fall back to the real layout."""
    def __getattr__(self, k):
        return getattr(L, k)


def lay(edit=None):
    """A layout namespace with deep copies of the tables check_handling reads; edit(ns) plants the fault."""
    ns = _NS(**{k: copy.deepcopy(getattr(L, k)) for k in TABLES}, YL=L.YL)
    ns.present_at = lambda step: [i for s in ns.STEPS if s['step'] <= step for i in s['adds']]
    if edit:
        edit(ns)
    return ns


@lru_cache(maxsize=1)
def parts():
    rows = dict(B.build_cots())
    for pid in L.PARTS:
        pth = os.path.join(HERE, 'out', 'step', 'parts', pid + '.step')
        if os.path.exists(pth):
            rows[pid] = dict(shape=B.as_shape(cq.importers.importStep(pth)))
        else:
            rows[pid] = B.build_printed(only=pid)[0][pid]
    return {i: r['shape'] for i, r in rows.items() if r.get('shape') is not None}


def run(ns=None, extra=None):
    P = dict(parts())
    if extra:
        extra(P)
    return CK.check_handling(ns or lay(), {}, parts_of=P)


def row(out, rid):
    return next(r for r in out if r.get('id') == rid)


def fails(out, rid, text=None):
    r = row(out, rid)
    assert r['status'] == 'fail', '%s did not fail: %s' % (rid, r)
    if text:
        assert text in r.get('error', ''), '%s: %r not in %r' % (rid, text, r.get('error'))
    return r


def _step(ns, n):
    return next(s for s in ns.STEPS if s['step'] == n)


def _pf(ns, part):
    return next(r for r in ns.PRESS_FITS if r['part'] == part)


def _rp(ns, rid):
    return next(r for r in ns.REST_POSES if r['id'] == rid)


def _r6_knobs(ns):
    """r6 state: knobs pushed on at step 9, not on the step-2 bench, not in the step-8 adds."""
    for n in (2, 8):
        st = _step(ns, n)
        for k in ('knob_exp', 'knob_fps'):
            for lst in ('bench', 'adds'):
                if k in st.get(lst, []):
                    st[lst].remove(k)
    _step(ns, 9)['adds'][:0] = ['knob_exp', 'knob_fps']


def _enc_axis_box(dx, y0, y1, dz):
    ex, ez = L.ENCODER['c']
    return cq.Solid.makeBox(dx, y1 - y0, dz, cq.Vector(ex - dx / 2, y0, ez - dz / 2))


def _fuse_panel(box):
    def f(P):
        P['panel'] = P['panel'].fuse(box)
    return f


# ------------------------------------------------------------------------------------------- positive control
def test_current_state_passes():
    out = run()
    bad = [r for r in out if r['status'] not in ('pass', 'info')]
    assert not bad, bad
    k = row(out, 'press_fit knob_exp')
    assert k['V_rigid'] < 0.05 and 1.3 < k['V_zone'] < 1.6, k        # SPEC-C5 s7: 0.0 / 1.44
    assert not k['backing_column']['blocked']
    assert row(out, 'press_fit knob_fps')['V_rigid_press'] > 15.0      # 15.92 (the nut on the panel face)
    sb = row(out, 'snap_basis knob_exp')
    assert sb['A_land'] > 380 and sb['A_panel'] >= 0.9 * sb['A_land'] and abs(sb['gP'] - 0.2) < 0.01, sb
    assert set(row(out, 'rest_pose hood_down')['touching']) == {'hood'}
    assert set(row(out, 'rest_pose hood_down_s7')['touching']) == {'hood'}
    assert row(out, 'press_cover')['press_mates'] == 5


# ------------------------------------------------------------------------------------------- BX-5 (press fits)
def test_knob_pressed_in_body_fails():
    fails(run(lay(_r6_knobs)), 'press_fit knob_exp', 'snap-retained target pressed in the body')


def test_knob_not_carried_fails():
    def e(ns):
        next(i for i in ns.INSERTIONS if i['id'] == 'panel_on')['moving'].remove('knob_exp')
    fails(run(lay(e)), 'press_fit knob_exp', 'not carried')


def test_press_mate_without_row_fails():
    fails(run(lay(lambda ns: ns.PRESS_FITS.remove(_pf(ns, 'knob_fps')))), 'press_cover')


def test_usb_press_uncovered_fails():
    fails(run(lay(lambda ns: ns.PRESS_FITS.remove(_pf(ns, 'usb_stick')))), 'press_cover')


def test_snap_declared_rigid_fails():
    fails(run(lay(lambda ns: _pf(ns, 'knob_exp').update(retention='rigid'))), 'press_fit knob_exp', 'declared rigid')


def test_backstop_makes_snap_stale():
    out = run(extra=_fuse_panel(_enc_axis_box(26.0, 19.3, 19.5, 26.0)))
    fails(out, 'press_fit knob_exp', 'declared snap but backed: update PRESS_FITS')


def test_thumb_column_blocked_fails():
    fails(run(extra=_fuse_panel(_enc_axis_box(30.0, 10.0, 13.0, 30.0))), 'press_fit knob_exp', 'backing access')


def test_push_commissioned_fails():
    def e(ns):
        ns.ENCODER['push']['required_travel_mm'] = 0.5
    fails(run(lay(e)), 'snap_basis knob_exp', 'push commissioned')


def test_low_release_fails():
    fails(run(lay(lambda ns: _pf(ns, 'knob_exp').update(release_N=18.0))), 'snap_basis knob_exp', 'G-ENC-1 below')


def test_knob_land_removed_fails():
    def lift(P):        # KNOBS['knob_exp']['y'] starting at YL + 0.5: the land no longer sits 0.2 off the panel
        P['knob_exp'] = P['knob_exp'].translate(cq.Vector(0, 0.3, 0))
    fails(run(extra=lift), 'snap_basis knob_exp', 'knob land lost')


# ------------------------------------------------------------------------------------------- BX-13 (rest poses)
def test_rest_on_left_side_fails():
    r = fails(run(lay(lambda ns: _rp(ns, 'hood_down').update(down='+Y', stop=None))), 'rest_pose hood_down')
    assert 'knob_exp' in r['touching'], r


def test_bare_shaft_rest_fails():
    def e(ns):
        _r6_knobs(ns)
        _rp(ns, 'hood_down').update(down='+Y', stop=None)
    r = fails(run(lay(e)), 'rest_pose hood_down')
    assert set(r['touching']) == {'encoder'}, r


def test_service_rest_on_eyecup_fails():
    r = fails(run(lay(lambda ns: _rp(ns, 'hood_down_s7').update(remove_first=[]))), 'rest_pose hood_down_s7')
    assert 'eyecup' in r['touching'], r


def test_stop_band_too_tall_fails():
    r = fails(run(lay(lambda ns: _rp(ns, 'hood_down')['stop'].update(band_mm=32.0))), 'rest_pose hood_down')
    assert 'knob_exp' in r['stop']['intruders'], r


def test_stop_over_eyepiece_fails():
    r = fails(run(lay(lambda ns: _rp(ns, 'hood_down')['stop'].update(x=(-160.0, -5.0)))), 'rest_pose hood_down')
    assert 'eyepiece' in r['stop']['intruders'], r


def test_screw_without_pose_fails():
    fails(run(lay(lambda ns: _rp(ns, 'hood_down')['screws'].remove('s_r2'))), 'rest_cover', 's_r2')


def test_hood_down_driver_without_edge_fails():
    """r7 fix-up (VERIFY-C5): without the bench-edge overhang the s_r1 driver handle crosses the hood-roof plane."""
    r = fails(run(lay(lambda ns: _rp(ns, 'hood_down').pop('overhang'))), 'rest_pose hood_down', 's_r1')
    d = {x['screw']: x for x in r['driver_plane']}
    assert d['s_r1']['status'] == 'fail' and d['s_r2']['status'] == 'pass', d


def test_base_down_unattended_fails():
    """r7 fix-up (VERIFY-C5): standing on the grip end is not a rest (tips at about 6 deg) unless held by hand."""
    r = fails(run(lay(lambda ns: _rp(ns, 'base_down_8').update(support='bench'))), 'rest_pose base_down_8',
              'unstable')
    assert r['stability']['worst']['tip_deg'] < 10.0, r['stability']['worst']


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
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
