"""Reuse the project's proven offline viewer and exact-geometry Blender bridge."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'jiheng-office'
for folder in ['src','outputs','tools']: (ROOT/folder).mkdir(exist_ok=True)
for name in ['build.cjs','src/app.js','src/shell.html','src/style.css','tools/blender_import.py','tools/render_blender.py','tools/blender_mcp.py','tools/run_blender_mcp.py']:
    s=(BASE/name).read_text(encoding='utf8')
    for a,b in [('霁衡中心','澄序住区'),('JIHENG ONE','CHENGXU COURTYARD'),('JIHENG_ONE','CHENGXU_COURTYARD'),('jiheng-landmark-office','chengxu-residential-courtyard'),('createLandmarkOffice','createResidentialCourtyard'),('LandmarkOfficeModule','ResidentialCourtyardModule'),('officeApp','courtyardApp'),('office-scene','courtyard-scene'),('office-manifest','courtyard-manifest'),('office_camera_','courtyard_camera_'),('NUANTING_','CHENGXU_'),('blender_start_office_render','blender_start_courtyard_render'),('blender_office_status','blender_courtyard_status'),('blender_open_office_scene','blender_open_courtyard_scene'),('nuanting_office_blender','chengxu_courtyard_blender')]:s=s.replace(a,b)
    (ROOT/name).write_text(s,encoding='utf8')
print(ROOT)
