import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\33864\Desktop\千人小镇\hospital-campus')
scene=next(s for s in bpy.data.scenes if s.get('hospital_buildings')==4)
campus=next(o for o in scene.objects if o.get('width_m')==112 and o.get('depth_m')==112)
def belongs(o):
    while o:
        if o==campus:return True
        o=o.parent
    return False
points=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and belongs(o) for v in o.bound_box]
minimum=[min(v[i] for v in points) for i in range(3)];maximum=[max(v[i] for v in points) for i in range(3)]
result={'scene':scene.name,'scenes':[s.name for s in bpy.data.scenes],'bounds_blender':{'min':minimum,'max':maximum},'units':scene.unit_settings.system,'building_ids':[o['id'] for o in scene.objects if o.get('id') in ['inpatient','outpatient','emergency','medical-tech']],'camera':scene.camera.name,'camera_frames':[scene.frame_start,scene.frame_end],'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'images':len(bpy.data.images),'engine':scene.render.engine}
assert minimum[0]>=-56.01 and maximum[0]<=56.01 and minimum[1]>=-56.01 and maximum[1]<=56.01
assert len(result['building_ids'])==4 and scene.frame_end==144
(ROOT/'outputs/blend-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
