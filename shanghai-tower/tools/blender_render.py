"""Blender-side geometry import and Cycles render. Receives project paths from MCP."""
import bpy,json,sys,math,base64
import numpy as np
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];root=Path(args[0]);samples=int(args[1]) if len(args)>1 else 48
data=json.loads((root/'outputs/scene.json').read_text(encoding='utf-8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
collection=bpy.data.collections.new('Shanghai_Tower_Architecture_and_Plaza');scene.collection.children.link(collection)
materials={}
for uid,info in data['materials'].items():
    mat=bpy.data.materials.new(info['name']);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*info['color'],1);bs.inputs['Roughness'].default_value=info['roughness'];bs.inputs['Metallic'].default_value=info['metalness']
    if info.get('emissive'):
        bs.inputs['Emission Color'].default_value=(*info['emissive'],1);bs.inputs['Emission Strength'].default_value=info['emissiveIntensity']
    if info['name']=='Outer glass':
        bs.inputs['Base Color'].default_value=(.72,.85,.93,1);bs.inputs['Metallic'].default_value=.08;bs.inputs['Transmission Weight'].default_value=.94;bs.inputs['IOR'].default_value=1.45;bs.inputs['Roughness'].default_value=.14
    if info.get('texture'):
        path=root/'outputs'/('texture-'+uid+'.png');path.write_bytes(base64.b64decode(info['texture'].split(',')[1]));image=bpy.data.images.load(str(path));image.pack();texture=mat.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image;mat.node_tree.links.new(texture.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(texture.outputs['Alpha'],bs.inputs['Alpha'])
    if info['name']=='Pale stone':
        nodes=mat.node_tree.nodes;noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=90;noise.inputs['Detail'].default_value=2
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.018;mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    materials[uid]=mat
geometry={}
for uid,g in data['geometries'].items():
    vertices=np.array(g['p'],dtype=np.float32).reshape(-1,3);indices=np.array(g['idx'] if g['idx'] is not None else range(len(vertices)),dtype=np.int32).reshape(-1,3);uv=np.array(g['uv'],dtype=np.float32).reshape(-1,2) if g.get('uv') else None
    geometry[uid]=(vertices,indices,uv)
groups={}
for ob in data['objects']:groups.setdefault(ob['m'],[]).append(ob)
for uid,items in groups.items():
    vertices=[];indices=[];uvs=[];offset=0
    for ob in items:
        p,idx,uv=geometry[ob['g']];a=np.array(ob['matrix'],dtype=np.float32).reshape((4,4),order='F');v=p@a[:3,:3].T+a[:3,3];v=np.stack((v[:,0],-v[:,2],v[:,1]),axis=1)
        vertices.append(v);indices.append(idx+offset);uvs.append(uv[idx].reshape(-1,2) if uv is not None else np.zeros((idx.size,2),dtype=np.float32));offset+=len(p)
    v=np.concatenate(vertices);idx=np.concatenate(indices);mesh=bpy.data.meshes.new(materials[uid].name+'_geometry');mesh.vertices.add(len(v));mesh.vertices.foreach_set('co',v.ravel());mesh.loops.add(idx.size);mesh.loops.foreach_set('vertex_index',idx.ravel());mesh.polygons.add(len(idx));mesh.polygons.foreach_set('loop_start',np.arange(len(idx),dtype=np.int32)*3);mesh.polygons.foreach_set('loop_total',np.full(len(idx),3,dtype=np.int32));mesh.update()
    uv=mesh.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.concatenate(uvs).ravel());mesh.materials.append(materials[uid]);obj=bpy.data.objects.new(materials[uid].name,mesh);collection.objects.link(obj)
    if materials[uid].name in ('Outer glass','Inner glass'):
        for polygon in mesh.polygons:polygon.use_smooth=True
    if materials[uid].name=='Outer glass':
        modifier=obj.modifiers.new('Physical glass thickness','SOLIDIFY');modifier.thickness=.012
    print('Imported',obj.name,len(v),'vertices',flush=True)

def simple_material(name,color,metal=0,rough=.5):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;return m
bpy.ops.mesh.primitive_plane_add(size=10000,location=(0,0,-.2));bpy.context.object.name='Photography ground';background_mat=simple_material('Blue hour ground',(.025,.055,.09),.1,.7);bpy.context.object.data.materials.append(background_mat)
# Camera-distance studio fade joins the ground into the world without a hard horizon.
nodes=background_mat.node_tree.nodes;links=background_mat.node_tree.links;camera_data=nodes.new('ShaderNodeCameraData');fade=nodes.new('ShaderNodeMapRange');fade.inputs['From Min'].default_value=280;fade.inputs['From Max'].default_value=1500;fade.clamp=True;links.new(camera_data.outputs['View Distance'],fade.inputs['Value']);emission=nodes.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(.044,.088,.16,1);emission.inputs['Strength'].default_value=1;mix=nodes.new('ShaderNodeMixShader');links.new(fade.outputs['Result'],mix.inputs[0]);links.new(nodes.get('Principled BSDF').outputs['BSDF'],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
world=bpy.data.worlds.new('Blue hour Shanghai');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.11,.22,.4,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.4;scene.world=world
def area(name,pos,target,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.name=name;ob.data.energy=power;ob.data.color=color;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
area('Cool architectural key',(40,-60,105),(0,0,50),125000,(.64,.81,1),70)
area('Silver side reflection',(-55,-15,65),(0,0,55),160000,(.8,.9,1),60)
area('Warm horizon accent',(-65,35,25),(0,0,40),65000,(1,.59,.3),45)
area('Crown rim',(30,35,105),(0,0,90),100000,(.48,.69,1),35)
# Subtle real volume around the crown, separated from the exported landmark.
bpy.ops.mesh.primitive_cube_add(size=1,location=(-8,4,98));cloud=bpy.context.object;cloud.name='Crown passing thin cloud';cloud.scale=(55,35,10)
cloudmat=bpy.data.materials.new('Cloud density volume');cloudmat.use_nodes=True;nodes=cloudmat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');volume=nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Color'].default_value=(.6,.7,.82,1);volume.inputs['Anisotropy'].default_value=.3;noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.2;noise.inputs['Detail'].default_value=3;ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.53;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(.02,.02,.02,1);cloudmat.node_tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac']);cloudmat.node_tree.links.new(ramp.outputs['Color'],volume.inputs['Density']);cloudmat.node_tree.links.new(volume.outputs['Volume'],out.inputs['Volume']);cloud.data.materials.append(cloudmat)
# Feather the volume boundary; its bounding cube must never become a visible rectangle.
coord=nodes.new('ShaderNodeTexCoord');subtract=nodes.new('ShaderNodeVectorMath');subtract.operation='SUBTRACT';subtract.inputs[1].default_value=(.5,.5,.5);length=nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=2.3;inverse=nodes.new('ShaderNodeMath');inverse.operation='SUBTRACT';inverse.inputs[0].default_value=1;inverse.use_clamp=True;density_product=nodes.new('ShaderNodeMath');density_product.operation='MULTIPLY';cloudmat.node_tree.links.new(coord.outputs['Generated'],subtract.inputs[0]);cloudmat.node_tree.links.new(subtract.outputs['Vector'],length.inputs[0]);cloudmat.node_tree.links.new(length.outputs['Value'],multiply.inputs[0]);cloudmat.node_tree.links.new(multiply.outputs[0],inverse.inputs[1]);cloudmat.node_tree.links.new(inverse.outputs[0],density_product.inputs[0]);cloudmat.node_tree.links.new(ramp.outputs['Color'],density_product.inputs[1]);cloudmat.node_tree.links.new(density_product.outputs[0],volume.inputs['Density'])
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='Architectural_Camera';scene.camera=camera;camera.data.clip_end=15000;camera.data.sensor_fit='VERTICAL';camera.data.sensor_height=36
def frame(position,target,lens):camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
scene.render.engine='CYCLES';scene.cycles.samples=samples;scene.cycles.use_denoising=True;scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=6;scene.cycles.transparent_max_bounces=8;scene.cycles.volume_bounces=1
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU';print('CYCLES',scene.cycles.device,flush=True)
except Exception as e:print('CPU fallback',e,flush=True)
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.3
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
scene.render.fps=24;scene.frame_start=1;scene.frame_end=96
for f,pos in [(1,(160,-200,145)),(48,(200,-120,125)),(96,(220,-30,115))]:frame(pos,(0,0,43),42);camera.keyframe_insert(data_path='location',frame=f);camera.keyframe_insert(data_path='rotation_euler',frame=f)
scene.frame_set(1);scene.render.resolution_x=1800;scene.render.resolution_y=1350
scene['nominalHeight']=632;scene['displayHeight']=96;scene['footprint']=112;scene['source']='Same Three.js geometry exported by Shanghai Tower HTML';scene['license_note']='Architectural interpretation, not measured BIM.'
blend=root/'上海中心.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
shots=[('blender-overview',(160,-200,145),(0,0,43),42,1800,1350),('blender-facade',(25,-32,58),(0,0,54),50,1600,1400),('blender-entry',(30,-46,12),(0,-10,3),46,1800,1200),('blender-crown',(24,-33,102),(0,0,92),45,1600,1400),('blender-hero-8k',(48,-70,9),(0,0,55),24,4320,7680)]
camera.animation_data_clear()
for name,pos,target,lens,w,h in shots:
    frame(pos,target,lens);scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(root/'outputs'/(name+'.png'));print('RENDER',name,w,h,flush=True);bpy.ops.render.render(write_still=True)
summary={'status':'complete','blend':str(blend),'engine':'CYCLES','samples':samples,'renders':[str(root/'outputs'/(shot[0]+'.png')) for shot in shots],'hero_pixels':[4320,7680],'camera_animation_frames':96,'device':scene.cycles.device}
(root/'outputs/blender-result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print('COMPLETE',json.dumps(summary,ensure_ascii=True),flush=True)
