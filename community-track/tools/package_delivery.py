"""Package the offline viewer, editable assets, sources and verified renders."""
import json,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'outputs/blender-result.json').read_text(encoding='utf8'))['status']=='complete'
assert all(c['passed'] for c in json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf8'))['checks'])
assert all(json.loads((ROOT/'outputs/integration-verification.json').read_text(encoding='utf8')).values())
assert all(json.loads((ROOT/'outputs/blender-verification.json').read_text(encoding='utf8'))['checks'].values())
files=[]
for file in ROOT.rglob('*'):
    if not file.is_file() or '__pycache__' in file.parts or 'node_modules' in file.parts:continue
    rel=file.relative_to(ROOT)
    if file.name.startswith('texture_') or file.suffix in ['.blend1','.pyc']:continue
    if rel.parts[0]=='outputs' and file.suffix=='.log' and file.name not in ['blender-render.log','mcp-client-final.log']:continue
    if file.suffix in ['.html','.mjs','.blend','.glb','.json','.md','.txt','.cjs','.js','.css','.py','.png','.log']:files.append(file)
destination=ROOT.parent/'青禾运动场-完整交付.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for file in sorted(files):archive.write(file,Path(ROOT.name)/file.relative_to(ROOT))
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
    required=['青禾运动场.html','青禾运动场.blend','qinghe-sports-field.glb','model.mjs','integration-example.mjs','README.md']
    assert all(ROOT.name+'/'+name in archive.namelist() for name in required)
print(json.dumps({'archive':str(destination),'files':len(files),'bytes':destination.stat().st_size,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()},ensure_ascii=False))
