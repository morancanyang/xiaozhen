"""Read the delivered blend without modifying it; run with blender --background."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'青禾运动场.blend'))
scene=bpy.data.scenes['QINGHE_SPORTS_FIELD']
collection=bpy.data.collections['Sports field model only']
root=bpy.data.objects['qinghe-sports-field']
points=[o.matrix_world@Vector(c) for o in collection.all_objects if o.type=='MESH' for c in o.bound_box]
low=[min(v[i] for v in points) for i in range(3)]
high=[max(v[i] for v in points) for i in range(3)]
checks={
 'square_112m':abs(high[0]-low[0]-112)<.01 and abs(high[1]-low[1]-112)<.01,
 'eight_components':len(root.children)==8,
 'five_view_cameras':sum(o.type=='CAMERA' for o in scene.objects)==5,
 'cycles_gpu':scene.render.engine=='CYCLES' and scene.cycles.device=='GPU',
 'overview_camera':scene.camera.name==scene['sports_camera_Overview'],
 'packed_textures':all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.name.startswith('texture_')),
 'presentation_separate':'Backdrop' not in collection.all_objects,
}
report={'checks':checks,'bounds_blender':{'min':low,'max':high},'objects':len(scene.objects),'model_meshes':sum(o.type=='MESH' for o in collection.all_objects),'packed_texture_count':sum(bool(im.packed_file) for im in bpy.data.images),'engine':scene.render.engine,'device':scene.cycles.device}
(ROOT/'outputs/blender-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report),flush=True)
if not all(checks.values()):raise RuntimeError('Blend validation failed')
