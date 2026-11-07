"""Read the delivered .blend back in a fresh background Blender process."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'穹光体育中心.blend'))
day=bpy.data.scenes['DOME_ARENA_Final'];night=bpy.data.scenes['DOME_ARENA_Night']
roof=[o for o in day.objects if o.type=='MESH' and o.parent and o.parent.name=='roof']
checks={
    'opens_in_complete_day_scene':bpy.context.scene==day,
    'day_and_night_scenes':day is not night,
    'cycles_gpu':day.render.engine=='CYCLES' and day.cycles.device=='GPU',
    'seven_day_cameras_or_more':sum(o.type=='CAMERA' for o in day.objects)>=6,
    'complete_roof_visible_by_default':bool(roof) and all(not o.hide_render for o in roof),
    'day_and_night_cameras_independent':day.camera is not night.camera,
    'all_images_packed':all(im.packed_file is not None for im in bpy.data.images if im.source=='FILE'),
    'night_has_floodlights_and_facade_wash':sum(o.type=='LIGHT' for o in night.objects)>=16,
    'metric_units':day.unit_settings.system=='METRIC',
}
(ROOT/'outputs/blend-verification.json').write_text(json.dumps({'checks':checks,'scene_objects':{'day':len(day.objects),'night':len(night.objects)}},indent=2),encoding='utf8')
print(json.dumps(checks),flush=True)
if not all(checks.values()):raise RuntimeError('Delivered Blender file validation failed')
