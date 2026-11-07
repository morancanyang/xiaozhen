import json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
qa=json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf8'))
render=json.loads((ROOT/'outputs/blender-result.json').read_text(encoding='utf8'))
assert not qa['errors'] and all(c['passed'] for c in qa['checks'])
assert render['status']=='complete' and len(render['views'])==7
for view in render['views']:assert (ROOT/'outputs'/('blender-'+view.lower()+'.png')).stat().st_size>10000
for name in ['云际中心.html','云际中心.blend','skyline-one.glb','skyline-module.mjs','skyline-manifest.json','README.md','town-integration.example.mjs']:assert (ROOT/name).stat().st_size>100
archive=ROOT.parent/'云际中心-完整交付.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for file in sorted(ROOT.rglob('*')):
        if not file.is_file() or '__pycache__' in file.parts or file.name=='mcp_last_result.json':continue
        z.write(file,'云际中心/'+str(file.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    count=len(z.infolist())
print(json.dumps({'archive':str(archive),'size_bytes':archive.stat().st_size,'files':count,'checks_passed':len(qa['checks']),'blender_views':len(render['views'])},ensure_ascii=True))
