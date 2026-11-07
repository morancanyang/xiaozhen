from pathlib import Path
import json,zipfile,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];archive=ROOT.parent/'衡联总部-完整交付.zip'
qa=json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf8'));assert all(qa['checks'].values())
integration=json.loads((ROOT/'outputs/integration-verification.json').read_text(encoding='utf8'));assert all(integration.values())
blend=json.loads((ROOT/'outputs/blender-verification.json').read_text(encoding='utf8'));assert all(blend['checks'].values())
render=json.loads((ROOT/'outputs/blender-result.json').read_text(encoding='utf8'));assert render['status']=='complete'
for path in (ROOT/'outputs').glob('*.png'):
 if path.name.startswith('texture_'):continue
 with Image.open(path) as im:im.verify()
with Image.open(ROOT/'outputs/衡联总部-8K.png') as im:assert im.size==(7680,4320) and all(v>=250 for v in im.getpixel((0,0))[:3])
for id in ['main','annex','bridge']:assert (ROOT/'outputs'/('henglian-'+id+'.glb')).read_bytes()[:4]==b'glTF'
include=[ROOT/n for n in ['衡联总部.html','衡联总部.blend','henglian-corporate-headquarters.glb','model.mjs','ecology.js','stairs.js','headquarters-manifest.json','integration-example.mjs','README.md','package.json','build.cjs','THREE-LICENSE.txt']]
include+=list((ROOT/'src').glob('*'))
include+=[p for p in (ROOT/'tools').glob('*.py') if p.name not in ['setup.py','refine.py','upgrade_v2.py']]
include+=[p for p in (ROOT/'outputs').glob('*') if p.suffix in ['.json','.png','.glb','.js'] and not p.name.startswith('texture_') and p.name not in ['blender-progress.json','delivery.json']]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(include)):z.write(p,'衡联总部/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;count=len(z.namelist())
result={'archive':str(archive),'bytes':archive.stat().st_size,'files':count,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'offline_checks':len(qa['checks']),'integration_checks':len(integration),'blender_checks':len(blend['checks']),'renderer':'Blender Cycles GPU','master_resolution':[7680,4320],'native_block_m':[112,112]}
(ROOT/'outputs/delivery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True),flush=True)
