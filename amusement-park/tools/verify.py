import json,struct,threading
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';checks=[];errors=[];requests=[]
def check(name,value):
 print(('PASS ' if value else 'FAIL ')+name,flush=True)
 if not value:raise AssertionError(name)
 checks.append(name)
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files']);page=b.new_page(viewport={'width':1600,'height':1080},accept_downloads=True);page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('https:','http:')) else None)
 page.goto((ROOT/'晴空游乐园.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.parkApp?.ready');page.wait_for_timeout(800);check('Loads offline without network requests',not requests)
 check('Five rides and no people declared',page.evaluate("['ferrisWheel','rollerCoaster','carousel','pirateShip','slide'].every(k=>parkApp.park.parts[k])&&!parkApp.park.metadata.containsPeople"))
 audit=page.evaluate('''()=>{const p=parkApp.park;let contained=true,upright=true,tracked=true;let min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];for(let i=0;i<256;i++){p.update(.25,{paused:false});const box=p.getBounds(),motion=p.getMotionBounds();if(!motion.containsBox(box))contained=false;min=min.map((v,k)=>Math.min(v,box.min.toArray()[k]));max=max.map((v,k)=>Math.max(v,box.max.toArray()[k]));for(const c of p.mechanics.cabins)if(Math.abs(c.rotation.z)>1e-8)upright=false;for(let n=0;n<4;n++){const f=p.mechanics.frame(p.motors.rollerCoaster.phase-n*3.2/p.mechanics.trackLength),expected=f.point.addScaledVector(f.up,.25);if(expected.distanceTo(p.mechanics.cars[n].position)>.001)tracked=false;}}return{contained,upright,tracked,min,max,phases:Object.fromEntries(Object.entries(p.motors).map(([k,v])=>[k,v.phase]))};}''')
 print(json.dumps(audit),flush=True);check('Full 64 second motion sweep stays inside parcel',audit['contained'] and all(abs(audit[k][i])<=56 for k in ['min','max'] for i in [0,2]));check('Sweep covers wheel and train full cycles',audit['phases']['ferrisWheel']*.11>6.28 and audit['phases']['rollerCoaster']>1);check('Cabins remain upright throughout sweep',audit['upright']);check('All train cars remain on their independent track positions',audit['tracked'])
 check('Track is closed and tangent continuous',page.evaluate('(()=>{const p=parkApp.park.mechanics.path;return p.getPointAt(0).distanceTo(p.getPointAt(1))<.001&&p.getTangentAt(0).dot(p.getTangentAt(1))>.999})()'))
 for name in ['overview','front','coaster','entry','flag','roof']:
  page.evaluate('(v)=>parkApp.view(v,true)',name);page.wait_for_timeout(250);page.screenshot(path=str(OUT/f'final-{name}.png'))
 check('Six camera presets render',True);page.evaluate("parkApp.view('overview',true)");before=page.evaluate('parkApp.camera.position.toArray()');page.mouse.move(800,550);page.mouse.down();page.mouse.move(930,610,steps=12);page.mouse.up();page.wait_for_timeout(250);check('Drag rotates',before!=page.evaluate('parkApp.camera.position.toArray()'))
 before=page.evaluate('parkApp.controls.target.toArray()');page.mouse.move(800,550);page.mouse.down(button='right');page.mouse.move(880,580,steps=10);page.mouse.up(button='right');page.wait_for_timeout(200);check('Right drag pans',before!=page.evaluate('parkApp.controls.target.toArray()'))
 before=page.evaluate('parkApp.camera.position.distanceTo(parkApp.controls.target)');page.mouse.wheel(0,-400);page.wait_for_timeout(250);check('Wheel zooms',page.evaluate('parkApp.camera.position.distanceTo(parkApp.controls.target)')<before)
 page.locator('#collapse').click();page.locator('#pause').click();page.wait_for_timeout(100);before=page.evaluate('JSON.stringify(parkApp.park.motors)');page.wait_for_timeout(300);check('Pause freezes all ride motors',before==page.evaluate('JSON.stringify(parkApp.park.motors)'));page.locator('#pause').click();page.wait_for_timeout(250);check('Resume advances rides',before!=page.evaluate('JSON.stringify(parkApp.park.motors)'))
 off=page.evaluate("(()=>{const p=parkApp.park;for(let i=0;i<44;i++)p.update(.25,{rides:{carousel:false}});const t=p.motors.carousel.phase;p.update(.25,{rides:{carousel:false}});return t===p.motors.carousel.phase})()");check('Individual ride decelerates to a complete stop',off)
 for k in ['ferrisWheel','rollerCoaster','carousel','pirateShip']:
  page.locator('#'+k).uncheck();check('Independent switch '+k,page.evaluate('(k)=>parkApp.state[k]===false',k));page.locator('#'+k).check()
 page.locator('[data-time=night]').click();page.wait_for_timeout(1600);check('Night illumination switches on',page.evaluate("parkApp.park.materials['Warm park lighting'].emissiveIntensity>2.9"));page.evaluate("parkApp.view('overview',true)");page.locator('#collapse').click();page.screenshot(path=str(OUT/'final-night.png'));page.locator('#collapse').click();page.locator('#lights').uncheck();page.wait_for_timeout(60);check('Light switch works',not page.evaluate('parkApp.park.parts.lighting.visible'));page.locator('#lights').check();page.locator('[data-time=morning]').click();page.wait_for_timeout(1600)
 page.locator('#quality').select_option('low');check('Lightweight quality hides garden details',not page.evaluate('parkApp.park.parts.detail.visible'));page.locator('#quality').select_option('high');page.locator('#collapse').click();page.locator('#photo').click();check('Photography mode works',page.locator('body').evaluate('(e)=>e.classList.contains("photo")'));page.keyboard.press('Escape')
 page.evaluate("parkApp.view('overview',true);parkApp.state.paused=true");page.wait_for_timeout(100)
 with page.expect_download(timeout=60000) as task:page.locator('#export-glb').click()
 task.value.save_as(ROOT/'晴空游乐园.glb');raw=(ROOT/'晴空游乐园.glb').read_bytes();check('GLB is valid glTF2',struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw)))
 data=page.evaluate('parkApp.exportData()');(OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8');check('Same reviewed geometry exported for Blender',len(data['objects'])>4000)
 page.locator('#resolution').select_option('3840')
 with page.expect_download(timeout=60000) as task:page.locator('#save-png').click()
 task.value.save_as(OUT/'browser-4k.png');check('Actual 4K PNG export',Image.open(OUT/'browser-4k.png').size==(3840,2160))
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(400);check('Mobile fits and collapses panel',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===390'));page.evaluate("parkApp.view('overview',true)");page.screenshot(path=str(OUT/'final-mobile.png'))
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  host=b.new_page();host.on('pageerror',lambda e:errors.append(str(e)));host.goto(f'http://127.0.0.1:{server.server_port}/接入演示.html',wait_until='networkidle');host.wait_for_function('window.parkHost?.ready');check('Host factory mounts without own renderer',host.evaluate('parkHost.park.model.parent===parkHost.scene&&!parkHost.assetFrame.contentWindow.parkApp&&parkHost.assetFrame.contentDocument.querySelectorAll("canvas").length===0'))
  check('Idempotent dispose removes only model',host.evaluate('(()=>{const e=parkHost.scene.environment;parkHost.park.dispose();parkHost.park.dispose();return !parkHost.park.model.parent&&parkHost.scene.environment===e})()'))
 finally:server.shutdown();server.server_close()
 check('No JS or WebGL errors',not errors);(OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'motionAudit':audit,'metrics':page.evaluate('parkApp.metrics')},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks),flush=True);b.close()
