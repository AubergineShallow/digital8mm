# SPDX-License-Identifier: MIT
"""GS8 D2 release build: assemble every printed module + COTS proxies from layout.py, run the SPEC s6 checks,
export STL (print orientation), STEP, manifests, receipts and renders.

Run (repo root, always through the lock):
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py [--fast] [--part ID]
      [--lens kowa_lm6hc|fujinon_hf6xa] [--sweep-step 2.0] [--no-sweeps] [--no-thin] [--out DIR]
--part ID  quick single-part run (printed id: contract, bed, thin wall, keep-outs, interference with COTS; STL)
--fast     skip renders (and the STEP export)
Outputs in cad/gs8-d2-v1/out/: stl/<id>.stl, step/gs8-d2-assembly.step, print-manifest.json, parts-manifest.json,
checks.json, build-receipt.json, renders/{hero,exploded,xray}.png (part runs: part-<id>.json, stl/<id>.stl).
A printed module that is missing or fails to build is replaced by its envelope box (stub=True): it is assembled and
checked, but a stub result never passes and cad_release_candidate stays false. Purchased parts are proxies; nothing is
printed, bought or measured. r2 (R3): the receipt carries status_states (cad_checks computed; slicer_review,
coupon_validation, measured_fit, assembly_operation from structured evidence records, r3: evidence/README.md, bound to
the sha256 of the tested artifacts; pass / fail / conflict / stale / not run per item); critical_features
gates local thickness (thin_wall is a secondary screen); evf_restraint, removals and service_driver check finding 6
and the service paths; renders/section-<id>.png come from layout.SECTIONS.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cadquery as cq  # noqa: E402

import checks as CK  # noqa: E402
import cots  # noqa: E402
import d2_common as dc  # noqa: E402
import layout as L  # noqa: E402

OUT = os.path.join(HERE, 'out')
T0 = time.time()
TIMES = {}


def log(*a):
    print('[%6.1fs]' % (time.time() - T0), *a, flush=True)


def lap(name, t0):
    TIMES[name] = round(time.time() - t0, 2)
    log('%s done in %.1f s' % (name, TIMES[name]))


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_json(name, data):
    p = os.path.join(OUT, name)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=1, default=str)
    return p


def as_shape(obj):
    """Workplane / Shape -> one cq.Shape (Solid, or Compound when several)."""
    if obj is None:
        return None
    if isinstance(obj, cq.Workplane):
        vals = [v for v in obj.vals() if isinstance(v, cq.Shape)]
        sols = [s for v in vals for s in v.Solids()]
        if len(sols) == 1:
            return sols[0]
        return cq.Compound.makeCompound(sols if sols else vals)
    return obj


# ------------------------------------------------------------------------------------------- printed modules
def load_module(fname):
    path = os.path.join(HERE, fname)
    if not os.path.exists(path):
        return None, 'missing'
    try:
        spec = importlib.util.spec_from_file_location(fname[:-3], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, 'ok'
    except Exception:  # noqa: BLE001
        return None, 'import error: ' + traceback.format_exc(limit=3)


STUB_WALL = 2.0


def stub_shape(env):
    """Envelope box, hollowed to a closed 2.0 shell when every side is >= 10 mm (keeps stub masses plausible)."""
    b = dc.box_solid(env)
    d = [env[k][1] - env[k][0] for k in 'xyz']
    if min(d) >= 10.0:
        w = STUB_WALL
        b = b.cut(dc.box_solid({k: (env[k][0] + w, env[k][1] - w) for k in 'xyz'}))
    return b


def stub_row(pid, why):
    p = L.PARTS[pid]
    return dict(shape=stub_shape(p['envelope']), kind='printed', stub=True, stub_reason=why, module=p['module'],
                print=dict(face_down=p['face_down'], supports=p['supports'], notes='stub (envelope box)'))


def build_printed(only=None):
    """{pid: row}. only = a single printed id for --part runs."""
    rows, mods = {}, {}
    by_mod = {}
    for pid, p in L.PARTS.items():
        if only is None or pid == only:
            by_mod.setdefault(p['module'], []).append(pid)
    for fname, pids in by_mod.items():
        t0 = time.time()
        mod, st = load_module(fname)
        mods[fname] = dict(status=st, parts=pids)
        built = {}
        if mod is not None:
            try:
                if only is not None and hasattr(mod, 'build_part'):
                    built = {only: mod.build_part(L, only)}
                else:
                    built = mod.build(L)
                mods[fname]['status'] = 'built'
            except Exception:  # noqa: BLE001
                mods[fname]['status'] = 'build error: ' + traceback.format_exc(limit=4)
                built = {}
        pr = getattr(mod, 'PRINT', {}) if mod is not None else {}
        for pid in pids:
            if pid in built and built[pid] is not None:
                rows[pid] = dict(shape=as_shape(built[pid]), kind='printed', stub=False, module=fname,
                                 print=pr.get(pid, {}), n_solids=len(built[pid].solids().vals())
                                 if isinstance(built[pid], cq.Workplane) else 1)
            else:
                rows[pid] = stub_row(pid, mods[fname]['status'] if mod is None or pid not in built
                                     else 'part missing from build()')
        mods[fname]['seconds'] = round(time.time() - t0, 2)
        log('module %s: %s (%s)' % (fname, mods[fname]['status'].split('\n')[0], ', '.join(pids)))
    return rows, mods


def contract_checks(rows):
    out = []
    for pid, r in rows.items():
        if r['kind'] != 'printed':
            continue
        p = L.PARTS[pid]
        if r.get('stub'):
            out.append(dict(part=pid, status='stub', reason=r['stub_reason'].split('\n')[0]))
            continue
        sh = r['shape']
        bb = CK.bb_tuple(sh)
        env = CK.box_bb(p['envelope'])
        over = [_round(env[0] - bb[0]), _round(bb[1] - env[1]), _round(env[2] - bb[2]), _round(bb[3] - env[3]),
                _round(env[4] - bb[4]), _round(bb[5] - env[5])]
        inside = max(over) <= 1e-3
        nsol = len(sh.Solids())
        valid = sh.isValid()
        fd_ok = r['print'].get('face_down', p['face_down']) == p['face_down']
        ok = inside and nsol == 1 and valid and fd_ok and bool(r['print'])
        out.append(dict(part=pid, status='pass' if ok else 'fail', one_solid=nsol == 1, n_solids=nsol, valid=valid,
                        inside_envelope=inside, envelope_excess=over, face_down_matches=fd_ok,
                        print_entry=bool(r['print']), volume_mm3=round(sh.Volume(), 1)))
    return out


def _round(x, n=3):
    return round(float(x), n)


# ------------------------------------------------------------------------------------------- COTS
def build_cots(only=None):
    t = cots.build_all(L, only=only)
    rows = {}
    for cid, r in t.items():
        rows[cid] = dict(r, shape=as_shape(r['shape']) if r['shape'] is not None else None, stub=False)
    return rows


def cots_containment(rows):
    out = []
    for cid, r in rows.items():
        if r['kind'] == 'printed' or r.get('box') is None or r.get('shape') is None:
            continue
        bb, env = CK.bb_tuple(r['shape']), CK.box_bb(r['box'])
        over = max(env[0] - bb[0], bb[1] - env[1], env[2] - bb[2], bb[3] - env[3], env[4] - bb[4], bb[5] - env[5])
        out.append(dict(id=cid, status='pass' if over <= 0.02 else 'fail', excess=_round(over)))
    return out


# ------------------------------------------------------------------------------------------- exports
PRINT_RATE = 6.0     # mm3/s effective extrusion (0.4 nozzle, 0.2 layers, ASA, enclosed) -> time estimate only


def export_part(pid, r, bed_rows, thin_rows, mesh_rows):
    """Print-pose STL + manifest row for one printed part."""
    p = L.PARTS[pid]
    fd = p['face_down']
    pose = dc.to_print_pose(r['shape'], fd)
    os.makedirs(os.path.join(OUT, 'stl'), exist_ok=True)
    path = os.path.join(OUT, 'stl', pid + '.stl')
    if r.get('stub'):                  # never leave a printable file for a stub (or a stale one from an older build)
        if os.path.exists(path):
            os.remove(path)
    else:
        pose.exportStl(path, 0.03, 0.2)
    mesh_rows.append(stl_mesh_check(pid, pose, r))
    bed = CK.check_bed(L, pid, pose)
    if r.get('stub'):
        bed['status'] = 'stub'
    bed_rows.append(bed)
    vol = r['shape'].Volume()
    rho = L.TPU_DENSITY if p['material'].startswith('TPU') else L.FDM['ASA_DENSITY']
    m = L.mass_g(vol, pid)
    hours = (vol * L.INFILL_FACTOR[p['infill']] / PRINT_RATE) / 3600 * 1.15 + 0.1
    pr = r.get('print') or {}
    th = next((t for t in thin_rows if t['part'] == pid), None)
    ov = overhang_screen(pose)
    return dict(overhang_screen=ov,
                id=pid, module=p['module'], material=p['material'], colour=p['colour'], face_down=fd,
                supports=pr.get('supports', p['supports']), notes=pr.get('notes', ''), infill_class=p['infill'],
                infill_factor=L.INFILL_FACTOR[p['infill']], volume_mm3=round(vol, 1), mass_100pct_g=round(vol * rho, 1),
                mass_est_g=round(m, 1), filament_g_est=round(m * 1.05, 1), print_time_est_h=round(hours, 2), print_bbox_mm=bed['print_bbox'],
                bed_fit=bed['beds'], stl=None if r.get('stub') else 'stl/%s.stl' % pid,
                stl_sha256=None if r.get('stub') else sha(path), stub=bool(r.get('stub')),
                thin_wall=None if th is None else dict(status=th['status'], p1=th.get('p1'), min=th.get('min')))


def stl_mesh_check(pid, pose, r):
    """The print mesh (STL tolerance 0.03 mm / 0.2 rad) must be one watertight 2-manifold shell whose volume
    matches the BRep within 0.5 %."""
    try:
        man = CK.manifold_of_tol(pose, 0.03, 0.2)
        if man is None:
            return dict(part=pid, status='stub' if r.get('stub') else 'fail', error='not a 2-manifold mesh')
        shells = len(man.decompose())
        vb = pose.Volume()
        dv = abs(man.volume() - vb) / max(vb, 1e-9)
        ok = shells == 1 and dv <= 0.005
        st = 'pass' if ok else 'fail'
        if r.get('stub'):
            st = 'stub'
        return dict(part=pid, status=st, watertight=True, shells=shells, volume_brep=round(vb, 1),
                    volume_mesh=round(man.volume(), 1), volume_dev=round(dv, 5))
    except Exception as e:  # noqa: BLE001
        return dict(part=pid, status='fail', error=str(e))


def overhang_screen(pose):
    """Info only: downward faces steeper than 45 deg from vertical in print pose, above the bed (z > 0.05).
    Bridges (<= 30 mm) and listed supports are allowed, so this is not a pass/fail check."""
    import numpy as np
    Vm, Fm = CK.mesh_of(pose, tol=0.1, ang=0.3)
    if len(Fm) == 0:
        return None
    a, b, c = Vm[Fm[:, 0]], Vm[Fm[:, 1]], Vm[Fm[:, 2]]
    cr = np.cross(b - a, c - a)
    area = np.linalg.norm(cr, axis=1) / 2
    if np.einsum('ij,ij->i', a, cr).sum() < 0:
        cr = -cr
    nz = cr[:, 2] / np.maximum(1e-12, 2 * area)
    zc = (a[:, 2] + b[:, 2] + c[:, 2]) / 3
    m = (nz < -math.sin(math.radians(45.0)) + 1e-6) & (zc > 0.05)
    lo = m & (zc <= 0.6)
    bed = (nz < -0.999) & (zc <= 0.02)
    return dict(bed_contact_mm2=round(float(area[bed].sum()), 1), area_mm2=round(float(area[m].sum()), 1), share=round(float(area[m].sum() / area.sum()), 4),
                lowest_z=round(float(zc[m].min()), 2) if m.any() else None,
                near_bed_area_mm2=round(float(area[lo].sum()), 1),
                note='downward faces > 45 deg from vertical above the bed: bridges, supports or chamfer candidates')


COLOURS = {'satin silver': '#c9cac6', 'black': '#2b2c2f', 'clear/natural': '#e6e0cc'}
COTS_COLOUR = {'pi5': '#2f6b45', 'x1203': '#24563a', 'evf_board': '#2f6b45', 'encoder': '#2a4f8a', 'cooler': '#9a9ea3',
               'gs_camera': '#3b3f45', 'lens': '#1c1d1f', 'c_cs_adapter': '#7d7f82', 'eyepiece': '#46494e',
               'hmx039': '#151515', 'usb_stick': '#a3262b', 'switch_1824': '#6b6d70', 'run_button': '#c8262b',
               'pack': '#3a6ea5', 'xt30_pair': '#e0b020', 'tripod_nut': '#a9a9a2', 'strap': '#3d3328',
               'foam_pad': '#222222', 'x1203_kit': '#c9a86a'}


def hex_rgb(c):
    return tuple(int(c[k:k + 2], 16) / 255 for k in (1, 3, 5))


def colour_of(i, r):
    if r.get('stub'):
        return '#e0904a'
    if r['kind'] == 'printed':
        return COLOURS.get(L.PARTS[i]['colour'], '#2b2c2f')
    if i.startswith('s_'):
        return '#b8b8b0'
    return COTS_COLOUR.get(i, '#5d7a62')


def export_step(rows):
    os.makedirs(os.path.join(OUT, 'step'), exist_ok=True)
    asm = cq.Assembly(name='gs8_d2')
    for i, r in rows.items():
        if r.get('shape') is None:
            continue
        asm.add(r['shape'], name=i, color=cq.Color(*hex_rgb(colour_of(i, r)), 1.0))
    os.makedirs(os.path.join(OUT, 'step', 'parts'), exist_ok=True)
    for i, r in rows.items():          # one STEP per printed part, assembly pose (for edits in other CAD tools)
        pth = os.path.join(OUT, 'step', 'parts', i + '.step')
        if r['kind'] == 'printed' and not r.get('stub') and r.get('shape') is not None:
            cq.exporters.export(cq.Workplane().add(r['shape']), pth)
        elif r['kind'] == 'printed' and os.path.exists(pth):
            os.remove(pth)
    path = os.path.join(OUT, 'step', 'gs8-d2-assembly.step')
    if hasattr(asm, 'export'):
        asm.export(path)
    else:
        asm.save(path)
    return path


# ------------------------------------------------------------------------------------------- renders (VTK)
EXPLODE = {'hood': (0, 0, 70), 'plunger': (35, 0, 0), 'panel': (0, 85, 0), 'knob_exp': (0, 125, 0),
           'knob_fps': (0, 125, 0), 'encoder': (0, 85, 0), 'switch_1824': (0, 85, 0), 'base_grip': (0, 0, -60),
           'skirt_l': (0, 25, -60), 'skirt_r': (0, -25, -60), 'cap': (0, 0, -150), 'pack': (0, 0, -105),
           'xt30_pair': (0, 0, -85), 'tripod_nut': (0, 0, -45), 'run_button': (25, 0, -60), 'strap': (0, -30, -60),
           'eyecup': (-60, 0, 0), 'eyepiece': (-35, 0, 0), 'stick_sleeve': (-75, 0, 0), 'usb_stick': (-60, 0, 0),
           'lens': (75, 0, 0), 'c_cs_adapter': (45, 0, 0), 'gs_camera': (0, 55, 15), 'pi5': (0, 0, 25),
           'cooler': (0, 0, 35), 'x1203': (0, 0, 15), 'x1203_kit': (0, 0, 20), 'hmx039': (0, 45, 0),
           'evf_board': (0, 50, 0), 'foam_pad': (0, 45, 0)}


def explode_of(i):
    if i.startswith('s_'):
        s = next(s for s in L.SCREWS if s['id'] == i)
        base = (0, 0, -60) if s['axis'][2] else (0, 0, 0)
        return tuple(base[k] - s['axis'][k] * 30 for k in range(3))
    return EXPLODE.get(i, (0, 0, 0))


VIEWS = {'hero': ((230.0, 260.0, 190.0), (-70.0, 0.0, -2.0), 158.0, 'assembled'),
         'exploded': ((260.0, 300.0, 210.0), (-62.0, 20.0, -35.0), 255.0, 'exploded'),
         'xray': ((-62.0, 500.0, -5.0), (-62.0, 0.0, -5.0), 130.0, 'xray'),
         'section-lens-axis': ((-62.0, 500.0, -5.0), (-62.0, 0.0, -5.0), 130.0, 'section 0.0'),
         'section-evf-axis': ((-120.0, 500.0, 60.0), (-120.0, 16.0, 60.0), 70.0, 'section 16.0')}


def _actor(vtk, Vm, Fm, colour, opacity, pos, clip=None):
    import numpy as np
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    pts = vtk.vtkPoints()
    pts.SetData(numpy_to_vtk(np.ascontiguousarray(Vm, np.float32), deep=True))
    cells = np.hstack([np.full((len(Fm), 1), 3, np.int64), Fm.astype(np.int64)]).ravel()
    ca = vtk.vtkCellArray()
    ca.SetCells(len(Fm), numpy_to_vtkIdTypeArray(cells, deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(pts)
    poly.SetPolys(ca)
    nr = vtk.vtkPolyDataNormals()
    nr.SetInputData(poly)
    nr.SetFeatureAngle(35)
    nr.SplittingOn()
    mp = vtk.vtkPolyDataMapper()
    mp.SetInputConnection(nr.GetOutputPort())
    a = vtk.vtkActor()
    if clip is not None:            # section view: keep the half behind the plane, cut faces in orange
        pl = vtk.vtkPlane()
        pl.SetOrigin(*clip[0])
        pl.SetNormal(*clip[1])
        mp.AddClippingPlane(pl)
        bp = vtk.vtkProperty()
        bp.SetColor(*hex_rgb('#d9622b'))
        bp.SetAmbient(.55)
        bp.SetDiffuse(.45)
        a.SetBackfaceProperty(bp)
    a.SetMapper(mp)
    pr = a.GetProperty()
    pr.SetColor(*hex_rgb(colour))
    pr.SetAmbient(.25)
    pr.SetDiffuse(.72)
    pr.SetSpecular(.2)
    pr.SetSpecularPower(25)
    pr.SetOpacity(opacity)
    a.SetPosition(*pos)
    return a


def render_all(rows):
    import vtk
    rdir = os.path.join(OUT, 'renders')
    os.makedirs(rdir, exist_ok=True)
    meshes = {i: CK.mesh_of(r['shape'], tol=0.1, ang=0.3) for i, r in rows.items() if r.get('shape') is not None}
    files = {}
    for name, (pos, tgt, scale, mode) in VIEWS.items():
        ren = vtk.vtkRenderer()
        ren.SetBackground(0.93, 0.93, 0.91)
        ren.SetBackground2(0.99, 0.99, 0.97)
        ren.GradientBackgroundOn()
        if mode == 'xray':
            ren.SetUseDepthPeeling(1)
            ren.SetMaximumNumberOfPeels(8)
        clip = None
        if mode.startswith('section'):    # cut plane y = value; the camera looks from +Y at the far half
            clip = ((0.0, float(mode.split()[1]), 0.0), (0.0, -1.0, 0.0))
        for i, (Vm, Fm) in meshes.items():
            op = 0.16 if (mode == 'xray' and rows[i]['kind'] == 'printed') else 1.0
            off = explode_of(i) if mode == 'exploded' else (0, 0, 0)
            ren.AddActor(_actor(vtk, Vm, Fm, colour_of(i, rows[i]), op, off, clip))
        for lp, inten in (((-150, -220, 450), .7), ((300, 250, 240), .55), ((0, 300, 100), .35)):
            lt = vtk.vtkLight()
            lt.SetLightTypeToSceneLight()
            lt.SetPosition(*lp)
            lt.SetFocalPoint(*tgt)
            lt.SetIntensity(inten)
            ren.AddLight(lt)
        cam = ren.GetActiveCamera()
        cam.SetPosition(*pos)
        cam.SetFocalPoint(*tgt)
        cam.SetViewUp(0, 0, 1)
        cam.ParallelProjectionOn()
        cam.SetParallelScale(scale)
        ren.ResetCameraClippingRange()
        win = vtk.vtkRenderWindow()
        win.SetOffScreenRendering(1)
        win.SetSize(1600, 1200)
        win.SetAlphaBitPlanes(1)
        win.SetMultiSamples(0)
        win.AddRenderer(ren)
        win.Render()
        cap = vtk.vtkWindowToImageFilter()
        cap.SetInput(win)
        cap.ReadFrontBufferOff()
        cap.Update()
        p = os.path.join(rdir, name + '.png')
        w = vtk.vtkPNGWriter()
        w.SetFileName(p)
        w.SetInputConnection(cap.GetOutputPort())
        w.Write()
        win.Finalize()
        files['renders/%s.png' % name] = sha(p)
        log('render', name)
    files.update(render_print_poses(rows, vtk))
    files.update(render_steps(rows, meshes, vtk))
    return files


def render_print_poses(rows, vtk):
    """renders/print-poses.png: every printed part in its print pose (face down on z = 0), on a grid."""
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.95, 0.95, 0.93)
    x = y = 0.0
    row_h = 0.0
    cols = 0
    for pid in L.PARTS:
        r = rows.get(pid)
        if r is None or r.get('shape') is None:
            continue
        pose = dc.to_print_pose(r['shape'], L.PARTS[pid]['face_down'])
        bb = pose.BoundingBox()
        if cols == 4:
            x, y, cols = 0.0, y - row_h - 25.0, 0
            row_h = 0.0
        Vm, Fm = CK.mesh_of(pose, tol=0.1, ang=0.3)
        ren.AddActor(_actor(vtk, Vm, Fm, colour_of(pid, r), 1.0, (x, y - bb.ylen, 0.0)))
        bed = vtk.vtkPlaneSource()
        bed.SetOrigin(x - 3, y - bb.ylen - 3, -0.05)
        bed.SetPoint1(x + bb.xlen + 3, y - bb.ylen - 3, -0.05)
        bed.SetPoint2(x - 3, y + 3, -0.05)
        bm = vtk.vtkPolyDataMapper()
        bm.SetInputConnection(bed.GetOutputPort())
        ba = vtk.vtkActor()
        ba.SetMapper(bm)
        ba.GetProperty().SetColor(0.75, 0.78, 0.82)
        ren.AddActor(ba)
        tx = vtk.vtkBillboardTextActor3D()
        tx.SetInput('%s  %s' % (pid, L.PARTS[pid]['face_down']))
        tx.SetPosition(x, y + 6.0, 0.0)
        tx.GetTextProperty().SetFontSize(22)
        tx.GetTextProperty().SetColor(0.15, 0.15, 0.15)
        ren.AddActor(tx)
        x += bb.xlen + 25.0
        row_h = max(row_h, bb.ylen)
        cols += 1
    b = ren.ComputeVisiblePropBounds()
    c = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*c)
    cam.SetPosition(c[0] + 150.0, c[1] - 600.0, c[2] + 520.0)
    cam.SetViewUp(0, 0, 1)
    cam.ParallelProjectionOn()
    cam.SetParallelScale(0.42 * max(b[1] - b[0], (b[3] - b[2]) * 1.3))
    ren.ResetCameraClippingRange()
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(1800, 1300)
    win.AddRenderer(ren)
    win.Render()
    cap = vtk.vtkWindowToImageFilter()
    cap.SetInput(win)
    cap.ReadFrontBufferOff()
    cap.Update()
    p = os.path.join(OUT, 'renders', 'print-poses.png')
    w = vtk.vtkPNGWriter()
    w.SetFileName(p)
    w.SetInputConnection(cap.GetOutputPort())
    w.Write()
    win.Finalize()
    log('render print-poses')
    return {'renders/print-poses.png': sha(p)}



# ------------------------------------------------------------------------------------------- step renders (ASSEMBLY.md)
GHOST = '#d4d4cf'
STEP_VIEWS = {   # step: (camera position offset from target, target, parallel scale)
    1: ((260.0, -300.0, 260.0), (-48.0, -4.0, 30.0), 70.0),
    2: ((200.0, 420.0, 160.0), (-93.0, 30.0, 57.0), 75.0),
    3: ((260.0, -320.0, -160.0), (-70.0, 0.0, -30.0), 130.0),
    4: ((230.0, 260.0, 300.0), (-70.0, 0.0, 30.0), 115.0),
    5: ((260.0, 260.0, 260.0), (-70.0, 0.0, 50.0), 125.0),
    6: ((-320.0, 260.0, 200.0), (-158.0, 16.0, 72.0), 72.0),
    7: ((200.0, 360.0, 180.0), (-40.0, 20.0, 55.0), 95.0),
    8: ((200.0, 300.0, -230.0), (-70.0, 10.0, 20.0), 140.0),
    9: ((240.0, 280.0, 200.0), (-70.0, 0.0, 20.0), 165.0),
    10: ((240.0, -280.0, -160.0), (-50.0, 0.0, -60.0), 125.0),
}


def _scene(vtk, items, pos, tgt, scale, path, size=(1400, 1050)):
    """items: [(Vm, Fm, colour, opacity, offset)] -> PNG at path."""
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.95)
    ren.SetUseDepthPeeling(1)
    for Vm, Fm, col, op, off in items:
        ren.AddActor(_actor(vtk, Vm, Fm, col, op, off))
    for lp, inten in (((-150, -220, 450), .7), ((300, 250, 240), .55), ((0, 300, 100), .35), ((0, -300, -200), .3)):
        lt = vtk.vtkLight()
        lt.SetLightTypeToSceneLight()
        lt.SetPosition(*lp)
        lt.SetFocalPoint(*tgt)
        lt.SetIntensity(inten)
        ren.AddLight(lt)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*tgt)
    cam.SetPosition(*[tgt[k] + pos[k] for k in range(3)])
    cam.SetViewUp(0, 0, 1)
    cam.ParallelProjectionOn()
    cam.SetParallelScale(scale)
    ren.ResetCameraClippingRange()
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.SetAlphaBitPlanes(1)
    win.SetMultiSamples(0)
    win.AddRenderer(ren)
    win.Render()
    cap = vtk.vtkWindowToImageFilter()
    cap.SetInput(win)
    cap.ReadFrontBufferOff()
    cap.Update()
    w = vtk.vtkPNGWriter()
    w.SetFileName(path)
    w.SetInputConnection(cap.GetOutputPort())
    w.Write()
    win.Finalize()


def render_steps(rows, meshes, vtk):
    """renders/step-NN.png: parts already in the body in light grey, this step's parts in colour at the start of
    their insertion path (bench steps: the sub-assembly pulled apart). Illustration only."""
    files = {}
    start = {}
    for ins in L.INSERTIONS:
        for m in ins['moving']:
            start[m] = tuple(0.6 * v for v in ins['path'][0])
    bench_off = {'x1203': (0, 0, -18), 'x1203_kit': (0, 0, -9), 'pi5': (0, 0, 0), 'cooler': (0, 0, 22),
                 'panel': (0, 0, 0), 'encoder': (0, -30, 0), 'switch_1824': (0, -30, 0)}
    for st in L.STEPS:
        n = st['step']
        if n not in STEP_VIEWS:
            continue
        items = []
        if not st.get('in_body', True):
            for i in st.get('bench', []):
                if i in meshes:
                    Vm, Fm = meshes[i]
                    items.append((Vm, Fm, colour_of(i, rows[i]), 1.0, bench_off.get(i, (0, 0, 0))))
        else:
            new = set(st['adds'])
            for i in L.present_at(n):
                if i not in meshes:
                    continue
                Vm, Fm = meshes[i]
                if i in new:
                    off = start.get(i, (0, 0, 0))
                    if i.startswith('s_'):
                        s = next(s for s in L.SCREWS if s['id'] == i)
                        off = tuple(-s['axis'][k] * 25.0 for k in range(3))
                    items.append((Vm, Fm, colour_of(i, rows[i]), 1.0, off))
                else:
                    items.append((Vm, Fm, GHOST, 0.45 if rows[i]['kind'] == 'printed' else 0.8, (0, 0, 0)))
        pos, tgt, scale = STEP_VIEWS[n]
        p = os.path.join(OUT, 'renders', 'step-%02d.png' % n)
        _scene(vtk, items, pos, tgt, scale, p)
        files['renders/step-%02d.png' % n] = sha(p)
    log('render steps', len(files))
    return files

# ------------------------------------------------------------------------------------------- r2 (R3) section views
def render_sections(rows, R):
    """renders/section-<id>.png for every layout SECTIONS entry: exact B-rep section outlines (OCP BRepAlgoAPI_Section)
    of the listed parts in the plane, plotted to scale (matplotlib). EVF sections carry the restraint gaps."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    files = {}
    os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)
    names = 'xyz'
    for sec in CK.registry(L, 'SECTIONS'):
        ax_k = names.index(sec['axis'])
        uv = [names[i] for i in range(3) if i != ax_k]
        u0, u1, v0, v1 = sec['window']
        fig, ax = plt.subplots(figsize=(8, 8 * (v1 - v0) / max(1e-6, u1 - u0) + 0.8), dpi=150)
        seen = set()
        for n_p, pid in enumerate(sec['parts']):
            r = rows.get(pid)
            if r is None or r.get('shape') is None:
                continue
            col = plt.cm.tab10(n_p % 10)
            try:
                lines = CK.section_lines(r['shape'], sec['axis'], sec['at'])
            except Exception as e:  # noqa: BLE001
                log('section', sec['id'], pid, 'failed', e)
                continue
            for ln in lines:
                xs, ys = zip(*ln)
                ax.plot(xs, ys, '-', color=col, lw=1.1, label=None if pid in seen else
                        (pid + (' (STUB envelope)' if r.get('stub') else '')))
                seen.add(pid)
        ttl = sec.get('title', sec['id'])
        if R.get('evf_restraint') and sec['id'].startswith('evf'):
            ttl += chr(10) + ', '.join('%s %s%s' % (x['direction'], x.get('gap_mm'), '' if x['status'] == 'pass' else ' FAIL')
                                    for x in R['evf_restraint']) + ' (gap mm, limit %.1f)' % L.EVF_RESTRAINT['limit_mm']
        ax.set_title(ttl, fontsize=9)
        ax.set_xlim(u0, u1)
        ax.set_ylim(v0, v1)
        ax.set_aspect('equal')
        ax.set_xlabel(uv[0] + ' mm')
        ax.set_ylabel(uv[1] + ' mm')
        ax.grid(True, lw=0.3, alpha=0.5)
        ax.legend(fontsize=7, loc='best')
        fig.text(0.01, 0.005, 'CAD section of built solids (proxies for purchased parts); not a measurement', fontsize=6)
        p = os.path.join(OUT, 'renders', 'section-%s.png' % sec['id'])
        fig.savefig(p, bbox_inches='tight')
        plt.close(fig)
        files['renders/section-%s.png' % sec['id']] = sha(p)
    log('render sections', len(files))
    return files


