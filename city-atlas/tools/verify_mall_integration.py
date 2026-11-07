import json,struct,subprocess,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/mall-integration';OUT.mkdir(parents=True,exist_ok=True)
BASE='e84f29f47e53938f0902529654a253c46194b6d5'
baseline=subprocess.check_output(['git','show',BASE+':dist/city.js'],cwd=ROOT).decode('utf-8')
checks=[];errors=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
    if not value:raise AssertionError(name)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True)
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready');page.wait_for_timeout(1200)
    check('BLK-10 is the eastern inner-column second parcel',page.evaluate("cityApp.mallSite.blockId==='BLK-10'&&cityApp.mallSite.x===112&&cityApp.mallSite.z===-70"))
    check('Exactly the four target residences have been removed',page.evaluate("['QR-037','QR-038','QR-039','QR-040'].every(id=>!cityApp.scene.getObjectByName(id))"))
    check('The full mall is the only selectable building in BLK-10',page.evaluate("(()=>{const b=cityApp.plan.buildings.filter(b=>b.blockId==='BLK-10');return b.length===1&&b[0].id==='MALL-TAOLI'&&b[0].floors===6&&b[0].height===31.175})()"))
    check('16 parcels with four homes per unmodified block and registered landmarks',page.evaluate('cityApp.plan.blocks.length===16&&cityApp.plan.buildings.length===cityApp.plan.blocks.filter(b=>!b.moduleId).length*4+cityApp.plan.buildings.filter(b=>b.moduleId).length'))
    compare=page.evaluate('''async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),old=await import(url);URL.revokeObjectURL(url);const custom=new Set(cityApp.plan.blocks.filter(b=>b.moduleId).map(b=>b.id)),prior=old.buildCity(new T.Scene()),expected=prior.plan.buildings.filter(b=>!custom.has(b.blockId)),current=cityApp.plan.buildings.filter(b=>!b.moduleId);const match=expected.length>0&&expected.length===current.length&&expected.every(b=>current.some(c=>JSON.stringify(b)===JSON.stringify(c)));const gs=new Set(),ms=new Set(),ts=new Set();prior.root.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material){ms.add(o.material);if(o.material.map)ts.add(o.material.map)}});gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());ts.forEach(t=>t.dispose());return match;}''',baseline)
    check('All residences outside custom parcels keep IDs dimensions positions and materials',compare)
    check('Hospital and skyline remain installed on their original parcels',page.evaluate("cityApp.hospitalSite.blockId==='BLK-13'&&cityApp.skylineSite.blockId==='BLK-2'&&cityApp.plan.buildings.filter(b=>b.moduleId==='hospital-campus').length===4&&!!cityApp.scene.getObjectByName('SKY-ONE')"))
    check('Future 64m river corridor remains free of buildings',page.evaluate('cityApp.plan.buildings.every(b=>Math.abs(b.x)-b.width/2>=56)'))
    check('Old target landscaping paving and parked cars are removed',page.evaluate("cityApp.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-10'))"))
    check('Mall geometry fits the target 112m square and meets the sidewalk height',page.evaluate('''()=>{const b=cityApp.mall.getBounds(),s=cityApp.mallSite;return b.min.x>=s.x-56&&b.max.x<=s.x+56&&b.min.z>=s.z-56&&b.max.z<=s.z+56&&s.groundY===.34&&cityApp.mall.model.scale.toArray().every(v=>v===1)}'''))
    check('The public pedestrian approach is graded to the existing road edge',page.evaluate("!!cityApp.scene.getObjectByName('Mall_gently_graded_public_approach')"))
    check('The original blue grey asphalt stays unchanged',page.evaluate("(()=>{const o=cityApp.scene.getObjectByName('world:asphalt'),c=o.material.map.image,p=c.getContext('2d').getImageData(0,0,1,1).data;return Math.abs(p[0]-8)<5&&Math.abs(p[1]-39)<5&&Math.abs(p[2]-66)<5})()"))
    check('Only one WebGL viewer canvas is created',page.locator('#viewport canvas').count()==1)
    page.screenshot(path=str(OUT/'city-overview.png'))
    page.locator('#mall-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x-112)<.1&&Math.abs(cityApp.controls().target.z+70)<.1',timeout=15000);page.wait_for_timeout(600)
    page.screenshot(path=str(OUT/'mall-context.png'));check('Mall shortcut reaches BLK-10',page.evaluate("cityApp.state.selected.id==='MALL-TAOLI'"))
    click=page.evaluate("async()=>{const T=await import('three'),v=new T.Vector3(112,23,-39.4).project(cityApp.camera());return{x:(v.x*.5+.5)*innerWidth,y:(.5-v.y*.5)*innerHeight}}")
    page.evaluate('cityApp.state.selected=null');page.mouse.click(click['x'],click['y']);check('Ray picking the main facade selects the mall',page.evaluate("cityApp.state.selected?.id==='MALL-TAOLI'"))
    page.locator('#focus-building').click();page.wait_for_timeout(2000);page.screenshot(path=str(OUT/'mall-isolated.png'))
    check('Single-building view frames the complete mall parcel',page.evaluate('''async()=>{const T=await import('three'),b=cityApp.mall.getBounds(),c=cityApp.camera();return [b.min.x,b.max.x].every(x=>[b.min.y,b.max.y].every(y=>[b.min.z,b.max.z].every(z=>{const v=new T.Vector3(x,y,z).project(c);return Math.abs(v.x)<.98&&Math.abs(v.y)<.98})))}'''))
    with page.expect_download(timeout=60000) as d:page.locator('#export-building').click()
    single=OUT/'BLK-10-mall.glb';d.value.save_as(str(single));raw=single.read_bytes();length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+length]);names=[n.get('name','') for n in gltf['nodes']]
    check('Selected GLB contains the mall atrium automatic doors and landscape',raw[:4]==b'glTF' and all(n in names for n in ['MALL-TAOLI','Glazed_atrium_roof','Automatic_door_left','Landscape']))
    page.locator('#close-selection').click();page.locator('#mall-view').click();page.wait_for_timeout(2100)
    page.locator('#pause').click();before=page.evaluate('({time:cityApp.mall.time,door:cityApp.mall.model.getObjectByName("Automatic_door_left").position.x,sky:cityApp.skyline.simulationTime})');page.wait_for_timeout(450)
    check('Global pause freezes mall dynamics and existing skyline',before==page.evaluate('({time:cityApp.mall.time,door:cityApp.mall.model.getObjectByName("Automatic_door_left").position.x,sky:cityApp.skyline.simulationTime})'))
    page.locator('#pause').click();page.wait_for_timeout(200);check('Resuming advances mall dynamics',page.evaluate('cityApp.mall.time')>before['time'])
    page.locator('#traffic').uncheck();page.wait_for_timeout(150);check('City traffic toggle also controls mall visitors',not page.evaluate('cityApp.mall.parts.people.visible'));page.locator('#traffic').check()
    page.locator('#wind').uncheck();page.wait_for_timeout(150);check('Wind switch freezes mall banners',page.evaluate("(()=>{const p=cityApp.mall.model.getObjectByName('Wind_banner').geometry.attributes.position;return Array.from(p.array).filter((v,i)=>i%3===2).every(v=>v===0)})()"));page.locator('#wind').check()
    page.locator('#quality').select_option('fast');check('Low quality synchronizes all three custom modules',page.evaluate("cityApp.mall.quality==='low'&&cityApp.skyline.quality==='low'&&cityApp.hospital.quality==='low'"));page.locator('#quality').select_option('cinema');page.wait_for_timeout(250)
    check('Cinema quality enables physical mall glazing',page.evaluate("cityApp.mall.quality==='high'&&cityApp.mall.materials['Shop glazing'].transmission>.7"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click();page.wait_for_timeout(2100);check('City night preset illuminates the mall',page.evaluate("cityApp.mall.materials['Warm architectural light'].emissiveIntensity>2"));page.screenshot(path=str(OUT/'mall-night.png'));page.locator('[data-time=morning]').click();page.wait_for_timeout(1700)
    page.evaluate("cityApp.select('QR-010')");page.locator('#focus-building').click();page.wait_for_timeout(1900)
    check('Whole-city JSON retains all installed modules while another building is isolated',page.evaluate("(()=>{const d=cityApp.exportCity();return d.modules.length===cityApp.plan.blocks.filter(b=>b.moduleId).length&&d.modules.every(m=>m.snapshotSpace==='world'&&m.snapshot.objects.length>100)&&d.modules.find(m=>m.id==='mall-complex').snapshot.objects.every(o=>o.owner==='MALL-TAOLI')})()"))
    check('Mall-only JSON has the correct world location and only the selected module',page.evaluate("(()=>{const d=cityApp.exportCity('MALL-TAOLI');return d.modules.length===1&&d.modules[0].blockId==='BLK-10'&&d.modules[0].position[0]===112&&d.modules[0].position[2]===-70})()"))
    with page.expect_download(timeout=60000) as d:page.locator('#export').click()
    whole=OUT/'town-with-mall.glb';d.value.save_as(str(whole));raw=whole.read_bytes();length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+length]);names=[n.get('name','') for n in gltf['nodes']]
    check('Whole-city GLB restores mall and preserves hospital and skyline',all(n in names for n in ['MALL-TAOLI','SKY-ONE','HOSP-outpatient','HOSP-inpatient']) and not any(n in names for n in ['QR-037','QR-038','QR-039','QR-040']))
    page.locator('#home').click();page.wait_for_timeout(1800);page.locator('[data-view=free]').click();check('Existing free-view mode still works',page.evaluate('cityApp.state.freeView'));page.keyboard.press('Escape');check('Free-view Escape still restores camera',not page.evaluate('cityApp.state.freeView'))
    page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(250);page.locator('#collapse').click();page.locator('#mall-view').click();page.wait_for_timeout(2200);page.screenshot(path=str(OUT/'mall-mobile.png'))
    check('Mobile mall shortcut remains reachable and collapses settings',page.locator('#panel-content').is_hidden() and page.evaluate('Math.abs(cityApp.controls().target.x-112)<.1'))
    check('Mobile page has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth===420'))
    check('No browser runtime or WebGL errors',not errors)
    report={'baseline_commit':BASE,'checks':checks,'errors':errors,'site':page.evaluate('cityApp.mallSite'),'metrics':page.evaluate('cityApp.metrics()'),'single_glb_bytes':single.stat().st_size,'city_glb_bytes':whole.stat().st_size};(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');browser.close();print('COMPLETE',len(checks),flush=True)
server.shutdown();server.server_close()
