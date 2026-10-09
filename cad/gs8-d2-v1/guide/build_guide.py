# SPDX-License-Identifier: MIT
"""GS8 D2: IKEA-style assembly guide (pictures + written instructions + wiring diagrams).

Reads (read-only): layout.py (PARTS, STEPS, INSERTIONS, SCREWS, KEEPOUTS, present_at), the D2 part meshes in assembly
pose (cache guide/_cache/meshes.npz, made by --remesh from build_d2.build_printed + build_cots), out/build-receipt.json
(revision) and the step script guide_steps.py (all page text; it paraphrases ASSEMBLY.md and WIRING.md s7).
Writes guide/out/: pages/d2-NNN.png (A4 landscape, 150 dpi), GS8-D2-assembly-guide.pdf, index.html, guide-data.json.

Run (repo root):
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/guide/build_guide.py [--remesh] [--only ID,..]
Nothing here changes a CAD source or a receipt input; the guide is presentation only. Nothing has been assembled.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import math
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

GUIDE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(GUIDE)
sys.path.insert(0, CAD)
sys.path.insert(0, GUIDE)
import layout as L  # noqa: E402

CACHE = os.path.join(GUIDE, '_cache')
OUT = os.path.join(GUIDE, 'out')
DPI = 150
PW, PH = 1754, 1240
M = 40
FONT_DIR = os.path.join(CAD, 'fonts')
INK = (22, 22, 22)
GREY = (120, 120, 120)
WARN = (196, 72, 24)
OK = (40, 110, 60)
HL = (255, 238, 196)
BLUE = (60, 90, 160)


# ------------------------------------------------------------------------------------------------ fonts / text
_F = {}


def font(size, bold=False):
    key = (int(size), bold)
    if key not in _F:
        cands = (['DejaVuSans-Bold.ttf'] if bold else ['DejaVuSans.ttf'])
        for d in (FONT_DIR, os.path.join(os.path.dirname(sys.executable), '..', 'Lib', 'site-packages', 'matplotlib',
                                          'mpl-data', 'fonts', 'ttf'), 'C:/Windows/Fonts'):
            for c in cands + (['arialbd.ttf'] if bold else ['arial.ttf']):
                p = os.path.join(d, c)
                if os.path.exists(p):
                    _F[key] = ImageFont.truetype(p, int(size))
                    break
            if key in _F:
                break
        else:
            _F[key] = ImageFont.load_default()
    return _F[key]


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def wrap(d, s, f, width):
    out = []
    for para in s.split('\n'):
        words, line = para.split(' '), ''
        for w in words:
            t = (line + ' ' + w).strip()
            if tw(d, t, f) <= width or not line:
                line = t
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def text_block(d, xy, s, f, width, fill=INK, gap=1.25):
    x, y = xy
    lh = int(f.size * gap)
    for ln in wrap(d, s, f, width):
        d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y


def block_height(d, s, f, width, gap=1.25):
    return len(wrap(d, s, f, width)) * int(f.size * gap)


# ------------------------------------------------------------------------------------------------ meshes
def remesh():
    import build_d2 as B
    import checks as CK
    rows, _ = B.build_printed()
    rows.update(B.build_cots())
    arrs, meta = {}, {}
    for i, r in rows.items():
        if r.get('shape') is None:
            continue
        V, F = CK.mesh_of(r['shape'], tol=0.08, ang=0.25)
        arrs[i + '__V'] = np.asarray(V, np.float32)
        arrs[i + '__F'] = np.asarray(F, np.int32)
        meta[i] = dict(kind=r.get('kind'), stub=bool(r.get('stub')))
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(os.path.join(CACHE, 'meshes.npz'), **arrs)
    json.dump(dict(meta=meta, revision=L.REVISION if hasattr(L, 'REVISION') else ''),
              open(os.path.join(CACHE, 'meshes.json'), 'w'), indent=1)


def load_meshes():
    z = np.load(os.path.join(CACHE, 'meshes.npz'))
    out = {}
    for k in z.files:
        if k.endswith('__V'):
            i = k[:-3]
            out[i] = (z[k].astype(np.float64), z[i + '__F'])
    return out


# ------------------------------------------------------------------------------------------------ geometry helpers
INS = {}
for _ins in L.INSERTIONS:
    for _m in _ins['moving']:
        INS[_m] = _ins
SCREW = {s['id']: s for s in L.SCREWS}


def path_of(pid):
    """Waypoints (offsets from the final pose) of a part's insertion; screws come in along their axis."""
    if pid in SCREW:
        a = np.asarray(SCREW[pid]['axis'], float)
        return [tuple(-a * 28.0), (0, 0, 0)]
    if pid in INS:
        return [tuple(p) for p in INS[pid]['path']]
    return [(0, 0, 0)]


def centre(meshes, pid):
    V = meshes[pid][0]
    return (V.min(0) + V.max(0)) / 2.0


def view_dir(az, el):
    a, e = math.radians(az), math.radians(el)
    return np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])


def keepout_centre(name):
    b = L.KEEPOUTS[name]
    return np.array([sum(b[k]) / 2.0 for k in 'xyz'])


# ------------------------------------------------------------------------------------------------ drawing helpers
def arrow(d, pts, width=7, head=24, fill=INK, halo=True):
    pts = [tuple(map(float, p)) for p in pts]
    if len(pts) < 2:
        return
    if halo:
        d.line(pts, fill=(255, 255, 255), width=width + 8, joint='curve')
    d.line(pts[:-1] + [pts[-1]], fill=fill, width=width, joint='curve')
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    ang = math.atan2(y1 - y0, x1 - x0)
    tip = (x1, y1)
    l, r = (x1 - head * math.cos(ang) + head * 0.55 * math.sin(ang), y1 - head * math.sin(ang) - head * 0.55 * math.cos(ang)), \
           (x1 - head * math.cos(ang) - head * 0.55 * math.sin(ang), y1 - head * math.sin(ang) + head * 0.55 * math.cos(ang))
    if halo:
        d.polygon([tip, l, r], outline=(255, 255, 255), width=5)
    d.polygon([tip, l, r], fill=fill)


