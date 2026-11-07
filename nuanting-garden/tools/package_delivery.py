"""Package the standalone HTML, editable model, sources and verified actual renders."""
import json,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'outputs/blender-result.json').read_text(encoding='utf8'))['status']=='complete'
report=json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf8'))
assert all(c['passed'] for c in report['checks']) if isinstance(report['checks'],list) else all(report['checks'].values())
assert all(json.loads((ROOT/'outputs/blender-verification.json').read_text(encoding='utf8'))['checks'].values())
files=[]
for file in ROOT.rglob('*'):
    if not file.is_file() or any(part in ['__pycache__','node_modules','.git'] for part in file.parts):continue
    rel=file.relative_to(ROOT)
    if file.name.startswith('texture_') or file.suffix in ['.blend1','.pyc']:continue
    if rel.parts[0]=='outputs' and file.suffix=='.log' and file.name not in ['blender-render.log','mcp-client.log']:continue
    if file.suffix in ['.html','.mjs','.blend','.glb','.json','.md','.txt','.cjs','.js','.css','.py','.png','.log']:files.append(file)
destination=ROOT.parent/'暖庭花园-完整交付.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for file in sorted(files):archive.write(file,Path(ROOT.name)/file.relative_to(ROOT))
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
    required=['暖庭花园.html','暖庭花园.blend','nuanting-garden-housing.glb','model.mjs','integration-example.mjs','README.md']
    assert all(ROOT.name+'/'+name in archive.namelist() for name in required)
print(json.dumps({'archive':str(destination),'files':len(files),'bytes':destination.stat().st_size,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()},ensure_ascii=True))
