"""Offline artifact and meaningful spatial/interaction checks. No server/network required."""
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
    page.goto((ROOT/'霁衡中心.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.officeApp?.ready',timeout=120000,polling=100)
    check('one HTML runs with network disabled',not any(r.startswith(('http:','https:')) for r in requests))
    check('one scene canvas',page.locator('canvas').count()==1)
    bounds=page.evaluate('(()=>{const a=officeApp,b=new a.THREE.Box3().setFromObject(a.model.root);return{min:b.min.toArray(),max:b.max.toArray()}})()')
    check('all geometry remains inside 112m square',all(bounds['min'][i]>=-56.01 and bounds['max'][i]<=56.01 for i in [0,2]))
    check('184m roof and 46 floors',abs(bounds['max'][1]-184)<.01 and page.evaluate('officeApp.model.manifest.buildings[0].floors===46'))
    check('nine separately editable owner groups',page.evaluate('officeApp.model.groups.size===9'))
    page.click('#pause');before=page.evaluate('officeApp.model.simulationTime');page.wait_for_timeout(200);check('pause freezes simulation',before==page.evaluate('officeApp.model.simulationTime'))
    page.click('#pause');page.wait_for_timeout(200);check('resume advances simulation',page.evaluate('officeApp.model.simulationTime')>before)
    before=page.evaluate('officeApp.camera.position.toArray()');page.mouse.move(770,450);page.mouse.down();page.mouse.move(895,490,steps=8);page.mouse.up();page.wait_for_timeout(200)
    check('drag rotates model view',before!=page.evaluate('officeApp.camera.position.toArray()'))
    before=page.evaluate('officeApp.controls.target.toArray()');page.mouse.down(button='right');page.mouse.move(950,550,steps=8);page.mouse.up(button='right');page.wait_for_timeout(200)
    check('right drag pans model view',before!=page.evaluate('officeApp.controls.target.toArray()'))
    before=page.evaluate('officeApp.camera.zoom');page.mouse.move(750,650);page.mouse.wheel(0,-280);page.wait_for_function('(z)=>officeApp.camera.zoom>z',arg=before,timeout=8000,polling=100);check('wheel zooms orthographic view',page.evaluate('officeApp.camera.zoom')>before)
    page.click('#projection');check('perspective toggle works',page.evaluate('officeApp.camera.isPerspectiveCamera'))
    page.click('#free');before=page.evaluate('officeApp.camera.position.toArray()');page.locator('canvas').click(position={'x':700,'y':500});page.keyboard.down('w');page.wait_for_timeout(400);page.keyboard.up('w')
    check('free-view WASD moves camera',before!=page.evaluate('officeApp.camera.position.toArray()') and page.evaluate('officeApp.state.free'))
    for name in ['overview','front','top','low','entrance','terrace','roof']:
        page.evaluate('(v)=>officeApp.view(v)',name);check('valid camera '+name,page.evaluate('officeApp.camera.position.toArray().every(Number.isFinite)'))
    page.select_option('#part','roof');page.click('#isolate');check('part isolation hides other groups',page.evaluate("officeApp.model.groups.get('roof').visible&&[...officeApp.model.groups].filter(([id])=>id!=='roof').every(([,g])=>!g.visible)"))
    snapshot=page.evaluate('officeApp.exportScene()');check('full snapshot while isolated still includes whole model',len(set(o['owner'] for o in snapshot['objects']))==9)
    check('snapshot export restores isolation',page.evaluate("officeApp.state.isolated==='roof'&& !officeApp.model.groups.get('site').visible"))
    page.evaluate("officeApp.view('overview')");page.uncheck('#people');page.wait_for_timeout(120)
    check('people control independent of vehicles',page.evaluate("!officeApp.model.root.getObjectByName('Office pedestrian 0').visible&&officeApp.model.root.getObjectByName('Office car 0').visible"));page.check('#people')
    page.uncheck('#vehicles');page.wait_for_timeout(120);check('vehicle switch hides moving vehicles',page.evaluate("!officeApp.model.root.getObjectByName('Office car 0').visible"));page.check('#vehicles')
    page.uncheck('#mechanical');before=page.evaluate("officeApp.model.root.getObjectByName('Cooling fan 0').rotation.y");page.wait_for_timeout(200);check('mechanical switch freezes fan',before==page.evaluate("officeApp.model.root.getObjectByName('Cooling fan 0').rotation.y"));page.check('#mechanical')
    page.uncheck('#wind');before=page.evaluate('officeApp.model.windTime');page.wait_for_timeout(200);check('wind switch freezes foliage clock',before==page.evaluate('officeApp.model.windTime'));page.check('#wind')
    for name in ['day','evening','night','white','morning']:
        page.select_option('#time',name);check('lighting preset '+name,page.evaluate('(n)=>officeApp.state.time===n',name))
        if name=='night':check('night has real plaza lights and lit offices',page.evaluate("officeApp.scene.children.filter(o=>o.isPointLight&&o.intensity>0).length===16&&officeApp.model.materials['office-lit'].emissiveIntensity>1"));page.screenshot(path=str(OUT/'final-night.png'))
    page.select_option('#quality','low');check('quality applies real detail reduction',page.evaluate("officeApp.model.quality==='low'&&[...officeApp.model.groups.get('roof').children].some(o=>o.userData.tier===2&&!o.visible)"));page.select_option('#quality','high')
    sim=page.evaluate('''()=>{
      const a=officeApp,m=LandmarkOfficeModule.create({THREE:a.THREE,blockSize:84,quality:'low',coarse:true}),box=new a.THREE.Box3().setFromObject(m.root);
      let pure=true;m.root.traverse(o=>{if(o.isCamera||o.isLight)pure=false});
      const car=m.root.getObjectByName('Office car 0'),person=m.root.getObjectByName('Office pedestrian 0'),lastCar=car.position.clone(),lastPerson=person.position.clone();
      let outside=false,collision=false,maxCarStep=0,maxPersonStep=0,maxGate=0,moved=false,doorOpen=0,finite=true;
      for(let i=0;i<1200;i++){
        m.update(.25);maxCarStep=Math.max(maxCarStep,lastCar.distanceTo(car.position));lastCar.copy(car.position);maxPersonStep=Math.max(maxPersonStep,lastPerson.distanceTo(person.position));lastPerson.copy(person.position);
        maxGate=Math.max(maxGate,m.root.getObjectByName('Vehicle barrier').rotation.z);doorOpen=Math.max(doorOpen,Math.abs(m.root.getObjectByName('Automatic door 1').position.x));
        m.root.traverse(o=>{if(/^Office pedestrian |^Office car /.test(o.name)){const v=o.position;outside ||=Math.abs(v.x)>55||Math.abs(v.z)>55;collision ||=Math.abs(v.x)<35.5&&Math.abs(v.z)<31.9;finite&&=v.toArray().every(Number.isFinite)}});
      }
      const paused=m.simulationTime;m.setDynamicsEnabled(false);m.update(.25);const pauseWorks=paused===m.simulationTime;
      m.root.position.set(27,.34,-12);m.root.rotation.y=.4;m.root.updateMatrixWorld(true);const json=m.exportScene();const worldSpace=json.snapshotSpace==='world'&&json.objects.some(o=>Math.abs(o.matrix[12])>27);
      const scaled=Math.abs(box.max.x-box.min.x-84)<.02;m.dispose();m.dispose();
      return{pure,scaled,outside,collision,finite,maxCarStep,maxPersonStep,maxGate,doorOpen,pauseWorks,worldSpace,disposed:m.disposed&&m.root.children.length===0};
    }''')
    for key in ['pure','scaled','finite','pauseWorks','worldSpace','disposed']:check('factory and 300s simulation '+key,sim[key])
    check('actors stay on plot and out of building walls',not sim['outside'] and not sim['collision'])
    check('car and pedestrian routes have no teleport jumps',sim['maxCarStep']<1 and sim['maxPersonStep']<1)
    check('barrier opens for arriving cars',sim['maxGate']>1.2)
    check('doors respond to nearby people',sim['doorOpen']>2.5)
    with page.expect_download(timeout=180000) as dl:page.click('#export')
    dl.value.save_as(ROOT/'jiheng-landmark-office.glb');data=(ROOT/'jiheng-landmark-office.glb').read_bytes();check('full GLB valid binary header',data[:4]==b'glTF')
    size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);names=[n.get('name','') for n in doc['nodes']];check('full GLB retains architecture and scene groups',all(x in names for x in ['JH-01','lower','upper','podium','site','roof']))
    page.select_option('#part','roof');page.click('#isolate')
    with page.expect_download(timeout=180000) as dl:page.click('#export-part')
    dl.value.save_as(OUT/'jiheng-roof.glb');data=(OUT/'jiheng-roof.glb').read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);names=[n.get('name','') for n in doc['nodes']]
    check('selected GLB exports roof without site', 'roof' in names and 'site' not in names)
    page.evaluate("officeApp.view('overview')");page.wait_for_timeout(200);page.screenshot(path=str(OUT/'final-overview.png'))
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300);check('mobile has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth===390'))
    check('mobile settings collapsed by default',page.locator('#panel-body').is_hidden())
    mobile=page.evaluate('''()=>{const a=officeApp,box=new a.THREE.Box3().setFromObject(a.model.root);a.camera.updateMatrixWorld();return [box.min.x,box.max.x].flatMap(x=>[box.min.y,box.max.y].flatMap(y=>[box.min.z,box.max.z].map(z=>new a.THREE.Vector3(x,y,z).project(a.camera).toArray())))}''')
    check('mobile overview fits complete parcel and tower',all(abs(v[0])<=1 and abs(v[1])<=1 for v in mobile));page.screenshot(path=str(OUT/'final-mobile.png'))
    check('no JavaScript or WebGL errors',not errors)
    (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds,'simulation':sim,'mobile_ndc':mobile},indent=2),encoding='utf8');browser.close()
    if not all(c['passed'] for c in checks):raise RuntimeError('Validation failed; inspect outputs/verification.json')