def badge(d, xy, s, r=20, fill=INK, fg=(255, 255, 255), f=None):
    x, y = xy
    d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=(255, 255, 255), width=3)
    f = f or font(int(r * 1.05), True)
    d.text((x - tw(d, s, f) / 2, y - f.size * 0.62), s, font=f, fill=fg)


def callout(d, xy, label, anchor_xy, f=None, fill=INK):
    """A leader line from anchor_xy (on the part) to a label box at xy."""
    f = f or font(19, True)
    x, y = xy
    w = tw(d, label, f) + 16
    h = f.size + 12
    d.line([anchor_xy, (x + w / 2, y + h / 2)], fill=(255, 255, 255), width=6)
    d.line([anchor_xy, (x + w / 2, y + h / 2)], fill=fill, width=2)
    ax, ay = anchor_xy
    d.ellipse((ax - 5, ay - 5, ax + 5, ay + 5), fill=fill)
    d.rounded_rectangle((x, y, x + w, y + h), radius=6, fill=(255, 255, 255), outline=fill, width=2)
    d.text((x + 8, y + 5), label, font=f, fill=fill)


def warn_icon(d, x, y, s=34, fill=WARN):
    d.polygon([(x + s / 2, y), (x + s, y + s * 0.9), (x, y + s * 0.9)], fill=fill)
    f = font(int(s * 0.62), True)
    d.text((x + s / 2 - tw(d, '!', f) / 2, y + s * 0.18), '!', font=f, fill=(255, 255, 255))


def check_box(d, x, y, s=18):
    d.rectangle((x, y, x + s, y + s), outline=INK, width=2)


# ------------------------------------------------------------------------------------------------ page shell
class Doc:
    def __init__(self, revision, stamp):
        self.pages = []
        self.revision = revision
        self.stamp = stamp
        self.data = []

    def new(self):
        im = Image.new('RGB', (PW, PH), (255, 255, 255))
        return im, ImageDraw.Draw(im)

    def add(self, im, record):
        self.pages.append(im)
        self.data.append(record)

    def footer_all(self):
        n = len(self.pages)
        for k, im in enumerate(self.pages):
            d = ImageDraw.Draw(im)
            f = font(15)
            d.line((M, PH - 44, PW - M, PH - 44), fill=(200, 200, 200), width=1)
            d.text((M, PH - 36), 'GS8 D2 assembly guide  -  %s  -  %s' % (self.revision, self.stamp), font=f, fill=GREY)
            s = '%d / %d' % (k + 1, n)
            d.text((PW - M - tw(d, s, font(17, True)), PH - 38), s, font=font(17, True), fill=INK)


def header(d, num, title, sub=None):
    f = font(88, True)
    d.text((M, M - 14), num, font=f, fill=INK)
    x = M + tw(d, num, f) + 28
    d.text((x, M + 2), title, font=font(38, True), fill=INK)
    if sub:
        d.text((x, M + 52), sub, font=font(21), fill=GREY)
    d.line((M, M + 98, PW - M, M + 98), fill=INK, width=3)
    return M + 112


# ------------------------------------------------------------------------------------------------ step illustration
def step_items(st, meshes):
    """[(V, F, style, offset)], insertion paths of the new parts, installed ids, new ids."""
    new = [i for i in st.get('new', []) if i in meshes]
    if st.get('ctx') is None:
        inst = list(st.get('plus', []))
    else:
        inst = list(L.present_at(st['ctx'])) + list(st.get('plus', []))
    inst = [i for i in dict.fromkeys(inst) if i in meshes and i not in new and i not in st.get('minus', [])]
    ex = st.get('explode', 1.0)
    offs = st.get('offsets', {})
    items, info = [], {}
    for i in inst:
        V, F = meshes[i]
        items.append((V, F, 'old', (0, 0, 0)))
    for i in new:
        V, F = meshes[i]
        if i in offs:
            path = [tuple(offs[i]), (0, 0, 0)]
        else:
            path = [tuple(np.asarray(p, float) * ex) for p in path_of(i)]
        info[i] = path
        items.append((V, F, 'new', path[0]))
    return items, info, inst, new


def view_words(az, el):
    az = (az + 180) % 360 - 180
    side = {0: 'front', 45: 'front-left', 90: 'left', 135: 'rear-left', 180: 'rear', -180: 'rear', -135: 'rear-right',
            -90: 'right', -45: 'front-right'}[int(45 * round(az / 45.0))]
    if el >= 70:
        return 'from above'
    if el <= -70:
        return 'from below'
    return 'from the ' + side + (', above' if el >= 20 else (', below' if el <= -20 else ''))


def motion_axis(st, meshes):
    """Dominant axis (0 x, 1 y, 2 z) of the first non-screw insertion on the page, or None."""
    _, paths, _, new = step_items(st, meshes)
    for i in sorted(new, key=lambda i: i in SCREW):
        v = np.asarray(paths[i][0], float)
        if np.linalg.norm(v) > 1:
            return int(np.argmax(np.abs(v)))
    return None


