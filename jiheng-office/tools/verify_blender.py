import bpy,json,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'霁衡中心.blend'))
scene=bpy.data.scenes['JIHENG_ONE'];collection=bpy.data.collections['Landmark office model only'];root=bpy.data.objects['jiheng-landmark-office']
points=[o.matrix_world@Vector(c) for o in collection.all_objects if o.type=='MESH' for c in o.bound_box]
low=[min(v[i] for v in points) for i in range(3)];high=[max(v[i] for v in points) for i in range(3)]
packed=[im for im in bpy.data.images if im.source=='FILE' and im.name.startswith('texture_')]
png=(ROOT/'outputs/霁衡中心-8K.png').read_bytes();resolution=struct.unpack('>II',png[16:24])
checks={
 '112m_square':all(abs(high[i]-low[i]-112)<.02 for i in [0,1]),
 '184m_height':abs(high[2]-184)<.02,
 'one_editable_building':bpy.data.objects['JH-01'].parent==root,
 'separate_architecture_parts':all(bpy.data.objects[i].parent==bpy.data.objects['JH-01'] for i in ['lower','middle','upper','podium','roof','terraces']),
 'seven_named_cameras':sum(o.type=='CAMERA' for o in scene.objects)==7,
 'cycles_gpu':scene.render.engine=='CYCLES' and scene.cycles.device=='GPU',
 'actual_8k_png':resolution==(7680,4320),
 'packed_textures':len(packed)>0 and all(i.packed_file for i in packed),
 'presentation_separate':bpy.data.objects['Backdrop'] not in collection.all_objects[:],
 'model_no_lights_or_camera':not any(o.type in ['LIGHT','CAMERA'] for o in collection.all_objects),
 'overview_saved':scene.camera==scene.objects[scene['office_camera_Overview']],
}
report={'checks':checks,'bounds_blender':{'min':low,'max':high},'master_resolution':list(resolution),'objects':len(scene.objects),'model_meshes':sum(o.type=='MESH' for o in collection.all_objects),'packed_textures':len(packed),'engine':scene.render.engine,'device':scene.cycles.device,'compositor_properties':{'node_tree':hasattr(scene,'node_tree'),'compositing_node_group':hasattr(scene,'compositing_node_group')}}
(ROOT/'outputs/blender-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
if not all(checks.values()):raise RuntimeError('Blender verification failed')
