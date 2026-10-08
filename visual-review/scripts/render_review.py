"""Blender product/assembly review from explicit CAD tessellations; no geometry editing."""
import bpy, json, math, sys, argparse
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser(); p.add_argument('--assets',required=True); p.add_argument('--out',required=True); p.add_argument('--view',default='hero'); p.add_argument('--samples',type=int,default=64); p.add_argument('--raw',action='store_true'); p.add_argument('--revision',default='r5 baseline'); a=p.parse_args(argv)
assets=Path(a.assets); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=a.samples; scene.cycles.use_denoising=False
scene.render.resolution_x=1800; scene.render.resolution_y=1400; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=0.0
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.75,0.78,0.82,1); scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.5
colors={
'silver':((0.57,0.585,0.56,1),0.48,0.05),'black':((0.022,0.025,0.030,1),0.38,0.02),
'lens':((0.014,0.017,0.022,1),0.29,0.12),'rubber':((0.025,0.027,0.030,1),0.62,0),
'metal':((0.53,0.54,0.51,1),0.25,0.8),'brass':((0.48,0.31,0.10,1),0.33,0.7),
'pcb':((0.04,0.22,0.12,1),0.55,0),'red':((0.52,0.028,0.035,1),0.35,0),
'dark_red':((0.23,0.025,0.032,1),0.43,0),'battery':((0.05,0.13,0.25,1),0.48,0),
'connector':((0.50,0.32,0.025,1),0.5,0),'strap':((0.042,0.042,0.040,1),0.9,0),
'glass':((0.005,0.009,0.012,1),0.18,0.12),'paint_black':((0.011,0.012,0.013,1),0.52,0),
'paint_white':((0.76,0.76,0.72,1),0.5,0),'paper':((0.76,0.78,0.77,1),0.75,0),
'footer':((0.83,0.845,0.83,1),0.6,0),'caption':((0.012,0.024,0.030,1),0.6,0),'accent':((0.015,0.075,0.09,1),0.5,0)}
materials={}
for n,(col,rough,metal) in colors.items():
    mat=bpy.data.materials.new(n); mat.diffuse_color=col; mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF'); bsdf.inputs['Base Color'].default_value=col; bsdf.inputs['Roughness'].default_value=rough; bsdf.inputs['Metallic'].default_value=metal
    
    if n in ('caption','accent','footer'):
        tree=mat.node_tree; tree.nodes.clear(); em=tree.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=col; em.inputs['Strength'].default_value=1; output=tree.nodes.new('ShaderNodeOutputMaterial'); tree.links.new(em.outputs[0],output.inputs['Surface'])
    materials[n]=mat
objects={}
manifest=json.loads((assets/'manifest.json').read_text())
for row in manifest['rows']:
    d=json.loads((assets/row['mesh']).read_text()); name=d['id']; mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([[c/1000 for c in v] for v in d['vertices']],[],d['faces']); mesh.update()
    obj=bpy.data.objects.new(name,mesh); scene.collection.objects.link(obj); objects[name]=obj
    mats=sorted(set(d['materials'])); idx={n:i for i,n in enumerate(mats)}
    for m in mats:
        target='silver' if a.raw and m=='paint_black' else ('black' if a.raw and m=='paint_white' else m)
        mesh.materials.append(materials[target])
    for poly,m in zip(mesh.polygons,d['materials']): poly.material_index=idx[m]; poly.use_smooth=True
    # Merge tessellation seams, preserving CAD hard edges rather than rounding the geometry.
    mod=obj.modifiers.new('Tessellation weld','WELD'); mod.merge_threshold=0.000001
    split=obj.modifiers.new('CAD hard edges','EDGE_SPLIT'); split.split_angle=math.radians(35); split.use_edge_angle=True
    wn=obj.modifiers.new('Weighted face normals','WEIGHTED_NORMAL'); wn.keep_sharp=True; wn.weight=50
# Explicit offsets are explanatory exploded positions, never assembly instructions.
exploded={'hood':(0,0,58),'panel':(0,78,0),'knob_exp':(0,104,0),'knob_fps':(0,104,0),'encoder':(0,78,0),'switch_1824':(0,78,0),'base_grip':(0,0,-47),'cap':(0,0,-114),'pack':(0,0,-76),'run_button':(19,0,-47),'strap':(0,-24,-47),'tripod_nut':(0,0,-33),'xt30_pair':(0,0,-47),'lens_collar':(43,0,0),'lens':(90,0,0),'c_cs_adapter':(65,0,0),'gs_camera':(0,22,14),'pi5':(0,0,20),'cooler':(0,0,30),'x1203':(0,0,10),'x1203_kit':(0,0,15),'pi_keeper':(0,0,13),'eyecup':(-48,0,0),'eyepiece':(-23,0,0),'usb_stick':(-49,0,0),'stick_sleeve':(-65,0,0),'hmx039':(0,42,0),'evf_board':(0,40,0),'foam_pad':(0,42,0),'plunger':(25,0,0)}
views={
'hero':dict(pos=(300,410,245),target=(-66,0,-7),scale=365),
'controls':dict(pos=(-78,490,63),target=(-78,25,52),scale=187),
'collar':dict(pos=(220,215,133),target=(0,0,53),scale=155),
'collar_pinch':dict(pos=(180,-240,158),target=(0,-8,61),scale=172),
'rear':dict(pos=(-360,-285,190),target=(-86,-3,8),scale=345),
'service':dict(pos=(325,470,260),target=(-55,22,-28),scale=670),
'grip':dict(pos=(170,285,50),target=(-47,0,-54),scale=184),
}
v=views[a.view]
if a.view=='service':
    for n,o in objects.items():
        ofs=exploded.get(n,(0,0,0))
        if n.startswith('s_'):
            if n.startswith('s_c'): ofs=(63,0,10 if n=='s_c4' else 0)
            elif n.startswith('s_k'): ofs=(0,0,35)
            elif n.startswith('s_r'): ofs=(0,-24,0)
            else: ofs=(0,0,-70)
        o.location=Vector(ofs)/1000
