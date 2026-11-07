import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
scene=next(s for s in bpy.data.scenes if s.name.startswith('SKYLINE_ONE_Final'));bpy.context.window.scene=scene
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.type=='OPTIX' for d in prefs.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1200
# Preserve cloud reflections while keeping the camera horizon clean and bright.
nodes=scene.world.node_tree.nodes;links=scene.world.node_tree.links;out=nodes.get('World Output');bg=nodes.get('Background');original=bg.inputs['Color'].links[0].from_socket
lightpath=nodes.new('ShaderNodeLightPath');safe=nodes.new('ShaderNodeMixRGB');safe.blend_type='LIGHTEN';safe.inputs[0].default_value=1;safe.inputs[2].default_value=(.54,.65,.75,1);links.new(original,safe.inputs[1])
cb=nodes.new('ShaderNodeBackground');cb.inputs['Strength'].default_value=.7;links.new(safe.outputs['Color'],cb.inputs['Color']);mix=nodes.new('ShaderNodeMixShader');links.new(lightpath.outputs['Is Camera Ray'],mix.inputs[0]);links.new(bg.outputs[0],mix.inputs[1]);links.new(cb.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
overview=bpy.data.objects[scene['skyline_camera_Overview']];overview.data.type='ORTHO';overview.data.ortho_scale=285
records=[]
for name in ['Overview','Low','Entrance','Roof','Terrace','Garage']:
    scene.camera=scene.objects.get(scene['skyline_camera_'+name]);scene.render.filepath=str(ROOT/'outputs'/('blender-'+name.lower()+'.png'))
    bpy.ops.render.render(write_still=True);records.append(name);print('RENDERED',name,flush=True)
    (ROOT/'outputs/blender-progress.json').write_text(json.dumps({'status':'rendering','completed':records},indent=2),encoding='utf8')
# A second lighting setup is saved as its own scene, sharing the precise model geometry.
existing=bpy.data.scenes.get('SKYLINE_ONE_Night')
if existing:bpy.data.scenes.remove(existing)
night=scene.copy();night.name='SKYLINE_ONE_Night';bpy.context.window.scene=night
night.world=scene.world.copy();night.world.name='Skyline night';bg=night.world.node_tree.nodes.get('Background')
for link in list(bg.inputs['Color'].links):night.world.node_tree.links.remove(link)
bg.inputs['Color'].default_value=(.025,.055,.1,1);bg.inputs['Strength'].default_value=.45
for node in night.world.node_tree.nodes:
    if node.type=='BACKGROUND' and node!=bg:
        for link in list(node.inputs['Color'].links):night.world.node_tree.links.remove(link)
        node.inputs['Color'].default_value=(.025,.055,.1,1);node.inputs['Strength'].default_value=.45
for obj in list(night.objects):
    if obj.type=='LIGHT':
        copy=obj.copy();copy.data=obj.data.copy();night.collection.objects.link(copy)
        def unlink_from_scene(obj,collection):
            if obj.name in collection.objects:collection.objects.unlink(obj)
            for child in collection.children:unlink_from_scene(obj,child)
        # The source lighting collection is linked to the daylight scene; hide its light by per-scene exclusion.
        copy.data.energy=.28;copy.data.color=(.58,.74,1.)
# Use a separate scene collection tree so daylight lights can be excluded without changing the source scene.
for layer in night.view_layers:
    for c in layer.layer_collection.children:
        if c.collection.name.startswith('Presentation - not part of city module'):c.exclude=True
night.camera=scene.objects.get(scene['skyline_camera_Overview'])
# Share presentation ground and camera with the night scene through explicit object links.
for obj in scene.objects:
    if obj.type=='CAMERA' or obj.name.startswith(('Backdrop','Haze volume')):
        if obj.name not in night.collection.objects:night.collection.objects.link(obj)
night_materials={}
model_collection=next(c for c in scene.collection.children if c.name.startswith('Skyline model only'))
night_model=bpy.data.collections.new('Night model geometry');night.collection.children.link(night_model)
for c in list(night.collection.children):
    if c==model_collection:night.collection.children.unlink(c)
for obj in model_collection.objects:
    cp=obj.copy();cp.parent=None;cp.matrix_world=obj.matrix_world.copy()
    if obj.type=='MESH':
        cp.data=obj.data.copy()
        for i,m in enumerate(cp.data.materials):
            if m.name not in night_materials:
                nm=m.copy();nm.name=m.name+'_Night';bs=nm.node_tree.nodes.get('Principled BSDF')
                if 'office-lit-' in m.name:bs.inputs['Emission Strength'].default_value=2
                if 'lamp' in m.name:bs.inputs['Emission Strength'].default_value=5
                if 'beacon' in m.name:bs.inputs['Emission Strength'].default_value=2
                night_materials[m.name]=nm
            cp.data.materials[i]=night_materials[m.name]
    night_model.objects.link(cp)
for x,y,z in [(0,-26,4),(-21,-23,4),(21,-23,4),(25,-49,2)]:
    data=bpy.data.lights.new('Night plaza pool','AREA');data.energy=350;data.color=(1,.68,.34);data.shape='DISK';data.size=5
    ob=bpy.data.objects.new(data.name,data);ob.location=(x,y,z);night.collection.objects.link(ob)
night.render.filepath=str(ROOT/'outputs/blender-night.png');bpy.ops.render.render(write_still=True);records.append('Night');print('RENDERED Night',flush=True)
# Retain a six-second editable camera movement in the daylight scene.
bpy.context.window.scene=scene;scene.camera=scene.objects.get(scene['skyline_camera_Overview']);scene.frame_start=1;scene.frame_end=144;scene.render.fps=24
camera=scene.camera
for f,a in [(1,.7),(72,.98),(144,1.25)]:
    camera.location=(math.sin(a)*495,-math.cos(a)*495,252);camera.rotation_euler=(Vector((0,3,108))-camera.location).to_track_quat('-Z','Y').to_euler();camera.keyframe_insert(data_path='location',frame=f);camera.keyframe_insert(data_path='rotation_euler',frame=f)
scene.frame_set(1)
bpy.data.libraries.write(str(ROOT/'云际中心.blend'),{scene,night},fake_user=True)
(ROOT/'outputs/blender-result.json').write_text(json.dumps({'status':'complete','engine':'CYCLES','device':scene.cycles.device,'samples':64,'resolution':[1800,1200],'views':records,'editable_camera_frames':144},indent=2),encoding='utf8')
print('SKYLINE_RENDER_COMPLETE',flush=True)
