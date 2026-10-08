"""Read receipt-linked FR1 STEP parts and export display meshes only.

Run through ../run_locked.py from the repository root. Production files are never
written. Purchased parts are rebuilt from the receipt-linked proxy source; their
dimensions and fit remain unverified. Exploded offsets illustrate relationships,
not the actual sequence or path of assembly.
"""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import os
import sys
import time

HERE = Path(__file__).resolve().parent
MODEL = HERE.parent
OUT = MODEL / 'out'
os.environ['D2_FR'] = 'all'
sys.dont_write_bytecode = True
sys.path.insert(0, str(MODEL))

import cadquery as cq
import build_d2 as B
import layout as L


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group(pid):
    if pid in ('tub', 'hood', 'panel'):
        return 'shell'
    if pid in ('base_grip', 'cap', 'strap'):
        return 'grip'
    if pid in ('eyecup', 'eyepiece', 'hmx039', 'evf_board', 'foam_pad'):
        return 'evf'
    if pid in ('lens', 'c_cs_adapter', 'gs_camera'):
        return 'optics'
    if pid in ('plunger', 'knob_exp', 'knob_fps', 'encoder', 'switch_1824', 'run_button'):
        return 'controls'
    if pid in ('pack', 'xt30_pair'):
        return 'power'
    if pid.startswith('s_') or pid in ('tripod_nut', 'x1203_kit'):
        return 'hardware'
    return 'electronics'


LABELS = {
    'tub': 'Main body tub', 'hood': 'Sliding hood with rigid keys',
    'panel': 'Two-screw side panel', 'base_grip': 'Pistol grip and base',
    'cap': 'Sliding battery heel', 'pi_keeper': 'Keyed Pi keeper',
    'plunger': 'Power button plunger', 'knob_exp': 'Exposure / menu knob',
    'knob_fps': '18 / 24 fps knob', 'eyecup': 'Soft EVF eyecup',
    'stick_sleeve': 'Recording storage sleeve',
}


def main():
    started = time.time()
    receipt = json.loads((OUT / 'build-receipt.json').read_text())
    manifest = json.loads((OUT / 'parts-manifest.json').read_text())
    meta = {p['id']: p for p in manifest['parts']}
    inputs = {}
    for name in ('layout.py', 'cots.py', 'd2_common.py', 'build_d2.py'):
        actual = sha(MODEL / name)
        if actual != receipt['sources'][name]:
            raise ValueError('Source differs from FR1 receipt: ' + name)
        inputs[name] = actual
    pmp = OUT / 'parts-manifest.json'
    if sha(pmp) != receipt['files']['parts-manifest.json']:
        raise ValueError('Parts manifest differs from FR1 receipt')
    rows = {}
    for pid in L.PARTS:
        relative = 'step/parts/' + pid + '.step'
        path = OUT / relative
        actual = sha(path)
        if actual != receipt['files'][relative]:
            raise ValueError('STEP differs from FR1 receipt: ' + pid)
        inputs['out/' + relative] = actual
        shape = B.as_shape(cq.importers.importStep(str(path)))
        if not shape.isValid():
            raise ValueError('Invalid imported STEP: ' + pid)
        rows[pid] = dict(shape=shape, kind='printed', stub=False)
        print('Imported', pid, flush=True)
    rows.update(B.build_cots())
    parts = []
    skipped = []
    for pid, row in rows.items():
        shape = row.get('shape')
        if shape is None:
            skipped.append(pid)
            continue
        vertices, faces = shape.tessellate(0.08, 0.2)
        v = [[round(float(c), 5) for c in vert.toTuple()] for vert in vertices]
        f = [[int(c) for c in face] for face in faces]
        if not v or not f:
            raise ValueError('Empty mesh: ' + pid)
        bb = shape.BoundingBox()
        bbox = [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax]
        expected = meta[pid].get('bbox')
        if expected and max(abs(a-b) for a,b in zip(bbox, expected)) > 0.15:
            raise ValueError('Assembly bounds disagree with manifest: %s actual=%s expected=%s' % (pid, bbox, expected))
        part = dict(name=pid, label=LABELS.get(pid, meta[pid].get('name') or pid),
                    kind=row['kind'], group=group(pid), color=B.colour_of(pid, row),
                    explode=list(B.explode_of(pid)), step=meta[pid].get('step'),
                    manufacture=row['kind'] == 'printed',
                    fit_status='proposed; physically unverified',
                    source='receipt-linked STEP' if row['kind'] == 'printed' else 'receipt-linked purchased-part proxy source',
                    bbox=[round(n, 5) for n in bbox], vertices=v, triangles=f)
        parts.append(part)
        print('Meshed', pid, len(v), 'vertices', len(f), 'triangles', flush=True)
    data = dict(revision=L.REVISION, variant=L.FR_STATE,
                title='GS8 D2 / FR1 exploratory assembly', units='mm',
                axes='X front, Y left, Z up',
                notice='Exploratory candidate; all purchased-part fit and physical operation remain unverified. Exploded offsets are illustrative, not service motion.',
                geometry_method='Printed parts imported from receipt-linked assembly-pose STEP; purchased-part proxies rebuilt from the same receipt-linked source.',
                source_receipt_sha256=sha(OUT / 'build-receipt.json'),
                source_receipt_built_at=receipt['built_at'],
                mesh_tolerance_mm=0.08, angular_tolerance_rad=0.2,
                parts=parts)
    raw = json.dumps(data, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    (HERE / 'assembly-meshes.json').write_bytes(raw)
    (HERE / 'assembly-meshes.json.gz').write_bytes(compressed)
    (HERE / 'assembly-meshes.gzip-base64.txt').write_text(base64.b64encode(compressed).decode(), encoding='ascii')
    report = dict(parts=len(parts), printed=sum(p['kind']=='printed' for p in parts),
                  cots=sum(p['kind']=='cots' for p in parts), hardware=sum(p['kind']=='hardware' for p in parts),
                  vertices=sum(len(p['vertices']) for p in parts), triangles=sum(len(p['triangles']) for p in parts),
                  json_bytes=len(raw), gzip_bytes=len(compressed), base64_bytes=4*((len(compressed)+2)//3),
                  seconds=round(time.time()-started, 2), inputs_sha256=inputs,
                  outputs_sha256={'assembly-meshes.json': hashlib.sha256(raw).hexdigest(),
                                  'assembly-meshes.json.gz': hashlib.sha256(compressed).hexdigest()},
                  skipped_non_geometric_rows=skipped,
                  checks='Receipt source and STEP hashes match; each imported solid valid; assembly bounds match parts manifest within 0.15 mm (tessellation bounds); every mesh nonempty.',
                  notes='Display export only. No manufacturing, tolerance, assembly or physical validation is implied.')
    (HERE / 'mesh-export-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('inputs_sha256','outputs_sha256')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
