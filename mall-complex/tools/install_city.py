"""Apply only the BLK-10 integration to an isolated, freshly opened Site checkout."""
import json,re,shutil,sys
from pathlib import Path
town=Path(__file__).resolve().parents[2]/'city-atlas';release=Path(sys.argv[1]).resolve()
for name in ['mall-model.js','mall-site.js']:shutil.copyfile(town/'dist'/name,release/'dist'/name)
mainfile=release/'dist/main.js';s=mainfile.read_text(encoding='utf-8')
def replace_once(old,new):
    global s
    if old not in s:raise RuntimeError('Source changed: '+old[:90])
    s=s.replace(old,new,1)
if "import {installMall}" not in s:
    replace_once("import {installSkyline} from './skyline-site.js';","import {installSkyline} from './skyline-site.js';\nimport {installMall} from './mall-site.js';")
    replace_once('let city,life,hospitalIntegration,skylineIntegration','let city,life,hospitalIntegration,skylineIntegration,mallIntegration')
    replace_once('skylineIntegration=installSkyline(city);','skylineIntegration=installSkyline(city);mallIntegration=installMall(city);')
    match=re.search(r"^\$\('#city-count'\).*",s,re.M)
    replace_once(match.group(),match.group().replace('`;',' · 陶里汇`;'))
    replace_once("if(b.moduleId==='skyline-one')", "if(b.moduleId==='skyline-one'||b.moduleId==='mall-complex')")
    callback=next(line for line in (town/'dist/main.js').read_text(encoding='utf-8').splitlines() if line.startswith("$('#mall-view').onclick"))
    replace_once("$('#skyline-flight').onchange=e=>state.skylineFlight=e.target.checked;","$('#skyline-flight').onchange=e=>state.skylineFlight=e.target.checked;\n"+callback)
    replace_once('skylineIntegration.tower.setTimeOfDay(p.night*t);','skylineIntegration.tower.setTimeOfDay(p.night*t);mallIntegration.mall.setTimeOfDay(p.night*t);')
    needle="skylineIntegration.tower.setQuality({cinema:'high',balanced:'medium',fast:'low'}[state.quality]);"
    replace_once(needle,needle+"mallIntegration.mall.setQuality({cinema:'high',balanced:'medium',fast:'low'}[state.quality]);")
    tick="  mallIntegration.mall.update(dt,{time:simTime,paused:state.paused,people:state.traffic,wind:state.wind,cameraDistance:camera.position.distanceTo(mallIntegration.mall.model.position)*.6});"
    replace_once('  if(lightProgress<1){lightProgress=Math.min(1,lightProgress+rawDt*.7);applyLight(lightProgress);}','  if(lightProgress<1){lightProgress=Math.min(1,lightProgress+rawDt*.7);applyLight(lightProgress);}\n'+tick)
    export="  if(!onlyId||onlyId==='MALL-TAOLI'){const m=mallIntegration.mall;modules.push({id:'mall-complex',blockId:mallIntegration.site.blockId,position:m.model.position.toArray(),rotation:m.model.rotation.toArray(),source:'./mall-model.js',snapshotSpace:'world',snapshot:m.exportScene()});}"
    replace_once('  if(modules.length)data.modules=modules;',export+'\n  if(modules.length)data.modules=modules;')
    replace_once('window.cityApp={','window.cityApp={mall:mallIntegration.mall,mallSite:mallIntegration.site,')
s=s.replace('const rawDt=Math.min((now-last)/1000,.05);','const rawDt=Math.max(0,Math.min((now-last)/1000,.05));')
s=s.replace('cameraDistance:camera.position.distanceTo(mallIntegration.mall.model.position)}','cameraDistance:camera.position.distanceTo(mallIntegration.mall.model.position)*.6}')
mainfile.write_text(s,encoding='utf-8')
cityfile=release/'dist/city.js';s=cityfile.read_text(encoding='utf-8');match=re.search(r'const CUSTOM_BLOCKS=new Set\(\[([^\]]+)\]\);',s)
if not match:raise RuntimeError('Custom block registry missing')
if 'BLK-10' not in match.group(1):s=s[:match.start(1)]+match.group(1)+",'BLK-10'"+s[match.end(1):]
cityfile.write_text(s,encoding='utf-8')
html=release/'dist/index.html';s=html.read_text(encoding='utf-8')
if 'id="mall-view"' not in s:s=re.sub(r'(<button id="skyline-view"[^>]*>.*?</button>)',r'\1<button id="mall-view" class="hospital-jump">陶里汇商城 · BLK-10 ↗</button>',s,count=1)
html.write_text(s,encoding='utf-8')
packagefile=release/'package.json';package=json.loads(packagefile.read_text(encoding='utf-8'))
if 'dist/mall-model.js' not in package['scripts']['check']:package['scripts']['check']+=' && node --check dist/mall-model.js && node --check dist/mall-site.js'
packagefile.write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(release/'tools').mkdir(exist_ok=True);shutil.copyfile(town/'tools/verify_mall_integration.py',release/'tools/verify_mall_integration.py')
readme=release/'README.md';s=readme.read_text(encoding='utf-8')
if '## 陶里汇商城接入' not in s:s+='\n\n## 陶里汇商城接入\n\nBLK-10（东岸内侧第二排，中心 x=112、z=-70）接入完整陶里汇商城，替换该地块原四栋住宅及内部景观。占地 112 × 112 米，六层退台，最高约 31.175 米。入口朝 +Z，完成面 y=0.34 与城市铺装齐平，设置公共步行坡接，外围道路和中央河道预留区保持不变。\n\n右侧“陶里汇商城 · BLK-10”可快速定位。商城作为 MALL-TAOLI 独立选择、观察和导出，动态、风、访客、昼夜及画质跟随城市控制；整体 GLB 与 JSON 模块快照均包含商城。dist/mall-model.js 为独立模型工厂，dist/mall-site.js 负责地块安装、过渡及导出协议。\n\n运行 python tools/verify_mall_integration.py 会临时启动本地服务并检查地块位置、原住宅清理、其他建筑保持、动态联动、选择与取景、GLB/JSON 导出和手机布局。结果写入 outputs/mall-integration/。\n'
readme.write_text(s,encoding='utf-8');print('Installed only the BLK-10 mall integration in',release)