def auto_views(st, meshes):
    """Up to 3 points of view: A the motion (main), B the motion seen across it, C the result close-up."""
    if st.get('views'):
        return st['views']
    az, el = st.get('view', (-40, 30))
    k = motion_axis(st, meshes)
    if k == 2:                                      # vertical motion: look across it, from the side
        b = (90, 10) if abs(((az - 90) + 180) % 360 - 180) > 50 else (0, 10)
    elif k == 1:                                    # sideways slide: from above
        b = (az, 80)
    elif k == 0:                                    # fore-aft motion: side profile from the left (or right)
        b = (90, 12) if abs(((az - 90) + 180) % 360 - 180) > 50 else (-90, 12)
    else:
        b = (az + 180, max(15, el))
    views = [dict(view=(az, el), mode='motion', label='A')]
    if st.get('new'):
        views.append(dict(view=b, mode='motion', label='B'))
        views.append(dict(view=st.get('result_view', (az, el)), mode='result', label='C',
                          zoom=st.get('result_zoom', 0.55)))
    else:
        views.append(dict(view=(az + 180, max(15, el)), mode='motion', label='B'))
        views.append(dict(view=(az, 80), mode='motion', label='C'))
    return views


def render_step(st, meshes, W, H, view=None, mode='motion', zoom=None, focus=None, arrows=None, marks=None):
    import lineart as LA
    items, paths, inst, new = step_items(st, meshes)
    if mode == 'result':                            # the added parts in their final place, close up
        items = [(V, F, s, (0, 0, 0)) for V, F, s, off in items]
        paths = {i: [(0, 0, 0)] for i in paths}
        focus = 'new_final'
        arrows = False
    d = view_dir(*(view or st.get('view', (-40, 30))))
    focus = focus if focus is not None else st.get('focus')
    zoom = zoom if zoom is not None else st.get('zoom', 1.0)
    st = dict(st, zoom=zoom, arrows=st.get('arrows', True) if arrows is None else arrows,
              marks=st.get('marks', []) if marks is None else marks)
    pts = []
    if focus in ('new_final', 'new_final_ctx') and new:
        for i in new:
            V = meshes[i][0]
            pts += [V, V + np.asarray(paths[i][0])]
        if focus == 'new_final_ctx':
            for i in inst:
                if i in ('hood', 'tub'):
                    pts.append(meshes[i][0][::7])
    elif focus == 'ctx_parts':
        for i in st.get('focus_ids', []):
            pts.append(meshes[i][0])
    if not pts:
        for (V, F, s, off) in items:
            pts.append(V[::5] + np.asarray(off))
    P = np.vstack(pts)
    cam0 = LA.Camera(d, (0, 0, 0), 100, W, H)
    a, b = P @ cam0.r, P @ cam0.u
    cx, cy = (a.min() + a.max()) / 2, (b.min() + b.max()) / 2
    half = max((b.max() - b.min()) / 2, (a.max() - a.min()) / 2 * H / W, 18.0) * 1.12 / st.get('zoom', 1.0)
    cam = LA.Camera(d, cam0.r * cx + cam0.u * cy, half, W, H)
    im = LA.render(items, cam)
    dr = ImageDraw.Draw(im)
    if st.get('arrows', True) and new:             # motion arrows: one per insertion group (screws one each)
        groups = {}
        for i in new:
            key = i if (i in SCREW or i in st.get('offsets', {})) else INS.get(i, {}).get('id', i)
            groups.setdefault(key, []).append(i)
        for key, ids in groups.items():
            if key in st.get('arrow_dirs', {}):
                continue
            c = np.mean([centre(meshes, i) for i in ids], axis=0)
            wp = np.array([c + np.asarray(p) for p in paths[ids[0]]])
            if np.linalg.norm(wp[0] - wp[-1]) < 3.0:
                continue
            q = cam.project(wp)
            seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
            if seg.sum() < 30:
                continue
            trim = min(0.45 * seg.sum(), 0.8 * seg[0])
            q0 = q[0] + (q[1] - q[0]) * (trim / max(seg[0], 1e-6))
            arrow(dr, [q0] + list(q[1:]), width=6 if key in SCREW else 8, head=20 if key in SCREW else 26)
        for i, v in st.get('arrow_dirs', {}).items():
            if i not in paths:
                continue
            c = centre(meshes, i) + np.asarray(paths[i][0])
            q = cam.project([c - np.asarray(v) * 30, c + np.asarray(v) * 4])
            arrow(dr, [q[0], q[1]], width=7, head=22)
    marks = st.get('marks', [])
    if marks:                                      # leader-line callouts, labels in the side margins
        placed = []
        for ref, label in marks:
            if ref in SCREW:
                p = np.asarray(SCREW[ref]['head_point'], float)
            elif ref in L.KEEPOUTS:
                p = keepout_centre(ref)
            elif ref in meshes:
                p = centre(meshes, ref) + np.asarray(paths.get(ref, [(0, 0, 0)])[0])
            else:
                p = np.asarray(ref, float)
            placed.append((cam.project(p)[0], label))
        placed.sort(key=lambda t: t[0][1])
        f = font(19, True)
        used_y = {'l': -999, 'r': -999}
        for q, label in placed:
            side = 'l' if q[0] < W / 2 else 'r'
            wlab = tw(dr, label, f) + 16
            x = 12 if side == 'l' else W - wlab - 12
            y = max(12, min(H - 50, q[1] - 110, ))
            y = max(y, used_y[side] + 56)
            used_y[side] = y
            callout(dr, (x, y), label, (float(q[0]), float(q[1])), f=f)
    return im


# ------------------------------------------------------------------------------------------------ pages
def tool_name(n, GS):
    for k, t, b in GS.TOOLS:
        if k == n:
            return t
    return str(n)


def short_tool(n, GS):
    return tool_name(n, GS).split(' (')[0].split(',')[0]


def bag_line(bag, qty, GS):
    for b, desc, q, where in GS.BAGS:
        if b == bag:
            return 'Bag %s: %d x %s' % (b, qty, desc.split(' (')[0])
    return bag


