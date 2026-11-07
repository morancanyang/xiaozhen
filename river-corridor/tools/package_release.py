import json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
names=['青岚河.html','青岚河.blend','qinglan-river.glb','river-model.mjs','river-pass.mjs','town-integration.mjs','river-manifest.json','README.md','THREE-LICENSE.txt','package.json','build.cjs']
files=[(ROOT/n,n) for n in names]
for folder,pattern in [('src','*'),('tools','*.py'),('outputs','*')]:
    for f in sorted((ROOT/folder).glob(pattern)):
        if f.is_file() and f.name!='verified-river.glb' and not f.name.startswith('texture_'):files.append((f,f.relative_to(ROOT).as_posix()))
city=ROOT.parent/'city-atlas/outputs/river-integration'
for f in sorted(city.glob('*')):
    if f.is_file():files.append((f,'outputs/city-integration/'+f.name))
manifest=ROOT/'release-sha256.json';manifest.write_text(json.dumps({name:hashlib.sha256(f.read_bytes()).hexdigest() for f,name in files},ensure_ascii=False,indent=2),encoding='utf8');files.append((manifest,manifest.name))
target=ROOT.parent/'青岚河-完整交付.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f,name in files:z.write(f,'青岚河/'+name)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print(json.dumps({'zip':str(target),'files':len(files),'bytes':target.stat().st_size},ensure_ascii=True))
