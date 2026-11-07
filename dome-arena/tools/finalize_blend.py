"""Save a complete startup scene and a useful modeling viewport in the deliverable."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'穹光体育中心.blend'))
scene=bpy.data.scenes['DOME_ARENA_Final'];bpy.context.window.scene=scene
for old in list(bpy.data.scenes):
    if old.name not in ['DOME_ARENA_Final','DOME_ARENA_Night']:bpy.data.scenes.remove(old)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type!='VIEW_3D':continue
        space=area.spaces.active;space.clip_end=10000
        space.shading.type='SOLID';space.shading.color_type='MATERIAL'
        space.region_3d.view_location=(0,0,12);space.region_3d.view_distance=210
        space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion();space.region_3d.view_perspective='PERSP'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'穹光体育中心.blend'),compress=True)
