"""Independent read-only provenance and mesh review of the D2 r5 release (audit 2026-10-06)."""
from pathlib import Path
import hashlib, json
import trimesh

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / 'cad/gs8-d2-v1'
OUT = CAD / 'out'
HERE = Path(__file__).parent

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'missing'

def hashes(root, recs):
    return [dict(path=k, expected=v, actual=digest(root / k), match=digest(root / k) == v) for k, v in recs.items()]

r = json.loads((OUT / 'build-receipt.json').read_text())
src = hashes(CAD, r['sources'])
files = hashes(OUT, r['files'])
docs = hashes(ROOT, r['hardware_gates']['source_docs'])
# unhashed python sources in the release folder (top level)
unhashed_py = sorted(p.name for p in CAD.glob('*.py') if p.name not in r['sources'])
meshes = []
for p in sorted((OUT / 'stl').rglob('*.stl')):
    m = trimesh.load_mesh(p, process=True)
    rel = p.relative_to(OUT).as_posix()
    meshes.append(dict(path=rel, watertight=bool(m.is_watertight), winding=bool(m.is_winding_consistent),
                       positive_volume=bool(m.volume > 0), volume_mm3=round(float(m.volume), 3),
                       extents=[round(x, 2) for x in m.extents], linked=rel in r['files']))
r4 = OUT / '_r4-2026-10-06'
changed_vs_r4 = [m['path'] for m in meshes if (r4 / m['path']).is_file() and digest(OUT / m['path']) != digest(r4 / m['path'])]
new_vs_r4 = [m['path'] for m in meshes if not (r4 / m['path']).is_file()]
fuj = OUT / 'checks-fujinon-sweep1mm.json'
summary = dict(built_at=r['built_at'], cad_release_candidate=r['cad_release_candidate'], stubs=r['stubs'],
    sources=len(src), source_mismatch=[x['path'] for x in src if not x['match']], unhashed_py=unhashed_py,
    outputs=len(files), output_mismatch=[x['path'] for x in files if not x['match']],
    gate_docs=len(docs), gate_doc_mismatch=[x['path'] for x in docs if not x['match']],
    meshes=len(meshes), mesh_fail=[m['path'] for m in meshes if not (m['watertight'] and m['winding'] and m['positive_volume'])],
    unlinked_meshes=[m['path'] for m in meshes if not m['linked']],
    changed_vs_r4=changed_vs_r4, new_vs_r4=new_vs_r4,
    fujinon_checks_hash_in_receipt=r['files'].get('checks-fujinon-sweep1mm.json') == digest(fuj),
    summary=r['summary'], status_states={k: v.get('status') for k, v in r['status_states'].items()},
    warnings=r['warnings'], j7_float_min=r['j7_float_min'], blocking=r['blocking'])
rb = HERE / 'rebuild-kowa/build-receipt.json'
if rb.is_file():
    b = json.loads(rb.read_text())
    prod = {k: v for k, v in r['files'].items() if k.startswith('stl/') and k.count('/') == 1}
    hh = hashes(HERE / 'rebuild-kowa', prod)
    summary['rebuild'] = dict(built_at=b['built_at'], seconds=b.get('total_s'), summary=b['summary'],
        cad_release_candidate=b['cad_release_candidate'], stubs=b['stubs'],
        production_stl=len(hh), stl_mismatch=[x['path'] for x in hh if not x['match']],
        source_hashes_equal=b['sources'] == r['sources'])
(HERE / 'artifact-audit.json').write_text(json.dumps(dict(summary=summary, sources=src, outputs=files, gate_docs=docs, meshes=meshes), indent=1))
print(json.dumps(summary, indent=1, default=str)[:6000])
