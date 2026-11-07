import bpy,subprocess,json
from pathlib import Path
root=Path(r'C:\Users\33864\Desktop\千人小镇\hospital-campus')
log=(root/'outputs/blender-render.log').open('w',encoding='utf-8')
process=subprocess.Popen([bpy.app.binary_path,'-b',str(root/'澄和医院.blend'),'--python-exit-code','1','--python',str(root/'tools/render_blender.py')],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
print(json.dumps({'status':'render_started_via_blender_mcp','pid':process.pid,'log':str(root/'outputs/blender-render.log')}))
