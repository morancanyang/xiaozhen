import json,struct,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/slab-integration';OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
def check(name,ok):
 print(('PASS ' if ok else 'FAIL ')+name,flush=True);checks.append({'check':name,'passed':bool(ok)});assert ok,name
def names(path):
 d=path.read_bytes();assert d[:4]==b'glTF';n=struct.unpack_from('<I',d,12)[0];return [x.get('name','') for x in json.loads(d[20:20+n])['nodes']]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True);page.set_default_timeout(60000)
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready')
  check('BLK-12 installed at original scale and correct grade',page.evaluate("cityApp.slabSite.blockId==='BLK-12'&&cityApp.slab.root.position.toArray().join(',')==='112,0.34,210'&&cityApp.slab.root.scale.x===1"))
  check('Old homes and plot details removed',page.evaluate("['QR-045','QR-046','QR-047','QR-048'].every(id=>!cityApp.scene.getObjectByName(id))&&cityApp.exportCity('QIANXU-RESIDENTIAL').batches.every(b=>b.items.every(i=>i.blockId!=='BLK-12'))"))
  b=page.evaluate('({min:cityApp.slab.getBounds().min.toArray(),max:cityApp.slab.getBounds().max.toArray()})')
  check('Full model fits original 112 metre square',b['min'][0]>=55.999 and b['max'][0]<=168.001 and b['min'][2]>=153.999 and b['max'][2]<=266.001)
  check('Three buildings retain 16/18/20 floors and nine units',page.evaluate("cityApp.slab.buildings.map(b=>b.floors).join(',')==='16,18,20'&&cityApp.slab.buildings.reduce((a,b)=>a+b.units,0)===9"))
  baseline=(OUT/'city-before-slab.js').read_text(encoding='utf8')
  check('All other ordinary homes unchanged',page.evaluate("""async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),m=await import(url),before=m.buildCity(new T.Scene()).plan.buildings.filter(b=>b.blockId!=='BLK-12'),after=cityApp.plan.buildings.filter(b=>!b.moduleId);return JSON.stringify(before)===JSON.stringify(after)}""",baseline))
  check('All prior landmarks retained',page.evaluate("!!cityApp.sports&&!!cityApp.forest&&!!cityApp.park&&!!cityApp.residential&&!!cityApp.hospital&&!!cityApp.skyline&&!!cityApp.shanghai&&!!cityApp.university&&!!cityApp.mall&&!!cityApp.arena"))
  check('Lowered river retained',page.evaluate('cityApp.river.manifest.waterLevel===-3.2'))
  check('Descendant picking resolves to selectable city record',page.evaluate("(()=>{let ok=true;cityApp.slab.root.traverse(o=>{if(o.isMesh){let a=o;while(a.parent&&!a.userData.id)a=a.parent;ok&&=a.userData.id==='QIANXU-RESIDENTIAL';}});return ok;})()"))
  page.locator('#slab-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x-112)<.01&&Math.abs(cityApp.controls().target.z-210)<.01')
  page.wait_for_timeout(700);page.screenshot(path=str(OUT/'city-context.png'))
  check('Shortcut selects correct complex',page.evaluate("cityApp.state.selected.id==='QIANXU-RESIDENTIAL'"))
  page.locator('#pause').click();t=page.evaluate('cityApp.slab.simulationTime');page.wait_for_timeout(300);check('City pause freezes model',page.evaluate('cityApp.slab.simulationTime')==t)
  page.locator('#pause').click();page.wait_for_timeout(300);check('Resume advances model',page.evaluate('cityApp.slab.simulationTime')>t)
  page.locator('#wind').uncheck();page.wait_for_timeout(100);w=page.evaluate('cityApp.slab.windTime');page.wait_for_timeout(300);check('City wind freezes foliage and curtains',page.evaluate('cityApp.slab.windTime')==w);page.locator('#wind').check()
  page.locator('[data-time=night]').click();page.wait_for_function('cityApp.slab.nightFactor>.99');page.screenshot(path=str(OUT/'city-night.png'))
  check('Apartment lights follow city night',page.evaluate("Object.values(cityApp.slab.materials).filter(m=>m.name.startsWith('Apartment interior')).some(m=>m.emissiveIntensity>.5)"))
  page.locator('[data-time=morning]').click();page.wait_for_function('cityApp.slab.nightFactor<.01')
  page.locator('#quality').select_option('fast');check('Fast quality propagates',page.evaluate("cityApp.slab.quality==='low'"));page.locator('#quality').select_option('balanced')
  s=page.evaluate("cityApp.exportCity('QIANXU-RESIDENTIAL').modules[0].snapshot");check('JSON retains full world geometry and restored quality',s['snapshotSpace']=='world' and len(s['objects'])>34000 and page.evaluate("cityApp.slab.quality==='medium'"))
  page.locator('#focus-building').click();page.wait_for_timeout(2000);page.screenshot(path=str(OUT/'isolated.png'))
  check('Isolated view keeps complex visible',page.evaluate('cityApp.slab.root.visible'))
  with page.expect_download(timeout=180000) as d:page.locator('#export-building').click()
  d.value.save_as(OUT/'Qianxu-BLK12.glb');check('Single GLB contains all three slab groups',all(n in names(OUT/'Qianxu-BLK12.glb') for n in ['SLAB-A','SLAB-B','SLAB-C']))
  page.locator('#home').click();page.wait_for_timeout(2000)
  with page.expect_download(timeout=180000) as d:page.locator('#export').click()
  d.value.save_as(OUT/'City-with-Qianxu.glb');ns=names(OUT/'City-with-Qianxu.glb');check('City GLB preserves new and prior landmarks',all(n in ns for n in ['QIANXU-RESIDENTIAL','SHANGHAI-TOWER','QINGHE-SPORTS','SENYIN-PARK','RIVER-QINGLAN']))
  page.set_viewport_size({'width':420,'height':880})
  if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
  page.locator('#slab-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x-112)<.01');page.wait_for_timeout(1500);page.screenshot(path=str(OUT/'mobile.png'))
  check('Mobile closes panel without overflow',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'))
  check('No runtime or shader errors',not errors)
  (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':b},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks),flush=True);browser.close()
finally:server.shutdown()
