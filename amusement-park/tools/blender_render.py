"""Executed by Blender through the project-local MCP stdio server."""
import bpy,json,sys,math,base64
import numpy as np
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];root=Path(args[0]);samples=int(args[1]) if len(args)>1 else 48;preview=len(args)>2 and args[2]=='preview'
data=json.loads((root/'outputs/scene.json').read_text(encoding='utf-8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
architecture=bpy.data.collections.new('Amusement_Park_Model');scene.collection.children.link(architecture)
materials={}
for uid,info in data['materials'].items():
    mat=bpy.data.materials.new(info['name']);mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*info['color'],info.get('opacity',1));bs.inputs['Roughness'].default_value=info['roughness'];bs.inputs['Metallic'].default_value=info['metalness'];bs.inputs['Coat Weight'].default_value=info.get('clearcoat',0);bs.inputs['Coat Roughness'].default_value=.14;bs.inputs['IOR'].default_value=info.get('ior',1.46)
    if info.get('emissive'):bs.inputs['Emission Color'].default_value=(*info['emissive'],1);bs.inputs['Emission Strength'].default_value=info['emissiveIntensity']
    if info['name']=='Cabin glazing':
        bs.inputs['Base Color'].default_value=(.72,.83,.81,1);bs.inputs['Roughness'].default_value=.12;bs.inputs['Metallic'].default_value=.04;bs.inputs['Transmission Weight'].default_value=.94;bs.inputs['IOR'].default_value=1.46
    if info['name'] in ('Reflecting water','Fountain water'):
        bs.inputs['Transmission Weight'].default_value=.58;bs.inputs['IOR'].default_value=1.333;bs.inputs['Roughness'].default_value=.1
    if info.get('texture'):
        path=root/'outputs'/('texture-'+uid+'.png');path.write_bytes(base64.b64decode(info['texture'].split(',')[1]));image=bpy.data.images.load(str(path));image.pack();tex=nodes.new('ShaderNodeTexImage');tex.image=image;multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1;multiply.inputs[2].default_value=(*info['color'],1);links.new(tex.outputs['Color'],multiply.inputs[1]);links.new(multiply.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
        if any(k in info['name'] for k in ('material',)):
            links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
    if any(k in info['name'].lower() for k in ('concrete','granite','paving','precast')):
        coord=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=80;noise.inputs['Detail'].default_value=3;links.new(coord.outputs['Object'],noise.inputs['Vector'])
        bevel=nodes.new('ShaderNodeBevel');bevel.inputs['Radius'].default_value=.015;bevel.samples=3
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0015;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bevel.outputs['Normal'],bump.inputs['Normal']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    if 'flag' in info['name'].lower():
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=480;noise.inputs['Detail'].default_value=2;bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0006;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal']);bs.inputs['Sheen Weight'].default_value=.3
    materials[uid]=mat
geometry={}
for uid,g in data['geometries'].items():
    vertices=np.array(g['p'],dtype=np.float32).reshape(-1,3);idx=np.array(g['idx'] if g['idx'] is not None else range(len(vertices)),dtype=np.int32).reshape(-1,3);uv=np.array(g['uv'],dtype=np.float32).reshape(-1,2) if g.get('uv') else None;geometry[uid]=(vertices,idx,uv)
groups={}
for ob in data['objects']:groups.setdefault((ob.get('part','architecture'),ob['m']),[]).append(ob)
for (part,uid),items in groups.items():
    vertices=[];indices=[];uvs=[];offset=0
    for ob in items:
        p,idx,uv=geometry[ob['g']];a=np.array(ob['matrix'],dtype=np.float32).reshape((4,4),order='F');v=p@a[:3,:3].T+a[:3,3];v=np.stack((v[:,0],-v[:,2],v[:,1]),axis=1)
        vertices.append(v);indices.append(idx+offset);uvs.append(uv[idx].reshape(-1,2) if uv is not None else np.zeros((idx.size,2),dtype=np.float32));offset+=len(p)
    v=np.concatenate(vertices);idx=np.concatenate(indices);mesh=bpy.data.meshes.new(materials[uid].name+'_geometry');mesh.vertices.add(len(v));mesh.vertices.foreach_set('co',v.ravel());mesh.loops.add(idx.size);mesh.loops.foreach_set('vertex_index',idx.ravel());mesh.polygons.add(len(idx));mesh.polygons.foreach_set('loop_start',np.arange(len(idx),dtype=np.int32)*3);mesh.polygons.foreach_set('loop_total',np.full(len(idx),3,dtype=np.int32));mesh.update()
    uv=mesh.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.concatenate(uvs).ravel());mesh.materials.append(materials[uid]);obj=bpy.data.objects.new(part+' / '+materials[uid].name,mesh);collection=bpy.data.collections.get(part)
    if collection is None:collection=bpy.data.collections.new(part);architecture.children.link(collection)
    collection.objects.link(obj)
    if any(k in obj.name for k in ('leaves','flag cloth','flag red')):
        for poly in mesh.polygons:poly.use_smooth=True
    print('Imported',obj.name,len(v),'vertices',flush=True)

# The photography environment is a separate collection, excluded from the asset.
studio=bpy.data.collections.new('Photography_Environment');scene.collection.children.link(studio)
def move_studio(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    studio.objects.link(o)
def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.94;return m
bpy.ops.mesh.primitive_plane_add(size=5000,location=(0,0,-.31));ground=bpy.context.object;ground.name='Studio ground';ground.data.materials.append(material('Soft neutral ground',(.57,.60,.57)));move_studio(ground)
world=bpy.data.worlds.new('Soft morning sky');world.use_nodes=True;scene.world=world;nodes=world.node_tree.nodes;links=world.node_tree.links
sky=nodes.new('ShaderNodeTexSky');sky.sky_type='SINGLE_SCATTERING' if 'SINGLE_SCATTERING' in sky.bl_rna.properties['sky_type'].enum_items.keys() else 'NISHITA';sky.sun_elevation=math.radians(48);sky.sun_rotation=math.radians(140);sky.sun_disc=False;sky.air_density=1.1;setattr(sky,'aerosol_density' if hasattr(sky,'aerosol_density') else 'dust_density',.3);links.new(sky.outputs['Color'],nodes.get('Background').inputs['Color']);nodes.get('Background').inputs['Strength'].default_value=.12
bpy.ops.object.light_add(type='SUN',location=(-75,-65,65));sun=bpy.context.object;sun.name='Morning sunlight';sun.data.energy=2.6;sun.data.angle=.12;sun.data.color=(1,.91,.78);sun.rotation_euler=(Vector((0,0,0))-sun.location).to_track_quat('-Z','Y').to_euler();move_studio(sun)
bpy.ops.object.light_add(type='AREA',location=(40,-20,70));fill=bpy.context.object;fill.name='Cool sky fill';fill.data.energy=18000;fill.data.shape='DISK';fill.data.size=65;fill.data.color=(.88,.94,1);fill.rotation_euler=(Vector((0,0,10))-fill.location).to_track_quat('-Z','Y').to_euler();move_studio(fill)
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='Park architectural camera';camera.data.clip_end=8000;camera.data.sensor_fit='HORIZONTAL';camera.data.sensor_width=36;scene.camera=camera;move_studio(camera)
def frame(position,target,lens):camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
engines=[e.identifier for e in scene.render.bl_rna.properties['engine'].enum_items];print('AVAILABLE_ENGINES',engines,flush=True)
scene.render.engine='CYCLES';scene.cycles.samples=samples;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.018;scene.cycles.adaptive_min_samples=16;scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=6
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.2
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
scene['source']='Same reviewed Three.js amusement park geometry, including flag pose and embedded textures';scene['units']='metres';scene['parcel']=112;scene['interactive_animation']='Cloth, wind and day/night are driven by HTML/module; Blender contains the exported cloth pose.'
shots=[('blender-overview',(135,-170,115),(0,0,8),48,3840,2880),('blender-wheel',(-3,-86,42),(-29,0,21),48,1920,1440),('blender-coaster',(100,125,70),(0,33,9),48,1920,1280),('blender-carousel',(22,-30,16),(3,-4,5),48,1920,1280),('blender-pirate',(64,-36,26),(31,-9,10),48,1920,1280)]
if preview:shots=shots[:1]
frame(*shots[0][1:4]);scene.render.resolution_x=shots[0][4];scene.render.resolution_y=shots[0][5];blend=root/'晴空游乐园.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for name,pos,target,lens,w,h in shots:
    frame(pos,target,lens);scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(root/'outputs'/(name+'.png'));print('RENDER',name,w,h,scene.cycles.device,flush=True);bpy.ops.render.render(write_still=True)
# Night photography uses the same exported meshes and real local illumination.
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.025;sun.data.energy=.05;sun.data.color=(.6,.76,1);fill.data.energy=12000;fill.data.color=(.5,.7,1);scene.view_settings.exposure=.6
for material in materials.values():
 if material.name=='Warm park lighting':material.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=5
for x,z in [(-49,-8),(-49,17),(-49,43),(49,-8),(49,17),(49,43),(14,34),(-12,39)]:
 bpy.ops.object.light_add(type='POINT',location=(x,-z,5.1));lamp=bpy.context.object;lamp.data.energy=1100;lamp.data.color=(1,.73,.42);lamp.data.shadow_soft_size=.4;move_studio(lamp)
for pos,color in [((-29,-2,20),(.4,.8,1)),((3,-4,7),(1,.45,.25)),((31,-9,12),(.4,.8,1))]:
 bpy.ops.object.light_add(type='POINT',location=pos);lamp=bpy.context.object;lamp.data.energy=1600;lamp.data.color=color;lamp.data.shadow_soft_size=2;move_studio(lamp)
frame((135,-170,115),(0,0,8),48);scene.render.resolution_x=1920;scene.render.resolution_y=1440;scene.render.filepath=str(root/'outputs/blender-night.png');bpy.ops.render.render(write_still=True)
summary={'status':'complete','blend':str(blend),'engine':'CYCLES','samples':samples,'device':scene.cycles.device,'renders':[str(root/'outputs'/(s[0]+'.png')) for s in shots]+[str(root/'outputs/blender-night.png')],'geometry_objects':len(data['objects'])}
(root/'outputs/blender-result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',json.dumps(summary,ensure_ascii=True),flush=True)
