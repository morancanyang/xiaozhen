"""Exercise the offline deliverable and its host integration API in real Edge/WebGL."""
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
    page.goto((ROOT/'穹光体育中心.html').as_uri(),wait_until='load');page.wait_for_function('window.arenaApp?.ready',timeout=60000);page.wait_for_timeout(1200)
    check('offline HTML has no network dependencies',not any(u.startswith(('http:','https:')) for u in requests))
    check('112 metre square parcel',page.evaluate('arenaApp.arena.manifest.footprint.width===112&&arenaApp.arena.manifest.footprint.depth===112'))
    page.click('#pause');t=page.evaluate('arenaApp.arena.simulationTime');page.wait_for_timeout(200)
    check('pause freezes model simulation',page.evaluate('arenaApp.arena.simulationTime')==t)
    page.click('#pause');page.wait_for_timeout(250);check('resume advances model simulation',page.evaluate('arenaApp.arena.simulationTime')>t);page.click('#pause')
    check('all geometry inside square parcel and animated height limit',page.evaluate('(()=>{const a=arenaApp,b=new a.THREE.Box3().setFromObject(a.arena.root);return b.min.x>=-56.001&&b.max.x<=56.001&&b.min.z>=-56.001&&b.max.z<=56.001&&b.max.y<=41})()'))
    before=page.evaluate('arenaApp.camera().position.toArray()');page.mouse.move(970,560);page.mouse.down();page.mouse.move(1090,610,steps=10);page.mouse.up();page.wait_for_timeout(450)
    check('drag rotates camera',page.evaluate('arenaApp.camera().position.toArray()')!=before)
    before=page.evaluate('arenaApp.controls().target.toArray()');page.mouse.move(960,560);page.mouse.down(button='right');page.mouse.move(1030,600,steps=8);page.mouse.up(button='right');page.wait_for_timeout(450)
    check('right drag pans camera',page.evaluate('arenaApp.controls().target.toArray()')!=before)
    before=page.evaluate('arenaApp.camera().position.distanceTo(arenaApp.controls().target)');page.mouse.wheel(0,-300);page.wait_for_timeout(450)
    check('wheel zoom changes distance',page.evaluate('arenaApp.camera().position.distanceTo(arenaApp.controls().target)')<before)
    page.click('#projection');check('orthographic projection works',page.evaluate('arenaApp.camera().isOrthographicCamera===true'));page.click('#projection')
    for name in ['overview','low','entrance','structure','roof','interior']:
        page.evaluate('(n)=>arenaApp.view(n,true)',name);page.wait_for_timeout(100)
        check('view preset '+name,page.evaluate('(n)=>arenaApp.camera().position.toArray().every(Number.isFinite)&&arenaApp.arena.roofVisible===!(["structure","interior"].includes(n))',name))
    page.check('#roof-visible');check('roof switch restores shell',page.evaluate('arenaApp.arena.groups.get("roof").visible'))
    page.evaluate("arenaApp.select('structure')");check('selection shows component details',page.locator('#selection').is_visible() and '桁架' in page.locator('#selection-title').inner_text());page.click('#close-selection')
    page.select_option('#quality','low');page.wait_for_timeout(200)
    check('low quality reduces people and detail',page.evaluate('arenaApp.arena.quality==="low"&&!arenaApp.arena.root.getObjectByName("Visitor 20").visible'))
    page.select_option('#quality','high');page.wait_for_timeout(200)
    check('high quality restores people and detail',page.evaluate('arenaApp.arena.quality==="high"&&arenaApp.arena.root.getObjectByName("Visitor 20").visible'))
    page.uncheck('#traffic');check('people and traffic can be hidden',page.evaluate('!arenaApp.arena.root.getObjectByName("Visitor 0").visible&&!arenaApp.arena.root.getObjectByName("Service or dropoff EV 0").visible'));page.check('#traffic')
    page.uncheck('#wind');check('wind switch hides birds',page.evaluate('!arenaApp.arena.root.getObjectByName("Bird").visible'));page.check('#wind')
    page.click('[data-time="night"]');page.wait_for_timeout(250)
    check('night activates emissive materials and actual spot lights',page.evaluate('document.body.classList.contains("night")&&arenaApp.scene.children.filter(o=>o.isSpotLight&&o.intensity>0).length===4&&(()=>{let lit=false;arenaApp.arena.root.traverse(o=>{if(o.material?.name==="lamp"&&o.material.emissiveIntensity>1)lit=true});return lit})()'))
    page.click('[data-time="day"]')
    result=page.evaluate('''()=>{const a=arenaApp;let light=false;a.arena.root.traverse(o=>{if(o.isCamera||o.isLight)light=true});
      const m=ArenaModule.create({THREE:a.THREE,quality:'low',blockSize:84}),b=new a.THREE.Box3().setFromObject(m.root);const scaled=Math.abs(b.max.x-b.min.x-84)<.01&&Math.abs(b.max.z-b.min.z-84)<.01;
      m.root.position.set(100,2,-100);m.root.rotation.y=Math.PI/2;m.root.updateMatrixWorld(true);const entry=m.root.localToWorld(new a.THREE.Vector3(...m.manifest.entrances.public.position));const transformed=entry.distanceTo(new a.THREE.Vector3(142,2,-100))<.001;
      let g=0,mt=0,tx=0;const gs=new Set(),ms=new Set(),ts=new Set();m.root.traverse(o=>{if(!o.isMesh)return;gs.add(o.geometry);ms.add(o.material);if(o.material.map)ts.add(o.material.map)});gs.forEach(o=>o.addEventListener('dispose',()=>g++));ms.forEach(o=>o.addEventListener('dispose',()=>mt++));ts.forEach(o=>o.addEventListener('dispose',()=>tx++));m.dispose();m.dispose();return {pure:!light,scaled,transformed,disposed:m.disposed&&m.root.children.length===0&&g===gs.size&&mt===ms.size&&tx===ts.size};}''')
    check('host factory creates no cameras or lights',result['pure']);check('factory rescales to 84 metre parcel',result['scaled']);check('entry coordinates follow host scale rotation and translation',result['transformed']);check('dispose releases owned resources and is idempotent',result['disposed'])
    simulation=page.evaluate('''()=>{const a=arenaApp,m=a.arena;m.setDynamicsEnabled(true);const steps=m.root.getObjectByName('Moving escalator steps'),matrix=new a.THREE.Matrix4();steps.getMatrixAt(0,matrix);const start=matrix.toArray(),screen=m.root.getObjectByName('interior').children.find(o=>o.material?.name?.startsWith('sign:'));const version=screen.material.map.version;let doors=false,minGap=1e9,inside=true,collision=false;const cars=[0,1,2].map(i=>m.root.getObjectByName('Service or dropoff EV '+i));const overlaps=(a,b)=>{const axes=o=>[[Math.cos(o.rotation.y),-Math.sin(o.rotation.y)],[Math.sin(o.rotation.y),Math.cos(o.rotation.y)]],aa=axes(a),bb=axes(b),d=[b.position.x-a.position.x,b.position.z-a.position.z],dot=(x,y)=>x[0]*y[0]+x[1]*y[1],radius=(q,u)=>.95*Math.abs(dot(q[0],u))+2.1*Math.abs(dot(q[1],u));return [...aa,...bb].every(u=>Math.abs(dot(d,u))<radius(aa,u)+radius(bb,u));};
      for(let i=0;i<480;i++){m.update(.25);doors=doors||Math.abs(m.root.getObjectByName('Automatic door 1').position.x)>2;for(let j=0;j<3;j++){inside=inside&&Math.abs(cars[j].position.x)<50&&Math.abs(cars[j].position.z)<50;for(let k=j+1;k<3;k++){minGap=Math.min(minGap,cars[j].position.distanceTo(cars[k].position));collision=collision||overlaps(cars[j],cars[k]);}}}
      steps.getMatrixAt(0,matrix);const escalator=start.some((v,i)=>Math.abs(v-matrix.elements[i])>.001),score=screen.material.map.version>version;m.setActivity({people:false});for(let i=0;i<10;i++)m.update(.25);const closed=Math.abs(m.root.getObjectByName('Automatic door 1').position.x-.85)<.01;m.setActivity({people:true});m.setDynamicsEnabled(false);return {doors,closed,escalator,score,minGap,inside,collision};}''')
    check('automatic doors open with visitors',simulation['doors']);check('automatic doors close without visitors',simulation['closed']);check('escalator steps circulate',simulation['escalator']);check('scoreboard texture changes content',simulation['score']);check('vehicles stay inside internal lanes',simulation['inside']);check('vehicle bodies do not overlap over 120 second route cycle',not simulation['collision'])
    page.evaluate("arenaApp.view('overview',true)");data=page.evaluate('arenaApp.exportScene()')
    check('snapshot has full geometry and entry metadata',len(data['objects'])>1000 and len(data['manifest']['entrances'])==3 and data['snapshotSpace']=='world')
    check('snapshot transforms are finite',all(math.isfinite(v) for o in data['objects'] for v in o['matrix']))
    page.evaluate("arenaApp.view('interior',true)")
    with page.expect_download(timeout=120000) as d:page.click('#export-glb')
    d.value.save_as(OUT/'verified.glb');raw=(OUT/'verified.glb').read_bytes();check('GLB is valid binary',raw[:4]==b'glTF' and len(raw)>500000)
    length,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
    check('GLB includes full roof even when viewer is in cutaway',any(n.get('name','').startswith('Standing seam roof') for n in doc.get('nodes',[])))
    finite=True;components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    for ac in doc.get('accessors',[]):
        if ac['componentType']!=5126 or 'bufferView' not in ac:continue
        bv=doc['bufferViews'][ac['bufferView']];n=components[ac['type']];stride=bv.get('byteStride',n*4);offset=bv.get('byteOffset',0)+ac.get('byteOffset',0)
        for i in range(ac['count']):
            if not all(math.isfinite(v) for v in struct.unpack_from('<'+'f'*n,binary,offset+i*stride)):finite=False;break
    check('GLB float accessors have no NaN or infinity',finite)
    page.evaluate("arenaApp.view('overview',true)")
    with page.expect_download(timeout=20000) as d:page.click('#capture')
    d.value.save_as(OUT/'exported-screenshot.png');check('PNG screenshot export works',(OUT/'exported-screenshot.png').read_bytes()[:8]==b'\x89PNG\r\n\x1a\n')
    mobile=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True);mobile.set_offline(True);mp=mobile.new_page();mp.on('pageerror',lambda e:errors.append(str(e)))
    mp.goto((ROOT/'穹光体育中心.html').as_uri());mp.wait_for_function('window.arenaApp?.ready');mp.wait_for_timeout(1000);mp.screenshot(path=str(OUT/'final-mobile.png'))
    check('mobile viewport has no horizontal overflow',mp.evaluate('document.documentElement.scrollWidth===innerWidth&&document.querySelector("canvas").clientWidth===390'))
    check('mobile controls start collapsed',mp.locator('#panel-body').is_hidden());mp.click('#collapse');check('mobile controls expand on tap',mp.locator('#panel-body').is_visible());mobile.close()
    check('no browser or WebGL errors',not errors)
    report={'checks':checks,'errors':errors,'simulation':simulation,'metrics':page.evaluate('arenaApp.metrics()'),'browser':browser.version}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');browser.close()
    if not all(c['passed'] for c in checks):raise SystemExit('Verification failed')
