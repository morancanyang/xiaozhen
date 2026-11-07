"""Project-local MCP bridge: launches only isolated Blender GUI processes owned by this service."""
import json, subprocess, os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
ROOT = Path(__file__).resolve().parents[1]
BLENDER = Path(os.environ.get('GARDEN_BLENDER_EXE', r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'))
mcp = FastMCP('nuanting_garden_blender'); job = None

@mcp.tool()
def blender_start_garden_render(night_only: bool = False) -> dict:
    """Import the actual Three.js housing geometry and render seven views in a visible Blender window."""
    global job
    if job and job.poll() is None: return {'status': 'running', 'pid': job.pid}
    if not BLENDER.is_file(): raise FileNotFoundError(str(BLENDER))
    if not (ROOT / 'outputs/garden-scene.json').is_file(): raise ValueError('Export garden-scene.json first')
    if night_only and not (ROOT / '暖庭花园.blend').is_file(): raise ValueError('A full render must be created before night-only refinement')
    (ROOT / 'outputs/blender-result.json').unlink(missing_ok=True)
    log = (ROOT / 'outputs/blender-render.log').open('w', encoding='utf8')
    args = [str(BLENDER), '--factory-startup']
    if night_only: args += [str(ROOT / '暖庭花园.blend')]
    args += ['--python-exit-code', '1', '--python', str(ROOT / 'tools/render_blender.py')]
    if night_only: args += ['--', '--night-only']
    job = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, creationflags=0)
    return {'status': 'running', 'pid': job.pid, 'log': str(ROOT / 'outputs/blender-render.log')}

@mcp.tool()
def blender_open_garden_scene() -> dict:
    """Open the editable delivered garden scene and show the completed overview render."""
    global job
    if job and job.poll() is None: return {'status': 'already_open', 'pid': job.pid}
    job = subprocess.Popen([str(BLENDER), str(ROOT / '暖庭花园.blend'), '--python', str(ROOT / 'tools/show_scene.py')], creationflags=0)
    return {'status': 'opened', 'pid': job.pid}

@mcp.tool()
def blender_garden_status() -> dict:
    """Return actual Blender progress, renderer metadata, and GUI process liveness."""
    result = ROOT / 'outputs/blender-result.json'; log = ROOT / 'outputs/blender-render.log'
    running = job is not None and job.poll() is None
    if result.is_file(): return {**json.loads(result.read_text(encoding='utf8')), 'window_running': running, 'pid': job.pid if job else None}
    return {'status': 'running' if running else 'idle' if job is None else 'failed', 'pid': job.pid if job else None, 'log': log.read_text(encoding='utf8', errors='replace').splitlines()[-5:] if log.is_file() else []}

if __name__ == '__main__': mcp.run(transport='stdio')
