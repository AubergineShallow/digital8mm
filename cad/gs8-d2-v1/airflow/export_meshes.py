# SPDX-License-Identifier: MIT
"""D2 airflow study: one-time export of every printed part and COTS proxy in ASSEMBLY position (not print pose).

Run ONCE, under the CAD lock (repo root):
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- cad/gs8-d2-v1/airflow/export_meshes.py

Imports the baseline pipeline (build_d2.build_printed / build_cots, default lens = layout.LENS) and writes
  airflow/out/meshes/<id>.stl   (binary STL, assembly mm, linear tol 0.05 mm, angular 0.3 rad)
  airflow/out/meshes/index.json (bounds, triangle count, watertight flag, stub flag, source hashes)
Nothing is written in cad/gs8-d2-v1/out.
"""
import hashlib
import json
import os
import sys
import time

AF = os.path.dirname(os.path.abspath(__file__))
D2 = os.path.dirname(AF)
sys.path.insert(0, D2)
OUTM = os.path.join(AF, 'out', 'meshes')
TOL, ATOL = 0.05, 0.3


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    t0 = time.time()
    import build_d2 as B   # noqa: E402  (imports cadquery, layout, cots, checks)
    import trimesh
    L = B.L
    os.makedirs(OUTM, exist_ok=True)
    printed, mods = B.build_printed()
    print('printed built %.1f s' % (time.time() - t0), flush=True)
    cots = B.build_cots()
    print('cots built %.1f s' % (time.time() - t0), flush=True)
    index = dict(revision=L.REVISION, lens=L.LENS, variant=getattr(L, 'FR_STATE', None), tol_mm=TOL, ang_tol=ATOL,
                 frame='assembly mm (layout.py FRAME: X forward, Y left, Z up)', modules=mods, parts={},
                 sources={f: sha(os.path.join(D2, f)) for f in sorted(os.listdir(D2))
                          if f.endswith('.py') and (f.startswith('printed_') or f in ('layout.py', 'cots.py',
                                                                                      'd2_common.py', 'build_d2.py'))})
    rows = [(k, v) for k, v in printed.items()] + [(k, v) for k, v in cots.items()]
    for pid, r in rows:
        sh = r.get('shape')
        if sh is None:
            index['parts'][pid] = dict(kind=r.get('kind'), skipped='no shape')
            continue
        path = os.path.join(OUTM, pid + '.stl')
        sh.exportStl(path, TOL, ATOL)
        m = trimesh.load(path, force='mesh')
        bb = sh.BoundingBox()
        index['parts'][pid] = dict(
            kind=r.get('kind'), stub=bool(r.get('stub')), stub_reason=(r.get('stub_reason') or '').split('\n')[0],
            stl='meshes/%s.stl' % pid, triangles=int(len(m.faces)), watertight=bool(m.is_watertight),
            bounds=[[round(bb.xmin, 3), round(bb.ymin, 3), round(bb.zmin, 3)],
                    [round(bb.xmax, 3), round(bb.ymax, 3), round(bb.zmax, 3)]],
            volume_brep=round(sh.Volume(), 1), volume_mesh=round(float(m.volume), 1) if m.is_watertight else None,
            sha256=sha(path))
        print('%-14s tri %7d wt %s' % (pid, len(m.faces), m.is_watertight), flush=True)
    index['seconds'] = round(time.time() - t0, 1)
    with open(os.path.join(OUTM, 'index.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, indent=1)
    print('done %.1f s, %d parts' % (time.time() - t0, len(index['parts'])))


if __name__ == '__main__':
    main()