EVIDENCE = os.path.join(HERE, 'evidence')
EVIDENCE_STATES = [
    ('slicer_review', 'slicer', 'slice every production STL (out/stl/<part>.stl) with the PRINT-GUIDE settings; one '
     'record per part naming that STL and its sha256 (no slicer is installed on the build machine)'),
    ('coupon_validation', 'coupons', 'print the gate coupons (out/stl/coupons) and record fit, torque, insertion/'
     'release cycles; one record per gate or calibration id naming every coupon STL it used with its sha256'),
    ('measured_fit', 'measured', 'measure the purchased parts against the MEASURED-PARTS.md gates'),
    ('assembly_operation', 'assembly', 'dry assembly, non-destructive service cycles and a powered recording test '
     '(ASSEMBLY.md, WIRING.md bench gates)'),
]
# r3 checks (audit 2026-10-05 s2): evidence = structured JSON records (evidence/README.md), never file names. A record
# binds one item (part id or gate id) to the sha256 of the artifacts actually tested; a record whose artifact hash
# differs from the CURRENT artifact is stale. Completeness (a current valid record exists) and the acceptance outcome
# (pass / fail / conflict / stale / not run) are reported separately; anything but a current pass stays open.
RECORD_FIELDS = ('item', 'state', 'artifacts', 'profile', 'verdict', 'date', 'by')
VERDICTS = ('pass', 'fail')
OUTCOMES = ('pass', 'fail', 'conflict', 'stale', 'not run')
STATE_GATES = [('coupon_validation', r'^G-(PT|KEEP|PANEL|CAP|EVF-2|SNAP|KNOB|COMB|J4)(-[0-9]+)?$'),
               ('measured_fit', r'^(G-MP-|G-CAM-|G-HDMI|G-RUN-|G-ENC-|G-PI-|G-PLG-|G-LENS|EVF-G[178]$)'),
               ('assembly_operation', r'.')]          # every other gate: G-W*, G-EVF-1, EVF-G2..G6, G9
