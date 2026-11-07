"""Offline viewer, cloth constraints, exports, touch controls and host lifetime checks."""
import json,struct,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';report={'checks':[],'errors':[],'external_requests':[]}
def check(name,value):
    print(('PASS ' if value else 'FAIL ')+name,flush=True)
    if not value:raise AssertionError(name)
    report['checks'].append(name)
def cloth(page):return page.evaluate('Array.from(campusApp.campus.flags[0].geometry.attributes.position.array)')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files'])
    page=browser.new_page(viewport={'width':1600,'height':1080},accept_downloads=True)
    page.on('pageerror',lambda e:report['errors'].append(str(e)))
    page.on('console',lambda m:report['errors'].append(m.text) if m.type=='error' else None)
    page.on('request',lambda r:report['external_requests'].append(r.url) if r.url.startswith(('http:','https:')) else None)
    page.goto((ROOT/'大学主教学楼.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.campusApp?.ready');page.wait_for_timeout(800)
    check('Single HTML works offline',not report['external_requests'])
    bounds=page.evaluate('({min:campusApp.campus.getBounds().min.toArray(),max:campusApp.campus.getBounds().max.toArray()})');report['bounds']=bounds
    check('All geometry contained in 112m parcel',all(abs(bounds[k][i])<=56 for k in ['min','max'] for i in [0,2]))
    check('Height matches metadata',abs(bounds['max'][1]-page.evaluate('campusApp.campus.metadata.displayHeight'))<.02)
    check('One national flag and ten small flags',page.evaluate('campusApp.campus.flags.length===11&&campusApp.campus.flags.filter(f=>f.name==="Five_star_national_flag").length===1'))
    check('Seven-storey main building, five-storey wings, no roads',page.evaluate('campusApp.campus.metadata.floors===7&&campusApp.campus.metadata.sideWingFloors===5&&!campusApp.campus.metadata.containsRoads'))
    check('Instanced facade and landscape geometry',page.evaluate('(()=>{let n=0;campusApp.campus.model.traverse(o=>{if(o.isInstancedMesh)n+=o.count});return n>6000})()'))
    first=cloth(page);page.wait_for_timeout(350);check('Cloth deforms over time',first!=cloth(page))
    check('Flag remains fixed at pole edge',page.evaluate('campusApp.campus.flags.every(f=>{const p=f.geometry.attributes.position;for(let i=0;i<p.count;i++)if(Math.abs(p.getX(i))<.000001&&Math.abs(p.getZ(i))>.000001)return false;return true})'))
    for name in ['overview','front','entry','flag','roof']:
        page.evaluate('(name)=>campusApp.view(name,true)',name);page.wait_for_timeout(250);page.screenshot(path=str(OUT/f'final-{name}.png'))
    check('Five camera presets render',True)
    page.evaluate("campusApp.view('overview',true)")
    before=page.evaluate('campusApp.camera.position.toArray()');page.mouse.move(800,600);page.mouse.down();page.mouse.move(930,660,steps=12);page.mouse.up();page.wait_for_timeout(300);check('Drag rotates model view',before!=page.evaluate('campusApp.camera.position.toArray()'))
    before=page.evaluate('campusApp.controls.target.toArray()');page.mouse.move(780,580);page.mouse.down(button='right');page.mouse.move(855,610,steps=10);page.mouse.up(button='right');page.wait_for_timeout(300);check('Right drag pans view',before!=page.evaluate('campusApp.controls.target.toArray()'))
    before=page.evaluate('campusApp.camera.position.distanceTo(campusApp.controls.target)');page.mouse.wheel(0,-450);page.wait_for_timeout(350);check('Wheel zooms view',page.evaluate('campusApp.camera.position.distanceTo(campusApp.controls.target)')<before)
    page.locator('#collapse').click();page.locator('#pause').click();page.wait_for_timeout(100);before=cloth(page);t=page.evaluate('campusApp.campus.time');page.wait_for_timeout(350);check('Pause freezes cloth and module time',before==cloth(page) and t==page.evaluate('campusApp.campus.time'));page.locator('#pause').click();page.wait_for_timeout(350);check('Resume restarts cloth',before!=cloth(page))
    page.locator('#wind').uncheck();page.wait_for_timeout(100);before=cloth(page);page.wait_for_timeout(300);check('Wind switch freezes flag movement',before==cloth(page));page.locator('#wind').check()
    page.locator('#wind-strength').fill('0.1');page.locator('#wind-strength').dispatch_event('input');check('Wind strength control updates context',page.evaluate('campusApp.state.windStrength===.1'));page.locator('#wind-strength').fill('0.6');page.locator('#wind-strength').dispatch_event('input')
    page.locator('#flags').uncheck();page.wait_for_timeout(60);check('Flag switch works',not page.evaluate('campusApp.campus.parts.flags.visible'));page.locator('#flags').check()
    page.locator('[data-time=night]').click();page.wait_for_timeout(1650);check('Night lights synchronize',page.evaluate('campusApp.campus.materials["Warm architectural light"].emissiveIntensity>2.7'));page.evaluate("campusApp.view('overview',true)");page.locator('#collapse').click();page.screenshot(path=str(OUT/'final-night.png'));page.locator('#collapse').click()
    page.locator('#lights').uncheck();page.wait_for_timeout(80);check('Light switch controls illumination',not page.evaluate('campusApp.campus.parts.lighting.visible'));page.locator('#lights').check();page.locator('[data-time=morning]').click();page.wait_for_timeout(1650)
    page.locator('#quality').select_option('low');check('Low quality removes fine detail',not page.evaluate('campusApp.campus.parts.detail.visible'));page.locator('#quality').select_option('high')
    page.locator('#dof').check();check('Depth of field control works',page.evaluate('campusApp.state.dof'));page.locator('#dof').uncheck();page.locator('#collapse').click()
    page.locator('#orbit').click();page.wait_for_timeout(150);check('Auto orbit starts',page.evaluate('campusApp.state.orbit'));page.mouse.move(820,550);page.mouse.down();page.mouse.up();check('Manual input stops orbit',not page.evaluate('campusApp.state.orbit'))
    page.locator('#photo').click();check('Photography mode hides controls',page.locator('body').evaluate('(e)=>e.classList.contains("photo")'));page.keyboard.press('Escape');check('Escape restores interface',not page.locator('#exit-photo').is_visible())
    page.evaluate("campusApp.view('overview',true);campusApp.state.paused=true");page.wait_for_timeout(150)
    with page.expect_download(timeout=60000) as task:page.locator('#export-glb').click()
    task.value.save_as(ROOT/'大学主教学楼.glb');raw=(ROOT/'大学主教学楼.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+size]);check('GLB is valid glTF2',struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw)))
    names=[n.get('name','') for n in gltf['nodes']];check('GLB preserves building, flags and groups','University_Main_Teaching_Building' in names and 'Five_star_national_flag' in names and 'landscape' in names)
    page.locator('#resolution').select_option('3840')
    with page.expect_download(timeout=60000) as task:page.locator('#save-png').click()
    task.value.save_as(OUT/'browser-4k.png');check('PNG exports actual 4K resolution',Image.open(OUT/'browser-4k.png').size==(3840,2160))
    data=page.evaluate('campusApp.exportData()');(OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8');check('Blender snapshot contains textured cloth and grouped geometry',len(data['objects'])>6000 and any(m['name']=='National flag red silk' and m.get('texture') for m in data['materials'].values()))
    report['metrics']=page.evaluate('campusApp.metrics')
    # Mobile uses real touch events, not only resized desktop mouse events.
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);m=mobile.new_page();m.on('pageerror',lambda e:report['errors'].append(str(e)));m.goto((ROOT/'大学主教学楼.html').as_uri(),wait_until='networkidle');m.wait_for_function('window.campusApp?.ready');m.wait_for_timeout(500)
    check('Mobile fits viewport and collapses settings',m.locator('#panel-content').is_hidden() and m.evaluate('document.documentElement.scrollWidth===390'))
    cdp=mobile.new_cdp_session(m)
    before=m.evaluate('campusApp.camera.position.toArray()');cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':170,'y':430}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':245,'y':470}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(250);check('Touch drag rotates',before!=m.evaluate('campusApp.camera.position.toArray()'))
    before=m.evaluate('campusApp.camera.position.distanceTo(campusApp.controls.target)');cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':140,'y':420,'id':1},{'x':230,'y':420,'id':2}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':105,'y':420,'id':1},{'x':265,'y':420,'id':2}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(250);check('Two finger pinch zooms',m.evaluate('campusApp.camera.position.distanceTo(campusApp.controls.target)')<before)
    m.evaluate("campusApp.view('overview',true)");m.screenshot(path=str(OUT/'final-mobile.png'));mobile.close()
    reduced=browser.new_context(reduced_motion='reduce');q=reduced.new_page();q.goto((ROOT/'大学主教学楼.html').as_uri(),wait_until='networkidle');q.wait_for_function('window.campusApp?.ready');check('Reduced motion starts paused',q.evaluate('campusApp.state.paused'));reduced.close()
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        host=browser.new_page(viewport={'width':1400,'height':1000});host.on('pageerror',lambda e:report['errors'].append(str(e)));host.goto(f'http://127.0.0.1:{server.server_port}/接入演示.html',wait_until='networkidle');host.wait_for_function('window.campusHost?.ready');host.wait_for_timeout(500)
        check('Host factory mounts model',host.evaluate('campusHost.campus.model.parent===campusHost.scene'))
        check('Asset mode creates no viewer canvas',host.evaluate('!campusHost.assetFrame.contentWindow.campusApp&&campusHost.assetFrame.contentDocument.querySelectorAll("canvas").length===0'))
        host.screenshot(path=str(OUT/'integration-demo.png'))
        life=host.evaluate('''()=>{let g=0,m=0,t=0,envDisposals=0;const seen=new Set(),asset=campusHost.campus,env=campusHost.scene.environment;env.addEventListener('dispose',()=>envDisposals++);asset.materials['Blue grey glazing'].envMap=env;asset.model.traverse(o=>{if(o.geometry&&!seen.has(o.geometry)){seen.add(o.geometry);o.geometry.addEventListener('dispose',()=>g++);}for(const a of Array.isArray(o.material)?o.material:[o.material])if(a&&!seen.has(a)){seen.add(a);a.addEventListener('dispose',()=>m++);for(const k of ['map','bumpMap'])if(a[k]&&!seen.has(a[k])){seen.add(a[k]);a[k].addEventListener('dispose',()=>t++);}}});asset.dispose();asset.dispose();return{g,m,t,envDisposals,removed:!asset.model.parent};}''')
        check('Dispose is idempotent and preserves shared environment',life['g']>10 and life['m']>15 and life['t']>=3 and life['removed'] and life['envDisposals']==0);report['lifecycle']=life
    finally:server.shutdown();server.server_close()
    check('No runtime or WebGL errors',not report['errors']);(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(report['checks']),flush=True);browser.close()
