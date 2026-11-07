import json,time,struct
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];results=[]
def check(name,result):
    results.append({'check':name,'passed':bool(result)})
    if not result:raise AssertionError(name)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1);context.set_offline(True)
    page=context.new_page();errors=[];network=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda req:network.append(req.url))
    page.goto((ROOT/'澄和医院.html').as_uri(),wait_until='load');page.wait_for_function('window.hospitalApp?.ready');page.wait_for_timeout(1300)
    check('single HTML works offline',page.evaluate('hospitalApp.ready') and all(not u.startswith(('http:','https:')) for u in network))
    check('four independently named buildings',page.evaluate("['inpatient','outpatient','emergency','medical-tech'].every(id=>hospitalApp.hospital.buildings.has(id))"))
    check('112 m square and all geometry inside bounds',page.evaluate('(()=>{let a=hospitalApp,b=new a.THREE.Box3().setFromObject(a.hospital.root);return b.min.x>=-56.01&&b.max.x<=56.01&&b.min.z>=-56.01&&b.max.z<=56.01&&a.hospital.manifest.footprint.width===112})()'))
    check('garage has a real descending surface',page.evaluate("(()=>{let a=hospitalApp,g=a.hospital.root.getObjectByName('garage-ramp');let p=g.geometry.attributes.position;return Math.min(...Array.from(p.array).filter((v,i)=>i%3===1))<-4})()"))
    before=page.evaluate('hospitalApp.camera().position.toArray()');page.mouse.move(900,550);page.mouse.down();page.mouse.move(1000,590,steps=10);page.mouse.up();page.wait_for_timeout(200);check('drag orbit',before!=page.evaluate('hospitalApp.camera().position.toArray()'))
    before=page.evaluate('hospitalApp.controls().target.toArray()');page.mouse.move(900,550);page.mouse.down(button='right');page.mouse.move(950,550,steps=8);page.mouse.up(button='right');check('right drag pan',before!=page.evaluate('hospitalApp.controls().target.toArray()'))
    before=page.evaluate('hospitalApp.camera().position.distanceTo(hospitalApp.controls().target)');page.locator('#zoom-in').click();page.wait_for_timeout(100);check('zoom',page.evaluate('hospitalApp.camera().position.distanceTo(hospitalApp.controls().target)')<before)
    page.locator('#projection').click();check('orthographic view',page.evaluate('hospitalApp.camera().isOrthographicCamera'));page.locator('#projection').click()
    page.locator('#pause').click();t=page.evaluate('hospitalApp.state.simTime');position=page.evaluate("hospitalApp.hospital.root.getObjectByName('ambulance').position.toArray()");page.wait_for_timeout(500);check('pause freezes time and vehicles',t==page.evaluate('hospitalApp.state.simTime') and position==page.evaluate("hospitalApp.hospital.root.getObjectByName('ambulance').position.toArray()"));page.locator('#pause').click();page.wait_for_timeout(300);check('resume moves vehicles',position!=page.evaluate("hospitalApp.hospital.root.getObjectByName('ambulance').position.toArray()"))
    page.locator('#tour').click();check('tour enabled',page.evaluate('hospitalApp.state.tour'));page.mouse.move(900,550);page.mouse.down();page.mouse.move(920,550);page.mouse.up();check('manual interaction stops tour',not page.evaluate('hospitalApp.state.tour'))
    page.locator('[data-time=night]').click();check('night lighting',page.evaluate('hospitalApp.scene.children.find(o=>o.isDirectionalLight).intensity<1'));page.evaluate("hospitalApp.view('overview',true)");page.wait_for_timeout(300);page.screenshot(path=str(ROOT/'outputs/03-night.png'))
    page.locator('[data-time=morning]').click();page.locator('#quality').select_option('low');check('low quality',page.evaluate("hospitalApp.hospital.quality==='low'"));page.locator('#quality').select_option('high')
    page.evaluate("hospitalApp.select('emergency')");check('building selection',page.locator('#building-name').inner_text()=='急诊中心')
    with page.expect_download(timeout=60000) as dl:page.locator('#export-building').click()
    dl.value.save_as(ROOT/'hospital-emergency.glb');check('building GLB', (ROOT/'hospital-emergency.glb').read_bytes()[:4]==b'glTF');page.locator('#close-selection').click()
    page.evaluate("hospitalApp.view('overview',true)")
    with page.expect_download(timeout=60000) as dl:page.locator('#export-glb').click()
    dl.value.save_as(ROOT/'hospital-campus.glb');binary=(ROOT/'hospital-campus.glb').read_bytes();check('whole GLB',binary[:4]==b'glTF')
    length=struct.unpack('<I',binary[12:16])[0];gltf=json.loads(binary[20:20+length]);check('GLB excludes sky lights and display environment',not gltf.get('cameras') and not any(n.get('name','') in ['Backdrop','Display plinth'] for n in gltf.get('nodes',[])))
    lifecycle=page.evaluate('''()=>{const a=hospitalApp,T=a.THREE,host=new T.Scene(),before=host.children.length;const m=HospitalModule.create({THREE:T,embedded:true,quality:'medium'});host.add(m.root);let lights=0,cameras=0;m.root.traverse(o=>{if(o.isLight)lights++;if(o.isCamera)cameras++;});m.update(.1,10);m.setTimeOfDay('night');m.setQuality('low');let disposeEvents=0;m.root.traverse(o=>{if(o.geometry)o.geometry.addEventListener('dispose',()=>disposeEvents++);});m.dispose();m.dispose();const m2=HospitalModule.create({THREE:T,embedded:true});host.add(m2.root);const reloaded=m2.buildings.size===4;m2.dispose();return {clean:host.children.length===before,lights,cameras,disposed:m.disposed,disposeEvents,reloaded,originalWorks:a.hospital.buildings.size===4};}''')
    check('host factory creates no lights or cameras',lifecycle['lights']==0 and lifecycle['cameras']==0);check('dispose and repeat loading',lifecycle['clean'] and lifecycle['disposed'] and lifecycle['reloaded'] and lifecycle['disposeEvents']>0);check('disposing imported instance preserves standalone instance',lifecycle['originalWorks'])
    # Probe every animated route over two minutes, independently from the on-screen timeline.
    motion=page.evaluate('''()=>{const a=hospitalApp,T=a.THREE,m=HospitalModule.create({THREE:T,quality:'high'});let penetrations=0,escaped=0;for(let t=0;t<=120;t+=.5){m.update(.5,t);m.root.getObjectByName('Hospital local life').children.forEach(o=>{if(o.name==='visitor'||o.name==='medical-staff'||o.name==='wheelchair-visitor'||o.name==='ambulance'||o.name==='visitor-car'){if(Math.abs(o.position.x)>56||Math.abs(o.position.z)>56)escaped++;for(const b of m.manifest.buildings){if(Math.abs(o.position.x-b.x)<b.w/2-.15&&Math.abs(o.position.z-b.z)<b.d/2-.15&&o.position.y<b.height)penetrations++;}}});}m.dispose();return {penetrations,escaped};}''')
    check('two-minute route sampling does not cross buildings',motion['penetrations']==0);check('actors stay inside campus',motion['escaped']==0)
    page.evaluate("hospitalApp.view('overview',true)");page.wait_for_timeout(3200);page.screenshot(path=str(ROOT/'outputs/04-overview-final.png'))
    page.set_viewport_size({'width':420,'height':880});page.evaluate("hospitalApp.view('overview',true)");page.wait_for_timeout(350);page.locator('#collapse').click();page.screenshot(path=str(ROOT/'outputs/04-mobile.png'));check('mobile canvas and layout',page.evaluate('document.documentElement.scrollWidth===420'))
    check('no script or WebGL errors',not errors)
    result={'checks':results,'errors':errors,'motion':motion,'metrics':page.evaluate('hospitalApp.metrics()'),'browser':browser.version,'network_requests':network,'html_bytes':(ROOT/'澄和医院.html').stat().st_size}
    (ROOT/'outputs/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True));browser.close()