def right_column(d, st, x, y, w, ymax, GS):
    issues = ['%s (%s): %s' % (i, c, t) for i, c, t in GS.ISSUES.get(st['id'], [])] if hasattr(GS, 'ISSUES') else []
    tips = list(getattr(GS, 'TIPS', {}).get(st['id'], []))
    need = ['- ' + p for p in st.get('parts', [])]
    need += ['- ' + bag_line(b, q, GS) for b, q in st.get('hw', [])]
    if st.get('tools'):
        need += ['- Tools: ' + ', '.join('(%d) %s' % (n, short_tool(n, GS)) for n in st['tools'])]
    if st.get('torque'):
        need += ['- Torque: ' + st['torque']]
    for size in (21, 20, 19, 18, 17, 16, 15):
        fb, fr, fh = font(size, True), font(size), font(size + 3, True)
        h = sum(block_height(d, t, fr, w - 24) + fh.size + 30 for t in issues)
        if need:
            h += fh.size + 10 + sum(block_height(d, s, fr, w - 10) for s in need) + 14
        h += fh.size + 10 + sum(block_height(d, s, fr, w - 46) + 8 for s in st.get('do', [])) + 14
        if st.get('caution'):
            h += fh.size + 10 + sum(block_height(d, s, fb, w - 46) + 6 for s in st['caution']) + 14
        if st.get('check'):
            h += fh.size + 10 + sum(block_height(d, s, fr, w - 36) + 6 for s in st['check'])
        if tips:
            h += fh.size + 24 + sum(block_height(d, s, fr, w - 20) + 6 for s in tips)
        if y + h <= ymax:
            break
    for t in issues:
        hh = block_height(d, t, fr, w - 24) + fh.size + 18
        d.rectangle((x, y, x + w, y + hh), fill=(253, 236, 230), outline=WARN, width=3)
        d.text((x + 10, y + 6), 'OPEN DESIGN ISSUE (not yet fixed in CAD)', font=fh, fill=WARN)
        text_block(d, (x + 12, y + fh.size + 12), t, fr, w - 24)
        y += hh + 12
    if need:
        d.text((x, y), 'YOU NEED', font=fh, fill=GREY)
        y += fh.size + 10
        for s in need:
            y = text_block(d, (x + 4, y), s, fr, w - 10)
        y += 14
    d.text((x, y), 'DO THIS', font=fh, fill=INK)
    y += fh.size + 10
    for k, s in enumerate(st.get('do', [])):
        badge(d, (x + 14, y + fr.size * 0.62), str(k + 1), r=max(12, int(size * 0.62)), f=font(int(size * 0.8), True))
        y = text_block(d, (x + 40, y), s, fr, w - 46) + 8
    y += 6
    if st.get('caution'):
        warn_icon(d, x, y - 2, s=fh.size + 6)
        d.text((x + fh.size + 16, y), 'CAUTION', font=fh, fill=WARN)
        y += fh.size + 10
        for s in st['caution']:
            y = text_block(d, (x + 10, y), s, fb, w - 46, fill=WARN) + 6
        y += 8
    if st.get('check'):
        d.text((x, y), 'CHECK', font=fh, fill=OK)
        y += fh.size + 10
        for s in st['check']:
            check_box(d, x + 4, y + 3, s=max(14, size - 3))
            y = text_block(d, (x + 34, y), s, fr, w - 36) + 6
    if tips:
        y += 14
        d.text((x, y), 'TIPS (physical blocker check)', font=fh, fill=BLUE)
        y += fh.size + 10
        for s in tips:
            y = text_block(d, (x + 10, y), s, fr, w - 20, fill=BLUE) + 6
    return y


def step_page(doc, st, meshes, GS):
    import diagrams as DG
    im, d = doc.new()
    y0 = header(d, st['id'], st['title'], st.get('sub'))
    xr = 1110
    box = (M, y0 + 8, xr - 30, PH - 60)
    W, H = box[2] - box[0], box[3] - box[1]
    views_used = []
    if st.get('diagram'):
        DG.DIAGRAMS[st['diagram']](d, box)
    elif st.get('new') or st.get('ctx') is not None or st.get('plus'):
        views = auto_views(st, meshes)
        gap = 18
        hA = int(H * 0.6) if len(views) > 1 else H
        hB = H - hA - gap
        wB = (W - gap) // 2
        cells = [(box[0], box[1], W, hA), (box[0], box[1] + hA + gap, wB, hB),
                 (box[0] + wB + gap, box[1] + hA + gap, wB, hB)]
        for v, (x, y, w, h) in zip(views, cells):
            sub = render_step(st, meshes, w - 4, h - 50, view=v['view'], mode=v.get('mode', 'motion'), zoom=v.get('zoom'),
                              focus=v.get('focus'), marks=None if (v['label'] == 'A' or v.get('marks')) else [])
            im.paste(sub, (x + 2, y + 48))
            d.rectangle((x, y, x + w - 1, y + h - 1), outline=(205, 205, 205), width=2)
            cap = ('result, close-up, ' if v.get('mode') == 'result' else '') + view_words(*v['view'])
            fl = font(18, True)
            d.rounded_rectangle((x + 8, y + 8, x + 8 + 34, y + 8 + 34), radius=6, fill=INK)
            d.text((x + 25 - tw(d, v['label'], font(22, True)) / 2, y + 11), v['label'], font=font(22, True),
                   fill=(255, 255, 255))
            d.text((x + 52, y + 15), cap, font=fl, fill=GREY)
            views_used.append('%s: %s' % (v['label'], cap))
    d.line((xr - 14, y0 + 8, xr - 14, PH - 60), fill=(210, 210, 210), width=2)
    right_column(d, st, xr, y0 + 8, PW - M - xr, PH - 60, GS)
    doc.add(im, dict(kind='step', id=st['id'], title=st['title'], sub=st.get('sub', ''), do=st.get('do', []), views=views_used, tips=list(getattr(GS, 'TIPS', {}).get(st['id'], [])), issues=['%s (%s): %s' % t for t in getattr(GS, 'ISSUES', {}).get(st['id'], [])],
                     caution=st.get('caution', []), check=st.get('check', []), parts=st.get('parts', []),
                     hw=[bag_line(b, q, GS) for b, q in st.get('hw', [])],
                     tools=['(%d) %s' % (n, tool_name(n, GS)) for n in st.get('tools', [])], torque=st.get('torque')))