# r3 checks (audit s2): the three PRINT-GUIDE s6 calibrations are required coupon_validation items, bound to their
# coupon STLs (out/coupons-manifest.json ids).
CALIBRATION_ITEMS = {
    'G-KNOB-1': dict(coupons=['knob_bore_ladder_enc', 'knob_bore_ladder_sw'],
                     what='knob D-bore ladder: push fit on the encoder and switch shafts; sets FDM KNOB_BORE_OFFSET'),
    'G-COMB-1': dict(coupons=['clearance_comb'],
                     what='clearance comb 0.15/0.25/0.30: confirms LOCATE / SLIDE / SEAM on this printer and profile'),
    'G-J4-1': dict(coupons=['tongue', 'keyhole_slot'],
                   what='J4 tongue + keyhole slot: drop in, slide 10 mm, no rock'),
}


def find_root(start=HERE):
    """Repo root = the nearest folder at or above `start` holding both 'cad' and 'electronics' (r3: the fork
    candidate-fr1/ uses this file verbatim one level deeper)."""
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, 'cad')) and os.path.isdir(os.path.join(d, 'electronics')):
            return d
        up = os.path.dirname(d)
        if up == d:
            raise RuntimeError('no folder holding cad/ and electronics/ above %s' % start)
        d = up


ROOT = find_root(HERE)
RELEASE_DIR = os.path.join(ROOT, 'cad', 'gs8-d2-v1')     # release docs (MEASURED-PARTS.md, SPEC.md) live here


