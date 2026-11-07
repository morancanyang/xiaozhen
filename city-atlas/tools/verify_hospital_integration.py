import json,struct,subprocess
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/hospital-integration';OUT.mkdir(exist_ok=True);checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
baseline=subprocess.check_output(['git','show','b97615338c780a7f6a8291d0ab94fd1c6d8687b6:dist/city.js'],cwd=ROOT).decode('utf-8')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1600,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('cityApp?.ready');page.wait_for_timeout(1300)
    check('hospital installed in red-circled BLK-13 at (252,-210)',page.evaluate("cityApp.hospitalSite.blockId==='BLK-13'&&cityApp.hospitalSite.x===252&&cityApp.hospitalSite.z===-210"))
    check('hospital keeps original meter scale',page.evaluate('cityApp.hospital.root.scale.toArray().every(v=>v===1)&&cityApp.hospital.manifest.footprint.width===112'))
    check('only four hospital buildings replace the selected block',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-13').length===4&&cityApp.plan.buildings.filter(b=>b.blockId==='BLK-13').every(b=>b.moduleId==='hospital-campus')"))
    check('original QR-049 to QR-052 removed',page.evaluate("['QR-049','QR-050','QR-051','QR-052'].every(id=>!cityApp.scene.getObjectByName(id))"))
    unchanged=page.evaluate('''async source=>{const url=URL.createObjectURL(new Blob([source],{type:'text/javascript'}));const baseline=await import(url);URL.revokeObjectURL(url);const T=await import('three'),old=baseline.buildCity(new T.Scene()),strip=b=>JSON.stringify(b);const expected=old.plan.buildings.filter(b=>!['BLK-13','BLK-2'].includes(b.blockId));const current=cityApp.plan.buildings.filter(b=>!['BLK-13','BLK-2'].includes(b.blockId));const same=expected.length===56&&expected.every(b=>current.some(c=>c.id===b.id&&strip(c)===strip(b)));const geos=new Set(),mats=new Set(),textures=new Set();old.root.traverse(o=>{if(o.geometry)geos.add(o.geometry);if(o.material){mats.add(o.material);if(o.material.map)textures.add(o.material.map);}});geos.forEach(g=>g.dispose());mats.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());return same;}''',baseline)
    check('all other 56 residential buildings preserve original IDs, dimensions and positions',unchanged)
    check('city still has 16 blocks and 61 independently selectable buildings',page.evaluate('cityApp.plan.blocks.length===16&&cityApp.plan.buildings.length===61&&cityApp.plan.buildings.every(b=>cityApp.scene.getObjectByName(b.id))'))
    check('central future-river corridor remains empty',page.evaluate('cityApp.plan.buildings.every(b=>Math.abs(b.x)-b.width/2>32)'))
    check('no old target landscaping remains in batch export',page.evaluate("cityApp.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-13'))"))
    # Inspect exported ground rectangles, excluding the hospital snapshot, at the actual garage opening.
    check('base, soil and asphalt cut through the garage rectangle',page.evaluate('''()=>{let batches=cityApp.exportCity().batches.filter(b=>b.owner==='world'&&['base','soil','asphalt'].includes(b.material));return batches.every(b=>b.items.every(i=>{let [x,y,z]=i.p,[w,h,d]=i.s;return !(x-w/2<224&&x+w/2>210&&z-d/2<-230&&z+d/2>-250);}));}'''))
    check('three graded access connectors created',page.evaluate("['Public entrance graded connection','Emergency entrance graded connection','Service entrance graded connection'].every(n=>cityApp.hospital.root.getObjectByName(n))"))
    page.locator('#hospital-view').click();page.wait_for_timeout(2300);page.screenshot(path=str(OUT/'hospital-final.png'));check('hospital shortcut focuses correct neighborhood',page.evaluate('Math.abs(cityApp.controls().target.x-252)<.1&&Math.abs(cityApp.controls().target.z+210)<.1'))
    page.evaluate("cityApp.select('HOSP-emergency')");check('hospital building selection',page.locator('#building-name').inner_text()=='澄和医院 · 急诊中心')
    with page.expect_download(timeout=60000) as d:page.locator('#export-building').click()
    d.value.save_as(OUT/'hospital-emergency-city.glb');check('hospital single-building GLB export',(OUT/'hospital-emergency-city.glb').read_bytes()[:4]==b'glTF');page.locator('#close-selection').click()
    page.locator('#pause').click();pos=page.evaluate("cityApp.hospital.root.getObjectByName('ambulance').position.toArray()");page.wait_for_timeout(450);check('host pause freezes hospital traffic',pos==page.evaluate("cityApp.hospital.root.getObjectByName('ambulance').position.toArray()"));page.locator('#pause').click();page.wait_for_timeout(300);check('hospital traffic resumes',pos!=page.evaluate("cityApp.hospital.root.getObjectByName('ambulance').position.toArray()"))
    page.locator('#traffic').uncheck();page.wait_for_timeout(80);check('host traffic toggle hides hospital actors',page.evaluate("!cityApp.hospital.root.getObjectByName('ambulance').visible"));page.locator('#traffic').check()
    page.locator('#wind').uncheck();page.wait_for_timeout(80);check('host wind toggle applies to hospital birds',page.evaluate("cityApp.hospital.root.getObjectByName('Hospital local life').children.filter(o=>o.isMesh).every(o=>!o.visible)"));page.locator('#wind').check()
    page.locator('#quality').select_option('fast');check('host low quality controls hospital detail',page.evaluate("cityApp.hospital.quality==='low'"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click();page.wait_for_timeout(1800);check('host night mode controls hospital window emission',page.evaluate("(()=>{let m;cityApp.hospital.root.traverse(o=>{if(o.material?.name==='glass-lit')m=o.material;});return m.emissiveIntensity>1})()"));page.screenshot(path=str(OUT/'hospital-night.png'));page.locator('[data-time=morning]').click()
    # Also verify that hospital geometry is exported after a single residential building has been isolated.
    page.evaluate("cityApp.select('QR-010')");page.locator('#focus-building').click();page.wait_for_timeout(1800)
    with page.expect_download(timeout=60000) as d:page.locator('#export').click()
    d.value.save_as(OUT/'town-with-hospital.glb');binary=(OUT/'town-with-hospital.glb').read_bytes();length=struct.unpack_from('<I',binary,12)[0];gltf=json.loads(binary[20:20+length]);nodes=gltf.get('nodes',[])
    check('whole-city GLB contains all four hospital buildings',all(any(n.get('name')=='HOSP-'+s for n in nodes) for s in ['inpatient','outpatient','emergency','medical-tech']))
    check('whole-city GLB contains no replaced residential towers',not any(n.get('name') in ['QR-049','QR-050','QR-051','QR-052'] for n in nodes))
    finite=True;bin_offset=28+length
    for accessor in gltf.get('accessors',[]):
        if accessor.get('componentType')!=5126 or 'bufferView' not in accessor:continue
        view=gltf['bufferViews'][accessor['bufferView']];components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[accessor['type']];offset=bin_offset+view.get('byteOffset',0)+accessor.get('byteOffset',0);stride=view.get('byteStride',components*4);array=np.ndarray((accessor['count'],components),dtype='<f4',buffer=binary,offset=offset,strides=(stride,4));finite=finite and bool(np.isfinite(array).all())
    check('GLB numeric transforms and geometry contain no NaN',finite)
    check('JSON scene export includes hospital snapshot',page.evaluate("cityApp.exportCity().modules[0].snapshot.objects.length>100&&cityApp.exportCity().modules[0].snapshotSpace==='world'"))
    page.locator('#home').click();page.wait_for_timeout(2000);page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(300);page.screenshot(path=str(OUT/'mobile.png'));check('mobile layout retains canvas width',page.evaluate('document.documentElement.scrollWidth===420'))
    check('no browser or WebGL errors',not errors)
    report={'checks':checks,'errors':errors,'metrics':page.evaluate('cityApp.metrics()'),'browser':browser.version,'glb_bytes':len(binary)};(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True));browser.close()
