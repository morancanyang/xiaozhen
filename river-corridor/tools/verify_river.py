import json,math,struct
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';checks=[];errors=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
def read_glb(path):
    raw=path.read_bytes();assert raw[:4]==b'glTF';n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);ctx=browser.new_context(viewport={'width':1600,'height':1050},device_scale_factor=1,accept_downloads=True);ctx.set_offline(True);page=ctx.new_page();requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url))
    page.goto((ROOT/'青岚河.html').as_uri());page.wait_for_function('window.riverApp?.ready',timeout=60000);page.wait_for_timeout(1400)
    check('single HTML operates offline',not any(u.startswith(('http:','https:')) for u in requests))
    bounds=page.evaluate('(()=>{const a=riverApp,b=new a.THREE.Box3().setFromObject(a.river.root);return {min:b.min.toArray(),max:b.max.toArray()}})()')
    check('all geometry lies inside 64 x 600 metre corridor',bounds['min'][0]>=-32.001 and bounds['max'][0]<=32.001 and bounds['min'][2]>=-300.001 and bounds['max'][2]<=300.001)
    check('river has real below-grade bed and water surface',page.evaluate('riverApp.river.terrainHeight(0,0)<-2&&riverApp.river.manifest.waterLevel===-.75'))
    page.click('#pause');t=page.evaluate('riverApp.river.simulationTime');page.wait_for_timeout(250);check('pause freezes simulation',page.evaluate('riverApp.river.simulationTime')==t);page.click('#pause');page.wait_for_timeout(250);check('resume advances simulation',page.evaluate('riverApp.river.simulationTime')>t);page.click('#pause')
    start=page.evaluate('riverApp.camera.position.toArray()');page.mouse.move(900,500);page.mouse.down();page.mouse.move(1040,540,steps=10);page.mouse.up();page.wait_for_timeout(300);check('drag rotates camera',start!=page.evaluate('riverApp.camera.position.toArray()'))
    start=page.evaluate('riverApp.controls.target.toArray()');page.mouse.move(900,500);page.mouse.down(button='right');page.mouse.move(950,540,steps=6);page.mouse.up(button='right');page.wait_for_timeout(300);check('right drag pans camera',start!=page.evaluate('riverApp.controls.target.toArray()'))
    start=page.evaluate('riverApp.camera.position.distanceTo(riverApp.controls.target)');page.mouse.wheel(0,-250);page.wait_for_timeout(300);check('wheel zoom changes distance',page.evaluate('riverApp.camera.position.distanceTo(riverApp.controls.target)')<start)
    for view in ['overview','bend','bank','fish','length']:
        page.evaluate('(name)=>riverApp.view(name)',view);page.wait_for_timeout(120);check('finite camera preset '+view,page.evaluate('riverApp.camera.position.toArray().every(Number.isFinite)'))
    check('reflection and refraction render targets update',page.evaluate('riverApp.pass.metrics.updates>2&&riverApp.river.waterUniforms.uHasBuffers.value===1'))
    check('water has depth sampling and projection data',page.evaluate('!!riverApp.river.waterUniforms.uDepth.value&&riverApp.river.waterUniforms.uRefractionMatrix.value.elements.every(Number.isFinite)'))
    page.uncheck('#fish');check('fish switch hides school',not page.evaluate('riverApp.river.groups.get("fish").visible'));page.check('#fish')
    simulation=page.evaluate('''()=>{const a=riverApp,r=a.river;r.setDynamicsEnabled(true);r.setFlowSpeed(0);const wt=r.waterTime;const body=r.root.getObjectByName('Schooling fish bodies'),mx=new a.THREE.Matrix4();body.getMatrixAt(0,mx);const old=mx.elements.slice(12,15);let safe=true;for(let step=0;step<480;step++){r.update(.25);for(let i=0;i<body.count;i++){body.getMatrixAt(i,mx);const x=mx.elements[12],y=mx.elements[13],z=mx.elements[14];safe=safe&&Math.abs(x-r.center(z))<r.halfWidth(z)-1&&y<-.95&&y>r.terrainHeight(x,z)+.12&&Math.abs(z)<300;}}body.getMatrixAt(0,mx);const moved=old.some((v,i)=>Math.abs(v-mx.elements[12+i])>.01),flowStopped=r.waterTime===wt;r.setFlowSpeed(2);r.update(.1);const flowFast=Math.abs(r.waterTime-wt-.2)<.001;r.setWindEnabled(false);const wind=r.windTime;r.update(.1);const windStopped=r.windTime===wind;r.setWindEnabled(true);r.setFlowSpeed(1);r.setDynamicsEnabled(false);return{safe,moved,flowStopped,flowFast,windStopped};}''')
    for name,key in [('fish remain below water and above riverbed for 120 seconds','safe'),('fish school changes position','moved'),('zero flow speed stops water clock','flowStopped'),('two-times flow speed propagates','flowFast'),('wind can stop independently of fish','windStopped')]:check(name,simulation[key])
    page.select_option('#quality','low');page.wait_for_timeout(150);check('low quality reduces visible instance count',page.evaluate('riverApp.river.root.getObjectByName("meadow").count<4000&&riverApp.river.root.getObjectByName("Schooling fish bodies").count===36'))
    page.select_option('#quality','high');check('high quality restores all fish',page.evaluate('riverApp.river.root.getObjectByName("Schooling fish bodies").count===72'))
    page.click('#night');page.wait_for_timeout(150);check('night shading switches',page.evaluate('riverApp.river.waterUniforms.uNight.value===1'));page.click('#night')
    result=page.evaluate('''()=>{const a=riverApp,m=RiverModule.create({THREE:a.THREE,coarse:true,quality:'low'}),pass=RiverModule.createPass({THREE:a.THREE,river:m});let camera=false;m.root.traverse(o=>{if(o.isCamera||o.isLight)camera=true});const gs=new Set(),ms=new Set(),ts=new Set();let gd=0,md=0,td=0;m.root.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material)ms.add(o.material);if(o.material?.map)ts.add(o.material.map)});gs.forEach(g=>g.addEventListener('dispose',()=>gd++));ms.forEach(m=>m.addEventListener('dispose',()=>md++));ts.forEach(t=>t.addEventListener('dispose',()=>td++));pass.dispose();pass.dispose();m.dispose();m.dispose();return{pure:!camera,disposed:m.disposed&&m.root.children.length===0&&gd===gs.size&&md===ms.size&&td===ts.size,passDisposed:pass.disposed};}''')
    check('model factory owns no camera or lights',result['pure']);check('model disposal releases resources',result['disposed']);check('render pass disposal is idempotent',result['passDisposed'])
    with page.expect_download(timeout=120000) as result:page.click('#export')
    result.value.save_as(OUT/'verified-river.glb');doc,binary=read_glb(OUT/'verified-river.glb');check('static GLB includes water and fish',all(n in [x.get('name') for x in doc['nodes']] for n in ['Dynamic river surface','Schooling fish bodies']))
    check('GLB uses physical water material',any(m.get('name')=='River water static PBR' for m in doc['materials']))
    finite=True;components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    for ac in doc.get('accessors',[]):
        if ac['componentType']!=5126 or 'bufferView' not in ac:continue
        b=doc['bufferViews'][ac['bufferView']];n=components[ac['type']];offset=b.get('byteOffset',0)+ac.get('byteOffset',0);stride=b.get('byteStride',n*4)
        for i in range(ac['count']):
            if not all(math.isfinite(v) for v in struct.unpack_from('<'+'f'*n,binary,offset+i*stride)):finite=False;break
    check('GLB float data is finite',finite)
    mobile=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True);mobile.set_offline(True);mp=mobile.new_page();mp.on('pageerror',lambda e:errors.append(str(e)));mp.goto((ROOT/'青岚河.html').as_uri());mp.wait_for_function('window.riverApp?.ready');mp.wait_for_timeout(700);check('mobile layout fits viewport',mp.evaluate('document.documentElement.scrollWidth===innerWidth'));check('mobile panel starts collapsed',mp.locator('#panel-body').is_hidden());mp.click('#collapse');check('mobile panel expands',mp.locator('#panel-body').is_visible());mp.screenshot(path=str(OUT/'final-mobile.png'));mobile.close()
    check('no browser or WebGL errors',not errors);(OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'simulation':simulation,'bounds':bounds,'metrics':page.evaluate('riverApp.metrics()')},indent=2),encoding='utf8');browser.close()
    if not all(c['passed'] for c in checks):raise SystemExit('River verification failed')