def _rel_root(p):
    return os.path.relpath(p, ROOT).replace(os.sep, '/')


def _norm_key(k):
    k = str(k).replace('\\', '/').strip()
    while k.startswith('./'):
        k = k[2:]
    for pre in ('cad/gs8-d2-v1/candidate-fr1/out/', 'cad/gs8-d2-v1/out/', 'out/'):
        if k.startswith(pre):
            return k[len(pre):]
    return k


def validate_record(rec):
    """List of format errors of one record (empty = structurally valid)."""
    import re
    if not isinstance(rec, dict):
        return ['record is not a JSON object']
    err = ['missing field %s' % f for f in RECORD_FIELDS if f not in rec or rec[f] in (None, '', {}, [])]
    if rec.get('state') not in dict((k, 1) for k, _, _ in EVIDENCE_STATES):
        err.append('unknown state %r' % rec.get('state'))
    if str(rec.get('verdict', '')).lower() not in VERDICTS:
        err.append('verdict must be pass or fail, not %r' % rec.get('verdict'))
    art = rec.get('artifacts')
    if not isinstance(art, dict) or not art:
        err.append('artifacts must be a non-empty {path: sha256} object')
    else:
        err += ['artifact %s: sha256 must be 64 lower-case hex digits' % k for k, v in art.items()
                if not re.fullmatch(r'[0-9a-f]{64}', str(v))]
    return err


