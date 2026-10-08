# SPDX-License-Identifier: MIT
"""FR1 hood joint probe (owner fr-hood): free travel of the fitted hood along +-X, +-Y, +Z before first contact, for
the selected D2_FR hood variant, against (a) the tub alone (hood-service state) and (b) the in-use set (tub + panel +
gs_camera + eyepiece + microsd). Also the lift travel with the hood first pushed +Y to its in-use stop (keys still
engaged?). Mesh booleans (manifold3d, 0.05 mm), checks._first_contact. Computed only; nothing measured.

    D2_FR=hood=yslide .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- \
        cad/gs8-d2-v1/candidate-fr1/fr_hood_probe.py --out cad/gs8-d2-v1/candidate-fr1/out/_hood-probe
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as L  # noqa: E402
import checks as C  # noqa: E402
import cots  # noqa: E402


def _shape(pid):
    if pid in L.PARTS:
        mod = __import__(L.PARTS[pid]['module'][:-3])
        sh = mod.build_part(L, pid)
    else:
        sh = cots.build_one(L, pid)
        sh = sh.get('shape', sh) if isinstance(sh, dict) else sh
    return sh.val() if hasattr(sh, 'val') else sh


def main():
    out = os.path.join(HERE, 'out', '_hood-probe')
    if '--out' in sys.argv:
        out = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    os.makedirs(out, exist_ok=True)
    hood = C.manifold_of(_shape('hood'))
    sets = {'service (tub only)': ['tub'], 'in use (tub, panel, gs_camera, eyepiece, microsd)':
            ['tub', 'panel', 'gs_camera', 'eyepiece', 'microsd'],
            # fix-candidate VC-L1: panel-only service state (panel off, camera in). gs_camera is still a FIXED
            # obstacle here: its own Y hold by the tub pins with the panel off is NOT computed.
            'panel off (tub, gs_camera, eyepiece, microsd)': ['tub', 'gs_camera', 'eyepiece', 'microsd']}
    obs = {}
    for ids in sets.values():
        for i in ids:
            if i not in obs:
                obs[i] = C.manifold_of(_shape(i))
    dirs = {'+X': (1, 0, 0), '-X': (-1, 0, 0), '+Y': (0, 1, 0), '-Y': (0, -1, 0), '+Z (lift)': (0, 0, 1)}
    res = dict(fr_state=L.FR_STATE, method='manifold3d mesh boolean (0.05 mm); first contact = overlap growth > 0.02 '
               'mm3, bracket 0.1 then 8 bisections; None = no contact within tmax', tmax_mm=6.0, sets={})
    for name, ids in sets.items():
        row = {}
        for dn, d in dirs.items():
            hits = {i: C._first_contact(hood, obs[i], d, 6.0) for i in ids}
            t = [v for v in hits.values() if v is not None]
            row[dn] = dict(first_contact_mm=None if not t else round(min(t), 3),
                           by={k: (None if v is None else round(v, 3)) for k, v in hits.items()})
        res['sets'][name] = row
        print(name, {k: v['first_contact_mm'] for k, v in row.items()})
    yi = res['sets']['in use (tub, panel, gs_camera, eyepiece, microsd)']['+Y']['first_contact_mm']
    if yi is not None:                                     # worst case: hood at its +Y in-use stop, then lift
        moved = hood.translate([0, yi - 0.02, 0])
        lift = C._first_contact(moved, obs['tub'], (0, 0, 1), 6.0)
        res['lift_at_plusY_stop_mm'] = None if lift is None else round(lift, 3)
        print('lift with the hood at its +Y stop (%.3f):' % yi, res['lift_at_plusY_stop_mm'])
    yo = res['sets']['panel off (tub, gs_camera, eyepiece, microsd)']['+Y']['first_contact_mm']
    if yo is not None:                                     # fix-candidate VC-L1: same lift test at the panel-off stop
        lift = C._first_contact(hood.translate([0, yo - 0.02, 0]), obs['tub'], (0, 0, 1), 6.0)
        res['lift_at_plusY_stop_panel_off_mm'] = None if lift is None else round(lift, 3)
        print('panel off: lift with the hood at its +Y stop (%.3f):' % yo, res['lift_at_plusY_stop_panel_off_mm'])
    with open(os.path.join(out, 'fr-hood-motion.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(res, f, indent=1)


if __name__ == '__main__':
    main()
