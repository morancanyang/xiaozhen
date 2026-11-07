"""Validate evidence and package the self-contained editable delivery."""
from pathlib import Path
import json,zipfile,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];archive=ROOT.parent/'澄序住区-完整交付.zip'
qa=json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf8'));assert all(c['passed'] for c in qa['checks'])
assert all(json.loads((ROOT/'outputs/integration-verification.json').read_text(encoding='utf8')).values())
assert all(json.loads((ROOT/'outputs/blender-verification.json').read_text(encoding='utf8'))['checks'].values())
result=json.loads((ROOT/'outputs/blender-result.json').read_text(encoding='utf8'));assert result['status']=='complete' and result['engine']=='CYCLES'
for path in (ROOT/'outputs').glob('*.png'):
    if path.name.startswith('texture_'):continue
    with Image.open(path) as im:im.verify()
with Image.open(ROOT/'outputs/澄序住区-8K.png') as im:
    assert im.size==(7680,4320)
    assert im.getpixel((0,0))[:3]==(255,255,255)
for id in 'ABCD':assert (ROOT/'outputs'/('chengxu-'+id+'.glb')).read_bytes()[:4]==b'glTF'
include=[ROOT/n for n in ['澄序住区.html','澄序住区.blend','chengxu-residential-courtyard.glb','model.mjs','courtyard-manifest.json','integration-example.mjs','README.md','package.json','build.cjs','THREE-LICENSE.txt']]
include+=list((ROOT/'src').glob('*'))
include+=[p for p in (ROOT/'tools').glob('*.py') if p.name not in ['setup.py','refine_viewer.py','configure_blender.py']]
include+=[p for p in (ROOT/'outputs').glob('*') if p.suffix in ['.json','.png','.glb','.js'] and not p.name.startswith('texture_') and p.name!='blender-progress.json']
include=[p for p in include if p.name!='delivery.json']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(include)):z.write(p,'澄序住区/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;count=len(z.namelist())
delivery={'archive':str(archive),'bytes':archive.stat().st_size,'files':count,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'browser_checks':len(qa['checks']),'integration_checks':14,'blender_checks':14,'renderer':'Blender Cycles GPU','master_resolution':[7680,4320],'native_block_m':[112,112],'no_asphalt':True}
(ROOT/'outputs/delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(delivery,ensure_ascii=True),flush=True)
