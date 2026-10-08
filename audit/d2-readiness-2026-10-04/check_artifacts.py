"""Independent read-only review of exported D2 meshes and release provenance."""
from pathlib import Path
import hashlib, json
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[2]
cad=root/'cad/gs8-d2-v1'
out=cad/'out'
receipt=json.loads((out/'build-receipt.json').read_text())
manifest=json.loads((out/'print-manifest.json').read_text())
print('manifest type',type(manifest).__name__,list(manifest)[:8] if isinstance(manifest,dict) else len(manifest),flush=True)
rows=manifest if isinstance(manifest,list) else manifest.get('parts',[])
source_checks=[]
for name,expected in receipt['sources'].items():
    p=cad/name
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    source_checks.append(dict(name=name,match=actual==expected,actual=actual,expected=expected))
meshes=[]
for p in sorted((out/'stl').glob('*.stl')):
    m=trimesh.load_mesh(p,process=True)
    row=next((x for x in rows if x['id']==p.stem),{})
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    expected=row.get('stl_sha256')
    mass_v=row.get('volume_mm3',0)
    result=dict(part=p.stem,vertices=len(m.vertices),faces=len(m.faces),watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),signed_volume_mm3=round(float(m.volume),2),volume_difference_pct=round(100*abs(float(m.volume)-mass_v)/mass_v,4) if mass_v else None,minimum_print_z=float(m.bounds[0,2]),dimensions_mm=np.round(m.extents,3).tolist(),manifest_hash_match=digest==expected)
    meshes.append(result)
    print(result,flush=True)
file_checks=[]
for name,expected in receipt['files'].items():
    p=out/name
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    file_checks.append(dict(name=name,match=actual==expected))
coupons=[]
for p in sorted((out/'stl/coupons').glob('*.stl')):
    m=trimesh.load_mesh(p,process=True)
    coupons.append(dict(part=p.stem,watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),positive_volume=bool(m.volume>0)))
report=dict(source_hashes=source_checks,source_hashes_all_match=all(x['match'] for x in source_checks),recorded_output_hashes=file_checks,recorded_output_hashes_all_match=all(x['match'] for x in file_checks),meshes=meshes,coupons=coupons,note='Independent check of existing exported STL files; no source rebuild or physical/slicer validation.')
(Path(__file__).parent/'artifact-audit.json').write_text(json.dumps(report,indent=2))
print('SOURCE HASHES ALL MATCH:',report['source_hashes_all_match'],flush=True)
print('SOURCE MISMATCHES:',[x['name'] for x in source_checks if not x['match']],flush=True)
print('RECORDED OUTPUT HASHES:',len(file_checks),'all match:',report['recorded_output_hashes_all_match'],flush=True)
print('COUPON MESHES:',coupons,flush=True)
