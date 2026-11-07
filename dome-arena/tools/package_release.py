import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
names=['穹光体育中心.html','穹光体育中心.blend','arena-module.mjs','integration-example.mjs','arena-manifest.json','dome-arena.glb','README.md','THREE-LICENSE.txt','package.json','build.cjs']
files=[ROOT/n for n in names]+sorted((ROOT/'src').glob('*'))+sorted((ROOT/'tools').glob('*.py'))
files+=sorted(f for f in (ROOT/'outputs').iterdir() if (f.suffix=='.json' or f.name=='blender-render.log' or f.suffix=='.png' and not f.name.startswith('texture_')))
files=[f for f in files if f.name!='mcp_client.py']
hashes={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
manifest=ROOT/'release-sha256.json';manifest.write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf8');files.append(manifest)
target=ROOT.parent/'穹光体育中心-完整交付.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f in files:z.write(f,Path('穹光体育中心')/f.relative_to(ROOT))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
print(json.dumps({'zip':str(target),'files':len(files),'bytes':target.stat().st_size},ensure_ascii=True))
