"""Read-only independent audit of the supplied D2 r2 release artifacts."""
from pathlib import Path
import hashlib
import json
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / 'cad/gs8-d2-v1'
OUT = CAD / 'out'
receipt = json.loads((OUT / 'build-receipt.json').read_text())
manifest = json.loads((OUT / 'print-manifest.json').read_text())
rows = manifest if isinstance(manifest, list) else manifest['parts']

def verify_hashes(base, entries):
    result = []
    for name, expected in entries.items():
        path = base / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        result.append(dict(name=name, match=actual == expected, actual=actual, expected=expected))
    return result

def mesh_info(path, production=False):
    mesh = trimesh.load_mesh(path, process=True)
    result = dict(part=path.stem, vertices=len(mesh.vertices), faces=len(mesh.faces),
                  watertight=bool(mesh.is_watertight), winding_consistent=bool(mesh.is_winding_consistent),
                  positive_volume=bool(mesh.volume > 0), signed_volume_mm3=round(float(mesh.volume), 3),
                  minimum_print_z=float(mesh.bounds[0, 2]), dimensions_mm=np.round(mesh.extents, 3).tolist())
    if production:
        row = next((row for row in rows if row['id'] == path.stem), {})
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        volume = row.get('volume_mm3', 0)
        result.update(manifest_hash_match=digest == row.get('stl_sha256'),
                      manifest_volume_difference_pct=round(100 * abs(float(mesh.volume) - volume) / volume, 4) if volume else None)
    return result

report = dict(receipt_built_at=receipt['built_at'],
              source_hashes=verify_hashes(CAD, receipt['sources']),
              recorded_output_hashes=verify_hashes(OUT, receipt['files']),
              gate_document_hashes=verify_hashes(CAD, receipt['hardware_gates']['source_docs']),
              production_meshes=[mesh_info(path, True) for path in sorted((OUT / 'stl').glob('*.stl'))],
              coupon_meshes=[mesh_info(path) for path in sorted((OUT / 'stl/coupons').glob('*.stl'))],
              note='Independent checks of supplied exports. Mesh validity does not establish slicer quality, component fit, strength or operation.')
expected_parts = {row['id'] for row in rows}
actual_parts = {row['part'] for row in report['production_meshes']}
report['production_inventory'] = dict(missing=sorted(expected_parts - actual_parts), unexpected=sorted(actual_parts - expected_parts))
fujinon = json.loads((OUT / '_fujinon-r2/build-receipt.json').read_text())
report['alternate_lens'] = dict(built_at=fujinon['built_at'], argv=fujinon['argv'],
    source_hashes=verify_hashes(CAD, fujinon['sources']),
    copied_checks_match=hashlib.sha256((OUT / 'checks-fujinon-sweep1mm.json').read_bytes()).hexdigest()
        == hashlib.sha256((OUT / '_fujinon-r2/checks.json').read_bytes()).hexdigest(),
    all_groups_pass=all(row['status'] == 'pass' for row in fujinon['summary']))
summary = {}
for key in ('source_hashes', 'recorded_output_hashes', 'gate_document_hashes'):
    summary[key] = dict(count=len(report[key]), failures=[row['name'] for row in report[key] if not row['match']])
for key in ('production_meshes', 'coupon_meshes'):
    summary[key] = dict(count=len(report[key]), failures=[row['part'] for row in report[key]
                          if not all(row[x] for x in ('watertight', 'winding_consistent', 'positive_volume'))])
summary['production_inventory'] = report['production_inventory']
summary['alternate_lens'] = dict(source_failures=[row['name'] for row in report['alternate_lens']['source_hashes'] if not row['match']],
    copied_checks_match=report['alternate_lens']['copied_checks_match'], all_groups_pass=report['alternate_lens']['all_groups_pass'])
rebuilt_dir = Path(__file__).parent / 'rebuild-kowa'
if (rebuilt_dir / 'build-receipt.json').is_file():
    rebuilt = json.loads((rebuilt_dir / 'build-receipt.json').read_text())
    rebuilt_meshes = verify_hashes(rebuilt_dir, {key: value for key, value in receipt['files'].items()
        if key.startswith('stl/') and key.count('/') == 1})
    report['independent_rebuild'] = dict(built_at=rebuilt['built_at'], argv=rebuilt['argv'],
        seconds=rebuilt['total_s'], summary=rebuilt['summary'], stubs=rebuilt['stubs'],
        source_hashes=verify_hashes(CAD, rebuilt['sources']), production_mesh_hashes=rebuilt_meshes,
        note='Full Kowa source geometry/checks/STL rebuild with 1 mm sweeps. --fast skips full renders and STEP. Coupons were not regenerated.')
    summary['independent_rebuild'] = dict(all_groups_pass=all(row['status'] == 'pass' for row in rebuilt['summary']),
        groups=len(rebuilt['summary']), stubs=rebuilt['stubs'],
        source_hash_failures=[row['name'] for row in report['independent_rebuild']['source_hashes'] if not row['match']],
        production_stl_hash_mismatches=[row['name'] for row in rebuilt_meshes if not row['match']])
report['summary'] = summary
(Path(__file__).parent / 'artifact-audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps(summary, indent=2))
