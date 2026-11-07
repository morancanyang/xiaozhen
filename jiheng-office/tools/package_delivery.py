"""Package only the editable delivery, source, renders and verification evidence."""
from pathlib import Path
import zipfile,hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];archive=ROOT.parent/'霁衡中心-完整交付.zip'
report=json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf8'))
assert all(c['passed'] for c in report['checks'])
assert all(json.loads((ROOT/'outputs/integration-verification.json').read_text(encoding='utf8')).values())
assert all(json.loads((ROOT/'outputs/blender-verification.json').read_text(encoding='utf8'))['checks'].values())
render=json.loads((ROOT/'outputs/blender-white-result.json').read_text(encoding='utf8'));assert render['status']=='complete'
with Image.open(ROOT/'outputs/霁衡中心-8K.png') as im:
    assert im.size==(7680,4320)
    assert all(c==255 for c in im.getpixel((0,0)))
with Image.open(ROOT/'outputs/霁衡中心-8K.png') as im:
    im.verify()
include=[ROOT/n for n in ['霁衡中心.html','霁衡中心.blend','model.mjs','office-manifest.json','integration-example.mjs','jiheng-landmark-office.glb','README.md','package.json','build.cjs','THREE-LICENSE.txt']]
include+=list((ROOT/'src').glob('*'))
include.append(ROOT/'outputs/host-three-test.js')
include+=[p for p in (ROOT/'tools').glob('*.py') if p.name not in ['debug_zoom.py','inspect_compositor.py']]
include+=[p for p in (ROOT/'outputs').glob('*') if p.suffix in ['.json','.png','.glb'] and not p.name.startswith('texture_') and p.name!='blender-progress.json']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(include)):z.write(p,'霁衡中心/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None;count=len(z.namelist())
result={'archive':str(archive),'bytes':archive.stat().st_size,'files':count,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'browser_checks':len(report['checks']),'master_resolution':[7680,4320],'white_background':True}
(ROOT/'outputs/delivery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True),flush=True)
