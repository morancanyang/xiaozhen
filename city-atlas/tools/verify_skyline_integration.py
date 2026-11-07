import json,struct,subprocess
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/skyline-integration';OUT.mkdir(exist_ok=True,parents=True);checks=[]
BASE='d164d00b4476eb3fdcdbc3dfe078b2f6e9fbcd33'
baseline=subprocess.check_output(['git','show',BASE+':dist/city.js'],cwd=ROOT).decode('utf8')
def check(name,value):
    checks.append({'check':name,'passed':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
    if not value:raise AssertionError(name)
def parse_glb(path):
    raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);finite=True
    for ac in doc.get('accessors',[]):
        if ac.get('componentType')!=5126 or 'bufferView' not in ac:continue
        v=doc['bufferViews'][ac['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[ac['type']];offset=28+size+v.get('byteOffset',0)+ac.get('byteOffset',0);stride=v.get('byteStride',n*4)
        arr=np.ndarray((ac['count'],n),dtype='<f4',buffer=raw,offset=offset,strides=(stride,4));finite=finite and bool(np.isfinite(arr).all())
    return raw,doc,finite
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1700,'height':1100});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('cityApp?.ready');page.wait_for_timeout(1400)
    check('marked BLK-2 west-bank parcel at (-112,-70)',page.evaluate("cityApp.skylineSite.blockId==='BLK-2'&&cityApp.skylineSite.x===-112&&cityApp.skylineSite.z===-70"))
    check('native 112m footprint and 224m height preserved',page.evaluate('cityApp.skyline.root.scale.toArray().every(x=>x===1)&&cityApp.skyline.manifest.footprint.width===112&&cityApp.skyline.manifest.height===224'))
    check('target four residences removed',page.evaluate("['QR-005','QR-006','QR-007','QR-008'].every(id=>!cityApp.scene.getObjectByName(id))"))
    check('target block contains the complete landmark as one selectable building',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-2').length===1&&cityApp.plan.buildings.find(b=>b.id==='SKY-ONE').floors===55&&['tower','podium','roof'].every(id=>cityApp.skyline.groups.get(id).parent.name==='SKY-ONE')"))
    same=page.evaluate('''async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),old=await import(url);URL.revokeObjectURL(url);const prior=old.buildCity(new T.Scene()),expected=prior.plan.buildings.filter(b=>b.blockId!=='BLK-2'),current=cityApp.plan.buildings.filter(b=>!b.moduleId);const same=expected.length===56&&current.length===56&&expected.every(b=>current.some(c=>JSON.stringify(c)===JSON.stringify(b)));const gs=new Set(),ms=new Set(),ts=new Set();prior.root.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material){ms.add(o.material);if(o.material.map)ts.add(o.material.map)}});gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());ts.forEach(t=>t.dispose());return same;}''',baseline)
    check('all other 56 homes preserve IDs positions dimensions and materials',same)
    check('existing hospital keeps its block and all four buildings',page.evaluate("cityApp.hospitalSite.x===252&&cityApp.hospitalSite.z===-210&&cityApp.plan.buildings.filter(b=>b.moduleId==='hospital-campus').length===4&&['inpatient','outpatient','emergency','medical-tech'].every(id=>cityApp.scene.getObjectByName('HOSP-'+id))"))
    check('16 blocks and 61 individually selectable buildings',page.evaluate('cityApp.plan.blocks.length===16&&cityApp.plan.buildings.length===61&&cityApp.plan.buildings.every(b=>cityApp.scene.getObjectByName(b.id))'))
    check('central 64m future-river reservation remains clear',page.evaluate('cityApp.plan.buildings.every(b=>Math.abs(b.x)-b.width/2>32)&&cityApp.skylineSite.x+56<-32'))
    check('old target landscaping and storefronts removed',page.evaluate("cityApp.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-2'))"))
    check('city base soil and asphalt leave both garage holes open',page.evaluate('''()=>{const cuts=[[210,224,-250,-230],[-159,-147,-109,-82]],batches=cityApp.exportCity().batches.filter(b=>b.owner==='world'&&['base','soil','asphalt'].includes(b.material));return batches.every(b=>b.items.every(i=>cuts.every(([a,b,c,d])=>{const [x,y,z]=i.p,[w,h,l]=i.s;return !(x-w/2<b&&x+w/2>a&&z-l/2<d&&z+l/2>c)})))}'''))
    check('three graded public vehicle and service connections',page.evaluate("['Skyline public entrance connection','Skyline vehicle entrance connection','Skyline service entrance connection'].every(n=>cityApp.skyline.root.getObjectByName(n))"))
    check('landmark reflects the existing sky through its own environment probe',page.evaluate("(()=>{let m;cityApp.skyline.root.traverse(o=>{if(o.material?.name==='glass-0')m=o.material});return !!m.envMap&&m.envMap!==cityApp.scene.environment&&cityApp.skylineReflection().updates>0})()"))
    page.screenshot(path=str(OUT/'final-city-overview.png'))
    page.evaluate('''()=>{const a=cityApp,c=a.camera(),v=a.controls();c.position.set(0,1050,470);v.target.set(0,0,0);v.update()}''');page.wait_for_timeout(300);page.screenshot(path=str(OUT/'final-marked-location.png'))
    page.locator('#skyline-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x+112)<.1&&Math.abs(cityApp.controls().target.z+73)<.1',timeout=15000);page.wait_for_timeout(100);page.screenshot(path=str(OUT/'final-skyline-context.png'))
    check('landmark shortcut targets marked block',page.evaluate('Math.abs(cityApp.controls().target.x+112)<.1&&Math.abs(cityApp.controls().target.z+73)<.1'))
    # Ray selection should resolve the reparented facade and crown to the main building ID.
    click=page.evaluate("async()=>{const T=await import('three'),v=new T.Vector3(-112,170,-76).project(cityApp.camera());return {x:(v.x*.5+.5)*innerWidth,y:(-.5*v.y+.5)*innerHeight}}")
    page.evaluate('cityApp.state.selected=null');page.mouse.click(click['x'],click['y']);check('clicking tower facade selects SKY-ONE',page.evaluate("cityApp.state.selected?.id==='SKY-ONE'"))
    page.locator('#focus-building').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'final-single-building.png'))
    check('single-building camera frames full 224m structure',page.evaluate("async()=>{const T=await import('three'),c=cityApp.camera(),a=new T.Vector3(-112,.3,-76).project(c),b=new T.Vector3(-112,224.3,-76).project(c);return Math.abs(a.y)<.98&&Math.abs(b.y)<.98}"))
    with page.expect_download(timeout=60000) as d:page.locator('#export-building').click()
    d.value.save_as(OUT/'skyline-city.glb');raw,doc,finite=parse_glb(OUT/'skyline-city.glb');names=[n.get('name') for n in doc.get('nodes',[])]
    check('single GLB includes tower podium and helipad',raw[:4]==b'glTF' and all(n in names for n in ['tower','podium','roof','skyline-helicopter']))
    check('single GLB has no invalid numeric geometry or transforms',finite)
    page.locator('#close-selection').click();page.locator('#skyline-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x+112)<.1&&Math.abs(cityApp.controls().target.z+73)<.1',timeout=15000)
    page.locator('#pause').click();t=page.evaluate('cityApp.skyline.simulationTime');hp=page.evaluate("cityApp.hospital.root.getObjectByName('ambulance').position.toArray()");page.wait_for_timeout(350)
    check('global pause freezes landmark and hospital',page.evaluate('cityApp.skyline.simulationTime')==t and page.evaluate("cityApp.hospital.root.getObjectByName('ambulance').position.toArray()")==hp)
    page.locator('#pause').click();page.wait_for_timeout(250);check('resume advances landmark animation',page.evaluate('cityApp.skyline.simulationTime')>t)
    page.locator('#traffic').uncheck();page.wait_for_timeout(80)
    check('traffic toggle controls landmark people and cars',page.evaluate("!cityApp.skyline.root.getObjectByName('moving-EV').visible&&!cityApp.skyline.root.getObjectByName('plaza-person-0').visible"));page.locator('#traffic').check()
    page.locator('#wind').uncheck();page.wait_for_timeout(80);check('natural motion toggle controls landmark birds',page.evaluate("!cityApp.skyline.root.getObjectByName('bird').visible"));page.locator('#wind').check()
    page.locator('#skyline-flight').uncheck();page.wait_for_timeout(80);check('helicopter can be parked from city controls',page.evaluate("cityApp.skyline.root.getObjectByName('skyline-helicopter').position.y===219"));page.locator('#skyline-flight').check()
    page.locator('#quality').select_option('fast');check('low quality syncs with landmark and hospital',page.evaluate("cityApp.skyline.quality==='low'&&cityApp.hospital.quality==='low'"));page.locator('#quality').select_option('cinema');page.wait_for_timeout(200);check('cinema enables full landmark details',page.evaluate("cityApp.skyline.quality==='high'"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click();page.wait_for_timeout(2100);page.screenshot(path=str(OUT/'final-night.png'))
    check('night preset lights landmark and hospital',page.evaluate("(()=>{let a,b;cityApp.skyline.root.traverse(o=>{if(o.material?.name==='office-lit-0')a=o.material});cityApp.hospital.root.traverse(o=>{if(o.material?.name==='glass-lit')b=o.material});return a.emissiveIntensity>.5&&b.emissiveIntensity>1})()"));page.locator('[data-time=morning]').click()
    page.evaluate("cityApp.select('QR-010')");page.locator('#focus-building').click();page.wait_for_timeout(1900)
    with page.expect_download(timeout=60000) as d:page.locator('#export').click()
    d.value.save_as(OUT/'town-with-skyline.glb');raw,doc,finite=parse_glb(OUT/'town-with-skyline.glb');names=[n.get('name') for n in doc.get('nodes',[])]
    check('full city GLB restores landmark after isolating another building','SKY-ONE' in names and 'skyline-helicopter' in names)
    check('full city GLB retains hospital and excludes replaced residences',all('HOSP-'+n in names for n in ['inpatient','outpatient','emergency','medical-tech']) and not any(n in names for n in ['QR-005','QR-006','QR-007','QR-008']))
    check('full city GLB contains no NaN or infinity',finite)
    check('JSON export contains both complete module snapshots while another building is isolated',page.evaluate("(()=>{const d=cityApp.exportCity();return d.modules.length===2&&d.modules.every(m=>m.snapshotSpace==='world'&&m.snapshot.objects.length>100)&&d.modules.find(m=>m.id==='skyline-one').snapshot.objects.some(o=>o.owner==='SKY-ONE')})()"))
    check('selected landmark JSON contains only its own building geometry',page.evaluate("(()=>{const d=cityApp.exportCity('SKY-ONE');return d.modules.length===1&&d.modules[0].id==='skyline-one'&&d.modules[0].snapshot.objects.length>100&&d.modules[0].snapshot.objects.every(o=>o.owner==='SKY-ONE')})()"))
    page.locator('#home').click();page.wait_for_timeout(1900);page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(300)
    check('mobile canvas has no overflow',page.evaluate('document.documentElement.scrollWidth===420'))
    page.locator('#collapse').click();page.locator('#skyline-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x+112)<.1&&Math.abs(cityApp.controls().target.z+73)<.1',timeout=15000);page.screenshot(path=str(OUT/'final-mobile.png'))
    check('mobile landmark shortcut collapses settings to reveal the model',page.locator('#panel-content').is_hidden())
    check('mobile shortcut is accessible inside the bounded settings panel',page.evaluate('document.querySelector(".control-panel").getBoundingClientRect().bottom<innerHeight-65&&Math.abs(cityApp.controls().target.x+112)<.1'))
    check('no browser or WebGL errors',not errors)
    report={'checks':checks,'errors':errors,'site':page.evaluate('cityApp.skylineSite'),'metrics':page.evaluate('cityApp.metrics()'),'browser':browser.version,'city_glb_bytes':len(raw)}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');browser.close();print(json.dumps({'passed':len(checks),'city_glb_bytes':len(raw)}))
