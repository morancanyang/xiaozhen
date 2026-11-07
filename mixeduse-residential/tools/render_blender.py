"""Called by MCP in a new visible Blender. Renders are real responsive UI jobs."""
import json
import math
import re
import time
import traceback
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs'

def atomic_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')
    temp.replace(path)

try:
    atomic_json(OUT/'blender-progress.json', {'status':'importing','finished':[]})
    exec(compile((ROOT/'tools/blender_import.py').read_text(encoding='utf8'), str(ROOT/'tools/blender_import.py'), 'exec'))
    scene = SCENE
    state = {'index':0, 'running':False, 'finished':[], 'started':0}
    twilight_lights = []
    bg = scene.world.node_tree.nodes.get('Background')
    original_background = tuple(bg.inputs['Color'].default_value)
    original_strength = bg.inputs['Strength'].default_value
    original_emission = [(mat, mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value) for mat in EMISSIVE_MATERIALS]
    original_emission_colors = {mat.name:tuple(mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value) for mat in EMISSIVE_MATERIALS}
    bpy.context.preferences.view.render_display_type = 'WINDOW'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.clip_end = 3000
                space.shading.color_type = 'MATERIAL'
                space.region_3d.view_perspective = 'CAMERA'

    def progress(status):
        atomic_json(OUT/'blender-progress.json', {'status':status, 'view':SHOTS[min(state['index'],len(SHOTS)-1)]['name'], 'index':state['index'], 'total':len(SHOTS), 'finished':state['finished'], 'engine':scene.render.engine, 'device':scene.cycles.device, 'devices':DEVICE_NAMES})

    def reset_daylight():
        bg.inputs['Color'].default_value = original_background
        bg.inputs['Strength'].default_value = original_strength
        sun.data.energy = 2.5
        sun.data.color = (1, .94, .85)
        fill.data.energy = 14000
        scene.view_settings.exposure = .1
        for mat, emission in original_emission:
            bs = mat.node_tree.nodes.get('Principled BSDF')
            bs.inputs['Emission Strength'].default_value = emission
            bs.inputs['Emission Color'].default_value = original_emission_colors[mat.name]
        for ob in twilight_lights:
            ob.hide_render = True
            ob.hide_viewport = True

    def tick():
        try:
            if state['running']:
                if bpy.app.is_job_running('RENDER'):
                    return 1.0
                shot = SHOTS[state['index']]
                output = OUT / ('blender-' + shot['name'] + '.png')
                if not output.is_file() or output.stat().st_mtime < state['started'] - 1:
                    raise RuntimeError('Render did not create '+str(output))
                state['finished'].append({'view':shot['name'], 'path':str(output), 'resolution':list(shot['size']), 'samples':scene.cycles.samples})
                state['index'] += 1
                state['running'] = False
                progress('rendering')
            if state['index'] == len(SHOTS):
                reset_daylight()
                scene.camera = CAMERAS['overview']
                scene.render.resolution_x, scene.render.resolution_y = SHOTS[0]['size']
                scene.render.filepath = str(OUT/'blender-overview.png')
                bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'棕屿里.blend'), compress=True)
                result = {'status':'complete', 'engine':scene.render.engine, 'device':scene.cycles.device, 'devices':DEVICE_NAMES, 'blender_version':bpy.app.version_string, 'samples':scene.cycles.samples, 'blend':str(ROOT/'棕屿里.blend'), 'renders':state['finished'], 'visible_gui':True, 'source_snapshot':str(OUT/'scene.json'), 'model_batches':len(batches), 'model_objects':len(DATA['objects']), 'vertices':vertex_count, 'triangles':face_count}
                atomic_json(OUT/'blender-result.json', result)
                progress('complete')
                image = bpy.data.images.load(str(OUT/'blender-overview.png'), check_existing=True)
                for window in bpy.context.window_manager.windows:
                    areas = [a for a in window.screen.areas if a.type=='VIEW_3D']
                    if areas:
                        area = max(areas,key=lambda a:a.width*a.height)
                        area.type = 'IMAGE_EDITOR'
                        area.spaces.active.image = image
                        break
                print('SLAB_RENDER_COMPLETE', flush=True)
                return None
            shot = SHOTS[state['index']]
            if shot['name'] == 'twilight':
                bg.inputs['Color'].default_value = (.14, .24, .48, 1)
                bg.inputs['Strength'].default_value = .28
                sun.data.energy = .25
                sun.data.color = (1, .64, .35)
                fill.data.energy = 4000
                scene.view_settings.exposure = .8
                for mat, emission in original_emission:
                    bs = mat.node_tree.nodes.get('Principled BSDF')
                    if any(k in mat.name.lower() for k in ('lamp','diffuser')):
                        bs.inputs['Emission Strength'].default_value = max(emission, 3.5)
                    else:
                        apartment = re.search(r'Apartment interior (\d+)', mat.name)
                        if 'Shop luminous' in mat.name:
                            bs.inputs['Emission Strength'].default_value=2.8
                        if apartment:
                            index = int(apartment.group(1))
                            bs.inputs['Emission Strength'].default_value = 3.0+(index%4)*.6 if index%4 else .02
                            # Very warm interior illumination stays warm after the
                            # two silver-blue glazing layers of enclosed balconies.
                            bs.inputs['Emission Color'].default_value = (1,.26,.055,1)
                # A few real low-power entrance lights match the model fixtures.
                for z in (-39.0,):
                    for x in (-35,-26,-17,0,17,26,35):
                        light = bpy.data.lights.new('Entry warm light', 'AREA')
                        light.energy = 45
                        light.color = (1,.71,.42)
                        light.size = 1.5
                        ob = bpy.data.objects.new(light.name, light)
                        ob.location = (x, z, 3)
                        STUDIO.objects.link(ob)
                        twilight_lights.append(ob)
            scene.camera = CAMERAS[shot['name']]
            scene.render.resolution_x, scene.render.resolution_y = shot['size']
            scene.render.filepath = str(OUT/('blender-'+shot['name']+'.png'))
            progress('rendering')
            state['running'] = True
            state['started'] = time.time()
            bpy.ops.render.render('INVOKE_DEFAULT', write_still=True, scene=scene.name)
            return 2.0
        except Exception:
            atomic_json(OUT/'blender-result.json', {'status':'failed','error':traceback.format_exc()})
            traceback.print_exc()
            return None

    progress('opening')
    bpy.app.timers.register(tick, first_interval=3)
except Exception:
    atomic_json(OUT/'blender-result.json', {'status':'failed','error':traceback.format_exc()})
    traceback.print_exc()
    raise
