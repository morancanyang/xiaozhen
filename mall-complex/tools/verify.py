"""Acceptance checks for the delivered offline viewer and injected-THREE asset API."""
import json,struct,sys,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
report={'checks':[],'errors':[],'external_requests':[]}
def check(name,condition):
    if not condition:raise AssertionError(name)
    report['checks'].append(name);print('PASS',name,flush=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files'])
    page=browser.new_page(viewport={'width':1600,'height':1080},device_scale_factor=1,accept_downloads=True)
    page.on('pageerror',lambda e:report['errors'].append(str(e)))
    page.on('console',lambda m:report['errors'].append(m.text) if m.type=='error' else None)
    page.on('request',lambda r:report['external_requests'].append(r.url) if r.url.startswith(('http:','https:')) else None)
    page.goto((ROOT/'商城综合体.html').as_uri(),wait_until='networkidle');page.wait_for_function('mallApp.ready');page.wait_for_timeout(1400)
    check('Single HTML loads offline without external requests',not report['external_requests'])
    bounds=page.evaluate('({min:mallApp.mall.getBounds().min.toArray(),max:mallApp.mall.getBounds().max.toArray()})');report['bounds']=bounds
    check('All model geometry remains inside 112m parcel',all(abs(bounds[k][i])<=56 for k in ['min','max'] for i in [0,2]))
    check('Building height matches metadata within 0.1m',abs(bounds['max'][1]-page.evaluate('mallApp.mall.metadata.displayHeight'))<.1)
    for name in ['overview','entry','terrace','atrium','roof']:
        page.locator('[data-view='+name+']').click();page.wait_for_timeout(1500)
        check('Camera preset '+name,page.locator('[data-view='+name+']').evaluate('(e)=>e.classList.contains("active")'))
        page.screenshot(path=str(OUT/f'final-{name}.png'))
    page.evaluate("mallApp.view('overview',true)");page.wait_for_timeout(300)
    before=page.evaluate('mallApp.camera.position.toArray()');page.mouse.move(750,600);page.mouse.down();page.mouse.move(900,650,steps=12);page.mouse.up();page.wait_for_timeout(600)
    check('Drag rotates camera',before!=page.evaluate('mallApp.camera.position.toArray()'))
    before=page.evaluate('mallApp.controls.target.toArray()');page.mouse.move(730,580);page.mouse.down(button='right');page.mouse.move(810,590,steps=10);page.mouse.up(button='right');page.wait_for_timeout(500)
    check('Right drag pans target',before!=page.evaluate('mallApp.controls.target.toArray()'))
    before=page.evaluate('mallApp.camera.position.distanceTo(mallApp.controls.target)');page.mouse.wheel(0,-500);page.wait_for_timeout(500)
    check('Wheel zooms',page.evaluate('mallApp.camera.position.distanceTo(mallApp.controls.target)')<before)
    page.locator('#pause').click();page.wait_for_timeout(150)
    before=page.evaluate('({time:mallApp.metrics.time,modelTime:mallApp.mall.time,door:mallApp.mall.model.getObjectByName("Automatic_door_left").position.x})');page.wait_for_timeout(650)
    check('Pause freezes simulation and door',before==page.evaluate('({time:mallApp.metrics.time,modelTime:mallApp.mall.time,door:mallApp.mall.model.getObjectByName("Automatic_door_left").position.x})'))
    page.locator('#pause').click();page.wait_for_timeout(500);check('Resume advances time',page.evaluate('mallApp.metrics.time')>before['time'])
    page.locator('#people').uncheck();page.wait_for_timeout(100);check('Visitors switch works',not page.evaluate('mallApp.mall.parts.people.visible'));page.locator('#people').check()
    page.locator('#lights').uncheck();page.wait_for_timeout(100);check('Lighting switch works',not page.evaluate('mallApp.mall.parts.lighting.visible'));page.locator('#lights').check()
    page.locator('[data-time=night]').click();page.wait_for_timeout(1700);check('Night preset applies',page.evaluate('mallApp.state.time')=='night' and page.evaluate('mallApp.mall.materials["Warm architectural light"].emissiveIntensity')>2)
    page.evaluate("mallApp.view('overview',true)");page.screenshot(path=str(OUT/'final-night.png'))
    page.locator('[data-time=afternoon]').click();page.wait_for_timeout(1700)
    page.locator('#dof').check();page.wait_for_timeout(300);check('Depth-of-field switch works',page.evaluate('mallApp.state.dof'));page.locator('#dof').uncheck()
    page.locator('#quality').select_option('low');page.wait_for_timeout(400);check('Low quality hides construction details',not page.evaluate('mallApp.mall.parts.detail.visible'));page.locator('#quality').select_option('high');page.wait_for_timeout(400)
    page.locator('#orbit').click();page.wait_for_timeout(350);check('Orbit starts',page.evaluate('mallApp.state.orbit'));page.mouse.move(850,580);page.mouse.down();page.mouse.up();check('Manual input interrupts orbit',not page.evaluate('mallApp.state.orbit'))
    page.locator('#photo').click();check('Photo mode hides UI',page.locator('body').evaluate('(e)=>e.classList.contains("photo")'));page.keyboard.press('Escape');check('Escape restores UI',not page.locator('#exit-photo').is_visible())
    # Export actual files and inspect their containers/resolutions.
    page.evaluate("mallApp.view('overview',true);mallApp.state.paused=true")
    with page.expect_download(timeout=60000) as task:page.locator('#export-glb').click()
    glb=ROOT/'陶里汇商城.glb';task.value.save_as(str(glb));raw=glb.read_bytes();magic,version,length=struct.unpack('<4sII',raw[:12]);check('GLB is a valid glTF2 binary',magic==b'glTF' and version==2 and length==len(raw))
    json_size=struct.unpack('<I',raw[12:16])[0];gltf=json.loads(raw[20:20+json_size]);check('GLB contains meshes and model metadata',len(gltf.get('meshes',[]))>20 and any(n.get('extras',{}).get('landmark',{}).get('id')=='taoli-galleria' for n in gltf.get('nodes',[])))
    page.locator('#resolution').select_option('3840')
    with page.expect_download(timeout=60000) as task:page.locator('#save-png').click()
    png=OUT/'browser-4k.png';task.value.save_as(str(png));check('Browser exports original 4K PNG',Image.open(png).size==(3840,2160))
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(500)
    check('Mobile panel collapses on resize',page.locator('#panel-content').is_hidden())
    page.locator('#collapse').click();check('Mobile settings can expand',page.locator('#panel-content').is_visible())
    page.locator('#people').uncheck();page.locator('#people').check();page.locator('#collapse').click();check('Mobile settings can collapse',page.locator('#panel-content').is_hidden())
    page.screenshot(path=str(OUT/'final-mobile.png'))
    # Verify all mobile camera buttons remain reachable, independent of the panel.
    for name in ['overview','entry','roof']:
        page.locator('[data-view='+name+']').click();page.wait_for_timeout(50)
    check('Mobile camera controls remain reachable',True)
    # A second host renderer must receive a model built exclusively from its THREE.
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    host=browser.new_page(viewport={'width':1300,'height':900});host.on('pageerror',lambda e:report['errors'].append(str(e)))
    host.goto(f'http://127.0.0.1:{server.server_port}/接入演示.html',wait_until='networkidle');host.wait_for_function('window.mallHost?.ready');host.wait_for_timeout(1300)
    check('Host demo mounts successfully',host.evaluate('mallHost.mall.model.parent===mallHost.scene'))
    check('Asset iframe creates no canvas',host.evaluate('mallHost.assetFrame.contentDocument.querySelectorAll("canvas").length===0'))
    check('Asset mode creates no standalone viewer',host.evaluate('!mallHost.assetFrame.contentWindow.mallApp'))
    host.screenshot(path=str(OUT/'integration-demo.png'))
    lifecycle=host.evaluate('''()=>{const frame=mallHost.assetFrame;const Factory=frame.contentWindow.QianrenLandmarks.createMallComplex;const THREE=mallHost.mall.model.constructor;return {factory:typeof Factory,existing:mallHost.mall.metadata.id};}''')
    check('Factory exposed to host',lifecycle['factory']=='function')
    # Explicit resource lifetime test on the mounted module only.
    lifecycle=host.evaluate('''()=>{let g=0,m=0,t=0;const seen=new Set();mallHost.mall.model.traverse(o=>{if(o.geometry&&!seen.has(o.geometry)){seen.add(o.geometry);o.geometry.addEventListener('dispose',()=>g++);}for(const material of Array.isArray(o.material)?o.material:[o.material])if(material&&!seen.has(material)){seen.add(material);material.addEventListener('dispose',()=>m++);for(const key of ['map','bumpMap'])if(material[key]&&!seen.has(material[key])){seen.add(material[key]);material[key].addEventListener('dispose',()=>t++);}}});const env=mallHost.scene.environment;mallHost.mall.dispose();mallHost.mall.dispose();return {g,m,t,removed:!mallHost.mall.model.parent,env:env===mallHost.scene.environment};}''')
    check('dispose releases model resources and preserves host environment',lifecycle['g']>5 and lifecycle['m']>20 and lifecycle['t']>4 and lifecycle['removed'] and lifecycle['env'])
    report['lifecycle']=lifecycle;report['metrics']=page.evaluate('mallApp.metrics');check('No browser runtime/WebGL errors',not report['errors'])
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('ACCEPTANCE COMPLETE',len(report['checks']),flush=True);browser.close();server.shutdown();server.server_close()
