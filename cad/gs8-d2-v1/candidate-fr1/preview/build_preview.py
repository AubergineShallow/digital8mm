"""Embed the audited assembly display meshes into the interactive preview."""
from pathlib import Path
import base64
import gzip
import json

HERE = Path(__file__).resolve().parent
INLINE = Path('C:/Users/Pre-Installed User/.codex/visualizations/2026/10/03/01a1024d-75c7-74b2-a90e-15063b47bb87/fr1-camera-preview.html')
payload = (HERE / 'assembly-meshes.gzip-base64.txt').read_text().strip()
data = json.loads(gzip.decompress(base64.b64decode(payload)))
assert len(data['parts']) == 35
template = (HERE / 'viewer-template.html').read_text(encoding='utf-8')
assert template.count('__COMPRESSED_DATA__') == 1
fragment = template.replace('__COMPRESSED_DATA__', payload)
assert len(fragment.encode('utf-8')) < 1_000_000
INLINE.write_text(fragment, encoding='utf-8')
print(json.dumps(dict(path=str(INLINE), bytes=INLINE.stat().st_size,
                      parts=[dict(id=p['name'], kind=p['kind']) for p in data['parts']]), indent=2))
