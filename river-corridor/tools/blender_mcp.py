import json,subprocess,os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
ROOT=Path(__file__).resolve().parents[1]
BLENDER=Path(r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe')
mcp=FastMCP('qinglan_river_blender');job=None
@mcp.tool()
def blender_start_river_render()->dict:
    """Import the exact river geometry and render five views in a hidden, isolated Blender process."""
    global job
    if job and job.poll() is None:return {'status':'running','pid':job.pid}
    if not (ROOT/'outputs/river-scene.json').is_file():raise ValueError('Export river-scene.json first')
    (ROOT/'outputs/blender-result.json').unlink(missing_ok=True)
    log=(ROOT/'outputs/blender-render.log').open('w',encoding='utf8')
    job=subprocess.Popen([str(BLENDER),'-b','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/render_blender.py')],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    return {'status':'running','pid':job.pid,'log':str(ROOT/'outputs/blender-render.log')}
@mcp.tool()
def blender_river_status()->dict:
    """Read Blender progress and actual renderer information."""
    result=ROOT/'outputs/blender-result.json';log=ROOT/'outputs/blender-render.log'
    if result.is_file():return json.loads(result.read_text(encoding='utf8'))
    return {'status':'failed' if job and job.poll() is not None else 'running','log':log.read_text(encoding='utf8',errors='replace').splitlines()[-5:] if log.is_file() else []}
if __name__=='__main__':mcp.run(transport='stdio')
