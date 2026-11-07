"""Executed by Blender through the project-local MCP stdio server."""
import bpy,json,sys,math,base64
import numpy as np
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];root=Path(args[0]);samples=int(args[1]) if len(args)>1 else 48;preview=len(args)>2 and args[2]=='preview'
data=json.loads((root/'outputs/scene.json').read_text(encoding='utf-8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
architecture=bpy.data.collections.new('Taoli_Galleria_Model');scene.collection.children.link(architecture)
materials={}
for uid,info in data['materials'].items():
    mat=bpy.data.materials.new(info['name']);mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*info['color'],1);bs.inputs['Roughness'].default_value=info['roughness'];bs.inputs['Metallic'].default_value=info['metalness']
    if info.get('emissive'):bs.inputs['Emission Color'].default_value=(*info['emissive'],1);bs.inputs['Emission Strength'].default_value=info['emissiveIntensity']
    if info['name'] in ('Shop glazing','Atrium skylight'):
        bs.inputs['Base Color'].default_value=(.72,.83,.81,1);bs.inputs['Roughness'].default_value=.12;bs.inputs['Metallic'].default_value=.04;bs.inputs['Transmission Weight'].default_value=.94;bs.inputs['IOR'].default_value=1.46
    if info['name'] in ('Reflecting water','Fountain water'):
        bs.inputs['Transmission Weight'].default_value=.58;bs.inputs['IOR'].default_value=1.333;bs.inputs['Roughness'].default_value=.1
    if info.get('texture'):
        path=root/'outputs'/('texture-'+uid+'.png');path.write_bytes(base64.b64decode(info['texture'].split(',')[1]));image=bpy.data.images.load(str(path));image.pack();tex=nodes.new('ShaderNodeTexImage');tex.image=image;multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1;multiply.inputs[2].default_value=(*info['color'],1);links.new(tex.outputs['Color'],multiply.inputs[1]);links.new(multiply.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
        if any(k in info['name'] for k in ('material',)):
            links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
    if 'Terracotta' in info['name'] or any(k in info['name'] for k in ('limestone','granite')):
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=110 if 'Terracotta' in info['name'] else 72;noise.inputs['Detail'].default_value=3
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.018;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    materials[uid]=mat
geometry={}
for uid,g in data['geometries'].items():
    vertices=np.array(g['p'],dtype=np.float32).reshape(-1,3);idx=np.array(g['idx'] if g['idx'] is not None else range(len(vertices)),dtype=np.int32).reshape(-1,3);uv=np.array(g['uv'],dtype=np.float32).reshape(-1,2) if g.get('uv') else None;geometry[uid]=(vertices,idx,uv)
groups={}
for ob in data['objects']:groups.setdefault(ob['m'],[]).append(ob)
for uid,items in groups.items():
    vertices=[];indices=[];uvs=[];offset=0
    for ob in items:
        p,idx,uv=geometry[ob['g']];a=np.array(ob['matrix'],dtype=np.float32).reshape((4,4),order='F');v=p@a[:3,:3].T+a[:3,3];v=np.stack((v[:,0],-v[:,2],v[:,1]),axis=1)
        vertices.append(v);indices.append(idx+offset);uvs.append(uv[idx].reshape(-1,2) if uv is not None else np.zeros((idx.size,2),dtype=np.float32));offset+=len(p)
    v=np.concatenate(vertices);idx=np.concatenate(indices);mesh=bpy.data.meshes.new(materials[uid].name+'_geometry');mesh.vertices.add(len(v));mesh.vertices.foreach_set('co',v.ravel());mesh.loops.add(idx.size);mesh.loops.foreach_set('vertex_index',idx.ravel());mesh.polygons.add(len(idx));mesh.polygons.foreach_set('loop_start',np.arange(len(idx),dtype=np.int32)*3);mesh.polygons.foreach_set('loop_total',np.full(len(idx),3,dtype=np.int32));mesh.update()
    uv=mesh.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.concatenate(uvs).ravel());mesh.materials.append(materials[uid]);obj=bpy.data.objects.new(materials[uid].name,mesh);architecture.objects.link(obj)
    if any(k in obj.name for k in ('Leaf','Visitor','Tree','water')):
        for poly in mesh.polygons:poly.use_smooth=True
    print('Imported',obj.name,len(v),'vertices',flush=True)
def material(name,color,rough=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;return m
bpy.ops.mesh.primitive_plane_add(size=5000,location=(0,0,-.185));ground=bpy.context.object;ground.name='Photography_ground';ground.data.materials.append(material('Warm_studio_ground',(.63,.61,.55)))
world=bpy.data.worlds.new('Soft_afternoon_sky');world.use_nodes=True;scene.world=world;nodes=world.node_tree.nodes;links=world.node_tree.links;sky=nodes.new('ShaderNodeTexSky');sky.sky_type='SINGLE_SCATTERING' if 'SINGLE_SCATTERING' in sky.bl_rna.properties['sky_type'].enum_items.keys() else 'NISHITA';sky.sun_elevation=math.radians(38);sky.sun_rotation=math.radians(140);sky.altitude=.15;sky.air_density=1.1;setattr(sky,'aerosol_density' if hasattr(sky,'aerosol_density') else 'dust_density',.35);links.new(sky.outputs['Color'],nodes.get('Background').inputs['Color']);nodes.get('Background').inputs['Strength'].default_value=.32
def area(name,pos,target,energy,color,size):
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
sky.sun_disc=False;nodes.get('Background').inputs['Strength'].default_value=.18
key=area('Soft_sun_key',(-65,-70,95),(0,0,8),65000,(1,.83,.65),28)
fill=area('Cool_sky_fill',(55,-25,75),(0,0,10),40000,(.72,.85,1),65)
bpy.ops.object.light_add(type='SUN',location=(-65,-70,95));sun=bpy.context.object;sun.name='Warm_afternoon_sun';sun.data.energy=1.8;sun.data.angle=.14;sun.data.color=(1,.86,.7);sun.rotation_euler=(Vector((0,0,0))-sun.location).to_track_quat('-Z','Y').to_euler()
interior=[]
for x,y,z in [(-27,-20,3.7),(27,-24,3.7),(0,-20,9),(0,5,19)]:
    bpy.ops.object.light_add(type='POINT',location=(x,y,z));o=bpy.context.object;o.name='Warm_shop_interior';o.data.energy=95;o.data.color=(1,.69,.39);o.data.shadow_soft_size=1.5;interior.append(o)
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='Mall_architectural_camera';scene.camera=camera;camera.data.clip_end=8000;camera.data.lens=48;camera.data.sensor_fit='HORIZONTAL';camera.data.sensor_width=36
def frame(pos,target,lens=48):camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
scene.render.engine='CYCLES';scene.cycles.samples=samples;scene.cycles.use_denoising=True;scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8;scene.cycles.transparent_max_bounces=10
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU';print('CYCLES',scene.cycles.device,flush=True)
except Exception as e:print('CPU fallback',e,flush=True)
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100;scene.render.fps=24;scene.frame_start=1;scene.frame_end=120;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.25
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
for f,pos in [(1,(140,-170,115)),(60,(185,-105,90)),(120,(170,60,110))]:frame(pos,(0,0,10),48);camera.keyframe_insert(data_path='location',frame=f);camera.keyframe_insert(data_path='rotation_euler',frame=f)
scene.frame_set(1);scene.render.resolution_x=1920;scene.render.resolution_y=1440
scene['source']='Same Three.js geometry exported from mall HTML';scene['parcel_metres']=112;scene['model']='Taoli Galleria';scene['animation']='Camera orbit keyframes; interactive procedures remain in HTML/module'
blend=root/'陶里汇商城.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));camera.animation_data_clear()
shots=[('blender-overview',(140,-170,115),(0,0,0),48,1920,1440),('blender-entry',(51,-96,18),(0,-8,12),40,1920,1280),('blender-terrace',(73,-61,55),(4,0,15),47,1920,1440),('blender-hero-8k',(135,-175,108),(0,0,2),48,7680,4320)]
if preview:shots=[('blender-preview',(140,-170,115),(0,0,0),48,1440,1080)]
for name,pos,target,lens,w,h in shots:
    frame(pos,target,lens);scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(root/'outputs'/(name+'.png'));print('RENDER',name,w,h,flush=True);bpy.ops.render.render(write_still=True)
# A final twilight render uses the same geometry with changed environment and shop illumination.
sky.sun_elevation=math.radians(-4);nodes.get('Background').inputs['Strength'].default_value=.16;key.data.energy=9000;key.data.color=(.5,.65,1);fill.data.energy=45000;sun.data.energy=.06;sun.data.color=(.62,.75,1);scene.view_settings.exposure=.55
for o in interior:o.data.energy=700
for m in materials.values():
    if any(k in m.name for k in ('light','material')):
        m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=2.4 if 'light' in m.name else .7
frame((130,-175,88),(0,0,11),48);scene.render.resolution_x=1920;scene.render.resolution_y=1280;scene.render.filepath=str(root/'outputs/blender-twilight.png');bpy.ops.render.render(write_still=True)
summary={'status':'complete','preview':preview,'blend':str(blend),'engine':'CYCLES','samples':samples,'device':scene.cycles.device,'renders':[str(root/'outputs'/(s[0]+'.png')) for s in shots]+[str(root/'outputs/blender-twilight.png')],'hero_pixels':None if preview else [7680,4320],'camera_animation_frames':120,'geometry_objects':len(data['objects'])}
(root/'outputs/blender-result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print('COMPLETE',json.dumps(summary,ensure_ascii=True),flush=True)


