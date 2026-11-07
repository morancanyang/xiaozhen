import subprocess,os,json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
ROOT=Path(__file__).resolve().parents[1];BLENDER=Path(os.environ.get('CITY_BLENDER_EXE',r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'));mcp=FastMCP('quiet-park-blender');job=None
@mcp.tool()
def prepare_park_scene()->dict:
 """Build the reviewed Three.js geometry into a new Blender file without touching an existing window."""
 global job
 if not BLENDER.is_file():raise ValueError('Blender not found')
 for name in ['prepared.json','blender-result.json','visible-progress.json']:(ROOT/'outputs'/name).unlink(missing_ok=True)
 with (ROOT/'outputs/blender-prepare.log').open('w',encoding='utf8') as log:job=subprocess.Popen([str(BLENDER),'-b','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/blender_scene.py'),'--',str(ROOT),'64'],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
 return {'status':'preparing','pid':job.pid}
@mcp.tool()
def open_blender_and_render()->dict:
 """Open a NEW visible local Blender window and render via UI jobs. The user explicitly requested a visible session."""
 global job
 if not (ROOT/'outputs/prepared.json').is_file():raise ValueError('Prepare the scene first')
 with (ROOT/'outputs/blender-visible.log').open('w',encoding='utf8') as log:job=subprocess.Popen([str(BLENDER),str(ROOT/'森隐公园.blend'),'--python',str(ROOT/'tools/visible_render.py'),'--',str(ROOT)],stdout=log,stderr=subprocess.STDOUT,creationflags=0)
 return {'status':'rendering','pid':job.pid,'visible_window':True}
@mcp.tool()
def render_status()->dict:
 """Poll preparation and visible rendering without blocking the desktop."""
 for file in ['blender-result.json','visible-progress.json','prepared.json']:
  p=ROOT/'outputs'/file
  if p.is_file():return json.loads(p.read_text(encoding='utf8'))
 return {'status':'failed' if job and job.poll() is not None else 'preparing'}
if __name__=='__main__':mcp.run(transport='stdio')
