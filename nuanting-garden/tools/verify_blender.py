"""Read the saved editable blend without modifying the visible GUI instance."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'暖庭花园.blend'))
scene=bpy.data.scenes['NUANTING_GARDEN']
collection=bpy.data.collections['Garden housing model only']
root=bpy.data.objects['nuanting-garden-housing']
points=[o.matrix_world@Vector(c) for o in collection.all_objects if o.type=='MESH' for c in o.bound_box]
low=[min(v[i] for v in points) for i in range(3)]
high=[max(v[i] for v in points) for i in range(3)]
packed=[im for im in bpy.data.images if im.source=='FILE' and im.name.startswith('texture_')]
checks={
 'square_112m':abs(high[0]-low[0]-112)<.01 and abs(high[1]-low[1]-112)<.01,
 'four_separate_building_origins':all(bpy.data.objects.get(i) is not None and bpy.data.objects[i].parent==root for i in ['A','B','C','D']),
 'six_view_cameras':sum(o.type=='CAMERA' for o in scene.objects)==6,
 'cycles_renderer':scene.render.engine=='CYCLES',
 'overview_camera':scene.camera.name==scene['garden_camera_Overview'],
 'textures_embedded':bool(packed) and all(im.packed_file for im in packed),
 'presentation_separate':'Backdrop' not in collection.all_objects,
 'model_has_no_camera_or_light':not any(o.type in ['CAMERA','LIGHT'] for o in collection.all_objects),
}
report={'checks':checks,'bounds_blender':{'min':low,'max':high},'objects':len(scene.objects),'model_meshes':sum(o.type=='MESH' for o in collection.all_objects),'building_origins':{i:list(bpy.data.objects[i].location) for i in ['A','B','C','D']},'packed_texture_count':len(packed),'engine':scene.render.engine,'device':scene.cycles.device}
(ROOT/'outputs/blender-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report),flush=True)
if not all(checks.values()):raise RuntimeError('Blender validation failed')
