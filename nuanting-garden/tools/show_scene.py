import bpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def show():
    image = bpy.data.images.load(str(ROOT / 'outputs/blender-overview.png'), check_existing=True)
    areas = [a for a in bpy.context.window.screen.areas if a.type == 'VIEW_3D']
    if areas:
        area = max(areas, key=lambda a: a.width * a.height); area.type = 'IMAGE_EDITOR'; area.spaces.active.image = image
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(window=bpy.context.window, area=area, region=region): bpy.ops.image.view_all(fit_view=True)
    return None
bpy.app.timers.register(show, first_interval=1)
