"""Executed through the existing local Blender MCP. Creates a new scene, preserves all existing scenes."""
import bpy,json,math,base64,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\33864\Desktop\千人小镇\hospital-campus')
DATA=json.loads((ROOT/'outputs/hospital-scene.json').read_text(encoding='utf-8'))
scene=bpy.data.scenes.new('CH_Hospital_Final');bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
collection=bpy.data.collections.new('Hospital model only');scene.collection.children.link(collection)
studio=bpy.data.collections.new('Presentation - not part of city module');scene.collection.children.link(studio)
campus=bpy.data.objects.new('hospital-campus',None);collection.objects.link(campus);campus['width_m']=112;campus['depth_m']=112;campus['front']='+Z in Three.js / -Y in Blender'
owners={}
for b in DATA['manifest']['buildings']:
    empty=bpy.data.objects.new(b['id'],None);empty.location=(b['x'],-b['z'],0);empty.parent=campus;empty['id']=b['id'];empty['name_cn']=b['name'];collection.objects.link(empty);owners[b['id']]=empty
mats={}
for uid,m in DATA['materials'].items():
    mat=bpy.data.materials.new('CH_'+m['name']);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*m['color'],1);bs.inputs['Roughness'].default_value=m['roughness'];bs.inputs['Metallic'].default_value=m['metalness'];bs.inputs['Emission Color'].default_value=(*m['emissive'],1);bs.inputs['Emission Strength'].default_value=m['emissiveIntensity']
    if m['name'] in ['glass','glass-lit']:bs.inputs['Metallic'].default_value=.3;bs.inputs['Roughness'].default_value=.19
    if m.get('texture'):
        file=ROOT/'outputs'/('texture_'+uid+'.png');file.write_bytes(base64.b64decode(m['texture'].split(',')[1]));im=bpy.data.images.load(str(file));im.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT';uv=mat.node_tree.nodes.new('ShaderNodeTexCoord');mapping=mat.node_tree.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(*m.get('repeat',[1,1]),1);mat.node_tree.links.new(uv.outputs['UV'],mapping.inputs[0]);mat.node_tree.links.new(mapping.outputs['Vector'],tex.inputs['Vector']);mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if m['name'] in ['porcelain','warm-panel','stone','paving','asphalt','concrete']:
        noise=mat.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=40 if m['name']=='asphalt' else 24;bump=mat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.015;mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    mats[uid]=mat
geos={}
for uid,g in DATA['geometries'].items():
    p=np.array(g['positions'],dtype=np.float32).reshape((-1,3));idx=np.array(g['indices'] if g['indices'] is not None else np.arange(len(p)),dtype=np.int32).reshape((-1,3));uv=np.array(g['uv'],dtype=np.float32).reshape((-1,2)) if g.get('uv') else None;geos[uid]=(p,idx,uv)
groups={}
for o in DATA['objects']:groups.setdefault((o['owner'],o['m']),[]).append(o)
for (owner,mid),objects in groups.items():
    vertices=[];faces=[];uvs=[];offset=0;parent=owners.get(owner,campus)
    for o in objects:
        p,idx,uv=geos[o['g']];a=np.array(o['matrix'],dtype=np.float32).reshape((4,4),order='F');v=p@a[:3,:3].T+a[:3,3];v=np.stack((v[:,0],-v[:,2],v[:,1]),axis=1);v-=np.array(parent.location)
        vertices.append(v);faces.append(idx+offset);offset+=len(p);uvs.append(uv[idx].reshape((-1,2)) if uv is not None else np.zeros((idx.size,2),dtype=np.float32))
    v=np.concatenate(vertices);f=np.concatenate(faces);mesh=bpy.data.meshes.new(owner+'_'+mats[mid].name);mesh.vertices.add(len(v));mesh.vertices.foreach_set('co',v.ravel());mesh.loops.add(len(f)*3);mesh.loops.foreach_set('vertex_index',f.ravel());mesh.polygons.add(len(f));mesh.polygons.foreach_set('loop_start',np.arange(len(f),dtype=np.int32)*3);mesh.polygons.foreach_set('loop_total',np.full(len(f),3,dtype=np.int32));mesh.update();layer=mesh.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',np.concatenate(uvs).ravel());mesh.materials.append(mats[mid]);obj=bpy.data.objects.new(mesh.name,mesh);obj.parent=parent;collection.objects.link(obj)
    if DATA['materials'][mid]['name'] in ['leaf','leaf-light','bark','skin']:
        for poly in mesh.polygons:poly.use_smooth=True
    if DATA['materials'][mid]['name'] in ['porcelain','white-edge','concrete','warm-panel','metal']:
        bevel=obj.modifiers.new('Architectural edge highlights','BEVEL');bevel.width=.025;bevel.segments=2

