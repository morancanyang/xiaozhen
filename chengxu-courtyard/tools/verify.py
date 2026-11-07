"""Exercise offline UI, actual geometry, exports, routes and host integration."""
import json,struct,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
with sync_playwright() as p:
    ctx=p.chromium.launch_persistent_context(str(OUT/'qa-browser-profile'),channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'],viewport={'width':1280,'height':800},device_scale_factor=1,accept_downloads=True)
    ctx.set_offline(True);page=ctx.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url))
    page.goto((ROOT/'澄序住区.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.courtyardApp?.ready',polling=100,timeout=120000);page.wait_for_function('courtyardApp.metrics().frames>15',polling=100,timeout=120000)
    check('fully offline HTML',not any(r.startswith(('http:','https:')) for r in requests))
    check('four independent towers with correct floors',page.evaluate("courtyardApp.model.buildings.size===4&&courtyardApp.model.manifest.buildings.map(b=>b.floors).join(',')==='20,22,22,24'"))
    check('no asphalt material or transmission pass',page.evaluate("(()=>{let ok=true;courtyardApp.model.root.traverse(o=>{if(o.isMesh)ok&&=!/asphalt|沥青/i.test(o.material.name)&&!o.material.transmission});return ok})()"))
    page.click('#pause');t=page.evaluate('courtyardApp.model.simulationTime');page.wait_for_timeout(250);check('pause freezes motion',t==page.evaluate('courtyardApp.model.simulationTime'));page.click('#pause');page.wait_for_timeout(200);check('resume advances motion',page.evaluate('courtyardApp.model.simulationTime')>t)
    before=page.evaluate('courtyardApp.camera.position.toArray()');page.mouse.move(640,560);page.mouse.down();page.mouse.move(760,610,steps=10);page.mouse.up();page.wait_for_timeout(250);check('drag rotates',before!=page.evaluate('courtyardApp.camera.position.toArray()'))
    before=page.evaluate('courtyardApp.controls.target.toArray()');page.mouse.move(640,560);page.mouse.down(button='right');page.mouse.move(710,580,steps=8);page.mouse.up(button='right');page.wait_for_timeout(200);check('right drag pans',before!=page.evaluate('courtyardApp.controls.target.toArray()'))
    z=page.evaluate('courtyardApp.camera.zoom');page.mouse.move(640,560);page.mouse.wheel(0,-300);page.wait_for_timeout(250);check('wheel zooms orthographic view',page.evaluate('courtyardApp.camera.zoom')>z)
    page.click('#projection');check('perspective projection',page.evaluate('courtyardApp.camera.isPerspectiveCamera'));page.click('#free');before=page.evaluate('courtyardApp.camera.position.toArray()');page.locator('#viewport canvas').focus();page.keyboard.down('w');page.wait_for_timeout(400);page.keyboard.up('w');check('WASD moves free camera',before!=page.evaluate('courtyardApp.camera.position.toArray()'))
    for v in ['overview','front','top','low','entrance','garden','roof','A','B','C','D']:
        page.evaluate('(v)=>courtyardApp.view(v)',v);check('valid '+v+' view',page.evaluate('courtyardApp.camera.position.toArray().every(Number.isFinite)'))
    page.evaluate("courtyardApp.view('A')");check('A isolation retains its facade and roof',page.evaluate("courtyardApp.model.groups.get('A-facade').visible&&courtyardApp.model.groups.get('A-roof').visible&&!courtyardApp.model.buildings.get('B').visible"))
    with page.expect_download(timeout=120000) as dl:page.click('#export-part')
    dl.value.save_as(OUT/'chengxu-A.glb');data=(OUT/'chengxu-A.glb').read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);names=[n.get('name') for n in doc['nodes']];check('A exported independently without other towers','A' in names and all(v not in names for v in ['B','C','D']))
    page.evaluate("courtyardApp.view('overview')")
    page.uncheck('#people');check('residents can be hidden',page.evaluate("!courtyardApp.model.root.getObjectByName('Resident 0').visible"));page.check('#people');page.uncheck('#birds');check('birds toggle separately',page.evaluate("!courtyardApp.model.root.getObjectByName('Courtyard bird 0').visible&&courtyardApp.model.root.getObjectByName('Resident 0').visible"));page.check('#birds')
    page.select_option('#quality','low');check('quality propagates',page.evaluate("courtyardApp.model.quality==='low'"));page.select_option('#quality','high');page.select_option('#time','night');page.wait_for_timeout(500)
    check('night lighting stays within six point lights',page.evaluate('(()=>{let n=0;courtyardApp.scene.traverse(o=>{if(o.isPointLight&&o.intensity>0)n++});return n===6})()'));page.screenshot(path=str(OUT/'03-night.png'))
    page.select_option('#time','morning');page.evaluate("courtyardApp.view('overview')");page.wait_for_timeout(500)
    spatial=page.evaluate('''()=>{
      const a=courtyardApp,T=a.THREE,m=ResidentialCourtyardModule.create({THREE:T}),bounds=new T.Box3().setFromObject(m.root);
      let pure=true;m.root.traverse(o=>{if(o.isLight||o.isCamera)pure=false});
      const heights=m.manifest.buildings.every(b=>Math.abs(new T.Box3().setFromObject(m.buildings.get(b.id)).max.y-b.height)<.01);
      let outside=false,collision=false,finite=true;const actor=m.root.getObjectByName('Resident 18'),door=m.root.getObjectByName('A sensed door -1'),initial=door.position.x;let doorMoved=false;
      for(let i=0;i<800;i++){m.update(.25);for(let n=0;n<22;n++){const o=m.root.getObjectByName('Resident '+n),v=o.position;outside||=Math.abs(v.x)>55||Math.abs(v.z)>55;finite&&=v.toArray().every(Number.isFinite);for(const b of m.manifest.buildings)collision||=Math.abs(v.x-b.x)<b.w/2&&Math.abs(v.z-b.z)<b.d/2}doorMoved||=Math.abs(door.position.x-initial)>.05}
      const r={pure,heights,inside:!outside,no_collision:!collision,finite,doorMoved,square:Math.abs(bounds.max.x-bounds.min.x-112)<.01&&Math.abs(bounds.max.z-bounds.min.z-112)<.01};m.dispose();m.dispose();r.disposed=m.disposed&&m.root.children.length===0;const scaled=ResidentialCourtyardModule.create({THREE:T,blockSize:84,coarse:true});const sb=new T.Box3().setFromObject(scaled.root);r.scalable=Math.abs(sb.max.x-sb.min.x-84)<.01;scaled.dispose();return r;
    }''')
    for k,v in spatial.items():check('spatial / simulation '+k,v)
    # Measure real RAF intervals while repeatedly rotating the same camera for six seconds.
    bench=page.evaluate('''()=>new Promise(resolve=>{const a=courtyardApp,intervals=[],start=performance.now();let prev=start;function f(now){const elapsed=now-start;if(elapsed>350)intervals.push(now-prev);prev=now;const t=elapsed*.00042;a.camera.position.set(Math.sin(t)*240,155,Math.cos(t)*240);a.camera.lookAt(a.controls.target);if(elapsed<6500)requestAnimationFrame(f);else{intervals.sort((a,b)=>a-b);resolve({fps:1000/(intervals.reduce((a,b)=>a+b,0)/intervals.length),p95_ms:intervals[Math.floor(intervals.length*.95)],frames:intervals.length,metrics:a.metrics(),viewport:[innerWidth,innerHeight],userAgent:navigator.userAgent})}}requestAnimationFrame(f)})''')
    (OUT/'performance.json').write_text(json.dumps(bench,indent=2),encoding='utf8');check('interactive benchmark exceeds 30 FPS',bench['fps']>30)
    page.set_viewport_size({'width':390,'height':844});page.wait_for_function('courtyardApp.camera.aspect===390/844 || courtyardApp.camera.isOrthographicCamera',polling=100);page.wait_for_timeout(250);page.evaluate("courtyardApp.view('overview')");page.wait_for_timeout(300);page.screenshot(path=str(OUT/'03-mobile.png'));check('mobile page stays in viewport',page.evaluate('document.documentElement.scrollWidth===innerWidth'))
    if page.locator('#panel-body').is_hidden():page.click('#collapse')
    check('mobile controls expand',page.locator('#time').is_visible());check('no browser errors',not errors)
    (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'benchmark':bench},indent=2),encoding='utf8');ctx.close()
assert all(c['passed'] for c in checks),'Verification failure'
