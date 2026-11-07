"""Exact Three.js snapshot -> editable Cycles river scene. Invoked by the local MCP."""
import bpy,json,math,base64,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];DATA=json.loads((ROOT/'outputs/river-scene.json').read_text(encoding='utf8'))
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
scene=bpy.context.scene;scene.name='QINGLAN_RIVER';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
collection=bpy.data.collections.new('River model - 64 x 600 m');scene.collection.children.link(collection)
studio=bpy.data.collections.new('Presentation environment');scene.collection.children.link(studio)
owners={}
for name in DATA['manifest']['components']:
    o=bpy.data.objects.new(name,None);collection.objects.link(o);owners[name]=o
materials={}
for mid,m in DATA['materials'].items():
    material=bpy.data.materials.new(m['name']);material.use_nodes=True;nodes=material.node_tree.nodes;links=material.node_tree.links;bs=nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*m['color'],1);bs.inputs['Roughness'].default_value=m.get('roughness',.8);bs.inputs['Metallic'].default_value=m.get('metalness',0)
    attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1;multiply.inputs[2].default_value=(*m['color'],1);links.new(attr.outputs['Color'],multiply.inputs[1]);links.new(multiply.outputs[0],bs.inputs['Base Color'])
    if m.get('texture'):
        path=ROOT/'outputs'/('texture_'+mid+'.png');path.write_bytes(base64.b64decode(m['texture'].split(',')[1]));im=bpy.data.images.load(str(path));im.pack();tex=nodes.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT';mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;links.new(tex.outputs['Color'],mul.inputs[1]);links.new(multiply.outputs[0],mul.inputs[2]);links.new(mul.outputs[0],bs.inputs['Base Color'])
    if 'water static' in m['name']:
        for link in list(bs.inputs['Base Color'].links):links.remove(link)
        bs.inputs['Base Color'].default_value=(.42,.63,.58,1);bs.inputs['Roughness'].default_value=.075;bs.inputs['Metallic'].default_value=0;bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=1.333
        coord=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.6;noise.inputs['Detail'].default_value=3;links.new(coord.outputs['Object'],noise.inputs['Vector']);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.26;bump.inputs['Distance'].default_value=.025;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
        absorption=nodes.new('ShaderNodeVolumeAbsorption');absorption.inputs['Color'].default_value=(.10,.32,.29,1);absorption.inputs['Density'].default_value=.23;links.new(absorption.outputs[0],nodes.get('Material Output').inputs['Volume'])
    elif any(word in m['name'] for word in ['limestone','cobble','gravel','riverbed','soil','bark']):
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=28;noise.inputs['Detail'].default_value=3;coord=nodes.new('ShaderNodeTexCoord');links.new(coord.outputs['Object'],noise.inputs['Vector']);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.025;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
    if 'scales' in m['name']:bs.inputs['Coat Weight'].default_value=.3
    materials[mid]=material
geos={}
for uid,g in DATA['geometries'].items():
    vertices=np.array(g['positions'],dtype=np.float32).reshape((-1,3));faces=np.array(g['indices'] if g.get('indices') is not None else np.arange(len(vertices)),dtype=np.int32).reshape((-1,3));uv=np.array(g['uv'],dtype=np.float32).reshape((-1,2)) if g.get('uv') else np.zeros((len(vertices),2));colors=np.array(g['colors'],dtype=np.float32).reshape((-1,3)) if g.get('colors') else np.ones((len(vertices),3));geos[uid]=(vertices,faces,uv,colors)