def move_to_studio(obj):
    for old in list(obj.users_collection):old.objects.unlink(obj)
    studio.objects.link(obj)
world=bpy.data.worlds.new('Hospital soft daylight');world.use_nodes=True;scene.world=world;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.65,.78,.79,1);bg.inputs['Strength'].default_value=.5
sun_data=bpy.data.lights.new('Soft daylight','SUN');sun_data.energy=2.3;sun_data.angle=math.radians(3);sun_data.color=(1,.93,.8);sun=bpy.data.objects.new('Soft daylight',sun_data);studio.objects.link(sun);sun.location=(-100,-130,165);sun.rotation_euler=(-sun.location).to_track_quat('-Z','Y').to_euler()
back=bpy.data.materials.new('Studio pale sage');back.diffuse_color=(.68,.74,.66,1)
# Ground hole must extend through the presentation floor to keep the garage visible.
for xmin,xmax,ymin,ymax in [(-3500,-42,-3500,3500),(-28,3500,-3500,3500),(-42,-28,-3500,20),(-42,-28,40,3500)]:
    mesh=bpy.data.meshes.new('Backdrop');mesh.from_pydata([(xmin,ymin,-.62),(xmax,ymin,-.62),(xmax,ymax,-.62),(xmin,ymax,-.62)],[],[(0,1,2,3)]);obj=bpy.data.objects.new('Backdrop',mesh);mesh.materials.append(back);studio.objects.link(obj)
fog=bpy.data.materials.new('Morning participating medium');fog.use_nodes=True;fog.node_tree.nodes.clear();out=fog.node_tree.nodes.new('ShaderNodeOutputMaterial');volume=fog.node_tree.nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Density'].default_value=.00025;volume.inputs['Color'].default_value=(.8,.9,.84,1);volume.inputs['Anisotropy'].default_value=.3;fog.node_tree.links.new(volume.outputs['Volume'],out.inputs['Volume'])
mesh=bpy.data.meshes.new('Haze box');verts=[(x,y,z) for x in [-100,100] for y in [-100,100] for z in [-1,80]];mesh.from_pydata(verts,[],[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]);obj=bpy.data.objects.new('Haze volume',mesh);mesh.materials.append(fog);studio.objects.link(obj)
views={'Overview':([158,138,173],[0,12,0]),'Outpatient':([-2,21,78],[-28,8,29]),'Emergency':([74,28,76],[29,7,31]),'Garden':([46,37,53],[0,2,0]),'Roof':([57,89,-4],[0,32,-28]),'Garage':([-66,24,2],[-35,-1,-27])}
def cv(p):return Vector((p[0],-p[2],p[1]))
for name,(p,q) in views.items():
    cd=bpy.data.cameras.new(name);cam=bpy.data.objects.new(scene.name+'_'+name,cd);studio.objects.link(cam);cam.location=cv(p);cam.rotation_euler=(cv(q)-cam.location).to_track_quat('-Z','Y').to_euler();cd.sensor_fit='VERTICAL';cd.sensor_height=24;cd.lens=24/(2*math.tan(math.radians(35)/2));cd.clip_end=8000;scene['hospital_camera_'+name]=cam.name
scene.camera=scene.objects.get(scene['hospital_camera_Overview']);scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.max_bounces=6;scene.cycles.volume_bounces=1;scene.render.resolution_x=1920;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.1
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
scene['source']='hospital-scene.json / exact Three.js geometry';scene['width_m']=112;scene['depth_m']=112;scene['front_three_js']='+Z';scene['hospital_buildings']=4
bpy.data.libraries.write(str(ROOT/'澄和医院.blend'),{scene},fake_user=True)
print(json.dumps({'status':'imported','scene':scene.name,'objects':len(scene.objects),'model_batches':len(groups),'buildings':list(owners),'blend':str(ROOT/'澄和医院.blend')},ensure_ascii=False))
