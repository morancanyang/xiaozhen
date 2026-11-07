"""Runs in an isolated visible Blender window launched by the local MCP server."""
import bpy, json, traceback, sys, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
try:
    night_only = '--night-only' in sys.argv
    if night_only:
        from mathutils import Vector
        DATA = json.loads((ROOT / 'outputs/garden-scene.json').read_text(encoding='utf8'))
        def cv(p): return Vector((p[0], -p[2], p[1]))
    else:
        exec(compile((ROOT / 'tools/blender_import.py').read_text(encoding='utf8'), str(ROOT / 'tools/blender_import.py'), 'exec'))
    scene = bpy.data.scenes['NUANTING_GARDEN']; bpy.context.window.scene = scene
    for old in list(bpy.data.scenes):
        if old != scene: bpy.data.scenes.remove(old)
    preferences = bpy.context.preferences.addons['cycles'].preferences
    try:
        preferences.compute_device_type = 'OPTIX'; preferences.get_devices()
        for device in preferences.devices: device.use = device.type == 'OPTIX'
        scene.cycles.device = 'GPU' if any(d.use and d.type == 'OPTIX' for d in preferences.devices) else 'CPU'
    except Exception: scene.cycles.device = 'CPU'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active; space.clip_end = 3000; space.shading.color_type = 'MATERIAL'
                space.region_3d.view_location = (0, 0, 12); space.region_3d.view_distance = 170
                space.region_3d.view_rotation = scene.camera.rotation_euler.to_quaternion()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / '暖庭花园.blend'), compress=True)

    def render_sequence():
        try:
            for name in ([] if night_only else ['Overview', 'Top', 'Facade', 'Entrance', 'Garden', 'Roof']):
                scene.camera = scene.objects[scene['garden_camera_' + name]]
                scene.render.filepath = str(ROOT / 'outputs' / ('blender-' + name.lower() + '.png'))
                bpy.ops.render.render(write_still=True)
            sun = next(o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN')
            sun_power = sun.data.energy; sun.data.energy = .08
            background = scene.world.node_tree.nodes.get('Background')
            sky_power = background.inputs['Strength'].default_value; background.inputs['Strength'].default_value = .012
            changed = []
            for mat in bpy.data.materials:
                if not mat.use_nodes: continue
                bs = mat.node_tree.nodes.get('Principled BSDF')
                name = mat.name.lower()
                if bs and any(token in name for token in ['lamp', 'window-lit', 'interior-lit', 'warm-window']):
                    changed.append((bs, bs.inputs['Emission Strength'].default_value))
                    bs.inputs['Emission Strength'].default_value = 2.6 if 'lamp' in name else 1.2
            night_lights = []
            for fixture in DATA['manifest'].get('lightFixtures', []):
                data = bpy.data.lights.new('Garden actual night light', 'POINT')
                data.energy = fixture.get('blenderPower', max(6, min(100, fixture.get('power', 70) * .6)))
                data.color = (1, .72, .42); data.shadow_soft_size = .18
                light = bpy.data.objects.new(data.name, data); light.location = cv(fixture['position'])
                scene.collection.objects.link(light); night_lights.append(light)
            scene.camera = scene.objects[scene['garden_camera_Overview']]
            scene.render.filepath = str(ROOT / 'outputs/blender-night.png'); bpy.ops.render.render(write_still=True)
            for light in night_lights: bpy.data.objects.remove(light, do_unlink=True)
            sun.data.energy = sun_power; background.inputs['Strength'].default_value = sky_power
            for bs, value in changed: bs.inputs['Emission Strength'].default_value = value
            scene.render.filepath = str(ROOT / 'outputs/blender-overview.png')
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / '暖庭花园.blend'), compress=True)
            image = bpy.data.images.load(str(ROOT / 'outputs/blender-overview.png'), check_existing=True)
            areas = [a for a in bpy.context.window.screen.areas if a.type == 'VIEW_3D']
            if areas:
                area = max(areas, key=lambda a: a.width * a.height); area.type = 'IMAGE_EDITOR'; area.spaces.active.image = image
                region = next(r for r in area.regions if r.type == 'WINDOW')
                with bpy.context.temp_override(window=bpy.context.window, area=area, region=region): bpy.ops.image.view_all(fit_view=True)
            result = {'status': 'complete', 'engine': 'CYCLES', 'device': scene.cycles.device, 'blender_version': bpy.app.version_string, 'resolution': [1800, 1200], 'samples': 64, 'visible_window': True, 'views': ['Overview', 'Top', 'Facade', 'Entrance', 'Garden', 'Roof', 'Night'], 'source_snapshot': 'garden-scene.json', 'night_light_count': len(night_lights)}
            (ROOT / 'outputs/blender-result.json').write_text(json.dumps(result, indent=2), encoding='utf8')
            print('GARDEN_RENDER_COMPLETE', flush=True)
        except Exception:
            (ROOT / 'outputs/blender-result.json').write_text(json.dumps({'status': 'failed', 'error': traceback.format_exc()}), encoding='utf8')
            traceback.print_exc()
        return None
    bpy.app.timers.register(render_sequence, first_interval=3)
except Exception:
    (ROOT / 'outputs/blender-result.json').write_text(json.dumps({'status': 'failed', 'error': traceback.format_exc()}), encoding='utf8')
    raise
