# SPDX-License-Identifier: MIT
"""GS8 D2 assembly guide: IKEA-style line-art renderer (VTK offscreen ID / depth / normal passes + image-space edges).

Parts already in the body: light grey fill, grey outlines. Parts added in the step: pale highlight, black outlines.
Added parts hidden behind installed ones: dashed blue-grey outline. Motion arrows and point marks are drawn by the
page composer (build_guide.py) with project(). Frame: X forward (lens side), Y left (panel side), Z up.
"""
from __future__ import annotations

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy
from PIL import Image

SS = 2                                    # supersampling
HILITE = np.array([255, 238, 196], np.float32)
OLD_FILL = np.array([238, 238, 236], np.float32)
INK = np.array([22, 22, 22], np.float32)
OLD_LINE = np.array([150, 150, 150], np.float32)
HID_LINE = np.array([80, 110, 170], np.float32)


def _poly(V, F, rgb):
    pts = vtk.vtkPoints()
    pts.SetData(numpy_to_vtk(np.ascontiguousarray(V, np.float32), deep=True))
    cells = np.hstack([np.full((len(F), 1), 3, np.int64), F.astype(np.int64)]).ravel()
    ca = vtk.vtkCellArray()
    ca.SetCells(len(F), numpy_to_vtkIdTypeArray(cells, deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(pts)
    poly.SetPolys(ca)
    arr = numpy_to_vtk(np.ascontiguousarray(rgb, np.uint8), deep=True)
    arr.SetName('c')
    poly.GetCellData().SetScalars(arr)
    return poly


def face_normals(V, F):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-12)


class Camera:
    def __init__(self, d, target, scale, W, H):
        self.d = np.asarray(d, float) / np.linalg.norm(d)          # direction from target TO the camera
        self.target = np.asarray(target, float)
        self.scale = float(scale)                                  # half height in mm
        self.W, self.H = W, H
        up = np.array([0.0, 0.0, 1.0])
        if abs(self.d @ up) > 0.97:
            up = np.array([-1.0, 0.0, 0.0])
        dop = -self.d
        r = np.cross(dop, up)
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, dop)
        self.up = up

    def project(self, P):
        P = np.atleast_2d(np.asarray(P, float)) - self.target
        k = (self.H / 2.0) / self.scale
        x = self.W / 2.0 + (P @ self.r) * k
        y = self.H / 2.0 - (P @ self.u) * k
        return np.stack([x, y], 1)

    def depth(self, P):
        return (np.atleast_2d(np.asarray(P, float)) - self.target) @ self.d    # larger = nearer the viewer


