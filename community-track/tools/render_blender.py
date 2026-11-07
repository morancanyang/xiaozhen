"""Run in a newly opened visible Blender window through the local MCP."""
import bpy,json,traceback,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
try:
    night_only='--night-only' in sys.argv
    if night_only:
        from mathutils import Vector
        DATA=json.loads((ROOT/'outputs/sports-scene.json').read_text(encoding='utf8'))
        def cv(p):return Vector((p[0],-p[2],p[1]))
    else:
        exec(compile((ROOT/'tools/blender_import.py').read_text(encoding='utf8'),str(ROOT/'tools/blender_import.py'),'exec'))
    scene=bpy.data.scenes['QINGHE_SPORTS_FIELD'];bpy.context.window.scene=scene
    for old in list(bpy.data.scenes):
        if old!=scene:bpy.data.scenes.remove(old)
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU' if any(d.use and d.type=='OPTIX' for d in prefs.devices) else 'CPU'
    except Exception:scene.cycles.device='CPU'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.clip_end=3000;space.shading.color_type='MATERIAL';space.region_3d.view_location=(0,0,25);space.region_3d.view_distance=170;space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'青禾运动场.blend'),compress=True)
    def render_sequence():
        try:
            for name in ([] if night_only else ['Overview','Top','Track','Goal','Stands']):
                scene.camera=scene.objects[scene['sports_camera_'+name]];scene.render.filepath=str(ROOT/'outputs'/('blender-'+name.lower()+'.png'));bpy.ops.render.render(write_still=True)
            sun=next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN');power=sun.data.energy;sun.data.energy=.22
            background=scene.world.node_tree.nodes.get('Background');strength=background.inputs['Strength'].default_value;background.inputs['Strength'].default_value=.045
            changed=[]
            for m in bpy.data.materials:
                if m.use_nodes:
                    bs=m.node_tree.nodes.get('Principled BSDF')
                    if bs and any(n in m.name for n in ['lamp','window-lit']):changed.append((bs,bs.inputs['Emission Strength'].default_value));bs.inputs['Emission Strength'].default_value=2.5
            nightLights=[]
            from mathutils import Vector
            for f in DATA['manifest']['lightFixtures']:
                data=bpy.data.lights.new('Night floodlight','SPOT');data.energy=30000;data.color=(1,.9,.75);data.spot_size=1.4;data.spot_blend=.6
                light=bpy.data.objects.new(data.name,data);light.location=cv(f['position']);light.rotation_euler=(cv(f['target'])-light.location).to_track_quat('-Z','Y').to_euler();scene.collection.objects.link(light);nightLights.append(light)
            scene.camera=scene.objects[scene['sports_camera_Overview']];scene.render.filepath=str(ROOT/'outputs/blender-night.png');bpy.ops.render.render(write_still=True)
            for light in nightLights:bpy.data.objects.remove(light,do_unlink=True)
            sun.data.energy=power;background.inputs['Strength'].default_value=strength
            for bs,v in changed:bs.inputs['Emission Strength'].default_value=v
            scene.render.filepath=str(ROOT/'outputs/blender-overview.png');bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'青禾运动场.blend'),compress=True)
            image=bpy.data.images.load(str(ROOT/'outputs/blender-overview.png'),check_existing=True)
            areas=[a for a in bpy.context.window.screen.areas if a.type=='VIEW_3D']
            if areas:
                area=max(areas,key=lambda a:a.width*a.height);area.type='IMAGE_EDITOR';area.spaces.active.image=image
                region=next(r for r in area.regions if r.type=='WINDOW')
                with bpy.context.temp_override(window=bpy.context.window,area=area,region=region):bpy.ops.image.view_all(fit_view=True)
            result={'status':'complete','engine':'CYCLES','device':scene.cycles.device,'blender_version':bpy.app.version_string,'resolution':[1800,1200],'samples':64,'visible_window':True,'views':['Overview','Top','Track','Goal','Stands','Night']}
            (ROOT/'outputs/blender-result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('SPORTS_RENDER_COMPLETE',flush=True)
        except Exception:
            (ROOT/'outputs/blender-result.json').write_text(json.dumps({'status':'failed','error':traceback.format_exc()}),encoding='utf8');traceback.print_exc()
        return None
    bpy.app.timers.register(render_sequence,first_interval=3)
except Exception:
    (ROOT/'outputs/blender-result.json').write_text(json.dumps({'status':'failed','error':traceback.format_exc()}),encoding='utf8');raise
