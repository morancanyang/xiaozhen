"""Real Blender rendering, launched by a project-local MCP stdio server in a visible window."""
import bpy, json, traceback, math, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
try:
    exec(compile((ROOT/'tools/blender_import.py').read_text(encoding='utf8'),str(ROOT/'tools/blender_import.py'),'exec'))
    scene=bpy.data.scenes['CHENGXU_COURTYARD'];bpy.context.window.scene=scene
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
                space=area.spaces.active;space.clip_end=5000;space.shading.color_type='MATERIAL'
                space.region_3d.view_location=(0,0,28);space.region_3d.view_distance=200;space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'澄序住区.blend'),compress=True)
    def render_sequence():
        start=time.time();rendered=[]
        try:
            for name in ['Overview','Front','Top','Low','Entrance','Garden','Roof']:
                scene.camera=scene.objects[scene['courtyard_camera_'+name]]
                scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.cycles.samples=64
                scene.render.filepath=str(ROOT/'outputs'/('blender-'+name.lower()+'.png'))
                bpy.ops.render.render(write_still=True);rendered.append({'view':name,'resolution':[1800,1200]})
                (ROOT/'outputs/blender-progress.json').write_text(json.dumps({'status':'running','completed':rendered}),encoding='utf8')
            sun=next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN');sun_power=sun.data.energy;sun.data.energy=.12
            bg=scene.world.node_tree.nodes.get('Background');sky_power=bg.inputs['Strength'].default_value;bg.inputs['Strength'].default_value=.016
            changed=[]
            for m in bpy.data.materials:
                if not m.use_nodes:continue
                bs=m.node_tree.nodes.get('Principled BSDF')
                if bs and any(t in m.name.lower() for t in ['lamp','window-lit','sign-']):
                    changed.append((bs,bs.inputs['Emission Strength'].default_value));bs.inputs['Emission Strength'].default_value=3 if 'lamp' in m.name else 1.5
            night_lights=[]
            for f in DATA['manifest']['lightFixtures']:
                data=bpy.data.lights.new('Actual plaza light','POINT');data.energy=f['power']*.8;data.color=(1,.75,.5);data.shadow_soft_size=.2
                light=bpy.data.objects.new(data.name,data);light.location=cv(f['position']);studio.objects.link(light);night_lights.append(light)
            scene.camera=scene.objects[scene['courtyard_camera_Overview']];scene.render.filepath=str(ROOT/'outputs/blender-night.png');bpy.ops.render.render(write_still=True)
            rendered.append({'view':'Night','resolution':[1800,1200]})
            for o in night_lights:bpy.data.objects.remove(o,do_unlink=True)
            sun.data.energy=sun_power;bg.inputs['Strength'].default_value=sky_power
            for bs,value in changed:bs.inputs['Emission Strength'].default_value=value
            # Blender 5.2 compositor: retain AgX shading over a truly white background.
            scene.render.film_transparent=True;bpy.data.objects['Backdrop'].is_shadow_catcher=True
            bpy.data.objects['Afternoon atmosphere'].hide_render=True
            tree=bpy.data.node_groups.new('White studio composite','CompositorNodeTree')
            tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
            output=tree.nodes.new('NodeGroupOutput');rl=tree.nodes.new('CompositorNodeRLayers');rl.scene=scene
            display=tree.nodes.new('CompositorNodeConvertToDisplay');display.view_settings.view_transform='AgX';display.view_settings.look='AgX - Medium High Contrast'
            over=tree.nodes.new('CompositorNodeAlphaOver');over.inputs['Factor'].default_value=1;over.inputs['Background'].default_value=(1,1,1,1)
            tree.links.new(rl.outputs['Image'],display.inputs['Image']);tree.links.new(display.outputs['Image'],over.inputs['Foreground']);tree.links.new(over.outputs[0],output.inputs['Image']);scene.compositing_node_group=tree
            scene.view_settings.view_transform='Raw';scene.view_settings.look='None';scene.view_settings.exposure=0
            scene.render.filepath=str(ROOT/'outputs/blender-white.png');bpy.ops.render.render(write_still=True)
            rendered.append({'view':'White studio','resolution':[1800,1200]})
            scene.render.resolution_x=7680;scene.render.resolution_y=4320;scene.cycles.samples=96
            scene.render.filepath=str(ROOT/'outputs/澄序住区-8K.png');bpy.ops.render.render(write_still=True)
            rendered.append({'view':'Master8K','resolution':[7680,4320]})
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'澄序住区.blend'),compress=True)
            image=bpy.data.images.load(str(ROOT/'outputs/blender-overview.png'),check_existing=True)
            areas=[a for a in bpy.context.window.screen.areas if a.type=='VIEW_3D']
            if areas:
                area=max(areas,key=lambda a:a.width*a.height);area.type='IMAGE_EDITOR';area.spaces.active.image=image
                region=next(r for r in area.regions if r.type=='WINDOW')
                with bpy.context.temp_override(window=bpy.context.window,area=area,region=region):bpy.ops.image.view_all(fit_view=True)
            result={'status':'complete','engine':'CYCLES','device':scene.cycles.device,'blender_version':bpy.app.version_string,'samples_master':96,'views':rendered,'elapsed_seconds':round(time.time()-start,1),'source_snapshot':'courtyard-scene.json','visible_window':True,'actual_night_lights':len(night_lights)}
            (ROOT/'outputs/blender-result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('COURTYARD_RENDER_COMPLETE',flush=True)
        except Exception:
            (ROOT/'outputs/blender-result.json').write_text(json.dumps({'status':'failed','error':traceback.format_exc()}),encoding='utf8');traceback.print_exc()
        return None
    bpy.app.timers.register(render_sequence,first_interval=3)
except Exception:
    (ROOT/'outputs/blender-result.json').write_text(json.dumps({'status':'failed','error':traceback.format_exc()}),encoding='utf8');raise
