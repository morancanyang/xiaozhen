import bpy,sys,json,math
from pathlib import Path
ROOT=Path(r'C:\Users\33864\Desktop\千人小镇\hospital-campus')
scene=next(s for s in bpy.data.scenes if s.name.startswith('CH_Hospital_Final'));bpy.context.window.scene=scene
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.type=='OPTIX' for d in prefs.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
scene.cycles.samples=48;scene.cycles.use_denoising=True
for name in ['Overview','Outpatient','Emergency','Garden','Roof','Garage']:
    scene.camera=scene.objects.get(scene['hospital_camera_'+name]);scene.render.filepath=str(ROOT/'outputs'/('blender-'+name.lower()+'.png'));bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
scene.camera=scene.objects.get(scene['hospital_camera_Overview'])
# Retain an editable six-second camera orbit.
scene.frame_start=1;scene.frame_end=144;scene.render.fps=24
from mathutils import Vector
cam=scene.camera
for f,angle in [(1,.74),(72,1.06),(144,1.4)]:
    cam.location=(math.sin(angle)*235,-math.cos(angle)*235,138);cam.rotation_euler=(Vector((0,0,12))-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f)
scene.frame_set(1)
for s in list(bpy.data.scenes):
    if s!=scene and len(s.objects)==0:bpy.data.scenes.remove(s)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'澄和医院.blend'))
(ROOT/'outputs/blender-result.json').write_text(json.dumps({'status':'complete','engine':'CYCLES','device':scene.cycles.device,'samples':48,'resolution':[1920,1200],'views':6,'buildings':4,'editable_camera_frames':144},indent=2),encoding='utf-8')
print('HOSPITAL_RENDER_COMPLETE',flush=True)