def load_records(evdir):
    """(records, ignored files, record-file hashes). Every *.json under evdir is a record file (one object, a list,
    or {"records": [...]}); README / template files (name starts with '_' or contains 'template') are skipped; any
    other file is listed as ignored (not evidence)."""
    recs, ignored, hashes = [], [], {}
    if not os.path.isdir(evdir):
        return recs, ignored, hashes
    for dp, _, fs in os.walk(evdir):
        for f in sorted(fs):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, evdir).replace(os.sep, '/')
            low = f.lower()
            if low == 'readme.md' or low.startswith('_') or 'template' in low:
                continue
            hashes[rel] = sha(p)
            if not low.endswith('.json'):
                ignored.append(rel)
                continue
            try:
                with open(p, encoding='utf-8') as fh:
                    data = json.load(fh)
            except (OSError, ValueError) as e:
                recs.append(dict(file=rel, index=0, rec=None, errors=['unreadable JSON: %s' % e]))
                continue
            items = data.get('records') if isinstance(data, dict) and 'records' in data else data
            items = items if isinstance(items, list) else [items]
            for i, r in enumerate(items):
                recs.append(dict(file=rel, index=i, rec=r, errors=validate_record(r)))
    return recs, ignored, hashes


def _first_existing(*paths):
    return next((p for p in paths if os.path.isfile(p)), None)


def coupon_artifacts(out_dir):
    """({canonical coupon STL path: sha256}, {gate id: [coupon STL paths]}, where the coupons were read). Coupons come
    from this build's out dir, else from the release out/stl/coupons (make_coupons.py output)."""
    import re
    cdir = os.path.join(out_dir, 'stl', 'coupons')
    if not os.path.isdir(cdir):
        cdir = os.path.join(HERE, 'out', 'stl', 'coupons')
    cur = {}
    if os.path.isdir(cdir):
        cur = {'stl/coupons/' + f: sha(os.path.join(cdir, f)) for f in sorted(os.listdir(cdir)) if f.endswith('.stl')}
    gm = {}
    for name in ('coupons-manifest.json', 'coupons-r1-manifest.json'):
        p = _first_existing(os.path.join(out_dir, name), os.path.join(HERE, 'out', name))
        if not p:
            continue
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        for c in d.get('coupons', []):
            for g in re.findall(r'(?<![A-Za-z0-9])G-[A-Z0-9]+(?:-[A-Z0-9]+)*', str(c.get('gate', ''))):
                gm.setdefault(g, []).append(c['stl'])
    for g, v in CALIBRATION_ITEMS.items():
        gm[g] = ['stl/coupons/%s.stl' % c for c in v['coupons']]
    return cur, {g: sorted(set(v)) for g, v in gm.items()}, _rel_root(cdir)


def resolve_artifact(key, cur):
    """(canonical key, current sha256 or None): this build's files and coupons first, then a file under HERE or ROOT
    (sources and docs)."""
    k = _norm_key(key)
    if k in cur:
        return k, cur[k]
    if not k.startswith('stl/'):
        for base in (HERE, ROOT):
            p = os.path.normpath(os.path.join(base, k))
            if os.path.isfile(p):
                return k, sha(p)
    return k, None


def evaluate_item(state, item, recs, cur, required):
    """One required item. required = canonical artifact paths every record must name (the production STL for a
    slicer item, the gate's coupon STLs for a coupon item); [] = any current artifact. A record is: rejected (format,
    a coupon artifact on a production item, a required artifact not named), stale (an artifact hash differs from the
    current one or the artifact no longer exists) or current. outcome: pass / fail / conflict (current records
    disagree) / stale (only stale records) / not run."""
    current, stale, rejected = [], [], []
    for r in recs:
        rec = r['rec']
        if not isinstance(rec, dict) or rec.get('item') != item or rec.get('state') != state:
            continue
        tag = '%s#%d' % (r['file'], r['index'])
        if r['errors']:
            rejected.append(dict(record=tag, why='; '.join(r['errors'])))
            continue
        art = {_norm_key(k): str(v) for k, v in rec['artifacts'].items()}
        if state == 'slicer_review' and any(k.startswith('stl/coupons/') for k in art):
            rejected.append(dict(record=tag, why='a coupon artifact cannot satisfy a production-part item'))
            continue
        miss = [k for k in required if k not in art]
        if miss:
            rejected.append(dict(record=tag, why='does not name the required artifact(s): ' + ', '.join(miss)))
            continue
        diffs = []
        for k, v in sorted(art.items()):
            now = resolve_artifact(k, cur)[1]
            if now is None:
                diffs.append('%s: no current artifact' % k)
            elif now != v:
                diffs.append('%s: tested %s, current %s' % (k, v[:12], now[:12]))
        row = dict(record=tag, verdict=str(rec['verdict']).lower(), date=rec.get('date'), by=rec.get('by'),
                   profile=rec.get('profile'))
        if diffs:
            stale.append(dict(row, stale=diffs))
        else:
            current.append(row)
    verdicts = sorted({c['verdict'] for c in current})
    outcome = (('conflict' if len(verdicts) > 1 else verdicts[0]) if verdicts else ('stale' if stale else 'not run'))
    return dict(evidence_complete=bool(current), outcome=outcome, required_artifacts=list(required),
                current=current, stale=stale, rejected=rejected)