batches={}
for o in DATA['objects']:batches.setdefault((o['owner'],o['m']),[]).append(o)
for (owner,mid),objects in batches.items():
    vertices=[];faces=[];uvs=[];colors=[];offset=0
    for o in objects:
        p,idx,uv,col=geos[o['g']];a=np.array(o['matrix'],dtype=np.float32).reshape((4,4),order='F');v=p@a[:3,:3].T+a[:3,3];v=np.stack([v[:,0],-v[:,2],v[:,1]],axis=1)
        if owner=='water':
            t=DATA.get('state',{}).get('waterTime',0);edge=np.clip((1-np.abs(uv[:,0]))/.12,0,1);wave=(np.sin(v[:,0]*.72-v[:,1]*.16-t*1.4)+.42*np.sin(v[:,0]*1.6+v[:,1]*.3+t*.95)+.16*np.sin(v[:,0]*3.4-v[:,1]*.6-t*2.1))*.026*edge;v[:,2]+=wave
        vertices.append(v);faces.append(idx+offset);offset+=len(v);uvs.append(uv[idx].reshape((-1,2)));tint=np.array(o.get('tint') or [1,1,1]);colors.append((col[idx]*tint).reshape((-1,3)))
    v=np.concatenate(vertices);f=np.concatenate(faces);uv=np.concatenate(uvs);col=np.concatenate(colors)
    if owner=='water':
        # Close the actual river outline to form a physical absorbing water volume.
        n=len(v);bottom=v.copy();bottom[:,2]=-4.4;edges={}
        for tri in f:
            for a,b in zip(tri,[tri[1],tri[2],tri[0]]):key=tuple(sorted((int(a),int(b))));edges[key]=edges.get(key,0)+1
        sides=[]
        for (a,b),count in edges.items():
            if count==1:sides.extend([[a,b,b+n],[a,b+n,a+n]])
        bottom_faces=f[:,::-1]+n;extra=np.array(sides,dtype=np.int32);f=np.concatenate([f,bottom_faces,extra]);v=np.concatenate([v,bottom]);uv=np.concatenate([uv,uv,np.zeros((len(extra)*3,2))]);col=np.ones((len(f)*3,3))
    mesh=bpy.data.meshes.new(owner+'_'+materials[mid].name);mesh.vertices.add(len(v));mesh.vertices.foreach_set('co',v.ravel());mesh.loops.add(len(f)*3);mesh.loops.foreach_set('vertex_index',f.ravel());mesh.polygons.add(len(f));mesh.polygons.foreach_set('loop_start',np.arange(len(f),dtype=np.int32)*3);mesh.polygons.foreach_set('loop_total',np.full(len(f),3,dtype=np.int32));mesh.update();layer=mesh.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',uv.ravel());color=mesh.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='CORNER');rgba=np.ones((len(col),4),dtype=np.float32);rgba[:,:3]=col;color.data.foreach_set('color',rgba.ravel());mesh.materials.append(materials[mid]);obj=bpy.data.objects.new(mesh.name,mesh);obj.parent=owners[owner];collection.objects.link(obj)
    if owner in ['terrain','water','stones','trees','fish']:
        for poly in mesh.polygons:poly.use_smooth=True
    if owner=='water':obj['medium']='IOR 1.333 / closed volume / depth absorption'
world=bpy.data.worlds.new('River morning sky');world.use_nodes=True;scene.world=world;nodes=world.node_tree.nodes;links=world.node_tree.links;bg=nodes.get('Background');bg.inputs['Strength'].default_value=.25;sky=nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(32);sky.sun_rotation=math.radians(130);sky.sun_disc=False;links.new(sky.outputs['Color'],bg.inputs['Color'])
sun=bpy.data.lights.new('Soft morning daylight','SUN');sun.energy=2.5;sun.angle=math.radians(5);sun.color=(1,.94,.84);obj=bpy.data.objects.new(sun.name,sun);obj.location=(-100,-100,150);obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler();studio.objects.link(obj)
back=bpy.data.materials.new('Presentation ground');back.diffuse_color=(.40,.46,.38,1);mesh=bpy.data.meshes.new('Presentation ground');mesh.from_pydata([(-5000,-5000,-7.36),(5000,-5000,-7.36),(5000,5000,-7.36),(-5000,5000,-7.36)],[],[(0,1,2,3)]);obj=bpy.data.objects.new(mesh.name,mesh);mesh.materials.append(back);studio.objects.link(obj)
def cv(p):return Vector((p[0],-p[2],p[1]))
views={'Overview':([320,400,600],[0,-1,0]),'Bend':([48,27,100],[0,-.8,55]),'Bank':([28,4.5,58],[18,-.9,42]),'Fish':([12,4,58],[16,-1.25,39]),'Along':([35,20,290],[0,-.75,0])}
for name,(p,q) in views.items():
    data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);obj.location=cv(p);obj.rotation_euler=(cv(q)-obj.location).to_track_quat('-Z','Y').to_euler();data.sensor_fit='VERTICAL';data.sensor_height=24;data.lens=24/(2*math.tan(math.radians(43)/2));data.clip_start=.05;data.clip_end=3000;studio.objects.link(obj)
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8;scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.use and d.type=='OPTIX' for d in prefs.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
for name in views:
    scene.camera=bpy.data.objects[name];scene.render.filepath=str(ROOT/'outputs'/('blender-'+name.lower()+'.png'));bpy.ops.render.render(write_still=True);print('RENDERED '+name,flush=True)
scene.camera=bpy.data.objects['Bend'];scene['source']='Exact Three.js river-scene.json';scene['width_m']=64;scene['length_m']=600
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=180;area.spaces.active.region_3d.view_location=(0,-40,0);area.spaces.active.clip_end=4000
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'青岚河.blend'),compress=True)
result={'status':'complete','engine':'CYCLES','device':scene.cycles.device,'blender_version':bpy.app.version_string,'samples':64,'resolution':[1800,1200],'views':list(views),'water':'closed absorbing volume, IOR 1.333'};(ROOT/'outputs/blender-result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('RIVER_RENDER_COMPLETE',flush=True)
