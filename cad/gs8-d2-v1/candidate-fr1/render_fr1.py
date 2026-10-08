"""FR1 explanatory views (VTK offscreen + matplotlib sections) for every layout.FR_VIEWS entry, plus before (D2_FR=none)
views of the same windows. Reuses the fork build_d2 shape builders, _actor, colours and checks.section_lines.

Run from the repo root under the CAD lock:
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- cad/gs8-d2-v1/candidate-fr1/render_fr1.py
It runs one child process per state (layout reads D2_FR at import): all (every FR view), hood=screw1 (hood-screw1-*),
none (the 'before' of every section / closeup window). Output: candidate-fr1/out/renders/fr1-*.png + fr1-index.md.
Images are CAD renders of built solids (purchased parts are proxies); they show geometry, not a tested fit."""
import json, os, subprocess, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
RDIR = os.path.join(HERE, 'out', 'renders')
RUNS = [('all', None), ('hood=screw1', 'hood-screw1'), ('none', 'before')]
DIRS = {'front': (1, 0, 0), 'rear': (-1, 0, 0), 'left': (0, 1, 0), 'right': (0, -1, 0), 'top': (0, 0, 1),
        'bottom': (0, 0, -1), 'iso_left_front': (1, 1, .8), 'iso_right_rear': (-1, -1, .8),
        'iso_left_rear': (-1, 1, .8), 'iso_right_front': (1, -1, .8)}


def child(state, mode):
    sys.path.insert(0, HERE)
    import numpy as np
    import vtk
    import build_d2 as B
    import checks as CK
    L = B.L
    rows, _ = B.build_printed()
    rows.update(B.build_cots())
    shapes = {i: r for i, r in rows.items() if r.get('shape') is not None}
    meshes = {}

    def mesh(i):
        if i not in meshes:
            meshes[i] = CK.mesh_of(shapes[i]['shape'], tol=0.1, ang=0.3)
        return meshes[i]
    kos = L.KEEPOUTS if isinstance(L.KEEPOUTS, dict) else {}
    if mode == 'before':
        views = json.load(open(os.path.join(RDIR, 'fr1-views-all.json')))
        views = [v for v in views if v['kind'] in ('section', 'closeup')]
    else:
        views = [v for v in L.FR_VIEWS if mode is None or v['id'].startswith(mode)]
        if mode is None:
            json.dump(views, open(os.path.join(RDIR, 'fr1-views-all.json'), 'w'), indent=1, default=list)
    index = []
    for v in views:
        name = 'fr1-%s%s.png' % (v['id'], '-before' if mode == 'before' else '')
        p = os.path.join(RDIR, name)
        cap = ('BEFORE (D2_FR=none, r2 geometry): ' if mode == 'before' else '') + v.get('caption', v['id'])
        try:
            if v['kind'] == 'section':
                section(v, shapes, kos, CK, p, cap, L)
            else:
                scene(v, shapes, mesh, kos, B, vtk, np, p, cap)
            index.append(dict(file=name, id=v['id'], joint=v['joint'], kind=v['kind'], state=L.FR_STATE, caption=cap))
            print('render', name, flush=True)
        except Exception as e:  # noqa: BLE001
            index.append(dict(file=None, id=v['id'], joint=v['joint'], kind=v['kind'], state=L.FR_STATE,
                              caption=cap, error=repr(e)[:300]))
            print('FAILED', name, repr(e)[:300], flush=True)
    json.dump(index, open(os.path.join(RDIR, 'fr1-index-%s.json' % state.replace('=', '_')), 'w'), indent=1)