def evidence_state(state, sub, what, items, recs, cur, required_of):
    """One evidence state: per item completeness + outcome; the state is open unless EVERY required item has a
    current pass. The build reports person-recorded verdicts bound to artifact hashes; it never judges them."""
    items = list(items or [])
    per = {it: evaluate_item(state, it, recs, cur, required_of(it)) for it in items}
    by = {o: sorted(i for i, v in per.items() if v['outcome'] == o) for o in OUTCOMES}
    mine = [r for r in recs if isinstance(r['rec'], dict) and r['rec'].get('state') == state]
    unmatched = sorted('%s#%d (item %r)' % (r['file'], r['index'], r['rec'].get('item')) for r in mine
                       if r['rec'].get('item') not in per)
    n, k = len(items), len(by['pass'])
    st = dict(evidence_dir='evidence/%s/' % sub, needed=what, items_required=n,
              items_complete=sum(1 for v in per.values() if v['evidence_complete']), items_pass=k,
              outcomes={o: len(by[o]) for o in OUTCOMES}, failed=by['fail'], conflict=by['conflict'],
              stale=by['stale'], not_run=by['not run'], unmatched_records=unmatched, open=(n == 0 or k < n),
              items={i: v for i, v in per.items() if v['outcome'] != 'not run' or v['rejected']})
    if not mine:
        st['status'] = 'not run' + ('' if n else ' (no required items registered)')
    elif st['open']:
        st['status'] = ('open: %d of %d items have a current recorded pass (fail %d, conflict %d, stale %d, not run %d)'
                        % (k, n, len(by['fail']), len(by['conflict']), len(by['stale']), len(by['not run'])))
    else:
        st['status'] = ('all %d items have a current recorded pass (person-recorded verdicts bound to the tested '
                        'artifact hashes; not judged by this build)' % n)
    return st


def open_evidence_list(status_states):
    """Every evidence state that is not a current pass for all items, with failed / conflict / stale ids named."""
    out = []
    for k, v in status_states.items():
        if k == 'cad_checks' or not v.get('open', True):
            continue
        det = ['%s: %s' % (o, ', '.join(v[f])) for o, f in (('fail', 'failed'), ('conflict', 'conflict'),
                                                            ('stale', 'stale')) if v.get(f)]
        if v.get('not_run'):
            det.append('not run: %d item(s)' % len(v['not_run']))
        out.append(k + (' (%s)' % '; '.join(det) if det else ''))
    return out


def state_items(gates):
    """Required items per evidence state: slicer = every printed part id; the others = the live gate ids by
    STATE_GATES, plus the CALIBRATION_ITEMS (coupon_validation)."""
    import re
    live = [g for g, v in gates['gates'].items() if not v.startswith('withdrawn')]
    live += [g for g in CALIBRATION_ITEMS if g not in live]
    out = {'slicer_review': sorted(L.PARTS)}
    left = list(live)
    for st, pat in STATE_GATES:
        out[st] = sorted(g for g in left if re.search(pat, g))
        left = [g for g in left if g not in out[st]]
    return out


GATE_DOCS = [os.path.join(RELEASE_DIR, 'MEASURED-PARTS.md'), os.path.join(RELEASE_DIR, 'SPEC.md'),
             os.path.join(ROOT, 'electronics', 'gs8-d2-v1', 'WIRING.md')]
EVF_GATE_DOC = os.path.join(ROOT, 'electronics', 'gs8-evf-v1', 'EVF-SELECTION.md')   # its table gates G1..G9 -> EVF-G*


def hardware_gates():
    """Every bench/measurement gate id (G-...) named in GATE_DOCS (+ EVF-G* from the EVF-SELECTION table), 'open (no
    record)' or 'withdrawn'; apply_gate_outcomes() fills in the record outcome. Bare prefixes (G-W, G-MP) dropped."""
    import re
    ids, docs, text = set(), {}, ''
    for p in GATE_DOCS:
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                t = f.read()
            text += t
            ids |= set(re.findall(r'(?<![A-Za-z0-9])G-[A-Z0-9]+(?:-[A-Z0-9]+)*', t))
            docs[_rel_root(p)] = sha(p)
    if os.path.exists(EVF_GATE_DOC):
        with open(EVF_GATE_DOC, encoding='utf-8') as f:
            t = f.read()
        ids |= {'EVF-' + g for g in re.findall(r'(?m)^\|\s*(G[0-9]+[a-z]?)\s', t)}
        docs[_rel_root(EVF_GATE_DOC)] = sha(EVF_GATE_DOC)
    ids = sorted(i for i in ids if any(c.isdigit() for c in i) or not any(j != i and j.startswith(i) for j in ids))
    gates = {}
    for g in ids:
        gates[g] = 'open (no record)'
        if re.search(re.escape(g) + r'[.*:)\s]{0,6}[Ww]ithdrawn', text):   # INTEGRATOR r2: e.g. G-SNAP-1
            gates[g] = 'withdrawn (feature deleted; see the gate doc)'
    return dict(source_docs=docs, gates=gates)


def apply_gate_outcomes(hg, status_states):
    """Gate text from the record outcome of its item (any state): only a current recorded pass reads 'recorded pass'."""
    txt = {'pass': 'recorded pass (current record; person-recorded, not judged by this build)',
           'fail': 'open: recorded FAIL', 'conflict': 'open: conflicting records', 'stale': 'open: stale record only'}
    for k, v in status_states.items():
        for it, r in (v.get('items') or {}).items():
            if it in hg['gates'] or it in CALIBRATION_ITEMS:
                hg['gates'][it] = txt.get(r['outcome'], 'open (no current record)') + (
                    ' [%d rejected record(s)]' % len(r['rejected']) if r['rejected'] else '')
    for g in CALIBRATION_ITEMS:
        hg['gates'].setdefault(g, 'open (no record)')
    return hg


# ------------------------------------------------------------------------------------------- main
ROW_STATUSES = ('pass', 'fail', 'stub', 'info')


def summarize(name, rows, info_neutral=False):
    """r3 checks (audit s2): an unknown row status is rejected (category fail, listed). info_neutral: 'info' rows
    (non-structural entries, removed parts, gated exceptions) neither pass nor block, but the category passes only
    with >= 1 actual 'pass' row and no fail / stub row."""
    st = [r.get('status') for r in rows]
    base = dict(check=name, n=len(st), passed=st.count('pass'), failed=st.count('fail'), stub=st.count('stub'),
                info=st.count('info'))
    unknown = sorted({repr(s) for s in st if s not in ROW_STATUSES})
    if unknown:
        return dict(base, status='fail', unknown_statuses=unknown,
                    error='unknown row status(es) rejected: ' + ', '.join(unknown))
    if info_neutral:
        core = [x for x in st if x != 'info']
        status = 'fail' if 'fail' in core else ('stub' if 'stub' in core else ('pass' if core else 'fail'))
        out = dict(base, status=status)
        if not core:
            out['error'] = 'no actual pass row (informational rows only)'
        return out
    return dict(base, status='pass' if st and all(s == 'pass' for s in st) else
                ('fail' if 'fail' in st else ('stub' if 'stub' in st else ('pass' if not st else 'info'))))


def source_hashes():
    names = ['layout.py', 'd2_common.py', 'cots.py', 'checks.py', 'build_d2.py', 'make_coupons.py', 'make_tables.py',
             'SPEC.md', 'FASTENER-POLICY.md']
    names += sorted({p['module'] for p in L.PARTS.values()})
    names += sorted(f for f in os.listdir(HERE) if f.startswith('coupons') and f.endswith('.py'))   # r2: coupons_r1.py
    return {n: (sha(os.path.join(HERE, n)) if os.path.exists(os.path.join(HERE, n)) else 'missing') for n in names}


