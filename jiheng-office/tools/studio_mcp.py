import json,subprocess,os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
ROOT=Path(__file__).resolve().parents[1];mcp=FastMCP('jiheng_blender_studio');job=None
@mcp.tool()
def blender_render_white_master()->dict:
    """Render the existing editable tower on white using real Cycles and a shadow catcher."""
    global job
    if job and job.poll() is None:return{'status':'running','pid':job.pid}
    (ROOT/'outputs/blender-white-result.json').unlink(missing_ok=True)
    log=(ROOT/'outputs/blender-white.log').open('w',encoding='utf8')
    job=subprocess.Popen([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/render_white.py')],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    return{'status':'running','pid':job.pid}
@mcp.tool()
def blender_studio_status()->dict:
    """Read actual Blender process state and terminal render metadata."""
    path=ROOT/'outputs/blender-white-result.json'
    if path.is_file():return json.loads(path.read_text(encoding='utf8'))
    return{'status':'running' if job and job.poll() is None else 'failed','pid':job.pid if job else None}
if __name__=='__main__':mcp.run(transport='stdio')