def list_page(doc, num, title, sub, rows, kind, cols=1, size=22):
    im, d = doc.new()
    y = header(d, num, title, sub) + 10
    top = y
    colw = (PW - 2 * M - (cols - 1) * 40) // cols
    x = M
    ymax = PH - 70
    for r in rows:
        if isinstance(r, tuple):
            t, s = r
            hgt = font(size + 2, True).size + 6 + block_height(d, s, font(size), colw - 20) + 16
        else:
            hgt = block_height(d, r, font(size), colw - 40) + 12
        if y + hgt > ymax and cols > 1 and x == M:
            x, y = M + colw + 40, top
        if isinstance(r, tuple):
            y = text_block(d, (x, y), t, font(size + 2, True), colw) + 2
            y = text_block(d, (x + 14, y), s, font(size), colw - 20) + 16
        else:
            check_box(d, x, y + 4)
            y = text_block(d, (x + 34, y), r, font(size), colw - 40) + 12
    doc.add(im, dict(kind=kind, id=num, title=title, sub=sub,
                     rows=[r if isinstance(r, str) else ': '.join(r) for r in rows]))


def cover(doc, meshes, revision):
    import lineart as LA
    im, d = doc.new()
    d.text((M, M - 10), 'GS8 D2', font=font(110, True), fill=INK)
    d.text((M + 6, M + 125), 'Assembly guide', font=font(46, True), fill=INK)
    d.text((M + 6, M + 185), 'Digital Super 8 cine camera, D2 fork (cad/gs8-d2-v1)', font=font(26), fill=GREY)
    items = [(meshes[i][0], meshes[i][1], 'new', (0, 0, 0)) for i in L.present_at(10) if i in meshes]
    W, H = 1060, 860
    cam = LA.fit_camera(view_dir(35, 22), items, W, H, margin=1.05)
    im.paste(LA.render(items, cam), (PW - M - W, 300))
    y = 290
    for s in [revision, 'Guide built ' + doc.stamp, '',
              'DRAFT. Nobody has assembled a D2 yet. The steps follow ASSEMBLY.md (r7) and WIRING.md s7 and are '
              'checked only by computed insertion sweeps and the straight-driver audit.', '',
              'Read pages 0.1 to 0.7 before you start: rules, tools, hardware bags, parts, gates, contents.', '',
              'Each step page has the picture on the left (new parts highlighted, arrows show the motion) and the '
              'written instructions on the right: YOU NEED, DO THIS, CAUTION, CHECK.', '',
              'Directions in the text: forward = toward the lens, left = the panel side, as seen from behind the camera '
              'looking through the eyepiece.']:
        y = text_block(d, (M + 6, y), s, font(22), 560) + 4
    doc.add(im, dict(kind='cover', id='cover', title='GS8 D2 assembly guide'))


PRINTED_NAMES = {'tub': 'Tub (body)', 'hood': 'Hood', 'panel': 'Panel', 'base_grip': 'Base + grip', 'cap': 'Battery cap',
                 'plunger': 'Power plunger', 'knob_exp': 'Exposure knob', 'knob_fps': '18/24 knob', 'eyecup': 'Eyecup',
                 'stick_sleeve': 'USB stick sleeve', 'pi_keeper': 'Pi keeper', 'lens_collar': 'Lens collar'}