def peak_mem_mb():
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + \
                       [(n, ctypes.c_size_t) for n in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                                                       'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                                                       'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
        ctypes.windll.psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return round(c.PeakWorkingSetSize / 2 ** 20, 1)
    except Exception:  # noqa: BLE001
        return None


def lens_rows():
    out = {}
    for name in L.LENSES:
        shape, d = cots.lens_proxy(L, name)
        out[name] = dict(mass=d['mass'], com=d['com'], name=d['name'])
    return out


def run_part(pid, args):
    """--part: one printed id (or one COTS id) built and checked on its own."""
    os.makedirs(OUT, exist_ok=True)
    res = dict(part=pid, revision=L.REVISION,
               scope='this part + the COTS proxies only; other printed parts are absent (run the full build for '
                     'part-to-part checks); n/a = partner not in this run')
    if pid in L.PARTS:
        t0 = time.time()
        prow, mods = build_printed(only=pid)
        lap('build ' + pid, t0)
        r = prow[pid]
        crow = build_cots()
        rows = dict(crow, **prow)
        res['module'] = mods
        res['contract'] = contract_checks(prow)
        bed, thin = [], []
        if not args.no_thin and not r.get('stub'):
            thin.append(CK.thin_wall(L, pid, r['shape'], loaded_boxes=CK.loaded_boxes(L, pid)))
        res['thin_wall'] = thin
        mrow = []
        res['manifest'] = export_part(pid, r, bed, thin, mrow)
        res['stl_mesh'] = mrow
        res['bed'] = bed
        res['keepouts'] = [k for k in CK.check_keepouts(L, {pid: r})]
        res['critical_features'] = [x for x in CK.check_critical_features(L, rows) if x.get('part') == pid]   # r2 R3
        res['interference_with_cots'] = [x for x in CK.check_interference(L, rows) if pid in x['pair']]
        res['mate_overlap'] = [x for x in CK.check_mate_overlap(L, rows) if pid in x['pair']]
        res['clearance'] = [x for x in CK.check_clearances(L, rows) if pid in x['pair']]
        res['sweeps'] = []
        if not args.no_sweeps:      # insertions that move this part or meet it (other printed parts are stubs here)
            for sw in CK.check_sweeps(L, rows, args.sweep_step, only=pid):
                sw['hits'] = [h for h in sw['hits'] if pid in (h['moving'], h['obstacle'])]
                sw['status'] = 'pass' if not sw['hits'] else ('stub' if all(h['stub'] for h in sw['hits'])
                                                              else 'fail')
                res['sweeps'].append(sw)
        res['volume_mm3'] = round(r['shape'].Volume(), 1)
        res['mass_100pct_g'] = res['manifest']['mass_100pct_g']
        res['mass_est_g'] = res['manifest']['mass_est_g']
        bb = CK.bb_tuple(r['shape'])
        res['bbox_assembly'] = [round(x, 2) for x in bb]
        bad = [x for x in res['contract'] + res['keepouts'] + res['interference_with_cots'] + bed + mrow +
               [c for c in res['critical_features'] if c.get('status') != 'info'] + thin +
               res['mate_overlap'] + [c for c in res['clearance'] if c['status'] != 'n/a'] + res['sweeps']
               if x.get('status') not in ('pass',)]
        res['status'] = 'stub' if r.get('stub') else ('pass' if not bad else
                                                      ('fail' if any(x.get('status') == 'fail' for x in bad)
                                                       else 'pass (stub partners)'))
    elif pid in L.COTS or pid.startswith('s_'):
        crow = build_cots(only={pid})
        r = crow[pid]
        res.update(cots_containment(crow) and dict(containment=cots_containment(crow)) or {})
        if r['shape'] is not None:
            res['volume_mm3'] = round(r['shape'].Volume(), 1)
            res['bbox_assembly'] = [round(x, 2) for x in CK.bb_tuple(r['shape'])]
        res['mass_g'] = r['mass']
        res['status'] = 'info'
    else:
        raise SystemExit('unknown id %s' % pid)
    res['seconds'] = round(time.time() - T0, 1)
    write_json('part-%s.json' % pid, res)
    log('part %s: %s, volume %s mm3, mass %s g (100 %%: %s g)' % (pid, res['status'], res.get('volume_mm3'),
                                                                 res.get('mass_est_g', res.get('mass_g')),
                                                                 res.get('mass_100pct_g')))
    return 0


def run_full(args):
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    selfc = L.self_check()
    lap('layout self-check', t0)
    t0 = time.time()
    prow, mods = build_printed()
    lap('printed modules', t0)
    t0 = time.time()
    crow = build_cots()
    lap('cots', t0)
    rows = dict(crow, **prow)
    stubs = sorted(i for i, r in prow.items() if r.get('stub'))
    R = {}
    t0 = time.time()
    R['contract'] = contract_checks(prow)
    R['cots_containment'] = cots_containment(crow)
    lap('contract', t0)
    t0 = time.time()
    R['interference'] = CK.check_interference(L, rows)
    R['mate_overlap'] = CK.check_mate_overlap(L, rows)
    lap('interference', t0)
    t0 = time.time()
    R['clearance'] = CK.check_clearances(L, rows)
    lap('clearance', t0)
    t0 = time.time()
    R['keepouts'] = CK.check_keepouts(L, rows)
    lap('keepouts', t0)
    t0 = time.time()
    R['thin_wall'] = []
    for pid, r in prow.items():
        if r.get('stub'):
            R['thin_wall'].append(dict(part=pid, status='stub'))
        elif not args.no_thin:
            R['thin_wall'].append(CK.thin_wall(L, pid, r['shape'], loaded_boxes=CK.loaded_boxes(L, pid)))
    lap('thin wall', t0)
    t0 = time.time()
    R['driver'] = CK.check_driver(L, rows)
    lap('driver audit', t0)
    t0 = time.time()
    R['critical_features'] = CK.check_critical_features(L, rows)        # r2 R3: finding 2 (gates; thin_wall is a screen)
    R['unclassified_thin_spots'] = CK.unclassified_thin_spots(L, R['thin_wall'])   # informational, not in the summary
    lap('critical features', t0)
    t0 = time.time()
    R['evf_restraint'] = CK.check_evf_restraint(L, rows)                # r2 R3: finding 6
    lap('evf restraint', t0)
    t0 = time.time()
    if args.no_sweeps:
        R['removals'], R['service_driver'] = [], []
    else:                                                               # r2 R3: findings 1/3 (service paths)
        R['removals'], R['service_driver'] = CK.check_removals(L, rows, args.sweep_step)
        R['removals'] += CK.removal_coverage(L)
    R['release_access'] = CK.check_release_access(L, rows)             # FIXER r2 (M-V-MPS-2): hood hold-open pins
    R['stack_retention'] = CK.check_stack_retention(L, rows)           # FIXER r2 (M-V-MPS-4): far-side stop
    lap('removals + service driver', t0)
    t0 = time.time()
    R['engrave_groove'] = CK.check_engrave(L)          # FIXER P1
    R['boss_geometry'] = CK.check_bosses(L, rows)      # FIXER P5
    lap('engrave + bosses', t0)
    t0 = time.time()
    R['sweeps'] = [] if args.no_sweeps else CK.check_sweeps(L, rows, args.sweep_step)
    lap('sweeps', t0)
    t0 = time.time()
    R['mass_com'] = {}
    for name, lr in lens_rows().items():
        R['mass_com'][name] = CK.mass_com(L, rows, lr)
    lap('mass/CoM', t0)
    R['layout_self_check'] = [dict(x, status='pass' if x['ok'] else 'fail') for x in selfc]
    t0 = time.time()
    bed, manifest, meshes = [], [], []
    for pid, r in prow.items():
        manifest.append(export_part(pid, r, bed, R['thin_wall'], meshes))
    R['bed_fit'] = bed
    R['stl_mesh'] = meshes
    lap('stl + bed fit', t0)
    files = {}
    if not args.fast:
        t0 = time.time()
        try:
            files['step/gs8-d2-assembly.step'] = sha(export_step(rows))
        except Exception as e:  # noqa: BLE001
            log('STEP export failed', e)
        lap('step', t0)
        t0 = time.time()
        try:
            files.update(render_all(rows))
        except Exception:  # noqa: BLE001
            log('render failed', traceback.format_exc(limit=3))
        lap('renders', t0)
    t0 = time.time()
    try:
        files.update(render_sections(rows, R))
    except Exception:  # noqa: BLE001
        log('section render failed', traceback.format_exc(limit=3))
    lap('section renders', t0)
    # ---- summaries
    order = ['contract', 'cots_containment', 'interference', 'mate_overlap', 'clearance', 'keepouts', 'bed_fit', 'stl_mesh', 'thin_wall',
             'critical_features', 'evf_restraint',
             'driver', 'engrave_groove', 'boss_geometry',
             'sweeps', 'removals', 'service_driver', 'release_access', 'stack_retention', 'layout_self_check']
    summ = [summarize(k, R[k], info_neutral=k in ('critical_features', 'removals')) for k in order]
    if args.no_sweeps:
        for k in ('sweeps', 'removals', 'service_driver'):
            summ[order.index(k)]['status'] = 'not run'
    if not R['service_driver'] and not args.no_sweeps:
        summ[order.index('service_driver')].update(status='pass', note='no screw is removed on a modelled service path')
    if args.no_thin:
        summ[order.index('thin_wall')]['status'] = 'not run'
    summ[order.index('thin_wall')]['role'] = ('secondary share-based screen: cannot pass the build alone; the gate for '
                                              'local thickness is critical_features (finding 2)')
    mc_ok = all(m['total_g'] > 0 for m in R['mass_com'].values())
    summ.append(dict(check='mass_com', status='pass' if mc_ok and not stubs else ('stub' if stubs else 'fail')))
    rc = all(s['status'] == 'pass' for s in summ) and not stubs and         summ[order.index('critical_features')]['status'] == 'pass'      # explicit: the screen alone never passes
    checks = dict(revision=L.REVISION, variant=getattr(L, 'FR_STATE', None), lens_default=L.LENS, stubs=stubs, summary=summ, results=R,
                  fit_language='Only computed checks say pass. Purchased parts are proxies; nothing is printed, '
                               'bought or measured.')
    write_json('checks.json', checks)
    write_json('print-manifest.json', dict(revision=L.REVISION, beds=L.PRINT_BEDS, fdm=L.FDM,
                                           time_model='%.1f mm3/s effective x 1.15 + 0.1 h (estimate, not a slicer result)' % PRINT_RATE,
                                           mass_model='volume x density x infill factor (estimate, not weighed)',
                                           parts=manifest,
                                           totals=dict(mass_est_g=round(sum(m['mass_est_g'] for m in manifest), 1),
                                                       mass_100pct_g=round(sum(m['mass_100pct_g'] for m in manifest), 1),
                                                       print_time_est_h=round(sum(m['print_time_est_h'] for m in manifest), 1))))
    parts = []
    for i, r in rows.items():
        sh = r.get('shape')
        parts.append(dict(id=i, kind=r['kind'], stub=bool(r.get('stub')), name=r.get('name', L.PARTS.get(i, {}).get('module')),
                          pn=r.get('pn'), src=r.get('src'), step=r.get('step', next((s['step'] for s in L.STEPS
                                                                                     if i in s['adds']), None)),
                          mass_g=(round(L.mass_g(sh.Volume(), i), 1) if r['kind'] == 'printed' else r.get('mass')),
                          bbox=None if sh is None else [round(x, 2) for x in CK.bb_tuple(sh)]))
    write_json('parts-manifest.json', dict(revision=L.REVISION, parts=parts, lens_options=list(L.LENSES)))
    for n in ('checks.json', 'print-manifest.json', 'parts-manifest.json'):
        files[n] = sha(os.path.join(OUT, n))
    if os.path.exists(os.path.join(OUT, 'coupons-manifest.json')):   # FIXER P-P11 (make_coupons.py output)
        files['coupons-manifest.json'] = sha(os.path.join(OUT, 'coupons-manifest.json'))
    for n in ('coupons-r1-manifest.json', 'checks-fujinon-sweep1mm.json'):   # FIXER r2 (E-V-E10): hash-linked
        if os.path.exists(os.path.join(OUT, n)):
            files[n] = sha(os.path.join(OUT, n))
    cdir = os.path.join(OUT, 'stl', 'coupons')                       # r2 R3: every coupon STL is hash-linked too
    if os.path.isdir(cdir):
        for f in sorted(os.listdir(cdir)):
            files['stl/coupons/' + f] = sha(os.path.join(cdir, f))
    for m in manifest:
        if m['stl']:
            files[m['stl']] = m['stl_sha256']
    n_pass = sum(1 for x in summ if x['status'] == 'pass')
    hgates = hardware_gates()                          # r3 checks: structured records, per item and state
    sitems = state_items(hgates)
    recs, ev_ignored, ev_files = load_records(EVIDENCE)
    ccur, cmap, csrc = coupon_artifacts(OUT)
    cur = dict(files, **ccur)        # the CURRENT artifacts: this build's production STL + manifests, the coupon STLs

    def required_of(state):
        if state == 'slicer_review':
            return lambda it: ['stl/%s.stl' % it]
        if state == 'coupon_validation':
            return lambda it: cmap.get(it, [])
        return lambda it: []
    status_states = dict(       # r2 R3 (finding 8): separate evidence states; only cad_checks is computed here
        cad_checks=dict(status='computed: ' + ('pass' if rc else 'fail'), checks_passed=n_pass,
                        checks_not_passed=len(summ) - n_pass, failed=[x['check'] for x in summ if x['status'] == 'fail'],
                        rows_passed=sum(x.get('passed', 0) for x in summ), rows_failed=sum(x.get('failed', 0) for x in summ),
                        checks_json_sha256=files['checks.json'],
                        note='CAD geometry checks on built solids and purchased-part proxies only'),
        **{k: evidence_state(k, sub, what, sitems.get(k), recs, cur, required_of(k)) for k, sub, what in EVIDENCE_STATES})
    apply_gate_outcomes(hgates, status_states)
    evidence_meta = dict(record_files=ev_files, ignored_files=ev_ignored, coupons_from=csrc,
                         rejected_records=sorted({x['record'] + ': ' + x['why'] for v in status_states.values()
                                                  for r in (v.get('items') or {}).values() for x in r['rejected']}),
                         format='evidence/README.md (structured JSON records bound to artifact sha256; no file-name '
                                'matching)')
    receipt = dict(revision=L.REVISION, variant=getattr(L, 'FR_STATE', None), built_at=time.strftime('%Y-%m-%d %H:%M:%S %z'), argv=sys.argv[1:],
                   sources=source_hashes(), modules=mods, stubs=stubs, summary=summ, status_states=status_states,
                   totals=dict(printed=len(prow), cots=len([r for r in crow.values() if r['kind'] == 'cots']),
                               screws=len(L.SCREWS), printed_mass_est_g=round(sum(m['mass_est_g'] for m in manifest), 1),
                               print_time_est_h=round(sum(m['print_time_est_h'] for m in manifest), 1),
                               estimates_note='mass = solid volume x density x infill factor; print time = volume / '
                                              '%.1f mm3/s x 1.15 + 0.1 h per part. Estimates, NOT slicer results '
                                              '(slicer_review: see status_states).' % PRINT_RATE,
                               mass_com={k: dict(total_g=v['total_g'], com=v['com'],
                                                 ahead_of_grip_axis=v['com_ahead_of_grip_axis'],
                                                 above_grip_top=v['com_above_grip_top'])
                                         for k, v in R['mass_com'].items()}),
                   files=files, timings_s=TIMES, total_s=round(time.time() - T0, 1), peak_mem_mb=peak_mem_mb(),
                   cad_release_candidate=rc, blocking=[x['check'] for x in summ if x['status'] != 'pass'] + (
                       ['stubs: ' + ', '.join(stubs)] if stubs else []),
                   open_evidence=open_evidence_list(status_states),
                   open_evidence_detail={k: dict(failed=v['failed'], conflict=v['conflict'], stale=v['stale'],
                                                 not_run=len(v['not_run']), items_pass=v['items_pass'],
                                                 items_required=v['items_required'])
                                         for k, v in status_states.items() if k != 'cad_checks' and v['open']},
                   evidence=evidence_meta, hardware_gates=hgates,
                   unclassified_thin_spots=[dict(part=x['part'], at=x['at'], t_min=x['t_min']) for x in
                                            R['unclassified_thin_spots']],
                   note='cad_release_candidate (was release_candidate) is true only if every CAD check passes, the '
                        'critical-feature gate passes and no printed part is a stub. It is NOT a hardware, print or '
                        'finished-camera claim: slicer review, coupons, measured fit and assembly/operation are '
                        'separate states (status_states) and stay "not run" until structured evidence records exist '
                        '(evidence/README.md); a state stays in open_evidence until every item has a current pass.')
    write_json('build-receipt.json', receipt)
    for s in summ:
        log('%-18s %s %s' % (s['check'], s['status'], '' if 'n' not in s else '(%d: %d pass, %d fail, %d stub)'
                             % (s['n'], s['passed'], s['failed'], s['stub'])))
    for k, v in R['mass_com'].items():
        log('mass/CoM %-14s %.0f g, CoM %s, ahead of grip axis %+.1f, above grip top %+.1f'
            % (k, v['total_g'], v['com'], v['com_ahead_of_grip_axis'], v['com_above_grip_top']))
    log('stubs:', stubs or 'none', ' cad_release_candidate:', rc, ' blocking:', receipt['blocking'] or 'none',
        ' total %.1f s' % (time.time() - T0))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--part')
    ap.add_argument('--fast', action='store_true')
    ap.add_argument('--lens', choices=sorted(L.LENSES), default=L.LENS)
    ap.add_argument('--sweep-step', type=float, default=2.0)
    ap.add_argument('--no-sweeps', action='store_true')
    ap.add_argument('--no-thin', action='store_true')
    ap.add_argument('--out', help='output directory (default cad/gs8-d2-v1/out); r2 trial builds use out/_trial-<who>')
    args = ap.parse_args(argv)
    if args.out:
        global OUT
        OUT = os.path.abspath(args.out)
    L.LENS = args.lens
    if args.part:
        return run_part(args.part, args)
    return run_full(args)


if __name__ == '__main__':
    sys.exit(main())
