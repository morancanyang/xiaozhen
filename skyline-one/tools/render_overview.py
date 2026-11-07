import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
day=bpy.data.scenes['SKYLINE_ONE_Final'];night=bpy.data.scenes['SKYLINE_ONE_Night']
cam=bpy.data.objects[day['skyline_camera_Overview']];cam.data.type='ORTHO';cam.data.ortho_scale=285
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
except Exception:pass
for scene,name in [(day,'overview'),(night,'night')]:
    bpy.context.window.scene=scene;scene.camera=cam;scene.cycles.device='GPU';scene.render.filepath=str(ROOT/'outputs'/('blender-'+name+'.png'));bpy.ops.render.render(write_still=True)
bpy.context.window.scene=day
bpy.data.libraries.write(str(ROOT/'云际中心.blend'),{day,night},fake_user=True)
print('FINAL_OVERVIEWS_COMPLETE',flush=True)
