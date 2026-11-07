import bpy,json,bmesh
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'青岚河.blend'))
scene=bpy.context.scene;water=next(o for o in scene.objects if o.type=='MESH' and o.parent and o.parent.name=='water');bm=bmesh.new();bm.from_mesh(water.data)
checks={'opens_in_river_scene':scene.name=='QINGLAN_RIVER','five_cameras':sum(o.type=='CAMERA' for o in scene.objects)==5,'cycles_gpu':scene.render.engine=='CYCLES' and scene.cycles.device=='GPU','water_volume_is_closed':all(e.is_manifold for e in bm.edges),'water_ior_1333':abs(water.active_material.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value-1.333)<.001,'volume_absorption_present':any(n.type=='VOLUME_ABSORPTION' for n in water.active_material.node_tree.nodes),'all_file_images_packed':all(im.packed_file for im in bpy.data.images if im.source=='FILE'),'metric_dimensions':scene['width_m']==64 and scene['length_m']==600};bm.free()
(ROOT/'outputs/blend-verification.json').write_text(json.dumps({'checks':checks,'objects':len(scene.objects)},indent=2),encoding='utf8');print(json.dumps(checks),flush=True)
if not all(checks.values()):raise RuntimeError('Blender deliverable check failed')
