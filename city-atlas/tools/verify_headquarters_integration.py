from pathlib import Path
import json,struct
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/headquarters-integration';OUT.mkdir(parents=True,exist_ok=True);checks={};errors=[]
def check(name,value):
 checks[name]=bool(value);print(('PASS ' if value else 'FAIL ')+name,flush=True)
 assert value,name
with sync_playwright() as p:
 ctx=p.chromium.launch_persistent_context(str(OUT/'browser-profile'),channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'],viewport={'width':1500,'height':1000},device_scale_factor=1,accept_downloads=True)
 page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',polling=100,timeout=180000);page.wait_for_function("!document.querySelector('#loading')",polling=100,timeout=180000)
 check('BLK-3 mounted at correct center',page.evaluate("cityApp.headquartersSite.x===-112&&cityApp.headquartersSite.z===70&&cityApp.plan.blocks.find(b=>b.id==='BLK-3').moduleId==='henglian-corporate-headquarters'"))
 check('main, annex and bridge replace BLK-3 homes',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-3').map(b=>b.id).sort().join(',')==='HENGLIAN-ANNEX,HENGLIAN-BRIDGE,HENGLIAN-MAIN'"))
 check('old four homes and site furniture removed',page.evaluate("async()=>{const m=await import('/city.js');return ['QR-009','QR-010','QR-011','QR-012'].every(id=>!cityApp.scene.getObjectByName(id))&&m.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-3'))}"))
 check('floors and height retained',page.evaluate("cityApp.headquarters.manifest.buildings.every((b,i)=>b.floors===[24,16][i])&&cityApp.headquarters.manifest.buildings[0].height===100"))
 check('all existing landmark modules retained',page.evaluate("['hospital-campus','skyline-one','mall-complex','shanghai-tower','university-campus','dome-arena','amusement-park','linxu-residential','zongyu-mixeduse','qinghe-sports-field','qianxu-slab-residential','nuanting-garden-housing','jiheng-landmark-office','chengxu-residential-courtyard'].every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))&&cityApp.river.manifest.id==='qinglan-river'"))
 check('v2 refined stairs and botanical geometry retained',page.evaluate("cityApp.headquarters.manifest.version===2&&cityApp.headquarters.manifest.stairs.internal.map(s=>s.flights).join(',')==='48,32'&&cityApp.headquarters.manifest.ecology.leaves>90000&&cityApp.headquarters.manifest.ecology.grassBlades===792000"))
 check('one canvas',page.locator('#viewport canvas').count()==1)
 check('no asphalt inside new module',page.evaluate("(()=>{let ok=true;cityApp.headquarters.root.traverse(o=>{if(o.isMesh)ok&&=!/asphalt|沥青/i.test(o.material.name)});return ok})()"))
 check('module stays within parcel, approaches within roadway',page.evaluate("async()=>{const T=await import('three'),b=new T.Box3().setFromObject(cityApp.headquarters.root);return b.min.x>=-168-.01&&b.max.x<=-56+.01&&b.min.z>=14-.01&&b.max.z<=140.01&&Math.abs(b.max.y-100.34)<.01}"))
 page.click('#headquarters-view');page.wait_for_function('Math.abs(cityApp.controls().target.x+112)<.1&&Math.abs(cityApp.controls().target.z-77)<.1',polling=100,timeout=120000);page.screenshot(path=str(OUT/'headquarters-context.png'))
 check('shortcut frames the headquarters',page.evaluate('Math.abs(cityApp.controls().target.x+112)<.1'))
 check('main, annex and bridge selectable',page.evaluate("()=>['MAIN','ANNEX','BRIDGE'].every(id=>{cityApp.select('HENGLIAN-'+id);return cityApp.state.selected.id==='HENGLIAN-'+id})"))
 # Hit a real facade point and verify the city picker climbs through editable subgroups.
 hit=page.evaluate("async()=>{const T=await import('three');const v=new T.Vector3(-135,50,79).project(cityApp.camera());return{x:(v.x+1)*innerWidth/2,y:(1-v.y)*innerHeight/2}}")
 page.evaluate("cityApp.select('JIHENG-ONE')");page.mouse.click(hit['x'],hit['y']);check('actual facade click selects headquarters tower',page.evaluate("cityApp.state.selected?.id?.startsWith('HENGLIAN-')"))
 page.click('#pause');t=page.evaluate('cityApp.headquarters.simulationTime');page.wait_for_timeout(200);check('global pause',t==page.evaluate('cityApp.headquarters.simulationTime'));page.click('#pause')
 page.uncheck('#traffic');page.wait_for_function("!cityApp.headquarters.root.getObjectByName('Resident 0').visible",polling=100);check('global people toggle',page.evaluate("!cityApp.headquarters.root.getObjectByName('Resident 0').visible"));page.check('#traffic')
 page.select_option('#quality','fast');check('fast tier controls headquarters',page.evaluate("cityApp.headquarters.quality==='low'"));page.select_option('#quality','balanced')
 # Ensure the full-detail single-building snapshot remains complete under isolation.
 snap=page.evaluate("()=>{cityApp.select('HENGLIAN-MAIN');const s=cityApp.exportCity('HENGLIAN-MAIN');return{modules:s.modules.map(m=>m.id),owners:[...new Set(s.modules[0].snapshot.objects.map(o=>o.owner))],count:s.modules[0].snapshot.objects.length}}")
 check('single-building snapshot has only main',snap['modules']==['henglian-corporate-headquarters'] and snap['count']>1000 and all(o.startswith('main-') or o=='HENGLIAN-MAIN' for o in snap['owners']))
 page.evaluate("cityApp.select('HENGLIAN-MAIN')")
 with page.expect_download(timeout=180000) as dl:page.click('#export-building')
 dest=OUT/'HENGLIAN-MAIN.glb';dl.value.save_as(dest);raw=dest.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);names=[v.get('name','') for v in doc['nodes']]
 check('independent GLB export',raw[:4]==b'glTF' and 'HENGLIAN-MAIN' in names and 'HENGLIAN-ANNEX' not in names)
 page.click('#focus-building');page.wait_for_function("!cityApp.headquarters.buildings.get('annex').visible",polling=100);check('isolation hides other headquarters towers',page.evaluate("cityApp.headquarters.buildings.get('main').visible&&!cityApp.headquarters.buildings.get('annex').visible"));page.click('#headquarters-view')
 page.wait_for_function("cityApp.headquarters.buildings.get('annex').visible",polling=100)
 check('restoring view shows all towers',page.evaluate('[...cityApp.headquarters.buildings.values()].every(g=>g.visible)'))
 page.click('[data-time=night]');page.wait_for_function("(()=>{let on=false;cityApp.headquarters.root.traverse(o=>{if(o.material?.name==='window-lit'&&o.material.emissiveIntensity>1)on=true});return on})()",polling=100,timeout=120000);page.screenshot(path=str(OUT/'headquarters-night.png'));check('night lights synchronized',True);page.click('[data-time=morning]')
 for key in ['bridge','birds','mechanical']:
  page.locator('#headquarters-'+key).evaluate("e=>e.closest('details').open=true");page.uncheck('#headquarters-'+key);page.wait_for_timeout(150);check('headquarters switch '+key,page.evaluate('(key)=>cityApp.headquartersActivities[key]===false',key));page.check('#headquarters-'+key)
 check('render budget retained',page.evaluate('!!cityApp.performance'))
 page.wait_for_timeout(1500);metrics=page.evaluate('cityApp.metrics()');check('no browser errors',not errors)
 (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'metrics':metrics},indent=2),encoding='utf8');ctx.close()
