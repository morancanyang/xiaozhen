"""Package only the reviewed standalone asset and its actual completed renders."""
import hashlib, json, zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
result=json.loads((OUT/'blender-result.json').read_text(encoding='utf8'))
assert result['status']=='complete' and result['engine']=='CYCLES'
snapshot=json.loads((OUT/'scene.json').read_text(encoding='utf8'))
assert result['model_objects']==len(snapshot['objects'])
checks=json.loads((OUT/'verification.json').read_text(encoding='utf8'))
assert checks['checks'] and all(c['passed'] for c in checks['checks'])
assert not checks.get('errors') and not checks.get('requests')
for shot in result['renders']:
    file=Path(shot['path'])
    with Image.open(file) as image:
        assert image.size==tuple(shot['resolution'])
        assert any(a!=b for a,b in image.convert('RGB').getextrema())

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
manifest={**snapshot['metadata'],'integration':{'factory':'createMixedUseResidential','module':'mixeduse-module.mjs','example':'integration-example.mjs','hostOwns':['THREE','renderer','scene','camera','animationLoop'],'methods':['update','setQuality','setTimeOfDay','getBounds','exportGLB','exportScene','dispose']},'verification':{'passed':len(checks['checks']),'file':'outputs/verification.json'},'render':result,'sha256':{n:sha(ROOT/n) for n in ('棕屿里.html','棕屿里.glb','棕屿里.blend','mixeduse-module.mjs')}}
(ROOT/'residential-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
archive=ROOT.parent/'棕屿里-完整交付.zip'
count=0
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for file in sorted(ROOT.rglob('*')):
        rel=file.relative_to(ROOT)
        if not file.is_file() or any(p in ('node_modules','__pycache__','.git') for p in rel.parts) or file.suffix in ('.blend1','.tmp','.pyc'):continue
        z.write(file,Path('棕屿里')/rel);count+=1
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'archive':str(archive),'files':count,'bytes':archive.stat().st_size,'checks':len(checks['checks']),'engine':result['engine'],'device':result['device'],'images':len(result['renders'])},ensure_ascii=True))
