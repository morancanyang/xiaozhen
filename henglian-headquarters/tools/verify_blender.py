import bpy,json,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'衡联总部.blend'));scene=bpy.data.scenes['HENGLIAN_CAMPUS'];collection=bpy.data.collections['Corporate headquarters model only'];root=bpy.data.objects['henglian-corporate-headquarters'];bpy.context.view_layer.update()
points=[o.matrix_world@Vector(c) for o in collection.all_objects if o.type=='MESH' for c in o.bound_box]
low=[min(v[i] for v in points) for i in range(3)];high=[max(v[i] for v in points) for i in range(3)]
packed=[im for im in bpy.data.images if im.source=='FILE' and im.name.startswith('texture_')];png=(ROOT/'outputs/衡联总部-8K.png').read_bytes();resolution=struct.unpack('>II',png[16:24]);manifest=json.loads((ROOT/'headquarters-manifest.json').read_text(encoding='utf8'))
checks={
 '112m_square':all(abs(high[i]-low[i]-112)<.02 for i in [0,1]),
 '100m_height':abs(high[2]-100)<.02,
 'two_editable_buildings':all(bpy.data.objects[id].parent==root for id in ['main','annex']),
 'independent_bridge':bpy.data.objects['bridge'].parent==root,
 'separate_architectural_parts':all(bpy.data.objects[id+'-'+key].parent==bpy.data.objects[id] for id in ['main','annex'] for key in ['facade','roof','entrance','interior']),
 'correct_building_origins':all((bpy.data.objects[b['id']].location-Vector((b['x'],-b['z'],0))).length<1e-5 for b in manifest['buildings']),
 'twelve_named_cameras':sum(o.type=='CAMERA' for o in scene.objects)==12,
 'separate_editable_stairs':all(bpy.data.objects[id+'-stairs'].parent==bpy.data.objects[id] for id in ['main','annex']),
 'leaf_geometry':any('foliage-' in o.name for o in collection.all_objects),
 'grass_vertex_colors':any(o.type=='MESH' and len(o.data.color_attributes)>0 for o in collection.all_objects),
 'cycles_gpu':scene.render.engine=='CYCLES' and scene.cycles.device=='GPU',
 'actual_8k_png':resolution==(7680,4320),
 'packed_textures':len(packed)>0 and all(i.packed_file for i in packed),
 'presentation_separate':bpy.data.objects['Backdrop'] not in collection.all_objects[:],
 'model_no_lights_or_camera':not any(o.type in ['LIGHT','CAMERA'] for o in collection.all_objects),
 'overview_saved':scene.camera==scene.objects[scene['headquarters_camera_Overview']],
 'white_studio_compositor':scene.render.film_transparent and scene.compositing_node_group is not None
}
report={'checks':checks,'bounds_blender':{'min':low,'max':high},'master_resolution':list(resolution),'objects':len(scene.objects),'model_meshes':sum(o.type=='MESH' for o in collection.all_objects),'packed_textures':len(packed),'engine':scene.render.engine,'device':scene.cycles.device}
(ROOT/'outputs/blender-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True);assert all(checks.values())
