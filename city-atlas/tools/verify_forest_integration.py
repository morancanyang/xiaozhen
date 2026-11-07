import json,struct,threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/forest-integration';OUT.mkdir(parents=True,exist_ok=True)
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
    check('BLK-15 position and refined model version',page.evaluate("cityApp.forestSite.blockId==='BLK-15'&&cityApp.forestSite.x===252&&cityApp.forestSite.z===70&&cityApp.forest.metadata.version==='1.0.0'"))
    check('Four original homes and details removed',page.evaluate("['QR-057','QR-058','QR-059','QR-060'].every(id=>!cityApp.scene.getObjectByName(id))&&cityApp.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-15'))"))
    bounds=page.evaluate('({min:cityApp.forest.getBounds().min.toArray(),max:cityApp.forest.getBounds().max.toArray()})')
    check('Full model stays inside reserved square',bounds['min'][0]>=196 and bounds['max'][0]<=308 and bounds['min'][2]>=14 and bounds['max'][2]<=126)
    check('Full forest scale and 62 trees preserved',page.evaluate("cityApp.forest.model.scale.toArray().every(v=>v===1)&&cityApp.forest.metadata.treeCount===62"))
    check('Pavement joins match city grade',page.evaluate("['Forest foundation below basin','Forest west pedestrian seam','Forest east pedestrian seam','Forest north pedestrian seam','Forest south pedestrian seam'].every(n=>cityApp.scene.getObjectByName(n))"))
    check('One selectable park and no source camera',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-15').length===1&&(()=>{let clean=true;cityApp.forest.model.traverse(o=>{if(o.isCamera)clean=false});return clean})()"))
    baseline=(OUT/'city-before-forest.js').read_text(encoding='utf8')
    check('All other homes unchanged',page.evaluate("""async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),base=await import(url);URL.revokeObjectURL(url);const prior=base.buildCity(new T.Scene()),custom=new Set(cityApp.plan.buildings.filter(b=>b.moduleId).map(b=>b.blockId)),expected=prior.plan.buildings.filter(b=>!custom.has(b.blockId)),actual=cityApp.plan.buildings.filter(b=>!b.moduleId);return expected.length===actual.length&&expected.every(b=>actual.some(a=>JSON.stringify(a)===JSON.stringify(b)));}""",baseline))
    check('All prior landmarks retained',page.evaluate("['hospital-campus','skyline-one','mall-complex','shanghai-tower','university-campus','dome-arena','amusement-park','linxu-residential'].every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))"))
    check('River and corridor remain intact',page.evaluate('cityApp.plan.corridor.width===64&&!!cityApp.river&&cityApp.forest.getBounds().min.x>32'))
    check('City sky reflection assigned to park glass',page.evaluate("!!cityApp.forest.materials['Deep green lake water'].envMap"))
    page.screenshot(path=str(OUT/'city-overview.png'));page.locator('#forest-view').click();page.wait_for_function("Math.abs(cityApp.controls().target.x-252)<.1&&Math.abs(cityApp.controls().target.z-70)<.1",timeout=30000);page.screenshot(path=str(OUT/'forest-context.png'))
    check('Forest shortcut selects correct plot',page.evaluate("cityApp.state.selected.id==='SENYIN-PARK'&&Math.abs(cityApp.controls().target.x-252)<.1"))
    page.locator('#focus-building').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'forest-isolated.png'))
    with page.expect_download(timeout=60000) as task:page.locator('#export-building').click()
    task.value.save_as(OUT/'Forest-BLK-15.glb');n=names(OUT/'Forest-BLK-15.glb');check('Single GLB includes complete forest and basin','SENYIN-PARK' in n and 'Living_lake_surface' in n and 'Excavated_terrain_and_lakebed' in n)
    page.locator('#close-selection').click();page.locator('#forest-view').click();page.wait_for_timeout(1600)
    page.locator('#pause').click();page.wait_for_timeout(100);before=page.evaluate('JSON.stringify({time:cityApp.forest.time,tree:cityApp.forest.canopies[0].group.rotation.z,water:Array.from(cityApp.forest.water.geometry.attributes.position.array).slice(0,30)})');page.wait_for_timeout(300);check('Global pause freezes water and foliage',before==page.evaluate('JSON.stringify({time:cityApp.forest.time,tree:cityApp.forest.canopies[0].group.rotation.z,water:Array.from(cityApp.forest.water.geometry.attributes.position.array).slice(0,30)})'));page.locator('#pause').click();page.wait_for_timeout(300);check('Global resume restarts forest dynamics',before!=page.evaluate('JSON.stringify({time:cityApp.forest.time,tree:cityApp.forest.canopies[0].group.rotation.z,water:Array.from(cityApp.forest.water.geometry.attributes.position.array).slice(0,30)})'))
    page.locator('#forest-water').uncheck();page.wait_for_timeout(80);before=page.evaluate('cityApp.forest.water.geometry.attributes.position.getY(0)');page.wait_for_timeout(300);check('Independent water switch freezes waves',before==page.evaluate('cityApp.forest.water.geometry.attributes.position.getY(0)'));page.locator('#forest-water').check()
    page.locator('#quality').select_option('fast');check('Quality switch controls park',page.evaluate("cityApp.forest.quality==='low'"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click();page.wait_for_timeout(1900);check('Park lights follow city night',page.evaluate("cityApp.forest.materials['Warm lantern diffuser'].emissiveIntensity>2.5"));page.screenshot(path=str(OUT/'forest-night.png'));page.locator('[data-time=morning]').click();page.wait_for_timeout(1700)
    page.evaluate("cityApp.select('QR-010')");page.locator('#focus-building').click();page.wait_for_timeout(1700)
    check('World JSON retains complete park while isolated elsewhere',page.evaluate("(()=>{const m=cityApp.exportCity().modules.find(m=>m.id==='quiet-city-park');return m.blockId==='BLK-15'&&m.snapshotSpace==='world'&&m.snapshot.objects.length>50000})()"))
    with page.expect_download(timeout=120000) as task:page.locator('#export').click()
    task.value.save_as(OUT/'Town-with-Forest.glb');n=names(OUT/'Town-with-Forest.glb');check('City GLB retains park and all prior landmarks',all(x in n for x in ['SENYIN-PARK','SKYDAY-PARK','SHANGHAI-TOWER','SKY-ONE','MALL-TAOLI','UNIVERSITY-CAMPUS','ARENA-DOME']) and any(x.startswith('HOSP-') for x in n))
    page.locator('#home').click();page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(1700);
    if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
    page.locator('#forest-view').click();page.wait_for_timeout(1700);check('Mobile shortcut reveals park and fits screen',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'));page.screenshot(path=str(OUT/'forest-mobile.png'))
    check('Actual lakebed remains below the water',page.evaluate('cityApp.forest.terrain.groundHeight(12,-5)<-1.7&&cityApp.forest.water.geometry.attributes.position.getY(0)>-.4'))
    check('Original city soil and asphalt do not fill the lake',page.evaluate("""(()=>{const d=cityApp.exportCity();return d.batches.filter(b=>b.owner==='world'&&b.type==='box'&&['base','soil','asphalt'].includes(b.material)).every(b=>b.items.every(i=>{const [x,y,z]=i.p,[w,h,l]=i.s;return x+w/2<=242.001||x-w/2>=285.999||z+l/2<=48.001||z-l/2>=83.999;}));})()"""))
    check('Ground vertex colours preserved in world snapshot',page.evaluate("(()=>{const s=cityApp.exportCity('SENYIN-PARK').modules[0].snapshot;return Object.values(s.geometries).some(g=>g.colors?.length>10000)})()"))
    check('Tree layout matches standalone model',page.evaluate("""async()=>{const T=await import('three'),m=await import('./forest-model.js'),base=m.createQuietCityPark({THREE:T,quality:'low'}),same=JSON.stringify(base.terrain.treeSites)===JSON.stringify(cityApp.forest.terrain.treeSites);base.dispose();return same;}"""))
    check('Forest remains unoccupied',page.evaluate('!cityApp.forest.metadata.containsPeople'))
    check('No runtime or WebGL errors',not errors);(OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds,'metrics':page.evaluate('cityApp.metrics()')},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks),flush=True);browser.close()

server.shutdown();server.server_close()
