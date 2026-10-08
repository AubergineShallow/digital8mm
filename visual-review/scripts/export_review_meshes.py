#!/usr/bin/env python3
"""Export already-built D2 assembly geometry for review-only visualization.
Read saved STEP for production parts; rebuild only purchased-part proxies.
No production STEP/STL/receipt is written. Run through the working D2 run_locked.py.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--cad-root', required=True); p.add_argument('--out', required=True); p.add_argument('--build-out'); a=p.parse_args()
root=Path(a.cad_root).resolve(); out=Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
built=Path(a.build_out).resolve() if a.build_out else root/'out'
sys.path.insert(0,str(root))
import cadquery as cq
import layout as L
import cots

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
receipt_path=built/'build-receipt.json'
receipt=json.loads(receipt_path.read_text())
verified=[]
for fn in sorted(k for k in receipt['sources'] if k.endswith(('.py','.ttf','.otf'))):
    expected=receipt['sources'].get(fn)
    if not expected or sha(root/fn)!=expected: raise ValueError('Geometry source does not match receipt: '+fn)
    verified.append(fn)
font_file=L.ENGRAVE.get('font_file')
if font_file:
    if sha(root/font_file)!=L.ENGRAVE.get('font_sha256'): raise ValueError('Pinned engraving font hash mismatch')
    if font_file not in verified: verified.append(font_file+' (layout-pinned hash)')
args=receipt.get('argv',[])
if '--lens' in args:
    L.LENS=args[args.index('--lens')+1]
elif any(x.startswith('--lens=') for x in args):
    L.LENS=next(x.split('=',1)[1] for x in args if x.startswith('--lens='))
if L.LENS not in L.LENSES: raise ValueError('Unknown lens in build receipt')

def export(pid,shape,kind,source=None):
    vertices, faces=shape.tessellate(0.07,0.15)
    vv=[[v.x,v.y,v.z] for v in vertices]; ff=[list(f) for f in faces]
    mats=[]
    for f in ff:
        pts=[vv[i] for i in f]; c=[sum(v[k] for v in pts)/3 for k in range(3)]
        mat='silver' if pid in ('tub','panel','stick_sleeve') else 'black'
        if kind=='cots':
            mat={'lens':'lens','eyepiece':'lens','encoder':'pcb','run_button':'red','pi5':'pcb','x1203':'pcb','evf_board':'pcb','pack':'battery','cooler':'metal','x1203_kit':'brass','c_cs_adapter':'metal','switch_1824':'metal','usb_stick':'dark_red','xt30_pair':'connector','tripod_nut':'metal','strap':'strap','hmx039':'glass','gs_camera':'black','foam_pad':'rubber'}.get(pid,'black')
        if pid.startswith('s_'): mat='metal'
        if pid=='eyecup': mat='rubber'
        # Color only the exact existing recessed floors. This represents paint fill already required in assembly.
        if pid=='panel' and all(abs(q[1]-(L.YL-L.FDM['ENGRAVE_DEPTH']))<0.008 for q in pts): mat='paint_black'
        if pid=='knob_fps' and all(abs(q[1]-(L.KNOBS[pid]['y'][1]-0.6))<0.008 for q in pts): mat='paint_white'
        if pid=='plunger' and all(abs(q[0]-(L.PLUNGER['stem']['x'][1]-L.FDM['ENGRAVE_DEPTH']))<0.008 for q in pts): mat='paint_white'
        # The source renderer paints the complete encoder blue, including the shaft. Neutral hardware proxy here.
        if pid=='encoder' and c[1]>L.ENCODER['bushing']['a'][0]: mat='metal'
        mats.append(mat)
    data={'id':pid,'kind':kind,'vertices':vv,'faces':ff,'materials':mats,'source':source}
    path=out/(pid+'.json'); path.write_text(json.dumps(data,separators=(',',':')))
    print(pid,len(vv),len(ff),flush=True)
    return {'id':pid,'kind':kind,'mesh':path.name,'mesh_sha256':sha(path),'source':source}
rows=[]
for pid in L.PARTS:
    path=built/'step'/'parts'/(pid+'.step')
    key='step/parts/'+pid+'.step'
    if key not in receipt['files'] or sha(path)!=receipt['files'][key]: raise ValueError('Saved STEP does not match receipt: '+key)
    verified.append(key)
    wp=cq.importers.importStep(str(path)); shape=wp.val()
    rows.append(export(pid,shape,'printed',{'path':str(path),'sha256':sha(path)}))
for pid,row in cots.build_all(L).items():
    if row.get('shape') is not None:
        rows.append(export(pid,row['shape'].val(),'cots',{'proxy_source':str(root/'cots.py'),'sha256':sha(root/'cots.py')}))
manifest={'purpose':'Review-only material/lighting visualization. Exact saved printed STEP geometry, source COTS proxies. Intended paint fill; not printed or tested.','cad_root':str(root),'rows':rows,'layout_sha256':sha(root/'layout.py'),'cots_sha256':sha(root/'cots.py'),'lens':L.LENS,'cadquery_runtime':cq.__version__,'build_receipt':{'path':str(receipt_path),'sha256':sha(receipt_path),'built_at':receipt['built_at'],'variant':receipt['variant'],'cad_release_candidate':receipt.get('cad_release_candidate'),'blocking':receipt.get('blocking')},'verified_against_receipt':verified}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
