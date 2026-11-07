import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
exec(compile((ROOT/'tools/blender_import.py').read_text(encoding='utf8'),str(ROOT/'tools/blender_import.py'),'exec'))
scene=bpy.data.scenes['DOME_ARENA_Final'];bpy.context.window.scene=scene
available=[e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.use and d.type=='OPTIX' for d in prefs.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.render.resolution_x=1800;scene.render.resolution_y=1200
# Camera-only background avoids the physical sky's dark below-horizon region.
nodes=scene.world.node_tree.nodes;links=scene.world.node_tree.links;output=nodes.get('World Output');bg=nodes.get('Background');path=nodes.new('ShaderNodeLightPath');camera_bg=nodes.new('ShaderNodeBackground');camera_bg.inputs['Color'].default_value=(.5,.65,.77,1);camera_bg.inputs['Strength'].default_value=.7;mix=nodes.new('ShaderNodeMixShader');links.new(path.outputs['Is Camera Ray'],mix.inputs[0]);links.new(bg.outputs[0],mix.inputs[1]);links.new(camera_bg.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
roofObjects=[o for o in scene.objects if o.type=='MESH' and o.parent and o.parent.name=='roof']
def roof(show):
    for o in roofObjects:o.hide_render=not show
records=[]
for name in ['Overview','Low','Entrance','Structure','Interior','Roof']:
    roof(name not in ['Structure','Interior']);scene.camera=scene.objects[scene['arena_camera_'+name]];scene.render.filepath=str(ROOT/'outputs'/('blender-'+name.lower()+'.png'));bpy.ops.render.render(write_still=True);records.append(name);print('RENDERED '+name,flush=True)
roof(True);scene.camera=scene.objects[scene['arena_camera_Overview']]
# Keep the editable daylight project intact; a second scene has independent night materials.
night=scene.copy();night.name='DOME_ARENA_Night';night.world=scene.world.copy();night.world.name='Arena night sky'
for n in night.world.node_tree.nodes:
    if n.type=='BACKGROUND':
        for l in list(n.inputs['Color'].links):night.world.node_tree.links.remove(l)
        n.inputs['Color'].default_value=(.018,.04,.075,1);n.inputs['Strength'].default_value=.35
for child in list(night.collection.children):night.collection.children.unlink(child)
night_mats={}
for obj in scene.objects:
    copy=obj.copy();copy.parent=None;copy.matrix_world=obj.matrix_world.copy()
    if obj.type=='MESH':
        copy.data=obj.data.copy()
        for i,m in enumerate(copy.data.materials):
            if m.name not in night_mats:
                nm=m.copy();bs=nm.node_tree.nodes.get('Principled BSDF')
                if 'warm-light' in m.name:bs.inputs['Emission Strength'].default_value=3
                if m.name.endswith('_lamp'):bs.inputs['Emission Strength'].default_value=4
                night_mats[m.name]=nm
            copy.data.materials[i]=night_mats[m.name]
    if obj.type=='LIGHT':copy.data=obj.data.copy();copy.data.energy=.18;copy.data.color=(.6,.78,1)
    night.collection.objects.link(copy)
    if obj==scene.camera:night.camera=copy
for fixture in DATA['manifest']['lightFixtures']:
    data=bpy.data.lights.new('Arena floodlight','SPOT');data.energy=6000;data.color=(.65,.84,1);data.spot_size=1.2;data.spot_blend=.6
    o=bpy.data.objects.new(data.name,data);o.location=cv(fixture['position']);o.rotation_euler=(cv(fixture['target'])-o.location).to_track_quat('-Z','Y').to_euler();night.collection.objects.link(o)
for x in [-12,0,12]:
    data=bpy.data.lights.new('Entrance glow','AREA');data.energy=480;data.color=(1,.7,.4);data.size=6;o=bpy.data.objects.new(data.name,data);o.location=(x,-30,6);night.collection.objects.link(o)
# Broad architectural wash keeps the blue curtain wall readable without flattening night contrast.
for i in range(8):
    a=2*math.pi*i/8;p=Vector((math.cos(a)*48,math.sin(a)*42,11));target=Vector((0,0,10))
    data=bpy.data.lights.new('Blue facade wash','AREA');data.energy=1100;data.color=(.42,.72,1);data.shape='DISK';data.size=12
    o=bpy.data.objects.new(data.name,data);o.location=p;o.rotation_euler=(target-p).to_track_quat('-Z','Y').to_euler();night.collection.objects.link(o)
bpy.context.window.scene=night;night.render.filepath=str(ROOT/'outputs/blender-night.png');bpy.ops.render.render(write_still=True);records.append('Night')
bpy.context.window.scene=scene
for old in list(bpy.data.scenes):
    if old not in [scene,night]:bpy.data.scenes.remove(old)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type!='VIEW_3D':continue
        space=area.spaces.active;space.clip_end=10000;space.shading.type='SOLID';space.shading.color_type='MATERIAL'
        space.region_3d.view_location=(0,0,12);space.region_3d.view_distance=210
        space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion();space.region_3d.view_perspective='PERSP'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'穹光体育中心.blend'),compress=True)
result={'status':'complete','engine':'CYCLES','device':scene.cycles.device,'octane_available':any('OCTANE' in e.upper() for e in available),'blender_version':bpy.app.version_string,'samples':64,'resolution':[1800,1200],'views':records}
(ROOT/'outputs/blender-result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('ARENA_RENDER_COMPLETE',flush=True)
