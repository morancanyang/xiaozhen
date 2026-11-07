import json,struct,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/mixed-integration';OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
def check(name,ok):
 print(('PASS ' if ok else 'FAIL ')+name,flush=True);checks.append({'check':name,'passed':bool(ok)});assert ok,name
def capture(page,path):
 page.evaluate("()=>{const a=cityApp;a.renderer.render=window.actualRender;try{window.actualRiverPass(a.renderer,a.scene,a.camera());a.renderer.setRenderTarget(null);a.renderer.render(a.scene,a.camera());}finally{a.renderer.render=()=>{};}}")
 page.screenshot(path=str(path))
def names(path):
 d=path.read_bytes();assert d[:4]==b'glTF';n=struct.unpack_from('<I',d,12)[0];return [x.get('name','') for x in json.loads(d[20:20+n])['nodes']]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader']);page=browser.new_page(viewport={'width':900,'height':600},accept_downloads=True);page.set_default_timeout(180000)
  page.on('pageerror',lambda e:(errors.append(str(e)),print('BROWSER ERROR',str(e),flush=True)));page.on('console',lambda m:(errors.append(m.text),print('CONSOLE ERROR',m.text,flush=True)) if m.type=='error' else None)
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',polling=200,timeout=360000);page.evaluate("()=>{window.actualRender=cityApp.renderer.render.bind(cityApp.renderer);window.actualRiverPass=cityApp.riverPass.beforeRender;cityApp.renderer.render=()=>{};cityApp.riverPass.beforeRender=()=>{};const q=document.querySelector('#quality');q.value='fast';q.dispatchEvent(new Event('change'));}")
  check('BLK-15 installed at original scale and correct grade',page.evaluate("cityApp.mixedSite.blockId==='BLK-15'&&cityApp.mixed.root.position.toArray().join(',')==='252,0.34,70'&&cityApp.mixed.root.scale.x===1"))
  check('Old homes and plot details removed',page.evaluate("['QR-057','QR-058','QR-059','QR-060'].every(id=>!cityApp.scene.getObjectByName(id))&&cityApp.exportCity('ZONGYU-RESIDENCES').batches.every(b=>b.items.every(i=>i.blockId!=='BLK-15'))"))
  b=page.evaluate('({min:cityApp.mixed.getBounds().min.toArray(),max:cityApp.mixed.getBounds().max.toArray()})')
  check('Full model fits original 112 metre square',b['min'][0]>=195.999 and b['max'][0]<=308.001 and b['min'][2]>=13.999 and b['max'][2]<=126.001)
  check('22 residential floors, 3 units and 6 shops retained',page.evaluate("cityApp.mixed.metadata.residentialFloors===22&&cityApp.mixed.metadata.shops.length===6&&cityApp.mixed.buildings[0].units===3"))
  baseline=(OUT/'city-before-mixed.js').read_text(encoding='utf8')
  check('All other ordinary homes unchanged',page.evaluate("""async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),m=await import(url),before=m.buildCity(new T.Scene()).plan.buildings.filter(b=>b.blockId!=='BLK-15'),after=cityApp.plan.buildings.filter(b=>!b.moduleId);return JSON.stringify(before)===JSON.stringify(after)}""",baseline))
  check('All prior landmarks retained',page.evaluate("!!cityApp.sports&&!!cityApp.slab&&!!cityApp.garden&&!!cityApp.office&&!!cityApp.park&&!!cityApp.residential&&!!cityApp.hospital&&!!cityApp.skyline&&!!cityApp.shanghai&&!!cityApp.university&&!!cityApp.mall&&!!cityApp.arena"))
  check('Forest removed completely',page.evaluate("!cityApp.scene.getObjectByName('SENYIN-PARK')&&!cityApp.scene.getObjectByName('Forest_Plaza_Connections')&&!cityApp.plan.buildings.some(b=>b.moduleId==='quiet-city-park')"))
  check('Former lake soil restored',page.evaluate("async()=>{const m=await import('./city.js');return m.exportCity().batches.some(b=>b.owner==='world'&&b.material==='soil'&&b.items.some(i=>Math.abs(i.p[0]-264)<i.s[0]/2&&Math.abs(i.p[2]-66)<i.s[2]/2));}"))
  check('Lowered river retained',page.evaluate('cityApp.river.manifest.waterLevel===-3.2'))
  check('Descendant picking resolves to selectable city record',page.evaluate("(()=>{let ok=true;cityApp.mixed.root.traverse(o=>{if(o.isMesh){let a=o;while(a.parent&&!a.userData.id)a=a.parent;ok&&=a.userData.id==='ZONGYU-RESIDENCES';}});return ok;})()"))
  page.locator('#mixed-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x-252)<.01&&Math.abs(cityApp.controls().target.z-70)<.01')
  page.wait_for_timeout(700);capture(page,OUT/'city-context.png')
  check('Shortcut selects correct complex',page.evaluate("cityApp.state.selected.id==='ZONGYU-RESIDENCES'"))
  page.locator('#pause').click();t=page.evaluate('cityApp.mixed.simulationTime');page.wait_for_timeout(300);check('City pause freezes model',page.evaluate('cityApp.mixed.simulationTime')==t)
  page.locator('#pause').click();page.wait_for_timeout(300);check('Resume advances model',page.evaluate('cityApp.mixed.simulationTime')>t)
  page.locator('#wind').uncheck();page.wait_for_timeout(100);w=page.evaluate('cityApp.mixed.windTime');page.wait_for_timeout(300);check('City wind freezes foliage and curtains',page.evaluate('cityApp.mixed.windTime')==w);page.locator('#wind').check()
  page.locator('#mixed-doors').uncheck();page.wait_for_timeout(200);check('Shop doors independent control',page.evaluate('cityApp.mixed.doors.every(d=>d.rotation.y===0)'));page.locator('#mixed-doors').check()
  page.locator('[data-time=night]').click();page.wait_for_function('cityApp.mixed.nightFactor>.99');capture(page,OUT/'city-night.png')
  check('Apartment lights follow city night',page.evaluate("Object.values(cityApp.mixed.materials).filter(m=>m.name.startsWith('Apartment interior')).some(m=>m.emissiveIntensity>.5)"))
  page.locator('[data-time=morning]').click();page.wait_for_function('cityApp.mixed.nightFactor<.01')
  page.locator('#quality').select_option('fast');check('Fast quality propagates',page.evaluate("cityApp.mixed.quality==='low'"));page.evaluate("()=>{window.actualRender=cityApp.renderer.render.bind(cityApp.renderer);window.actualRiverPass=cityApp.riverPass.beforeRender;cityApp.renderer.render=()=>{};cityApp.riverPass.beforeRender=()=>{};const q=document.querySelector('#quality');q.value='fast';q.dispatchEvent(new Event('change'));}")
  s=page.evaluate("cityApp.exportCity('ZONGYU-RESIDENCES').modules[0].snapshot");check('JSON retains full world geometry and restored quality',s['snapshotSpace']=='world' and len(s['objects'])>12000 and page.evaluate("cityApp.mixed.quality==='low'"))
  page.locator('#focus-building').click();page.wait_for_timeout(2000);capture(page,OUT/'isolated.png')
  check('Isolated view keeps complex visible',page.evaluate('cityApp.mixed.root.visible'))
  with page.expect_download(timeout=180000) as d:page.locator('#export-building').click()
  d.value.save_as(OUT/'Zongyu-BLK12.glb');check('Single GLB contains residential facade and shops',all(n in names(OUT/'Zongyu-BLK12.glb') for n in ['facade','balconies','roof','lobby','SHOP-1','SHOP-6']))
  page.locator('#home').click();page.wait_for_timeout(2000)
  with page.expect_download(timeout=180000) as d:page.locator('#export').click()
  d.value.save_as(OUT/'City-with-Zongyu.glb');ns=names(OUT/'City-with-Zongyu.glb');check('City GLB preserves new and prior landmarks',all(n in ns for n in ['ZONGYU-RESIDENCES','SHANGHAI-TOWER','QINGHE-SPORTS','QIANXU-RESIDENTIAL','RIVER-QINGLAN']))
  page.set_viewport_size({'width':420,'height':880})
  if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
  page.locator('#mixed-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x-252)<.01');page.wait_for_timeout(1500);capture(page,OUT/'mobile.png')
  check('Mobile closes panel without overflow',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'))
  check('No runtime or shader errors',not errors)
  (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':b,'renderVerification':'Software renderer: geometry and controls update normally; actual frames drawn explicitly for each screenshot, no FPS claims'},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks),flush=True);browser.close()
finally:server.shutdown()
