import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/name for name in ['澄和医院.html','澄和医院.blend','hospital-campus.glb','hospital-emergency.glb','hospital-module.mjs','hospital-manifest.json','town-integration.example.mjs','使用与接入说明.txt','THREE-LICENSE.txt','package.json','build.cjs']]
files+=list((ROOT/'src').glob('*'))
files+=list((ROOT/'tools').glob('*.py'))
for name in ['01-graybox.png','02-overview.png','04-overview-final.png','04-mobile.png','03-night.png','verification.json','first-inspection.json','hospital-scene.json','blender-result.json','blend-verification.json','mcp-import-result.json','mcp-render-start-result.json','blender-render.log']:
    p=ROOT/'outputs'/name
    if p.is_file():files.append(p)
files+=list((ROOT/'outputs').glob('blender-*.png'))
manifest={str(f.relative_to(ROOT)).replace('\\','/'):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files}
(ROOT/'交付清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(ROOT/'交付清单.json')
destination=ROOT/'澄和医院_完整交付.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for f in files:archive.write(f,f.relative_to(ROOT))
with zipfile.ZipFile(destination) as archive:assert archive.testzip() is None
print(json.dumps({'zip':str(destination),'bytes':destination.stat().st_size,'files':len(files)},ensure_ascii=True))
