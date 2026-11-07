"""Project-local Blender MCP bridge. stdout is reserved for MCP JSON-RPC."""
import json,os,subprocess,uuid
from pathlib import Path
from typing import Annotated
from mcp.server.fastmcp import FastMCP
from pydantic import Field

ROOT=Path(__file__).resolve().parents[1]
BLENDER=Path(os.environ.get('CITY_BLENDER_EXE',r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'))
mcp=FastMCP('blender_mcp')
jobs={}

def inside(relative:str)->Path:
    p=(ROOT/relative).resolve()
    if not p.is_relative_to(ROOT):raise ValueError('Path must stay within the city-atlas project directory.')
    return p

@mcp.tool(annotations={'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False})
def blender_inspect_environment()->dict:
    """Inspect the local Blender executable and available scene input. Does not launch Blender."""
    return {'available':BLENDER.is_file(),'executable':str(BLENDER),'scene_available':(ROOT/'outputs/qianren-city.json').is_file(),'project':str(ROOT)}

@mcp.tool(annotations={'readOnlyHint':False,'destructiveHint':False,'idempotentHint':False,'openWorldHint':False})
def blender_start_city_render(scene_path:str='outputs/qianren-city.json',samples:Annotated[int,Field(ge=8,le=256)]=32)->dict:
    """Rebuild a Three.js city JSON in Blender, save an editable .blend, and render two Cycles stills. Starts a background job; use blender_get_render_status to inspect progress."""
    source=inside(scene_path)
    if not BLENDER.is_file():raise ValueError('Blender missing. Set CITY_BLENDER_EXE to an installed blender.exe.')
    if not source.is_file():raise ValueError('Scene input missing. Export the scene from the website first.')
    data=json.loads(source.read_text(encoding='utf-8'))
    if data.get('format')!='qianren-city-v1':raise ValueError('Expected a qianren-city-v1 scene export.')
    job_id='render-'+uuid.uuid4().hex[:10];job_dir=inside('outputs/'+job_id);job_dir.mkdir()
    with (job_dir/'render.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen([str(BLENDER),'-b','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/blender_scene.py'),'--',str(source),str(job_dir),str(samples)],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    jobs[job_id]=process
    meta={'job_id':job_id,'pid':process.pid,'directory':str(job_dir),'status':'running'}
    (job_dir/'job.json').write_text(json.dumps(meta),encoding='utf-8')
    return meta

@mcp.tool(annotations={'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False})
def blender_get_render_status(job_id:Annotated[str,Field(pattern=r'^render-[a-f0-9]{10}$')])->dict:
    """Return job progress, recent log lines, and verified output paths without waiting for rendering."""
    folder=inside('outputs/'+job_id)
    if not folder.is_dir():raise ValueError('Unknown job ID. Use the ID returned by blender_start_city_render.')
    result=folder/'blender-result.json';text=(folder/'render.log').read_text(encoding='utf-8',errors='replace')
    exited=job_id in jobs and jobs[job_id].poll() is not None
    status='complete' if result.is_file() else 'failed' if exited or 'Traceback (most recent call last)' in text or 'Error:' in text else 'running'
    return {'job_id':job_id,'status':status,'recent_log':text.splitlines()[-12:],'outputs':[str(p) for p in folder.iterdir() if p.suffix in ('.png','.blend','.json')],'result':json.loads(result.read_text(encoding='utf-8')) if result.is_file() else None}

if __name__=='__main__':mcp.run(transport='stdio')
