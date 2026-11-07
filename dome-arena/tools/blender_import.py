"""Executed through the project-local Blender MCP. Creates a new scene, preserves all existing scenes."""
import bpy,json,math,base64,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'outputs/arena-scene.json').read_text(encoding='utf-8'))
scene=bpy.data.scenes.new('DOME_ARENA_Final');bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
collection=bpy.data.collections.new('Arena model only');scene.collection.children.link(collection)
studio=bpy.data.collections.new('Presentation - not part of city module');scene.collection.children.link(studio)
campus=bpy.data.objects.new('dome-arena',None);collection.objects.link(campus);campus['width_m']=112;campus['depth_m']=112;campus['front']='+Z in Three.js / -Y in Blender'
owners={}
for b in DATA['manifest']['buildings']:
    empty=bpy.data.objects.new(b['id'],None);empty.location=(0,0,0);empty.parent=campus;empty['id']=b['id'];empty['name_cn']=b['name'];collection.objects.link(empty);owners[b['id']]=empty
mats={}
for uid,m in DATA['materials'].items():
    mat=bpy.data.materials.new('ARENA_'+m['name']);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*m['color'],1);bs.inputs['Roughness'].default_value=m['roughness'];bs.inputs['Metallic'].default_value=m['metalness'];bs.inputs['Emission Color'].default_value=(*m['emissive'],1);bs.inputs['Emission Strength'].default_value=m['emissiveIntensity']
    if m['name'].startswith(('glass-','office-lit-')):
        bs.inputs['Coat Weight'].default_value=1;bs.inputs['Coat Roughness'].default_value=.07;bs.inputs['Transmission Weight'].default_value=.12;bs.inputs['IOR'].default_value=1.45
    if m['name'] in ['glass','skylight']:
        bs.inputs['Transmission Weight'].default_value=.78;bs.inputs['Metallic'].default_value=.05;bs.inputs['IOR'].default_value=1.45;bs.inputs['Roughness'].default_value=.09
    if m.get('texture'):
        file=ROOT/'outputs'/('texture_'+uid+'.png');file.write_bytes(base64.b64decode(m['texture'].split(',')[1]));im=bpy.data.images.load(str(file));im.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT';uv=mat.node_tree.nodes.new('ShaderNodeTexCoord');mapping=mat.node_tree.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(*m.get('repeat',[1,1]),1);mat.node_tree.links.new(uv.outputs['UV'],mapping.inputs[0]);mat.node_tree.links.new(mapping.outputs['Vector'],tex.inputs['Vector']);mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if m['name'] in ['stone','paving','asphalt']:
        noise=mat.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=40 if m['name']=='asphalt' else 24;bump=mat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.015;mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    mats[uid]=mat
geos={}
for uid,g in DATA['geometries'].items():
    p=np.array(g['positions'],dtype=np.float32).reshape((-1,3));idx=np.array(g['indices'] if g['indices'] is not None else np.arange(len(p)),dtype=np.int32).reshape((-1,3));uv=np.array(g['uv'],dtype=np.float32).reshape((-1,2)) if g.get('uv') else None;geos[uid]=(p,idx,uv)
groups={}
for o in DATA['objects']:groups.setdefault((o['owner'],o['m']),[]).append(o)
for owner in ['site','structure','roof','interior','landscape','lights','life']:
    empty=bpy.data.objects.new(owner,None);empty.parent=campus;collection.objects.link(empty);owners[owner]=empty
for (owner,mid),objects in groups.items():
    vertices=[];faces=[];uvs=[];offset=0;parent=owners.get(owner,campus)
    for o in objects:
        p,idx,uv=geos[o['g']];a=np.array(o['matrix'],dtype=np.float32).reshape((4,4),order='F');v=p@a[:3,:3].T+a[:3,3];v=np.stack((v[:,0],-v[:,2],v[:,1]),axis=1);v-=np.array(parent.location)
        vertices.append(v);faces.append(idx+offset);offset+=len(p);uvs.append(uv[idx].reshape((-1,2)) if uv is not None else np.zeros((idx.size,2),dtype=np.float32))
    v=np.concatenate(vertices);f=np.concatenate(faces);mesh=bpy.data.meshes.new(owner+'_'+mats[mid].name);mesh.vertices.add(len(v));mesh.vertices.foreach_set('co',v.ravel());mesh.loops.add(len(f)*3);mesh.loops.foreach_set('vertex_index',f.ravel());mesh.polygons.add(len(f));mesh.polygons.foreach_set('loop_start',np.arange(len(f),dtype=np.int32)*3);mesh.polygons.foreach_set('loop_total',np.full(len(f),3,dtype=np.int32));mesh.update();layer=mesh.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',np.concatenate(uvs).ravel());mesh.materials.append(mats[mid]);obj=bpy.data.objects.new(mesh.name,mesh);obj.parent=parent;collection.objects.link(obj)
    if DATA['materials'][mid]['name'] in ['leaf','leaf-light','sage','wood','skin'] or DATA['materials'][mid]['name'].startswith('silver-'):
        for poly in mesh.polygons:poly.use_smooth=True
    if DATA['materials'][mid]['name'] in ['copper','steel','stone','warm-stone']:
        bevel=obj.modifiers.new('Architectural edge highlights','BEVEL');bevel.width=.025;bevel.segments=2