def section(v, shapes, kos, CK, p, cap, L):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    ax_k = 'xyz'.index(v['axis'])
    uv = [c for c in 'xyz' if c != v['axis']]
    u0, u1, v0, v1 = v['window']
    fig, ax = plt.subplots(figsize=(8, 8 * (v1 - v0) / max(1e-6, u1 - u0) + 1.2), dpi=150)
    n = 0
    for pid, r in sorted(shapes.items(), key=lambda t: (t[1]['kind'] != 'printed', t[0])):
        bb = r['shape'].BoundingBox()
        lo, hi = [(bb.xmin, bb.xmax), (bb.ymin, bb.ymax), (bb.zmin, bb.zmax)][ax_k]
        if not lo - 0.01 <= v['at'] <= hi + 0.01:
            continue
        try:
            lines = CK.section_lines(r['shape'], v['axis'], v['at'])
        except Exception:  # noqa: BLE001
            continue
        lines = [ln for ln in lines if any(u0 <= a <= u1 and v0 <= b <= v1 for a, b in ln)]
        if not lines:
            continue
        col = plt.cm.tab10(n % 10)
        n += 1
        for k, ln in enumerate(lines):
            xs, ys = zip(*ln)
            ax.plot(xs, ys, '-', color=col, lw=1.4 if r['kind'] == 'printed' else 0.9,
                    label=None if k else pid + ('' if r['kind'] == 'printed' else ' (purchased, proxy)'))
    for kid, b in kos.items():
        if b[v['axis']][0] <= v['at'] <= b[v['axis']][1]:
            (a0, a1), (b0, b1) = b[uv[0]], b[uv[1]]
            if a1 >= u0 and a0 <= u1 and b1 >= v0 and b0 <= v1:
                ax.add_patch(Rectangle((a0, b0), a1 - a0, b1 - b0, fill=False, ls='--', lw=0.8, ec='#d9622b'))
                ax.text(max(a0, u0) + 0.2, min(b1, v1) - 0.6, kid, fontsize=5, color='#d9622b')
    ax.set_xlim(u0, u1)
    ax.set_ylim(v0, v1)
    ax.set_aspect('equal')
    ax.set_xlabel(uv[0] + ' mm')
    ax.set_ylabel(uv[1] + ' mm')
    ax.grid(True, lw=0.3, alpha=0.5)
    ax.legend(fontsize=6, loc='best')
    ax.set_title('%s  [%s, %s = %.2f]\n%s' % (v['id'], L.FR_STATE, v['axis'], v['at'], textwrap.fill(cap, 110)), fontsize=7)
    fig.text(0.01, 0.003, 'CAD section of built solids; dashed orange = cable keep-out boxes; not a measurement', fontsize=6)
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)


