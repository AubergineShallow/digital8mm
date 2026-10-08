"""Independent read-only export/provenance review of r3 release and FR1 candidate."""
from pathlib import Path
import hashlib
import json
import trimesh

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'cad/gs8-d2-v1'
HERE = Path(__file__).parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else 'missing'

def hashes(root, records):
    return [dict(path=name, expected=expected, actual=digest(root / name),
                 match=digest(root / name) == expected) for name, expected in records.items()]

def inspect(cad):
    out = cad / 'out'
    receipt = json.loads((out / 'build-receipt.json').read_text())
    source = hashes(cad, receipt['sources'])
    files = hashes(out, receipt['files'])
    # r3 records gate-document paths relative to the repository root.
    docs = hashes(ROOT, receipt['hardware_gates']['source_docs'])
    meshes = []
    for path in sorted((out / 'stl').rglob('*.stl')):
        mesh = trimesh.load_mesh(path, process=True)
        meshes.append(dict(path=path.relative_to(out).as_posix(), watertight=bool(mesh.is_watertight),
            consistent_winding=bool(mesh.is_winding_consistent), positive_volume=bool(mesh.volume > 0),
            volume_mm3=round(float(mesh.volume), 4), extents_mm=mesh.extents.tolist(),
            sha256=digest(path), linked_by_receipt=path.relative_to(out).as_posix() in receipt['files']))
    old = BASE / 'out/_r2-2026-10-05'
    comparison = [dict(path=row['path'], same_as_r2=row['sha256'] == digest(old / row['path'])) for row in meshes
                  if (old / row['path']).is_file()]
    coupon_check = out / 'fr1-coupons-check.json'
    coupon_hashes = hashes(out, {row['stl']: row['sha256'] for row in json.loads(coupon_check.read_text())['coupons']}) if coupon_check.exists() else []
    states = {key: {field: value[field] for field in ('status', 'items_required', 'items_with_verdict', 'outcome') if field in value}
              for key, value in receipt['status_states'].items()}
    summary = dict(built_at=receipt['built_at'], variant=receipt.get('variant'),
        source_count=len(source), source_mismatches=[row for row in source if not row['match']],
        declared_missing_sources=[row['path'] for row in source if row['actual'] == 'missing'],
        output_count=len(files), output_mismatches=[row for row in files if not row['match']],
        gate_doc_count=len(docs), gate_doc_mismatches=[row for row in docs if not row['match']],
        mesh_count=len(meshes), production_mesh_count=sum(row['path'].count('/') == 1 for row in meshes),
        mesh_failures=[row['path'] for row in meshes if not all(row[key] for key in ('watertight','consistent_winding','positive_volume'))],
        unlinked_meshes=[row['path'] for row in meshes if not row['linked_by_receipt']],
        separate_coupon_hash_count=len(coupon_hashes), separate_coupon_hash_mismatches=[row for row in coupon_hashes if not row['match']],
        changed_from_r2=[row['path'] for row in comparison if not row['same_as_r2']],
        cad_categories=receipt['summary'], states=states)
    return dict(summary=summary, source_hashes=source, output_hashes=files, gate_doc_hashes=docs,
                meshes=meshes, comparison_to_r2=comparison, separate_coupon_hashes=coupon_hashes)

report = {name: inspect(cad) for name, cad in [('release', BASE), ('candidate_fr1', BASE / 'candidate-fr1')]}
rebuild_dir = HERE / 'rebuild-fr1'
if (rebuild_dir / 'build-receipt.json').is_file():
    rebuilt = json.loads((rebuild_dir / 'build-receipt.json').read_text())
    source_receipt = json.loads((BASE / 'candidate-fr1/out/build-receipt.json').read_text())
    mesh_hashes = hashes(rebuild_dir, {key: value for key, value in source_receipt['files'].items()
        if key.startswith('stl/') and key.count('/') == 1})
    report['independent_candidate_rebuild'] = dict(built_at=rebuilt['built_at'], seconds=rebuilt['total_s'],
        argv=rebuilt['argv'], variant=rebuilt['variant'], summary=rebuilt['summary'],
        categories_pass=all(row['status'] == 'pass' for row in rebuilt['summary']),
        source_hashes=hashes(BASE / 'candidate-fr1', rebuilt['sources']),
        production_stl_hashes=mesh_hashes,
        all_production_stl_hashes_match=all(row['match'] for row in mesh_hashes),
        note='Independent FR1 all source/checks/STL rebuild, 1 mm sweeps, --fast skips full renders and STEP. Coupons not regenerated.')
report['note'] = 'Independent checks of existing files. A valid mesh and matching hashes do not prove physical fit or operation.'
(HERE / 'artifact-audit.json').write_text(json.dumps(report, indent=2))
for name in ('release', 'candidate_fr1'):
    summary = dict(report[name]['summary'])
    summary['cad_categories'] = {row['check']: row['status'] for row in summary['cad_categories']}
    print(name, json.dumps(summary, indent=2))
if 'independent_candidate_rebuild' in report:
    print('independent candidate rebuild:', json.dumps({key:report['independent_candidate_rebuild'][key]
          for key in ('built_at','seconds','categories_pass','all_production_stl_hashes_match')}))
