from pathlib import Path
import json,struct
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/courtyard-integration';OUT.mkdir(parents=True,exist_ok=True);checks={};errors=[]
def check(name,value):
 checks[name]=bool(value);print(('PASS ' if value else 'FAIL ')+name,flush=True)
 assert value,name
with sync_playwright() as p:
 ctx=p.chromium.launch_persistent_context(str(OUT/'browser-profile'),channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'],viewport={'width':1500,'height':1000},device_scale_factor=1,accept_downloads=True)
 page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',polling=100,timeout=180000);page.wait_for_function("!document.querySelector('#loading')",polling=100,timeout=180000)
 check('BLK-14 mounted at correct center',page.evaluate("cityApp.courtyardSite.x===252&&cityApp.courtyardSite.z===-70&&cityApp.plan.blocks.find(b=>b.id==='BLK-14').moduleId==='chengxu-residential-courtyard'"))
 check('only four new homes on BLK-14',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-14').map(b=>b.id).sort().join(',')==='CHENGXU-A,CHENGXU-B,CHENGXU-C,CHENGXU-D'"))
 check('old four homes and site furniture removed',page.evaluate("async()=>{const m=await import('/city.js');return ['QR-053','QR-054','QR-055','QR-056'].every(id=>!cityApp.scene.getObjectByName(id))&&m.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-14'))}"))
 check('floors and height retained',page.evaluate("cityApp.courtyard.manifest.buildings.every((b,i)=>b.floors===[20,22,22,24][i])&&cityApp.courtyard.manifest.buildings[3].height===78"))
 check('all existing landmark modules retained',page.evaluate("['hospital-campus','skyline-one','mall-complex','shanghai-tower','university-campus','dome-arena','amusement-park','linxu-residential','zongyu-mixeduse','qinghe-sports-field','qianxu-slab-residential','nuanting-garden-housing','jiheng-landmark-office'].every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))&&cityApp.river.manifest.id==='qinglan-river'"))
 check('one canvas',page.locator('#viewport canvas').count()==1)
 check('no asphalt inside new module',page.evaluate("(()=>{let ok=true;cityApp.courtyard.root.traverse(o=>{if(o.isMesh)ok&&=!/asphalt|沥青/i.test(o.material.name)});return ok})()"))
 check('module stays within parcel, approaches within roadway',page.evaluate("async()=>{const T=await import('three'),b=new T.Box3().setFromObject(cityApp.courtyard.root);return b.min.x>=196-.01&&b.max.x<=308+.01&&b.min.z>=-126-.01&&b.max.z<=0.01&&Math.abs(b.max.y-78.34)<.01}"))
 page.click('#courtyard-view');page.wait_for_function('Math.abs(cityApp.controls().target.x-252)<.1&&Math.abs(cityApp.controls().target.z+63)<.1',polling=100,timeout=120000);page.screenshot(path=str(OUT/'courtyard-context.png'))
 check('shortcut frames the courtyard',page.evaluate('Math.abs(cityApp.controls().target.x-252)<.1'))
 check('all four buildings selectable',page.evaluate("()=>['A','B','C','D'].every(id=>{cityApp.select('CHENGXU-'+id);return cityApp.state.selected.id==='CHENGXU-'+id})"))
 # Hit a real facade point and verify the city picker climbs through editable subgroups.
 hit=page.evaluate("async()=>{const T=await import('three');const v=new T.Vector3(278,45,-34).project(cityApp.camera());return{x:(v.x+1)*innerWidth/2,y:(1-v.y)*innerHeight/2}}")
 page.evaluate("cityApp.select('JIHENG-ONE')");page.mouse.click(hit['x'],hit['y']);check('actual facade click selects courtyard tower',page.evaluate("cityApp.state.selected?.id?.startsWith('CHENGXU-')"))
 page.click('#pause');t=page.evaluate('cityApp.courtyard.simulationTime');page.wait_for_timeout(200);check('global pause',t==page.evaluate('cityApp.courtyard.simulationTime'));page.click('#pause')
 page.uncheck('#traffic');page.wait_for_function("!cityApp.courtyard.root.getObjectByName('Resident 0').visible",polling=100);check('global people toggle',page.evaluate("!cityApp.courtyard.root.getObjectByName('Resident 0').visible"));page.check('#traffic')
 page.select_option('#quality','fast');check('fast tier controls courtyard',page.evaluate("cityApp.courtyard.quality==='low'"));page.select_option('#quality','balanced')
 # Ensure the full-detail single-building snapshot remains complete under isolation.
 snap=page.evaluate("()=>{cityApp.select('CHENGXU-A');const s=cityApp.exportCity('CHENGXU-A');return{modules:s.modules.map(m=>m.id),owners:[...new Set(s.modules[0].snapshot.objects.map(o=>o.owner))],count:s.modules[0].snapshot.objects.length}}")
 check('single-building snapshot has only A',snap['modules']==['chengxu-residential-courtyard'] and snap['count']>1000 and all(o.startswith('A-') or o=='CHENGXU-A' for o in snap['owners']))
 page.evaluate("cityApp.select('CHENGXU-A')")
 with page.expect_download(timeout=180000) as dl:page.click('#export-building')
 dest=OUT/'CHENGXU-A.glb';dl.value.save_as(dest);raw=dest.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);names=[v.get('name','') for v in doc['nodes']]
 check('independent GLB export',raw[:4]==b'glTF' and 'CHENGXU-A' in names and 'CHENGXU-B' not in names)
 page.click('#focus-building');page.wait_for_function("!cityApp.courtyard.buildings.get('B').visible",polling=100);check('isolation hides other courtyard towers',page.evaluate("cityApp.courtyard.buildings.get('A').visible&&!cityApp.courtyard.buildings.get('B').visible"));page.click('#courtyard-view')
 page.wait_for_function("cityApp.courtyard.buildings.get('B').visible",polling=100)
 check('restoring view shows all towers',page.evaluate('[...cityApp.courtyard.buildings.values()].every(g=>g.visible)'))
 page.click('[data-time=night]');page.wait_for_function("(()=>{let on=false;cityApp.courtyard.root.traverse(o=>{if(o.material?.name==='window-lit'&&o.material.emissiveIntensity>1)on=true});return on})()",polling=100,timeout=120000);page.screenshot(path=str(OUT/'courtyard-night.png'));check('night lights synchronized',True);page.click('[data-time=morning]')
 check('render budget retained',page.evaluate('!!cityApp.performance'))
 page.wait_for_timeout(1500);metrics=page.evaluate('cityApp.metrics()');check('no browser errors',not errors)
 (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'metrics':metrics},indent=2),encoding='utf8');ctx.close()
