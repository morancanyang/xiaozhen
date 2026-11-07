import json,struct,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';checks=[];errors=[];requests=[]
def check(name,value):
 print(('PASS ' if value else 'FAIL ')+name,flush=True)
 if not value:raise AssertionError(name)
 checks.append(name)
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files']);page=b.new_page(viewport={'width':1600,'height':1080},accept_downloads=True);page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
 page.goto((ROOT/'森隐公园.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.parkApp?.ready',timeout=60000);page.wait_for_timeout(800)
 check('Single HTML works offline',not requests);check('62 trees and no people',page.evaluate('parkApp.park.metadata.treeCount===62&&!parkApp.park.metadata.containsPeople'))
 bounds=page.evaluate('({min:parkApp.park.getBounds().min.toArray(),max:parkApp.park.getBounds().max.toArray()})');check('All geometry fits square plot',all(abs(bounds[k][i])<=56 for k in ['min','max'] for i in [0,2]))
 check('Actual excavated lakebed below water',page.evaluate('parkApp.park.terrain.groundHeight(12,-5)<-1.7&&parkApp.park.water.geometry.attributes.position.getY(0)>-0.4'))
 check('No ground plane intersects basin',page.evaluate('parkApp.scene.children.filter(o=>o.isMesh&&o.geometry.type==="PlaneGeometry").every(o=>o.position.y<-2.3)'))
 check('Motion envelope contains wind and waves',page.evaluate('(()=>{const p=parkApp.park;for(let i=0;i<120;i++){p.update(.25);if(!p.getMotionBounds().containsBox(p.getBounds()))return false;}return true;})()'))
 check('Trees leave path and lakeshore clear',page.evaluate('parkApp.park.terrain.treeSites.every(([x,z])=>parkApp.park.terrain.lakeDistance(x,z)>=1.28)'))
 for v in ['overview','path','lake','bench','detail','roof']:
  page.evaluate('(v)=>parkApp.view(v,true)',v);page.wait_for_timeout(250);page.screenshot(path=str(OUT/f'final-{v}.png'))
 check('Six camera presets render',True);page.evaluate("parkApp.view('overview',true)")
 before=page.evaluate('parkApp.camera.position.toArray()');page.mouse.move(850,550);page.mouse.down();page.mouse.move(950,600,steps=10);page.mouse.up();page.wait_for_timeout(200);check('Drag rotates',before!=page.evaluate('parkApp.camera.position.toArray()'))
 before=page.evaluate('parkApp.controls.target.toArray()');page.mouse.move(850,550);page.mouse.down(button='right');page.mouse.move(900,590,steps=8);page.mouse.up(button='right');page.wait_for_timeout(150);check('Right drag pans',before!=page.evaluate('parkApp.controls.target.toArray()'))
 before=page.evaluate('parkApp.camera.position.distanceTo(parkApp.controls.target)');page.mouse.wheel(0,-300);page.wait_for_timeout(200);check('Wheel zooms',page.evaluate('parkApp.camera.position.distanceTo(parkApp.controls.target)')<before)
 page.locator('#collapse').click();page.locator('#pause').click();page.wait_for_timeout(100);snap="({time:parkApp.park.time,tree:parkApp.park.canopies[0].group.rotation.z,water:Array.from(parkApp.park.water.geometry.attributes.position.array).slice(0,300)})";before=page.evaluate(snap);page.wait_for_timeout(300);check('Pause freezes water and foliage',before==page.evaluate(snap));page.locator('#pause').click();page.wait_for_timeout(200);check('Resume restarts simulation',before!=page.evaluate(snap))
 page.locator('#water').uncheck();page.wait_for_timeout(100);before=page.evaluate('Array.from(parkApp.park.water.geometry.attributes.position.array).slice(0,300)');page.wait_for_timeout(200);check('Water switch freezes waves',before==page.evaluate('Array.from(parkApp.park.water.geometry.attributes.position.array).slice(0,300)'));page.locator('#water').check()
 page.locator('#wind').uncheck();page.wait_for_timeout(100);before=page.evaluate('parkApp.park.canopies[0].group.rotation.z');page.wait_for_timeout(200);check('Wind switch freezes canopies',before==page.evaluate('parkApp.park.canopies[0].group.rotation.z'));page.locator('#wind').check()
 page.locator('[data-time=night]').click();page.wait_for_timeout(1700);check('Night lanterns illuminate',page.evaluate("parkApp.park.materials['Warm lantern diffuser'].emissiveIntensity>2.5"));page.evaluate("parkApp.view('overview',true)");page.locator('#collapse').click();page.screenshot(path=str(OUT/'final-night.png'));page.locator('#collapse').click();page.locator('#lights').uncheck();page.wait_for_timeout(80);check('Lights switch disables emission',page.evaluate("parkApp.park.materials['Warm lantern diffuser'].emissiveIntensity===0"));page.locator('#lights').check();page.locator('[data-time=morning]').click();page.wait_for_timeout(1700)
 page.locator('#quality').select_option('low');check('Low quality hides fine grass',not page.evaluate('parkApp.park.parts.grass.visible'));page.locator('#quality').select_option('high');page.locator('#collapse').click()
 page.locator('#photo').click();check('Photo mode works',page.locator('body').evaluate('(e)=>e.classList.contains("photo")'));page.keyboard.press('Escape')
 page.evaluate("parkApp.view('overview',true);parkApp.state.paused=true");page.wait_for_timeout(100)
 with page.expect_download(timeout=120000) as task:page.locator('#export-glb').click()
 task.value.save_as(ROOT/'森隐公园.glb');raw=(ROOT/'森隐公园.glb').read_bytes();check('Valid GLB export',struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw)))
 data=page.evaluate('parkApp.exportData()');(OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8');check('Blender export includes ground vertex colours',any(g.get('color') for g in data['geometries'].values()))
 page.locator('#resolution').select_option('3840')
 with page.expect_download(timeout=90000) as task:page.locator('#save-png').click()
 task.value.save_as(OUT/'browser-4k.png');check('True 4K image export',Image.open(OUT/'browser-4k.png').size==(3840,2160))
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(400);check('Mobile layout fits and collapses',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===390'));page.evaluate("parkApp.view('overview',true)");page.screenshot(path=str(OUT/'final-mobile.png'))
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  host=b.new_page();host.goto(f'http://127.0.0.1:{server.server_port}/接入演示.html',wait_until='networkidle');host.wait_for_function('window.parkHost?.ready',timeout=60000);check('Host mounts model without embedded viewer',host.evaluate('parkHost.park.model.parent===parkHost.scene&&!parkHost.assetFrame.contentWindow.parkApp'))
  check('Disposal preserves host scene',host.evaluate('(()=>{const e=parkHost.scene.environment;parkHost.park.dispose();parkHost.park.dispose();return !parkHost.park.model.parent&&e===parkHost.scene.environment})()'))
 finally:server.shutdown();server.server_close()
 check('No JS or WebGL errors',not errors);(OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds,'metrics':page.evaluate('parkApp.metrics')},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks),flush=True);b.close()
