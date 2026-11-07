import json,math,struct
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';checks=[]
def check(name,result):
    checks.append({'check':name,'passed':bool(result)})
    print(('PASS ' if result else 'FAIL ')+name,flush=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    ctx=browser.new_context(viewport={'width':1600,'height':1100},device_scale_factor=1,accept_downloads=True);ctx.set_offline(True)
    page=ctx.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url))
    page.goto((ROOT/'云际中心.html').as_uri(),wait_until='load');page.wait_for_function('skylineApp?.ready',timeout=60000);page.wait_for_timeout(1500)
    check('single HTML works offline without external requests',not any(u.startswith(('http:','https:')) for u in requests))
    check('112 m square parcel and 224 m tower',page.evaluate('skylineApp.tower.manifest.footprint.width===112&&skylineApp.tower.manifest.height===224'))
    page.click('#pause');t=page.evaluate('skylineApp.tower.simulationTime');page.wait_for_timeout(300)
    check('pause freezes simulation',page.evaluate('skylineApp.tower.simulationTime')==t)
    page.click('#pause');page.wait_for_timeout(250);check('resume advances simulation',page.evaluate('skylineApp.tower.simulationTime')>t)
    page.click('#pause')
    check('all model geometry stays in the square footprint',page.evaluate('(()=>{const a=skylineApp,b=new a.THREE.Box3().setFromObject(a.tower.root);return b.min.x>=-56.001&&b.max.x<=56.001&&b.min.z>=-56.001&&b.max.z<=56.001&&b.max.y<=224})()'))
    before=page.evaluate('skylineApp.camera().position.toArray()');page.mouse.move(970,560);page.mouse.down();page.mouse.move(1090,610,steps=10);page.mouse.up();page.wait_for_timeout(600)
    check('mouse drag rotates camera',page.evaluate('skylineApp.camera().position.toArray()')!=before)
    before=page.evaluate('skylineApp.controls().target.toArray()');page.mouse.move(960,560);page.mouse.down(button='right');page.mouse.move(1030,600,steps=8);page.mouse.up(button='right');page.wait_for_timeout(500)
    check('right drag pans camera',page.evaluate('skylineApp.controls().target.toArray()')!=before)
    before=page.evaluate('skylineApp.camera().position.distanceTo(skylineApp.controls().target)');page.mouse.wheel(0,-300);page.wait_for_timeout(500)
    check('wheel zoom changes distance',page.evaluate('skylineApp.camera().position.distanceTo(skylineApp.controls().target)')<before)
    page.click('#projection');check('orthographic camera toggle',page.evaluate('skylineApp.camera().isOrthographicCamera===true'));page.click('#projection')
    for name in ['overview','low','entrance','terrace','roof','garage']:
        page.evaluate('(n)=>skylineApp.view(n,true)',name);page.wait_for_timeout(120)
        check('camera preset '+name,page.evaluate('skylineApp.camera().position.toArray().every(Number.isFinite)'))
    page.evaluate("skylineApp.select('tower')");check('component selection shows details',page.locator('#selection').is_visible() and '塔楼' in page.locator('#selection-title').inner_text());page.click('#close-selection')
    page.select_option('#quality','low');page.wait_for_timeout(250)
    check('low quality reduces geometry detail',page.evaluate("skylineApp.tower.quality==='low'&&skylineApp.tower.root.getObjectByName('plaza-person-20').visible===false"))
    page.select_option('#quality','high');page.wait_for_timeout(250)
    check('high quality restores details',page.evaluate("skylineApp.tower.quality==='high'&&skylineApp.tower.root.getObjectByName('plaza-person-20').visible"))
    page.uncheck('#traffic');check('traffic switch hides cars and people',page.evaluate("!skylineApp.tower.root.getObjectByName('plaza-person-0').visible&&!skylineApp.tower.root.getObjectByName('moving-EV').visible"));page.check('#traffic')
    page.uncheck('#wind');check('wind switch hides birds',page.evaluate("!skylineApp.tower.root.getObjectByName('bird').visible"));page.check('#wind')
    page.click('[data-time="night"]');page.wait_for_timeout(300)
    check('night lights and readable night interface',page.evaluate("document.body.classList.contains('night')&&(()=>{let lit=false;skylineApp.tower.root.traverse(o=>{if(o.material?.name==='office-lit-0'&&o.material.emissiveIntensity>.5)lit=true});return lit})()"))
    page.evaluate("skylineApp.view('overview',true)");page.wait_for_timeout(700);page.screenshot(path=str(OUT/'final-night.png'))
    page.click('[data-time="morning"]');page.wait_for_timeout(400);page.screenshot(path=str(OUT/'final-overview.png'))
    for name in ['entrance','roof','garage']:
        page.evaluate('(n)=>skylineApp.view(n,true)',name);page.wait_for_timeout(700);page.screenshot(path=str(OUT/('final-'+name+'.png')))
    result=page.evaluate('''()=>{const a=skylineApp,m=a.tower;let light=false;m.root.traverse(o=>{if(o.isCamera||o.isLight)light=true});
      const sample=SkylineModule.create({THREE:a.THREE,quality:'low',blockSize:84});const b=new a.THREE.Box3().setFromObject(sample.root);const scaled=Math.abs(b.max.x-b.min.x-84)<.01;let g=0,mt=0,tx=0;const gs=new Set(),ms=new Set(),ts=new Set();sample.root.traverse(o=>{if(!o.isMesh)return;gs.add(o.geometry);ms.add(o.material);if(o.material.map)ts.add(o.material.map)});gs.forEach(o=>o.addEventListener('dispose',()=>g++));ms.forEach(o=>o.addEventListener('dispose',()=>mt++));ts.forEach(o=>o.addEventListener('dispose',()=>tx++));sample.dispose();sample.dispose();return {pure:!light,scaled,disposed:sample.disposed&&sample.root.children.length===0&&g===gs.size&&mt===ms.size&&tx===ts.size};}''')
    check('factory creates no camera or lights',result['pure']);check('factory accepts a different block size',result['scaled']);check('dispose releases geometry material and texture resources',result['disposed'])
    # Advance a full demonstration cycle without waiting for real time.
    simulation=page.evaluate('''()=>{const a=skylineApp,m=a.tower;m.setDynamicsEnabled(true);let maxFlight=0,doors=false,gate=false,minGap=1e9;const cars=[];m.root.traverse(o=>{if(o.name==='moving-EV')cars.push(o)});for(let i=0;i<440;i++){m.update(.25);maxFlight=Math.max(maxFlight,m.root.getObjectByName('skyline-helicopter').position.y);gate=gate||m.root.getObjectByName('garage-barrier').rotation.z>.5;m.root.traverse(o=>{if(o.name==='automatic-lobby-door'&&Math.abs(o.position.x)>1.5)doors=true});for(let j=0;j<3;j++)for(let k=j+1;k<3;k++)minGap=Math.min(minGap,cars[j].position.distanceTo(cars[k].position));}m.setDynamicsEnabled(false);return {flight:maxFlight>240,doors,gate,minGap};}''')
    check('helicopter takes off and follows demonstration cycle',simulation['flight']);check('automatic lobby doors react to visitors',simulation['doors']);check('garage barrier reacts to vehicles',simulation['gate']);check('circulating cars keep a following gap',simulation['minGap']>5)
    page.uncheck('#flight');page.evaluate('skylineApp.tower.update(0)');check('flight can be disabled and parked',page.evaluate("skylineApp.tower.root.getObjectByName('skyline-helicopter').position.y===219"));page.check('#flight')
    data=page.evaluate('skylineApp.exportScene()');check('snapshot export includes geometry and entry metadata',len(data['objects'])>1000 and len(data['manifest']['entrances'])==3 and data['snapshotSpace']=='world')
    check('snapshot transforms contain finite numbers',all(math.isfinite(v) for o in data['objects'] for v in o['matrix']))
    with page.expect_download(timeout=120000) as d:page.click('#export-glb')
    d.value.save_as(ROOT/'skyline-one.glb');raw=(ROOT/'skyline-one.glb').read_bytes();check('GLB export produces a valid binary container',raw[:4]==b'glTF' and len(raw)>500000)
    length,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+length]);binary=raw[28+length:];finite=True
    components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    for ac in doc.get('accessors',[]):
        if ac['componentType']!=5126 or 'bufferView' not in ac:continue
        bv=doc['bufferViews'][ac['bufferView']];n=components[ac['type']];stride=bv.get('byteStride',n*4);offset=bv.get('byteOffset',0)+ac.get('byteOffset',0)
        for i in range(ac['count']):
            if not all(math.isfinite(v) for v in struct.unpack_from('<'+'f'*n,binary,offset+i*stride)):finite=False;break
    check('GLB accessors contain no NaN or infinity',finite)
    page.evaluate("skylineApp.view('overview',true)")
    with page.expect_download(timeout=20000) as d:page.click('#capture')
    d.value.save_as(OUT/'exported-screenshot.png');check('PNG capture exports a real image',(OUT/'exported-screenshot.png').read_bytes()[:8]==b'\x89PNG\r\n\x1a\n')
    mobile=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True);mobile.set_offline(True);mp=mobile.new_page();mp.on('pageerror',lambda e:errors.append(str(e)))
    mp.goto((ROOT/'云际中心.html').as_uri());mp.wait_for_function('skylineApp?.ready');mp.wait_for_timeout(1200);mp.screenshot(path=str(OUT/'final-mobile.png'))
    check('mobile viewport has no horizontal overflow',mp.evaluate('document.documentElement.scrollWidth===innerWidth&&document.querySelector("canvas").clientWidth===390'))
    check('mobile controls start collapsed and expand',mp.locator('#panel-body').is_hidden());mp.click('#collapse');check('mobile panel expands on tap',mp.locator('#panel-body').is_visible());mobile.close()
    check('no browser or WebGL errors',not errors)
    report={'checks':checks,'errors':errors,'simulation':simulation,'metrics':page.evaluate('skylineApp.metrics()'),'browser':browser.version}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');browser.close()
    if not all(c['passed'] for c in checks):raise SystemExit('Verification failed')
