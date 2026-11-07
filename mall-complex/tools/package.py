"""Create a curated delivery archive after checking the real output files."""
import hashlib,json,zipfile,struct
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
verification=json.loads((OUT/'verification.json').read_text(encoding='utf-8'));render=json.loads((OUT/'blender-result.json').read_text(encoding='utf-8'))
assert len(verification['checks'])>=35 and not verification['errors']
assert render['status']=='complete' and render['preview'] is False and render['engine']=='CYCLES'
assert Image.open(OUT/'blender-hero-8k.png').size==(7680,4320)
assert Image.open(OUT/'browser-4k.png').size==(3840,2160)
assert (ROOT/'src/model.js').read_bytes()==(ROOT/'mall-module.mjs').read_bytes()
blend_header=(ROOT/'陶里汇商城.blend').read_bytes()[:7]
assert blend_header==b'BLENDER' or blend_header.startswith(bytes.fromhex('28b52ffd')) or blend_header.startswith(bytes.fromhex('1f8b'))
assert (ROOT/'陶里汇商城.glb').read_bytes()[:4]==b'glTF'
assert (OUT/'商城动态巡游.webm').stat().st_size>100000
files=[ROOT/n for n in ['商城综合体.html','接入演示.html','mall-module.mjs','town-integration.example.mjs','陶里汇商城.glb','陶里汇商城.blend','使用说明.md','THREE-LICENSE.txt','build.cjs','package.json']]
files+=list((ROOT/'src').glob('*'))+list((ROOT/'tools').glob('*.py'))
files+=[p for p in OUT.iterdir() if p.suffix in ['.png','.json','.webm','.log'] and not p.name.startswith('texture-') and not p.name.startswith('02-') and p.name!='blender-preview.png']
manifest={'parcel_metres':[112,112],'height_metres':31.175,'browser_checks':len(verification['checks']),'render_engine':'CYCLES','samples':render['samples'],'device':render['device'],'hero_pixels':[7680,4320],'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
(ROOT/'交付清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(ROOT/'交付清单.json')
archive=ROOT/'陶里汇商城-完整交付.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(files)):z.write(p,str(p.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'file_count':len(set(files)),'checks':len(verification['checks']),'8K':[7680,4320]},ensure_ascii=True))
