"""Functional and spatial checks of the delivered offline artifact."""
import json,struct
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    ctx=browser.new_context(viewport={'width':1500,'height':1000},accept_downloads=True);ctx.set_offline(True)
    page=ctx.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url))
    page.goto((ROOT/'暖庭花园.html').as_uri(),wait_until='networkidle');page.wait_for_function('gardenApp?.ready',timeout=60000)
    check('single HTML works entirely offline',not any(r.startswith(('http:','https:')) for r in requests))
    bounds=page.evaluate('(()=>{const a=gardenApp,b=new a.THREE.Box3().setFromObject(a.model.root);return{min:b.min.toArray(),max:b.max.toArray()}})()')
    check('all geometry fits the 112m square',bounds['min'][0]>=-56.01 and bounds['max'][0]<=56.01 and bounds['min'][2]>=-56.01 and bounds['max'][2]<=56.01)
    check('four independent residential groups with correct floor counts',page.evaluate("gardenApp.model.buildings.size===4&&gardenApp.model.manifest.buildings.map(b=>b.floors).sort().join(',')==='4,5,5,6'"))
    check('building origins match the native site coordinates',page.evaluate("gardenApp.model.manifest.buildings.every(b=>{const g=gardenApp.model.buildings.get(b.id);return Math.abs(g.position.x-b.x)<.001&&Math.abs(g.position.z-b.z)<.001})"))
    page.click('#pause');time=page.evaluate('gardenApp.model.simulationTime');page.wait_for_timeout(180);check('pause freezes simulation',time==page.evaluate('gardenApp.model.simulationTime'))
    page.click('#pause');page.wait_for_timeout(180);check('resume advances simulation',page.evaluate('gardenApp.model.simulationTime')>time)
    before=page.evaluate('gardenApp.camera.position.toArray()');page.mouse.move(800,480);page.mouse.down();page.mouse.move(940,530,steps=8);page.mouse.up();page.wait_for_timeout(160)
    check('left drag rotates the view',before!=page.evaluate('gardenApp.camera.position.toArray()'))
    before=page.evaluate('gardenApp.controls.target.toArray()');page.mouse.down(button='right');page.mouse.move(1000,580,steps=8);page.mouse.up(button='right');page.wait_for_timeout(160)
    check('right drag pans the view',before!=page.evaluate('gardenApp.controls.target.toArray()'))
    before=page.evaluate('gardenApp.camera.position.distanceTo(gardenApp.controls.target)');page.mouse.move(750,650);page.mouse.wheel(0,-250);page.wait_for_function('(before)=>gardenApp.camera.position.distanceTo(gardenApp.controls.target)<before*.999',arg=before,timeout=5000)
    check('scroll zooms the view',page.evaluate('gardenApp.camera.position.distanceTo(gardenApp.controls.target)')<before)
    for view in ['overview','top','entrance','garden','roof','A','B','C','D']:
        page.evaluate('(v)=>gardenApp.view(v)',view)
        check('valid view '+view,page.evaluate('gardenApp.camera.position.toArray().every(Number.isFinite)'))
    page.evaluate("gardenApp.view('A')")
    check('single building view isolates A',page.evaluate("gardenApp.model.buildings.get('A').visible&&[...gardenApp.model.buildings].filter(([id])=>id!=='A').every(([,g])=>!g.visible)"))
    page.evaluate("gardenApp.view('overview')")
    check('overview restores every house',page.evaluate('[...gardenApp.model.buildings.values()].every(g=>g.visible)'))
    page.uncheck('#people');page.wait_for_timeout(160);check('people switch works independently',page.evaluate("!gardenApp.model.root.getObjectByName('Resident 0').visible&&gardenApp.model.root.getObjectByName('Moving car 0').visible"));page.check('#people')
    page.uncheck('#vehicles');page.wait_for_timeout(160);check('vehicles switch works independently',page.evaluate("!gardenApp.model.root.getObjectByName('Moving car 0').visible&&gardenApp.model.root.getObjectByName('Resident 0').visible"));page.check('#vehicles')
    page.select_option('#quality','low');check('quality propagates to the model',page.evaluate("gardenApp.model.quality==='low'"));page.select_option('#quality','high')
    page.select_option('#time','night');page.wait_for_timeout(450)
    check('night uses real scene lights',page.evaluate("(()=>{let n=0;gardenApp.scene.traverse(o=>{if(o.isPointLight&&o.intensity>0)n++});return n>0})()"));page.screenshot(path=str(OUT/'final-night.png'))
    page.select_option('#time','afternoon');page.wait_for_timeout(300)
    result=page.evaluate('''()=>{
      const a=gardenApp,m=GardenHousingModule.create({THREE:a.THREE,blockSize:84,coarse:true}),box=new a.THREE.Box3().setFromObject(m.root);
      let pure=true;m.root.traverse(o=>{if(o.isLight||o.isCamera)pure=false});
      const person=m.root.getObjectByName('Resident 0'),car=m.root.getObjectByName('Moving car 0'),beforePerson=person.position.clone(),beforeCar=car.position.clone();
      let outside=false,collision=false,finite=true,maxCarStep=0,last=car.position.clone();
      for(let i=0;i<800;i++){
        m.update(.25);m.root.updateWorldMatrix(true,true);
        const actors=[];m.root.traverse(o=>{if(/^Resident \\d+$|^Moving car \\d+$/.test(o.name)&&o.visible)actors.push(o)});
        for(const o of actors){const v=m.root.worldToLocal(o.getWorldPosition(new a.THREE.Vector3()));outside=outside||Math.abs(v.x)>54.5||Math.abs(v.z)>54.5;finite=finite&&v.toArray().every(Number.isFinite);for(const b of m.manifest.buildings){collision=collision||(Math.abs(v.x-b.x)<b.w/2-.1&&Math.abs(v.z-b.z)<b.d/2-.1);}}
        maxCarStep=Math.max(maxCarStep,last.distanceTo(car.position));last.copy(car.position);
      }
      const moving=beforePerson.distanceTo(person.position)>.1&&beforeCar.distanceTo(car.position)>.1,scaled=Math.abs(box.max.x-box.min.x-84)<.01;
      m.dispose();m.dispose();return{pure,scaled,moving,outside,collision,finite,maxCarStep,disposed:m.disposed&&m.root.children.length===0};
    }''')
    for key in ['pure','scaled','moving','finite','disposed']:check('factory and 200s simulation '+key,result[key])
    check('people and cars stay inside the site',not result['outside'])
    check('people and cars avoid building footprints',not result['collision'])
    check('car loop has no teleport jumps',result['maxCarStep']<3)
    with page.expect_download(timeout=180000) as dl:page.click('#export')
    dl.value.save_as(ROOT/'nuanting-garden-housing.glb');data=(ROOT/'nuanting-garden-housing.glb').read_bytes();check('GLB has a valid binary header',data[:4]==b'glTF')
    size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);names=[n.get('name','') for n in doc['nodes']]
    check('GLB contains all four independently named buildings',all(n in names for n in ['A','B','C','D']))
    page.screenshot(path=str(OUT/'final-overview.png'))
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(350)
    check('mobile layout has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth===390'))
    page.screenshot(path=str(OUT/'final-mobile.png'))
    check('no JavaScript or WebGL errors',not errors)
    report={'checks':checks,'errors':errors,'bounds':bounds,'simulation':result};(OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');browser.close()
    if not all(c['passed'] for c in checks):raise RuntimeError('Some validation checks failed; see outputs/verification.json')
