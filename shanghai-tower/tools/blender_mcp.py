"""Local stdio MCP bridge, derived from the existing project bridge."""
import subprocess,os,json
from pathlib import Path
from typing import Annotated
from pydantic import Field
from mcp.server.fastmcp import FastMCP
ROOT=Path(__file__).resolve().parents[1]
BLENDER=Path(os.environ.get('CITY_BLENDER_EXE',r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'))
mcp=FastMCP('blender_mcp');job=None
@mcp.tool(annotations={'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False})
def blender_inspect()->dict:
    """Inspect local Blender availability and the exported model input."""
    return {'blender_available':BLENDER.is_file(),'input_available':(ROOT/'outputs/scene.json').is_file(),'project':str(ROOT)}
@mcp.tool(annotations={'readOnlyHint':False,'destructiveHint':False,'idempotentHint':False,'openWorldHint':False})
def blender_render_landmark(samples:Annotated[int,Field(ge=8,le=128)]=48)->dict:
    """Import the project's reviewed Three.js geometry, save an editable .blend and start five Cycles renders including an 8K portrait. Poll blender_render_status until completion."""
    global job
    if job is not None and job.poll() is None:raise ValueError('Render already running. Poll blender_render_status.')
    if not BLENDER.is_file():raise ValueError('Blender missing. Set CITY_BLENDER_EXE to blender.exe.')
    data=json.loads((ROOT/'outputs/scene.json').read_text(encoding='utf-8'))
    if data.get('format')!='qianren-landmark-v1':raise ValueError('Export scene.json from the landmark HTML first.')
    (ROOT/'outputs/blender-result.json').unlink(missing_ok=True)
    with (ROOT/'outputs/blender.log').open('w',encoding='utf-8') as log:
        job=subprocess.Popen([str(BLENDER),'-b','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/blender_render.py'),'--',str(ROOT),str(samples)],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    return {'status':'running','pid':job.pid,'log':str(ROOT/'outputs/blender.log')}
@mcp.tool(annotations={'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False})
def blender_render_status()->dict:
    """Return recent Blender log lines and verified output files. Does not block."""
    result=ROOT/'outputs/blender-result.json';log=ROOT/'outputs/blender.log';lines=log.read_text(encoding='utf-8',errors='replace').splitlines()[-7:] if log.is_file() else []
    status='complete' if result.is_file() else 'failed' if job is not None and job.poll() is not None else 'running' if job is not None else 'idle'
    return {'status':status,'recent_log':lines,'result':json.loads(result.read_text(encoding='utf-8')) if result.is_file() else None}
if __name__=='__main__':mcp.run(transport='stdio')
