import json,struct,threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/park-integration';OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
def check(name,value):
    print(('PASS ' if value else 'FAIL ')+name,flush=True);checks.append({'check':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def names(path):
    raw=path.read_bytes();assert raw[:4]==b'glTF';size=struct.unpack_from('<I',raw,12)[0];return [n.get('name','') for n in json.loads(raw[20:20+size])['nodes']]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=[]);page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True)
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',timeout=60000);page.wait_for_timeout(800)
    check('BLK-16 position and refined model version',page.evaluate("cityApp.parkSite.blockId==='BLK-16'&&cityApp.parkSite.x===252&&cityApp.parkSite.z===210&&cityApp.park.metadata.version==='1.0.0'"))
    check('Four original homes and details removed',page.evaluate("['QR-061','QR-062','QR-063','QR-064'].every(id=>!cityApp.scene.getObjectByName(id))&&cityApp.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-16'))"))
    bounds=page.evaluate('({min:cityApp.park.getBounds().min.toArray(),max:cityApp.park.getBounds().max.toArray()})')
    check('Full model stays inside reserved square',bounds['min'][0]>=196 and bounds['max'][0]<=308 and bounds['min'][2]>=154 and bounds['max'][2]<=266)
    check('Full park scale and five rides preserved',page.evaluate("cityApp.park.model.scale.toArray().every(v=>v===1)&&['ferrisWheel','rollerCoaster','carousel','pirateShip','slide'].every(k=>cityApp.park.parts[k])"))
    check('Pavement joins match city grade',page.evaluate("['Park foundation to soil','Park west pedestrian seam','Park east pedestrian seam','Park north pedestrian seam','Park south pedestrian seam'].every(n=>cityApp.scene.getObjectByName(n))"))
    check('One selectable park and no source camera',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-16').length===1&&(()=>{let clean=true;cityApp.park.model.traverse(o=>{if(o.isCamera)clean=false});return clean})()"))
    baseline=(OUT/'city-before-park.js').read_text(encoding='utf8')
    check('All other homes unchanged',page.evaluate("""async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),base=await import(url);URL.revokeObjectURL(url);const prior=base.buildCity(new T.Scene()),custom=new Set(cityApp.plan.buildings.filter(b=>b.moduleId).map(b=>b.blockId)),expected=prior.plan.buildings.filter(b=>!custom.has(b.blockId)),actual=cityApp.plan.buildings.filter(b=>!b.moduleId);return expected.length===actual.length&&expected.every(b=>actual.some(a=>JSON.stringify(a)===JSON.stringify(b)));}""",baseline))
    check('All prior landmarks retained',page.evaluate("['hospital-campus','skyline-one','mall-complex','shanghai-tower','university-campus','dome-arena'].every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))"))
    check('River reservation unchanged',page.evaluate('cityApp.plan.corridor.width===64&&!!cityApp.river&&cityApp.park.getBounds().min.x>32'))
    check('City sky reflection assigned to park glass',page.evaluate("!!cityApp.park.materials['Lagoon blue enamel'].envMap"))
    page.screenshot(path=str(OUT/'city-overview.png'));page.locator('#park-view').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'park-context.png'))
    check('Park shortcut selects correct plot',page.evaluate("cityApp.state.selected.id==='SKYDAY-PARK'&&Math.abs(cityApp.controls().target.x-252)<.1"))
    page.locator('#focus-building').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'park-isolated.png'))
    with page.expect_download(timeout=60000) as task:page.locator('#export-building').click()
    task.value.save_as(OUT/'Park-BLK-16.glb');n=names(OUT/'Park-BLK-16.glb');check('Single GLB includes full building plaza and flag','SKYDAY-PARK' in n and 'Rotating_wheel' in n and 'landscape' in n)
    page.locator('#close-selection').click();page.locator('#park-view').click();page.wait_for_timeout(1600)
    page.locator('#pause').click();page.wait_for_timeout(100);before=page.evaluate('JSON.stringify(cityApp.park.motors)');page.wait_for_timeout(300);check('Global pause freezes all rides',before==page.evaluate('JSON.stringify(cityApp.park.motors)'));page.locator('#pause').click();page.wait_for_timeout(300);check('Global resume restarts rides',before!=page.evaluate('JSON.stringify(cityApp.park.motors)'))
    page.locator('.park-controls summary').click();page.locator('#park-carousel').uncheck();check('Independent carousel switch works',page.evaluate('cityApp.parkRides.carousel===false'));page.locator('#park-carousel').check()
    page.locator('#quality').select_option('fast');check('Quality switch controls park',page.evaluate("cityApp.park.quality==='low'"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click();page.wait_for_timeout(1900);check('Park lights follow city night',page.evaluate("cityApp.park.materials['Warm park lighting'].emissiveIntensity>2.9"));page.screenshot(path=str(OUT/'park-night.png'));page.locator('[data-time=morning]').click();page.wait_for_timeout(1700)
    page.evaluate("cityApp.select('QR-010')");page.locator('#focus-building').click();page.wait_for_timeout(1700)
    check('World JSON retains complete park while isolated elsewhere',page.evaluate("(()=>{const m=cityApp.exportCity().modules.find(m=>m.id==='amusement-park');return m.blockId==='BLK-16'&&m.snapshotSpace==='world'&&m.snapshot.objects.length>4000})()"))
    with page.expect_download(timeout=120000) as task:page.locator('#export').click()
    task.value.save_as(OUT/'Town-with-Park.glb');n=names(OUT/'Town-with-Park.glb');check('City GLB retains park and all prior landmarks',all(x in n for x in ['SKYDAY-PARK','SHANGHAI-TOWER','SKY-ONE','MALL-TAOLI','UNIVERSITY-CAMPUS','ARENA-DOME']) and any(x.startswith('HOSP-') for x in n))
    page.locator('#home').click();page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(1700);
    if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
    page.locator('#park-view').click();page.wait_for_timeout(1700);check('Mobile shortcut reveals park and fits screen',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'));page.screenshot(path=str(OUT/'park-mobile.png'))
    audit=page.evaluate('''()=>{const p=cityApp.park;let contained=true,upright=true;const reserved=p.getMotionBounds();for(let i=0;i<256;i++){p.update(.25);if(!reserved.containsBox(p.getBounds()))contained=false;for(const c of p.mechanics.cabins)if(c.rotation.z!==0)upright=false;}return{contained,upright};}''');check('64 second motion sweep stays inside world parcel',audit['contained'] and audit['upright'])
    check('Park remains unoccupied',page.evaluate('cityApp.park.metadata.containsPeople===false&&cityApp.metrics().pedestrians===84'))
    check('No runtime or WebGL errors',not errors);(OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds,'metrics':page.evaluate('cityApp.metrics()')},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks),flush=True);browser.close()

server.shutdown();server.server_close()