# The hero's transparent lens is not invented: purchased lenses remain opaque proxy surfaces.
if a.view in ('hero','rear','grip'):
    bpy.ops.mesh.primitive_plane_add(size=3,location=(0,0,-0.1163)); ground=bpy.context.object; ground.name='Review studio ground'; ground.data.materials.append(materials['paper'])
# Large sources make the black hood, collar and grip readable without changing their colors.
def area(n,loc,target,power,size):
    data=bpy.data.lights.new(n,'AREA'); data.energy=power * 0.016; data.shape='DISK'; data.size=size
    o=bpy.data.objects.new(n,data); scene.collection.objects.link(o); o.location=Vector(loc)/1000; o.rotation_euler=(Vector(target)/1000-o.location).to_track_quat('-Z','Y').to_euler()
area('Key',(60,270,470),(-65,0,20),70,0.4)
area('Fill',(-280,110,130),(-60,0,5),30,0.32)
area('Rim',(80,-260,250),(-55,0,10),95,0.26)
area('Front rim',(370,15,105),(-10,0,45),25,0.24)
cam_data=bpy.data.cameras.new('Review camera'); cam=bpy.data.objects.new('Review camera',cam_data); scene.collection.objects.link(cam); scene.camera=cam
cam.location=Vector(v['pos'])/1000; target=Vector(v['target'])/1000; cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cam_data.type='ORTHO'; cam_data.ortho_scale=v['scale']/1000; cam_data.lens=52; cam_data.clip_start=0.001; cam_data.clip_end=10
# Native scene captions ensure every delivered image carries its evidence/finish status.
width=cam_data.ortho_scale; height=width*scene.render.resolution_y/scene.render.resolution_x
q=cam.rotation_euler.to_quaternion(); d=(target-cam.location).length*0.72

def caption(text,x,y,size,mat='caption'):
    cu=bpy.data.curves.new('Caption','FONT'); cu.body=text; cu.size=size; cu.align_x='LEFT'; cu.space_character=1.08
    o=bpy.data.objects.new('Caption '+text,cu); scene.collection.objects.link(o); o.location=cam.location+q@Vector((x,y,-d)); o.rotation_euler=cam.rotation_euler; cu.materials.append(materials[mat])
    o.visible_shadow=False; o.visible_glossy=False; o.visible_transmission=False; o.visible_diffuse=False
# Footer backdrop stays in camera space, so fine print never disappears against a cropped part.
mesh=bpy.data.meshes.new('Footer background'); mesh.from_pydata([(-width/2,-height/2,0),(width/2,-height/2,0),(width/2,-height*0.418,0),(-width/2,-height*0.418,0)],[],[(0,1,2,3)]); mesh.update()
footer=bpy.data.objects.new('Footer background',mesh); scene.collection.objects.link(footer); footer.location=cam.location+q@Vector((0,0,-d-0.0002)); footer.rotation_euler=cam.rotation_euler; mesh.materials.append(materials['footer']); footer.visible_shadow=False; footer.visible_diffuse=False; footer.visible_glossy=False
label={'hero':'D2 cloud-polish fork','controls':'D2 / control surface','collar':'D2 / floating-camera lens collar','collar_pinch':'D2 / collar and pinch access','rear':'D2 / rear and grip-side access','service':'D2 / service architecture','grip':'D2 / grip and record control'}[a.view]
caption(label,-width*0.456,height*0.434,width*0.022)
caption('UNFILLED ENGRAVING / SAME CAD GEOMETRY' if a.raw else 'INTENDED FINISH / PAINT-FILLED MARKINGS',-width*0.455,height*0.399,width*0.0095,'accent')
lens_name={'kowa_lm6hc':'Kowa LM6HC','fujinon_hf6xa':'Fujinon HF6XA'}.get(manifest.get('lens'),'')
variant_label=(' | '+lens_name+' proxy') if lens_name else ''
caption(a.revision+variant_label+' | CAD/proxies. No physical build or test.',-width*0.455,-height*0.464,width*0.0095)
if a.view=='service': caption('Illustrative separation. Harnesses omitted. Follow the assembly and isolation procedure.',-width*0.455,-height*0.439,width*0.0085)
scene.render.filepath=str(out/(a.view+('-raw' if a.raw else '')+'.png'))
bpy.ops.wm.save_as_mainfile(filepath=str(out/(a.view+('-raw' if a.raw else '')+'.blend')))
bpy.ops.render.render(write_still=True)