def move_to_studio(obj):
    for old in list(obj.users_collection):old.objects.unlink(obj)
    studio.objects.link(obj)
world=bpy.data.worlds.new('Arena daylight with procedural clouds');world.use_nodes=True;scene.world=world
nodes=world.node_tree.nodes;links=world.node_tree.links;bg=nodes.get('Background');bg.inputs['Strength'].default_value=.4
sky=nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(32);sky.sun_rotation=math.radians(135);sky.sun_disc=False;sky.altitude=.1
coord=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=4;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.7;links.new(coord.outputs['Normal'],noise.inputs['Vector'])
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.47;ramp.color_ramp.elements[1].position=.67;links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(1.1,1.16,1.2,1);links.new(ramp.outputs['Color'],mix.inputs[0]);links.new(sky.outputs['Color'],mix.inputs[1]);links.new(mix.outputs['Color'],bg.inputs['Color'])
sun_data=bpy.data.lights.new('Soft daylight','SUN');sun_data.energy=2.8;sun_data.angle=math.radians(3);sun_data.color=(1,.93,.8);sun=bpy.data.objects.new('Soft daylight',sun_data);studio.objects.link(sun);sun.location=(-180,-180,280);sun.rotation_euler=(-sun.location).to_track_quat('-Z','Y').to_euler()
back=bpy.data.materials.new('Studio pale sage');back.diffuse_color=(.62,.68,.7,1)
# The presentation backdrop is separate from the model collection.
for xmin,xmax,ymin,ymax in [(-10000,10000,-10000,10000)]:
    mesh=bpy.data.meshes.new('Backdrop');mesh.from_pydata([(xmin,ymin,-.62),(xmax,ymin,-.62),(xmax,ymax,-.62),(xmin,ymax,-.62)],[],[(0,1,2,3)]);obj=bpy.data.objects.new('Backdrop',mesh);mesh.materials.append(back);studio.objects.link(obj)
fog=bpy.data.materials.new('Morning participating medium');fog.use_nodes=True;fog.node_tree.nodes.clear();out=fog.node_tree.nodes.new('ShaderNodeOutputMaterial');volume=fog.node_tree.nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Density'].default_value=.00012;volume.inputs['Color'].default_value=(.8,.9,.84,1);volume.inputs['Anisotropy'].default_value=.3;fog.node_tree.links.new(volume.outputs['Volume'],out.inputs['Volume'])
mesh=bpy.data.meshes.new('Haze box');verts=[(x,y,z) for x in [-100,100] for y in [-100,100] for z in [-1,65]];mesh.from_pydata(verts,[],[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]);obj=bpy.data.objects.new('Haze volume',mesh);mesh.materials.append(fog);studio.objects.link(obj)
views={'Overview':([150,125,170],[0,10,0],37),'Low':([85,10,100],[0,18,-6],43),'Entrance':([53,26,94],[0,9,26],43),'Structure':([95,87,108],[0,12,-6],43),'Interior':([28,39,43],[0,5,-6],65),'Roof':([60,105,78],[0,21,-6],43)}

def cv(p):return Vector((p[0],-p[2],p[1]))
for name,(p,q,fov) in views.items():
    cd=bpy.data.cameras.new(name);cam=bpy.data.objects.new(scene.name+'_'+name,cd);studio.objects.link(cam);cam.location=cv(p);cam.rotation_euler=(cv(q)-cam.location).to_track_quat('-Z','Y').to_euler();cd.sensor_fit='VERTICAL';cd.sensor_height=24;cd.lens=24/(2*math.tan(math.radians(fov)/2));cd.clip_end=8000;scene['arena_camera_'+name]=cam.name
scene.camera=scene.objects.get(scene['arena_camera_Overview']);scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.cycles.max_bounces=6;scene.cycles.volume_bounces=1;scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.1
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
scene['source']='arena-scene.json / exact Three.js geometry';scene['width_m']=112;scene['depth_m']=112;scene['front_three_js']='+Z';scene['arena_components']=8
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'穹光体育中心.blend'),compress=True)
print(json.dumps({'status':'imported','scene':scene.name,'objects':len(scene.objects),'model_batches':len(groups),'buildings':list(owners),'blend':str(ROOT/'穹光体育中心.blend')},ensure_ascii=False))