def fit_camera(d, items, W, H, margin=1.08, zoom=1.0, min_half=20.0, focus=None):
    """items: [(V, F, style, offset)]; focus: optional list of item indexes the frame must contain (else all)."""
    cam = Camera(d, (0, 0, 0), 100.0, W, H)
    pts = []
    for k, (V, F, st, off) in enumerate(items):
        if focus is not None and k not in focus:
            continue
        step = max(1, len(V) // 4000)
        pts.append(V[::step] + np.asarray(off, float))
    P = np.vstack(pts)
    a, b = P @ cam.r, P @ cam.u
    cx, cy = (a.min() + a.max()) / 2, (b.min() + b.max()) / 2
    hw, hh = (a.max() - a.min()) / 2, (b.max() - b.min()) / 2
    half = max(hh, hw * H / W, min_half) * margin / zoom
    tgt = cam.r * cx + cam.u * cy + cam.d * float(np.median(P @ cam.d))
    return Camera(d, tgt, half, W, H)


def _render(polys, cam, W, H, zbuf=False):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for poly, off in polys:
        mp = vtk.vtkPolyDataMapper()
        mp.SetInputData(poly)
        mp.SetScalarModeToUseCellData()
        mp.SetColorModeToDirectScalars()
        mp.ScalarVisibilityOn()
        a = vtk.vtkActor()
        a.SetMapper(mp)
        pr = a.GetProperty()
        pr.LightingOff()
        pr.SetInterpolationToFlat()
        a.SetPosition(*[float(v) for v in off])
        ren.AddActor(a)
    c = ren.GetActiveCamera()
    c.ParallelProjectionOn()
    c.SetFocalPoint(*cam.target)
    c.SetPosition(*(cam.target + cam.d * 2000.0))
    c.SetViewUp(*cam.up)
    c.SetParallelScale(cam.scale)
    ren.ResetCameraClippingRange()
    near, far = c.GetClippingRange()
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(W, H)
    win.SetMultiSamples(0)
    win.AddRenderer(ren)
    win.Render()
    cap = vtk.vtkWindowToImageFilter()
    cap.SetInput(win)
    cap.ReadFrontBufferOff()
    cap.SetInputBufferTypeToRGB()
    cap.Update()
    img = vtk_to_numpy(cap.GetOutput().GetPointData().GetScalars()).reshape(H, W, -1)[::-1, :, :3].copy()
    z = None
    if zbuf:
        cz = vtk.vtkWindowToImageFilter()
        cz.SetInput(win)
        cz.ReadFrontBufferOff()
        cz.SetInputBufferTypeToZBuffer()
        cz.Update()
        z = vtk_to_numpy(cz.GetOutput().GetPointData().GetScalars()).reshape(H, W)[::-1].astype(np.float64)
        z = near + z * (far - near)
    win.Finalize()
    return img, z


def _shift(a, dy, dx, fill):
    out = np.full_like(a, fill)
    H, W = a.shape[:2]
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = a[ys, xs]
    return out


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r + 1 and (dy or dx):
                out |= _shift(m, dy, dx, False)
    return out


def _enc(k):
    return np.array([10 + 4 * (k % 60), 30 + 4 * (k // 60), 200], np.uint8)


def _dec(img):
    obj = (img[:, :, 2] > 150) & (img[:, :, 2] < 240)
    k = np.rint((img[:, :, 0].astype(int) - 10) / 4).astype(int) + 60 * np.rint((img[:, :, 1].astype(int) - 30) / 4).astype(int)
    return np.where(obj, k, -1)


def render(items, cam, xray_old=False):
    """items: [(V, F, style, offset)] with style 'new' | 'old'. Returns a PIL RGB image of cam.W x cam.H."""
    W, H = cam.W * SS, cam.H * SS
    cam2 = Camera(cam.d, cam.target, cam.scale, W, H)
    id_polys, n_polys, new_polys = [], [], []
    for k, (V, F, st, off) in enumerate(items):
        e = np.tile(_enc(k), (len(F), 1))
        id_polys.append((_poly(V, F, e), off))
        n = face_normals(V, F)
        n_polys.append((_poly(V, F, np.clip((n + 1.0) * 127.5, 0, 255)), off))
        if st == 'new':
            new_polys.append((_poly(V, F, e), off))
    idimg, z = _render(id_polys, cam2, W, H, zbuf=True)
    nimg, _ = _render(n_polys, cam2, W, H)
    idm = _dec(idimg)
    styles = np.array([1 if it[2] == 'new' else 0 for it in items] + [0])
    is_new = (idm >= 0) & (styles[np.maximum(idm, 0)] == 1) & (idm >= 0)
    nrm = nimg.astype(np.float32) / 127.5 - 1.0
    # fill with gentle shading (light from upper left, towards the viewer)
    L = cam2.d * 0.75 + cam2.u * 0.5 - cam2.r * 0.35
    L = L / np.linalg.norm(L)
    lam = np.clip(nrm @ L.astype(np.float32), 0, 1)[..., None]
    out = np.full((H, W, 3), 255.0, np.float32)
    old = (idm >= 0) & ~is_new
    out[old] = (OLD_FILL * (0.93 + 0.07 * lam))[old]
    out[is_new] = (HILITE * (0.86 + 0.14 * lam))[is_new]
    # edges: id changes (owned by the nearer side), self-occlusion depth steps, creases
    px = 2.0 * cam2.scale / H                                       # mm per pixel
    big = 1e9
    zz = np.where(idm >= 0, z, big)
    line_new = np.zeros((H, W), bool)
    line_old = np.zeros((H, W), bool)
    crease_new = np.zeros((H, W), bool)
    crease_old = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        id2 = _shift(idm, dy, dx, -1)
        z2 = _shift(zz, dy, dx, big)
        diff = idm != id2
        front_self = zz <= z2                                       # this pixel is the nearer one
        own = np.where(front_self, idm, id2)
        own_new = (own >= 0) & (styles[np.maximum(own, 0)] == 1)
        # mark on the pixel that belongs to the front object
        m_self = diff & front_self
        m_other = diff & ~front_self
        tgt_other = _shift(m_other, -dy, -dx, False)
        tgt_other_new = _shift(m_other & own_new, -dy, -dx, False)
        line_new |= (m_self & own_new) | tgt_other_new
        line_old |= (m_self & ~own_new) | (tgt_other & ~tgt_other_new)
        same = (idm == id2) & (idm >= 0)
        dz = np.abs(zz - z2)
        step = same & (dz > max(1.2, 5.0 * px))
        line_new |= step & is_new
        line_old |= step & ~is_new
        n2 = _shift(nrm, dy, dx, 0.0)
        cosang = np.sum(nrm * n2, axis=2)
        cr = same & (cosang < 0.80) & ~step
        crease_new |= cr & is_new
        crease_old |= cr & ~is_new
    # hidden added parts: outline of the added-only render where an installed part is in front
    hid = np.zeros((H, W), bool)
    if new_polys and old.any():
        nid, _ = _render(new_polys, cam2, W, H)
        nm = _dec(nid)
        sil = np.zeros((H, W), bool)
        for dy, dx in ((0, 1), (1, 0)):
            sil |= (nm != _shift(nm, dy, dx, -1)) & ((nm >= 0) | (_shift(nm, dy, dx, -1) >= 0))
        yy, xx = np.mgrid[0:H, 0:W]
        dash = ((xx + yy) // (7 * SS)) % 2 == 0
        hid = dilate(sil & old & dash, 1)
    r_new = 2 if SS == 2 else 1
    out[dilate(crease_old, 0)] = out[dilate(crease_old, 0)] * 0.5 + OLD_LINE * 0.5
    out[dilate(line_old, 1)] = OLD_LINE
    out[hid] = HID_LINE
    out[dilate(crease_new, 1)] = INK * 0.65 + out[dilate(crease_new, 1)] * 0.35
    out[dilate(line_new, r_new)] = INK
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGB')
    return im.resize((cam.W, cam.H), Image.LANCZOS)