def _box_actor(vtk, b, colour, op):
    src = vtk.vtkCubeSource()
    src.SetBounds(b['x'][0], b['x'][1], b['y'][0], b['y'][1], b['z'][0], b['z'][1])
    mp = vtk.vtkPolyDataMapper()
    mp.SetInputConnection(src.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(mp)
    a.GetProperty().SetColor(*colour)
    a.GetProperty().SetOpacity(op)
    return a


def scene(v, shapes, mesh, kos, B, vtk, np, p, cap):
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.93, 0.93, 0.91)
    ren.SetUseDepthPeeling(1)
    ren.SetMaximumNumberOfPeels(10)
    planes = None
    if v['kind'] == 'closeup':
        x0, x1, y0, y1, z0, z1 = v['box']
        planes = [((x0, 0, 0), (1, 0, 0)), ((x1, 0, 0), (-1, 0, 0)), ((0, y0, 0), (0, 1, 0)), ((0, y1, 0), (0, -1, 0)),
                  ((0, 0, z0), (0, 0, 1)), ((0, 0, z1), (0, 0, -1))]
        # readability (integrate-fork 13:30): purchased parts translucent, the hood translucent over the tub
        items = [(i, (0, 0, 0), 0.35 if shapes.get(i, {}).get('kind') != 'printed' else
                  (0.45 if i == 'hood' and 'tub' in v['parts'] else 1.0)) for i in v['parts']]
        focus = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        scale = 0.62 * max(x1 - x0, y1 - y0, z1 - z0)
    else:
        path = [tuple(w) for w in v['path']]
        items = [(i, (0, 0, 0), 1.0) for i in v.get('context', []) if i not in v.get('ghost', [])]
        items += [(i, (0, 0, 0), 0.18) for i in v.get('ghost', [])]
        for k, w in enumerate(path):
            op = 1.0 if k == len(path) - 1 else 0.22
            items += [(i, w, op) for i in v['moving']]
        focus, scale = None, None
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for i, off, op in items:
        if i not in shapes:
            continue
        Vm, Fm = mesh(i)
        a = B._actor(vtk, Vm, Fm, B.colour_of(i, shapes[i]), op, off)
        if planes:
            for o, nrm in planes:
                pl = vtk.vtkPlane()
                pl.SetOrigin(*o)
                pl.SetNormal(*nrm)
                a.GetMapper().AddClippingPlane(pl)
            bp = vtk.vtkProperty()
            bp.SetColor(0.85, 0.38, 0.17)
            bp.SetAmbient(.6)
            bp.SetDiffuse(.4)
            a.SetBackfaceProperty(bp)
        ren.AddActor(a)
        if len(Vm):
            lo, hi = np.minimum(lo, Vm.min(0) + off), np.maximum(hi, Vm.max(0) + off)
    if v['kind'] == 'motion':
        mv = [mesh(i)[0] for i in v['moving'] if i in shapes]
        c = np.vstack(mv).mean(0) if mv else np.zeros(3)
        pts = vtk.vtkPoints()
        for w in path:
            pts.InsertNextPoint(*(c + np.array(w)))
        line = vtk.vtkPolyLineSource()
        line.SetNumberOfPoints(len(path))
        for k, w in enumerate(path):
            line.SetPoint(k, *(c + np.array(w)))
        tube = vtk.vtkTubeFilter()
        tube.SetInputConnection(line.GetOutputPort())
        tube.SetRadius(0.8)
        tm = vtk.vtkPolyDataMapper()
        tm.SetInputConnection(tube.GetOutputPort())
        ta = vtk.vtkActor()
        ta.SetMapper(tm)
        ta.GetProperty().SetColor(0.85, 0.1, 0.1)
        ren.AddActor(ta)
        sweep = [np.array(lo) - 4, np.array(hi) + 4]
        mlo = np.min([mesh(i)[0].min(0) + np.array(w) for i in v['moving'] if i in shapes for w in path], 0) - 6
        mhi = np.max([mesh(i)[0].max(0) + np.array(w) for i in v['moving'] if i in shapes for w in path], 0) + 6
        names = v.get('keepouts') or [k for k, b in kos.items() if all(b[a][1] >= mlo[n] and b[a][0] <= mhi[n]
                                                                       for n, a in enumerate('xyz'))]
        for k in names:
            if k in kos:
                ren.AddActor(_box_actor(vtk, kos[k], (0.95, 0.5, 0.15), 0.35))
        del sweep
        focus = tuple((lo + hi) / 2)
        scale = 0.58 * float(max(hi - lo))
        kn = ', '.join(names) if len(names) <= 8 else '%d boxes within 6 mm of the swept volume' % len(names)
        cap += '  [red line = path of the moving parts; translucent copies = waypoints; orange boxes = cable keep-outs: %s]' % (
            kn or 'none near')
    d = np.array(DIRS.get(v.get('view', 'iso_left_front'), (1, 1, .8)), float)
    d /= np.linalg.norm(d)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*focus)
    cam.SetPosition(*(np.array(focus) + d * 600))
    cam.SetViewUp(*((0, 1, 0) if abs(d[2]) > 0.95 else (0, 0, 1)))
    cam.ParallelProjectionOn()
    cam.SetParallelScale(scale)
    ren.ResetCameraClippingRange()
    for lp, inten in (((-150, -220, 450), .6), ((300, 250, 240), .55), (tuple(np.array(focus) + d * 400), .5)):
        lt = vtk.vtkLight()
        lt.SetLightTypeToSceneLight()
        lt.SetPosition(*lp)
        lt.SetFocalPoint(*focus)
        lt.SetIntensity(inten)
        ren.AddLight(lt)
    legend = ', '.join('%s %s%s' % (i, B.colour_of(i, shapes[i]), '' if op >= 1 else ' (translucent)')
                       for i, op in dict((i, op) for i, _, op in items if i in shapes).items())
    cap += '  | parts: ' + legend + ('  | orange faces = cut by the close-up box' if planes else '')
    tx = vtk.vtkTextActor()
    tx.SetInput('%s\n%s' % (v['id'], textwrap.fill(cap, 150)))
    tx.GetTextProperty().SetFontSize(15)
    tx.GetTextProperty().SetColor(0.1, 0.1, 0.1)
    tx.SetDisplayPosition(12, 10)
    ren.AddActor2D(tx)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(1500, 1150)
    win.SetAlphaBitPlanes(1)
    win.SetMultiSamples(0)
    win.AddRenderer(ren)
    win.Render()
    wi = vtk.vtkWindowToImageFilter()
    wi.SetInput(win)
    wi.ReadFrontBufferOff()
    wi.Update()
    w = vtk.vtkPNGWriter()
    w.SetFileName(p)
    w.SetInputConnection(wi.GetOutputPort())
    w.Write()
    win.Finalize()


def main():
    os.makedirs(RDIR, exist_ok=True)
    only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--states=')]
    runs = [r for r in RUNS if not only or r[0] in only[0].split(';')]
    for state, mode in runs:
        env = dict(os.environ, D2_FR=state)
        rc = subprocess.run([sys.executable, '-B', os.path.abspath(__file__), '--child', state, str(mode)], env=env).returncode
        print('state', state, 'rc', rc, flush=True)
    rows = []
    for state, _ in RUNS:
        f = os.path.join(RDIR, 'fr1-index-%s.json' % state.replace('=', '_'))
        if os.path.exists(f):
            rows += json.load(open(f))
    out = ['# FR1 renders (generated by render_fr1.py; CAD views of built solids, not a tested fit)', '',
           '| file | joint | kind | state | caption |', '|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: (r['joint'], r['id'], r['state'])):
        f = '[%s](%s)' % (r['file'], r['file']) if r['file'] else 'FAILED: ' + r.get('error', '')
        out.append('| %s | %s | %s | %s | %s |' % (f, r['joint'], r['kind'], r['state'], r['caption'].replace('|', '/')))
    open(os.path.join(RDIR, 'fr1-index.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    if '--child' in sys.argv:
        k = sys.argv.index('--child')
        child(sys.argv[k + 1], None if sys.argv[k + 2] == 'None' else sys.argv[k + 2])
    else:
        main()
