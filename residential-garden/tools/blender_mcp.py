import json,subprocess,os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
ROOT=Path(__file__).resolve().parents[1]
BLENDER=Path(r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe')
mcp=FastMCP('linxu_residential_blender');job=None
@mcp.tool()
def blender_start_residential_render()->dict:
    """Import the exact residential geometry and render six views in a visible, isolated Blender window."""
    global job
    if job and job.poll() is None:return {'status':'running','pid':job.pid}
    if not (ROOT/'outputs/residential-scene.json').is_file():raise ValueError('Export residential-scene.json first')
    (ROOT/'outputs/blender-result.json').unlink(missing_ok=True)
    log=(ROOT/'outputs/blender-render.log').open('w',encoding='utf8')
    job=subprocess.Popen([str(BLENDER),'--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/render_blender.py')],stdout=log,stderr=subprocess.STDOUT,creationflags=0)
    return {'status':'running','pid':job.pid,'log':str(ROOT/'outputs/blender-render.log')}
@mcp.tool()
def blender_open_residential_scene()->dict:
    """Keep the editable delivered scene and the completed render visible on this computer."""
    global job
    job=subprocess.Popen([str(BLENDER),str(ROOT/'林序住区.blend'),'--python',str(ROOT/'tools/show_scene.py')],creationflags=0)
    return {'status':'opened','pid':job.pid}
@mcp.tool()
def blender_residential_status()->dict:
    """Read Blender progress and actual renderer information."""
    result=ROOT/'outputs/blender-result.json';log=ROOT/'outputs/blender-render.log'
    if result.is_file():return {**json.loads(result.read_text(encoding='utf8')),'window_running':job is not None and job.poll() is None,'pid':job.pid if job else None}
    return {'status':'failed' if job and job.poll() is not None else 'running','log':log.read_text(encoding='utf8',errors='replace').splitlines()[-5:] if log.is_file() else []}
if __name__=='__main__':mcp.run(transport='stdio')
