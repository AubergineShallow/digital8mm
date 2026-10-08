"""integrate-fork: export every FR1 coupon set for the candidate (D2_FR=all) and check each mesh with trimesh.

Run from the repo root under the CAD lock:
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- cad/gs8-d2-v1/candidate-fr1/run_fr1_coupons.py
Steps (child processes, D2_FR=all unless noted): coupons_fr_panel.py, coupons_fr_keeper.py, coupons_fr_hood.py (forces
hood=yslide), make_coupons.py --out out (the r2 coupon set cut from the FR parts; rows of removed features dropped),
fr_hood_probe.py --out out/_int-hood-probe (hood's request: re-run on the merged fork). Then trimesh on every STL in
out/stl/coupons-fr and out/stl/coupons -> out/fr1-coupons-check.json. Nothing is printed or measured."""
import glob, hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
JOBS = [('coupons_fr_panel.py', []), ('coupons_fr_keeper.py', []), ('coupons_fr_hood.py', []),
        ('make_coupons.py', ['--out', OUT]), ('fr_hood_probe.py', ['--out', os.path.join(OUT, '_int-hood-probe')])]


def main():
    import trimesh
    log = []
    only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--only=')]
    for script, args in JOBS:
        if '--check-only' in sys.argv or (only and script not in only[0].split(',')):
            continue
        env = dict(os.environ, D2_FR='all')
        p = subprocess.run([sys.executable, '-B', os.path.join(HERE, script)] + args, env=env, capture_output=True,
                           text=True)
        log.append(dict(script=script, rc=p.returncode, tail=(p.stdout + p.stderr)[-1500:]))
        print('==', script, 'rc', p.returncode, flush=True)
        print((p.stdout + p.stderr)[-800:], flush=True)
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, 'stl', 'coupons-fr', '*.stl')) +
                    glob.glob(os.path.join(OUT, 'stl', 'coupons', '*.stl'))):
        m = trimesh.load(f, force='mesh')
        rows.append(dict(stl=os.path.relpath(f, OUT).replace('\\', '/'), watertight=bool(m.is_watertight),
                         winding_consistent=bool(m.is_winding_consistent), volume_mm3=round(float(m.volume), 1),
                         euler=int(m.euler_number), faces=len(m.faces),
                         sha256=hashlib.sha256(open(f, 'rb').read()).hexdigest()))
    bad = [r['stl'] for r in rows if not (r['watertight'] and r['winding_consistent'] and r['volume_mm3'] > 0)]
    json.dump(dict(note='trimesh mesh checks of the exported coupon STLs (computed only; nothing printed)',
                   jobs=log, coupons=rows, not_watertight=bad), open(os.path.join(OUT, 'fr1-coupons-check.json'), 'w'),
              indent=1)
    print('coupons', len(rows), 'not watertight / inconsistent:', bad)


if __name__ == '__main__':
    main()
