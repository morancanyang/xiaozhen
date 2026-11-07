"""Actual local MCP bridge for the requested visible Blender rendering session."""
import json
import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs'
BLENDER = Path(os.environ.get('CITY_BLENDER_EXE', r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'))
mcp = FastMCP('qianxu-slab-residential-blender')
job = None

@mcp.tool()
def blender_start_slab_render() -> dict:
    """Open a NEW visible Blender window and physically render the exact exported residential model."""
    global job
    if job is not None and job.poll() is None:
        return {'status':'running', 'pid':job.pid, 'visible_window':True}
    if not BLENDER.is_file():
        raise ValueError('Local Blender executable was not found')
    if not (OUT/'scene.json').is_file():
        raise ValueError('Export the reviewed Three.js model to outputs/scene.json first')
    for name in ('blender-progress.json','blender-result.json'):
        (OUT/name).unlink(missing_ok=True)
    with (OUT/'blender-visible.log').open('w',encoding='utf8') as log:
        # This interactive window is explicitly requested by the user.
        job = subprocess.Popen([str(BLENDER),'--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/render_blender.py')], stdout=log, stderr=subprocess.STDOUT, creationflags=0)
    return {'status':'running', 'pid':job.pid, 'visible_window':True, 'log':str(OUT/'blender-visible.log')}

@mcp.tool()
def blender_slab_status() -> dict:
    """Read real import/render progress without blocking the user's desktop."""
    for name in ('blender-result.json','blender-progress.json'):
        file = OUT/name
        if file.is_file():
            data = json.loads(file.read_text(encoding='utf8'))
            data['window_running'] = job is not None and job.poll() is None
            data['pid'] = job.pid if job is not None else None
            if job is not None and job.poll() is not None and data['status']!='complete':
                data['status'] = 'failed'
                data['exit_code'] = job.returncode
            return data
    log = OUT/'blender-visible.log'
    return {'status':'failed' if job is not None and job.poll() is not None else 'opening', 'pid':job.pid if job is not None else None, 'log_tail':log.read_text(encoding='utf8',errors='replace').splitlines()[-8:] if log.is_file() else []}

if __name__ == '__main__':
    mcp.run(transport='stdio')