def inventory_pages(doc, meshes):
    """IKEA-style parts inventory: one line-art thumbnail per printed and purchased part."""
    import lineart as LA
    try:
        man = {p['id']: p for p in json.load(open(os.path.join(CAD, 'out', 'parts-manifest.json')))['parts']}
    except Exception:  # noqa: BLE001
        man = {}
    printed = [(i, PRINTED_NAMES.get(i, i), '%s, %s' % (L.PARTS[i].get('material', ''), L.PARTS[i].get('colour', '')))
               for i in L.PARTS if i in meshes]
    cots = [(i, man.get(i, {}).get('name', i).split(' (')[0], man.get(i, {}).get('pn', '')) for i, p in man.items()
            if p.get('kind') == 'cots' and i in meshes]
    for title, rows in (('Printed parts', printed), ('Purchased parts', cots)):
        for k0 in range(0, len(rows), 15):
            im, d = doc.new()
            num = '0.4' if title.startswith('Printed') else '0.5'
            y0 = header(d, num, title + ('' if k0 == 0 else ' (continued)'),
                        'Check every part against this list before you start (not to scale)')
            cw, ch = (PW - 2 * M) // 5, (PH - 70 - y0) // 3
            for k, (pid, name, extra) in enumerate(rows[k0:k0 + 15]):
                cx, cy = M + (k % 5) * cw, y0 + 6 + (k // 5) * ch
                V, F = meshes[pid]
                items = [(V, F, 'new', (0, 0, 0))]
                cam = LA.fit_camera(view_dir(35, 25), items, cw - 20, ch - 90, margin=1.15)
                im.paste(LA.render(items, cam), (cx + 10, cy + 4))
                d.rectangle((cx + 4, cy, cx + cw - 6, cy + ch - 8), outline=(215, 215, 215), width=2)
                text_block(d, (cx + 12, cy + ch - 80), name, font(18, True), cw - 24)
                d.text((cx + 12, cy + ch - 28), extra[:34], font=font(15), fill=GREY)
            doc.add(im, dict(kind='list', id=num, title=title, rows=['%s (%s)' % (n, e) for _, n, e in rows]))


CABLE_COL = [(200, 40, 40), (40, 90, 200), (225, 150, 20), (40, 150, 70), (150, 60, 160), (210, 110, 20),
             (20, 150, 160), (120, 80, 40), (90, 90, 90), (200, 60, 140)]


def wiring_overview(doc, meshes):
    """Every cable of layout.CABLES drawn as a phantom polyline through its keep-out chain, over the body (panel off)."""
    import lineart as LA
    im, d = doc.new()
    y0 = header(d, 'W', 'Wiring overview', 'Every cable, its route (keep-out chain) and the steps where it is plugged '
                                           '(WIRING s6-s7). Panel removed; routes drawn through the parts.')
    xr = 1110
    ids = [i for i in L.present_at(8) if i in meshes and i not in ('panel', 'encoder', 'switch_1824', 'knob_exp',
                                                                    'knob_fps', 's_b1', 's_b2', 's_r1', 's_r2')]
    items = [(meshes[i][0], meshes[i][1], 'old', (0, 0, 0)) for i in ids]
    W = xr - 30 - M
    H = (PH - 60 - y0 - 30) // 2
    for k, (vw, cap) in enumerate((((75, 35), 'A  from the left, above (panel off)'), ((90, 88), 'B  from above'))):
        cam = LA.fit_camera(view_dir(*vw), items, W, H - 40, margin=1.04)
        sub = LA.render(items, cam)
        dr = ImageDraw.Draw(sub)
        for n, c in enumerate(L.CABLES):
            pts = [keepout_centre(v) for v in c.get('via', []) if v in L.KEEPOUTS]
            if len(pts) < 2:
                continue
            q = cam.project(np.array(pts))
            col = CABLE_COL[n % len(CABLE_COL)]
            dr.line([tuple(p) for p in q], fill=(255, 255, 255), width=10, joint='curve')
            dr.line([tuple(p) for p in q], fill=col, width=5, joint='curve')
            for p in (q[0], q[-1]):
                dr.ellipse((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=col, outline=(255, 255, 255), width=2)
            dr.text((q[-1][0] + 8, q[-1][1] - 10), c['id'], font=font(17, True), fill=col)
        y = y0 + 8 + k * (H + 20)
        im.paste(sub, (M, y + 36))
        d.rectangle((M, y, M + W - 1, y + H - 1), outline=(205, 205, 205), width=2)
        d.text((M + 10, y + 8), cap, font=font(19, True), fill=GREY)
    y = y0 + 8
    d.text((xr, y), 'CABLES', font=font(24, True), fill=INK)
    y += 36
    for n, c in enumerate(L.CABLES):
        col = CABLE_COL[n % len(CABLE_COL)]
        d.rectangle((xr, y + 6, xr + 26, y + 16), fill=col)
        s1 = '%s  (%s mm; plugged at step %s)' % (c['id'], c.get('length', '?'),
                                                  ', '.join(str(x) for x in c.get('steps', ())))
        d.text((xr + 36, y), s1, font=font(18, True), fill=INK)
        y += 24
        y = text_block(d, (xr + 36, y), '%s -> %s' % (c.get('frm', ''), c.get('to', '')), font(16), PW - M - xr - 40,
                       fill=GREY) + 8
    y += 6
    text_block(d, (xr, y), 'Polarity and pin rules: header pins on page 4d, EVF lead on 1c, fuse on 1a, XT30 on 10b. '
               'Every lead is made with the pack out (power last).', font(17, True), PW - M - xr, fill=WARN)
    doc.add(im, dict(kind='list', id='W', title='Wiring overview',
                     rows=['%s: %s -> %s, %s mm, step %s' % (c['id'], c.get('frm', ''), c.get('to', ''), c.get('length'),
                                                            ', '.join(str(x) for x in c.get('steps', ()))) for c in L.CABLES]))


def blockers_page(doc):
    p = os.path.join(GUIDE, 'BLOCKERS-2026-10-08.md')
    if not os.path.exists(p):
        return
    rows, verdict, in_v = [], '', False
    for ln in open(p, encoding='utf-8').read().replace('`', '').replace('**', '').splitlines():
        s = ln.strip()
        if s.startswith('## '):
            in_v = s.lower().startswith('## verdict')
            continue
        if in_v and s and not verdict:
            verdict = s
        if s.startswith('|') and not s.startswith('|-'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if len(cells) >= 4 and cells[1].strip('*').upper() in ('BLOCKER', 'MAJOR', 'MINOR'):
                cells[1] = cells[1].strip('*').upper()
                rows.append(cells)
    rows.sort(key=lambda c: {'BLOCKER': 0, 'MAJOR': 1, 'MINOR': 2}[c[1]])
    im, d = doc.new()
    y = header(d, '!', 'Physical blocker check', 'Review of this build sequence, 2026-10-08 (full text: '
                                                    'cad/gs8-d2-v1/guide/BLOCKERS-2026-10-08.md)')
    y = text_block(d, (M, y + 6), 'Review verdict (2026-10-08): ' + verdict, font(18), PW - 2 * M) + 10
    r7 = [ln.strip()[2:] for ln in open(p, encoding='utf-8').read().replace('`', '').splitlines()
          if ln.strip().startswith('- r7:')]
    if r7:
        d.text((M, y), 'Status after r7 (2026-10-09)', font=font(21, True), fill=OK)
        y += 30
        for s in r7:
            y = text_block(d, (M + 10, y), s, font(16), PW - 2 * M - 20, fill=OK) + 4
            if y > PH - 120:
                doc.add(im, dict(kind='blockers', id='!', title='Physical blocker check', sub=verdict, rows=r7))
                im, d = doc.new()
                y = header(d, '!', 'Physical blocker check (continued)') + 6
        y += 10
        d.text((M, y), 'Original findings (2026-10-08)', font=font(21, True), fill=INK)
        y += 30
    for c in rows:
        f = font(17)
        s = '%s  [%s]  step %s: %s' % (c[0], c[1], c[2], c[3]) + (('  ->  ' + c[5]) if len(c) > 5 else '')
        if y + block_height(d, s, f, PW - 2 * M - 20) > PH - 70:
            doc.add(im, dict(kind='blockers', id='!', title='Physical blocker check'))
            im, d = doc.new()
            y = header(d, '!', 'Physical blocker check (continued)') + 6
        y = text_block(d, (M + 10, y), s, f, PW - 2 * M - 20, fill=WARN if c[1] != 'MINOR' else INK) + 8
    doc.add(im, dict(kind='blockers', id='!', title='Physical blocker check', sub=verdict,
                     rows=[' | '.join(c) for c in rows]))


HTML_HEAD = """<title>GS8 D2 Assembly Guide</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800&family=Noto+Sans:wght@400;600&display=swap">
<style>
/* Layout: a binder of A4 sheets; a sticky strip of step chips; under each sheet the same steps as readable text */
:root{--paper:#f4f4f1;--sheet:#ffffff;--ink:#1b1c1f;--mute:#5d6168;--rule:#d8d9d4;--hl:#ffeec4;--warn:#b5461a;
--ok:#2a6e3c;--tip:#3c5aa0;--display:"Archivo","Arial Narrow",Arial,sans-serif;--body:"Noto Sans","Segoe UI",Arial,sans-serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#141517;--sheet:#1d1f22;--ink:#ecebe7;
--mute:#a3a6ad;--rule:#30333a;--hl:#4d421f;--warn:#f08a5d;--ok:#80cf95;--tip:#9db4ff;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#141517;--sheet:#1d1f22;--ink:#ecebe7;--mute:#a3a6ad;--rule:#30333a;--hl:#4d421f;
--warn:#f08a5d;--ok:#80cf95;--tip:#9db4ff;color-scheme:dark}
body{background:var(--paper);color:var(--ink);font:16px/1.55 var(--body)}
.wrap{max-width:1180px;margin:0 auto;padding-inline:16px;padding-block:20px 48px}
header.top h1{font:800 clamp(2rem,5vw,3.2rem)/1.05 var(--display);margin:0;text-wrap:balance}
header.top p{color:var(--mute);margin:.4em 0 0;max-width:70ch}
.draft{display:inline-block;margin-top:.6em;padding:.15em .6em;border:1.5px solid var(--warn);color:var(--warn);
font:600 .8rem/1.6 var(--body);letter-spacing:.06em;text-transform:uppercase;border-radius:4px}
nav.chips{position:sticky;top:env(safe-area-inset-top,0px);z-index:2;background:var(--paper);display:flex;flex-wrap:wrap;
gap:6px;padding-block:10px;border-bottom:1px solid var(--rule);margin-top:16px}
nav.chips a{font:600 .82rem/1 var(--display);text-decoration:none;color:var(--ink);border:1px solid var(--rule);
background:var(--sheet);padding:.42em .6em;border-radius:5px}
nav.chips a.bad{border-color:var(--warn);color:var(--warn)}
nav.chips a:focus-visible,nav.chips a:hover{outline:2px solid var(--ink);outline-offset:1px}
section.sheet{margin-top:28px;display:grid;gap:10px}
section.sheet h2{font:800 1.5rem/1.2 var(--display);margin:0;display:flex;gap:.6em;align-items:baseline;flex-wrap:wrap}
section.sheet h2 .id{font-size:2rem}
.sub{color:var(--mute);margin:0}
.page{border:1px solid var(--rule);border-radius:6px;background:#fff;overflow:hidden}
.page img{display:block;width:100%;height:auto}
.text{min-width:0;display:grid;gap:6px;max-width:80ch}
.text ol{margin:.2em 0;padding-left:1.4em}.text li{margin:.2em 0}
.issue{border:2px solid var(--warn);background:color-mix(in srgb,var(--warn) 10%,var(--sheet));padding:.5em .75em;
border-radius:6px}
.issue b,.warn{color:var(--warn)}.ok{color:var(--ok)}.tip{color:var(--tip)}
.need{color:var(--mute)}
@media (prefers-reduced-motion: no-preference){html{scroll-behavior:smooth}}
</style>"""


def write_html(doc, path, fragment=False):
    e = html.escape
    out = [] if fragment else ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
                               'content="width=device-width, initial-scale=1, viewport-fit=cover">']
    out.append(HTML_HEAD)
    if not fragment:
        out.append('</head><body>')
    out.append('<div class="wrap"><header class="top"><h1>GS8 D2 assembly guide</h1><p>%s &middot; built %s. Pictures '
               'on every page; the same steps in plain text under each page. New parts are highlighted; arrows show '
               'the motion; views A, B and C show the step from different sides.</p><span class="draft">Draft: '
               'computed, never built</span></header>' % (e(doc.revision), e(doc.stamp)))
    chips = []
    for k, r in enumerate(doc.data):
        cls = ' class="bad"' if r.get('issues') else ''
        chips.append('<a%s href="#p%d">%s</a>' % (cls, k + 1, e(r['id'])))
    out.append('<nav class="chips" aria-label="Pages">%s</nav>' % ''.join(chips))
    for k, r in enumerate(doc.data):
        out.append('<section class="sheet" id="p%d"><h2><span class="id">%s</span><span>%s</span></h2>' %
                   (k + 1, e(r['id']), e(r['title'])))
        if r.get('sub'):
            out.append('<p class="sub">%s</p>' % e(r['sub']))
        out.append('<div class="page"><img loading="lazy" src="pages/d2-%03d.png" width="1754" height="1240" '
                   'alt="Page %d: %s"></div>' % (k + 1, k + 1, e(r['title'])))
        out.append('<div class="text">')
        if r['kind'] == 'step':
            out += ['<div class="issue"><b>Open design issue %s</b></div>' % e(t) for t in r.get('issues', [])]
            if r.get('views'):
                out.append('<p class="sub">Views: %s</p>' % e('; '.join(r['views'])))
            need = r['parts'] + r['hw'] + r['tools'] + (['Torque: ' + r['torque']] if r.get('torque') else [])
            if need:
                out.append('<p class="need"><b>You need:</b> %s</p>' % e('; '.join(need)))
            out.append('<ol>%s</ol>' % ''.join('<li>%s</li>' % e(x) for x in r['do']))
            out += ['<p class="warn">Caution: %s</p>' % e(x) for x in r.get('caution', [])]
            if r.get('check'):
                out.append('<p class="ok">Check: %s</p>' % e('; '.join(r['check'])))
            out += ['<p class="tip">Tip %s</p>' % e(t) for t in r.get('tips', [])]
        elif r.get('rows'):
            out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % e(x) for x in r['rows']))
        out.append('</div></section>')
    out.append('</div>')
    if not fragment:
        out.append('</body></html>')
    open(path, 'w', encoding='utf-8').write('\n'.join(out))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--remesh', action='store_true')
    ap.add_argument('--only', default='')
    ap.add_argument('--no-pdf', action='store_true')
    a = ap.parse_args(argv)
    if a.remesh or not os.path.exists(os.path.join(CACHE, 'meshes.npz')):
        remesh()
    import guide_steps as GS
    meshes = load_meshes()
    try:
        revision = json.load(open(os.path.join(CAD, 'out', 'build-receipt.json')))['revision'].split(' (')[0]
    except Exception:  # noqa: BLE001
        revision = 'GS8 D2'
    doc = Doc(revision, _dt.datetime.now().strftime('%Y-%m-%d %H:%M'))
    only = [s for s in a.only.split(',') if s]
    t0 = time.time()
    if not only:
        cover(doc, meshes, revision)
        list_page(doc, '0.1', 'Read first', 'Rules for the whole build (ASSEMBLY s1)', GS.RULES, 'list', size=22)
        list_page(doc, '0.2', 'Tools', '14 tools (ASSEMBLY s1.1); the numbers are used on every step page',
                  [('(%d)  %s' % (n, t), 'BOM ' + b) for n, t, b in GS.TOOLS], 'list', cols=2, size=19)
        list_page(doc, '0.3', 'Hardware bags', 'Sort the loose hardware into these bags before you start',
                  [('Bag %s: %d x %s' % (b, q, desc), 'Used at: ' + where) for b, desc, q, where in GS.BAGS], 'list',
                  size=20)
        inventory_pages(doc, meshes)
        list_page(doc, '0.6', 'Gates before assembly', 'Do not start step 1 until these are recorded (ASSEMBLY s1)',
                  GS.GATES, 'list', size=21)
        wiring_overview(doc, meshes)
        list_page(doc, '0.7', 'Contents', 'B = bench; 1-10 = the build steps of layout.STEPS; letters are sub-steps',
                  [('%s  %s' % (s['id'], s['title']), s.get('sub', '')) for s in GS.STEPS], 'list', cols=2, size=17)
    for st in GS.STEPS:
        if only and st['id'] not in only:
            continue
        step_page(doc, st, meshes, GS)
        print('page', st['id'], round(time.time() - t0, 1), flush=True)
    if not only:
        list_page(doc, 'S', 'Before any service', 'ASSEMBLY s7: isolation first, every time (P1-P4)', [
            ('P1  Shut down', 'Hold the plunger 2 s. The EVF shows the shutdown screen, then goes dark. Wait 5 s more. If '
             'the EVF stays lit after the shutdown screen went away, do not press again (a press while halted boots the '
             'Pi): wait 5 s and go on.'),
            ('P2  Cap off', 'Slide the cap forward 52 mm off the grip.'),
            ('P3  Pack out', 'Pull the pack out of the bay by its ribbon; the XT30 junction follows it to the grip mouth.'),
            ('P4  XT30 apart', 'Unplug by the housings, never by the wires. The pack stays out until the body is closed.'),
            ('EVF out (s7 item 7)', 'Unplug the HDMI in place first: smooth-jaw long-nose pliers (tool 15) on the plug\'s '
             'deep half, pull straight down while a fingertip from the front backs the slab. Then slide the OLED and board '
             'out together; with the plug on, the pair cannot pass the rail.'),
            ('Hood release (BX-17)', 'If a release pin does not stay in its hole, hold both pins with one strip of tape '
             'across the right wall, then lift the hood straight up.'),
            ('Then', 'Service is the exact reverse of the build (ASSEMBLY s7 items 2-11). Lens swap without isolation: '
             'loosen s_c4 one turn, tip the body nose-down, carry the lens, unscrew with fingertips only (the hood tab '
             'catch holds the camera through its metal lock tab); a stuck thread: stop, never more than fingertip '
             'torque. Refit: lens seated, turn lens and camera to the middle of their free roll, then s_c4.')], 'list', size=21)
        blockers_page(doc)
    doc.footer_all()
    pdir = os.path.join(OUT, 'pages')
    os.makedirs(pdir, exist_ok=True)
    if not only:
        for f in os.listdir(pdir):
            if f.endswith('.png'):
                os.remove(os.path.join(pdir, f))
    for k, im in enumerate(doc.pages):
        name = ('d2-%03d.png' % (k + 1)) if not only else ('only-%s.png' % doc.data[k]['id'])
        im.save(os.path.join(pdir, name), optimize=True)
    if not only:
        if not a.no_pdf:
            doc.pages[0].save(os.path.join(OUT, 'GS8-D2-assembly-guide.pdf'), save_all=True,
                              append_images=doc.pages[1:], resolution=DPI)
        write_html(doc, os.path.join(OUT, 'index.html'))
        write_html(doc, os.path.join(OUT, 'artifact.html'), fragment=True)
        json.dump(dict(revision=revision, built=doc.stamp, pages=doc.data),
                  open(os.path.join(OUT, 'guide-data.json'), 'w'), indent=1)
    print('pages', len(doc.pages), 'seconds', round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
