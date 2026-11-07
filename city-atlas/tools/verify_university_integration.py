import json,struct
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/university-integration';OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
def check(name,value):
    print(('PASS ' if value else 'FAIL ')+name,flush=True);checks.append({'check':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def names(path):
    raw=path.read_bytes();assert raw[:4]==b'glTF';size=struct.unpack_from('<I',raw,12)[0];return [n.get('name','') for n in json.loads(raw[20:20+size])['nodes']]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True)
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready');page.wait_for_timeout(800)
    check('BLK-8 position and refined model version',page.evaluate("cityApp.universitySite.blockId==='BLK-8'&&cityApp.universitySite.x===-252&&cityApp.universitySite.z===210&&cityApp.university.metadata.version==='1.1.0'"))
    check('Four original homes and details removed',page.evaluate("['QR-029','QR-030','QR-031','QR-032'].every(id=>!cityApp.scene.getObjectByName(id))&&cityApp.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-8'))"))
    bounds=page.evaluate('({min:cityApp.university.getBounds().min.toArray(),max:cityApp.university.getBounds().max.toArray()})')
    check('Full model stays inside reserved square',bounds['min'][0]>=-308 and bounds['max'][0]<=-196 and bounds['min'][2]>=154 and bounds['max'][2]<=266)
    check('Full campus scale and eleven flags preserved',page.evaluate('cityApp.university.model.scale.toArray().every(v=>v===1)&&cityApp.university.flags.length===11') and abs(bounds['max'][1]-28.8525)<.01)
    check('Pavement joins match city grade',page.evaluate("['University foundation to soil','University west pedestrian seam','University east pedestrian seam','University north pedestrian seam','University south pedestrian seam'].every(n=>cityApp.scene.getObjectByName(n))"))
    check('One selectable campus and no source camera',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-8').length===1&&(()=>{let clean=true;cityApp.university.model.traverse(o=>{if(o.isCamera)clean=false});return clean})()"))
    baseline=(OUT/'city-before-university.js').read_text(encoding='utf8')
    check('All other homes unchanged',page.evaluate("""async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),base=await import(url);URL.revokeObjectURL(url);const prior=base.buildCity(new T.Scene()),custom=new Set(cityApp.plan.buildings.filter(b=>b.moduleId).map(b=>b.blockId)),expected=prior.plan.buildings.filter(b=>!custom.has(b.blockId)),actual=cityApp.plan.buildings.filter(b=>!b.moduleId);return expected.length===actual.length&&expected.every(b=>actual.some(a=>JSON.stringify(a)===JSON.stringify(b)));}""",baseline))
    check('All prior landmarks retained',page.evaluate("['hospital-campus','skyline-one','mall-complex','shanghai-tower'].every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))"))
    check('River reservation unchanged',page.evaluate('cityApp.plan.corridor.width===64&&cityApp.university.getBounds().max.x<-32'))
    check('City sky reflection assigned to campus glass',page.evaluate("!!cityApp.university.materials['Blue grey glazing'].envMap"))
    page.screenshot(path=str(OUT/'city-overview.png'));page.locator('#university-view').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'campus-context.png'))
    check('Campus shortcut selects correct plot',page.evaluate("cityApp.state.selected.id==='UNIVERSITY-CAMPUS'&&Math.abs(cityApp.controls().target.x+252)<.1"))
    page.locator('#focus-building').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'campus-isolated.png'))
    with page.expect_download(timeout=60000) as task:page.locator('#export-building').click()
    task.value.save_as(OUT/'University-BLK-8.glb');n=names(OUT/'University-BLK-8.glb');check('Single GLB includes full building plaza and flag','UNIVERSITY-CAMPUS' in n and 'Five_star_national_flag' in n and 'landscape' in n)
    page.locator('#close-selection').click();page.locator('#university-view').click();page.wait_for_timeout(1600)
    page.locator('#pause').click();page.wait_for_timeout(100);before=page.evaluate('Array.from(cityApp.university.flags[0].geometry.attributes.position.array)');page.wait_for_timeout(300);check('Global pause freezes flags',before==page.evaluate('Array.from(cityApp.university.flags[0].geometry.attributes.position.array)'));page.locator('#pause').click();page.wait_for_timeout(300);check('Global resume restarts flags',before!=page.evaluate('Array.from(cityApp.university.flags[0].geometry.attributes.position.array)'))
    page.locator('#wind').uncheck();page.wait_for_timeout(100);before=page.evaluate('Array.from(cityApp.university.flags[0].geometry.attributes.position.array)');page.wait_for_timeout(300);check('Wind switch freezes campus cloth',before==page.evaluate('Array.from(cityApp.university.flags[0].geometry.attributes.position.array)'));page.locator('#wind').check()
    page.locator('#quality').select_option('fast');check('Quality switch controls campus',page.evaluate("cityApp.university.quality==='low'"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click();page.wait_for_timeout(1900);check('Classroom and plaza lights follow city night',page.evaluate("cityApp.university.materials['Warm architectural light'].emissiveIntensity>2.7&&cityApp.university.model.getObjectByName('Campus_lamppost_light').intensity>65"));page.screenshot(path=str(OUT/'campus-night.png'));page.locator('[data-time=morning]').click();page.wait_for_timeout(1700)
    page.evaluate("cityApp.select('QR-010')");page.locator('#focus-building').click();page.wait_for_timeout(1700)
    check('World JSON retains complete campus while isolated elsewhere',page.evaluate("(()=>{const m=cityApp.exportCity().modules.find(m=>m.id==='university-campus');return m.blockId==='BLK-8'&&m.snapshotSpace==='world'&&m.snapshot.objects.length>20000})()"))
    with page.expect_download(timeout=120000) as task:page.locator('#export').click()
    task.value.save_as(OUT/'Town-with-University.glb');n=names(OUT/'Town-with-University.glb');check('City GLB retains campus and all prior landmarks',all(x in n for x in ['UNIVERSITY-CAMPUS','SHANGHAI-TOWER','SKY-ONE','MALL-TAOLI']) and any(x.startswith('HOSP-') for x in n))
    page.locator('#home').click();page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(1700);
    if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
    page.locator('#university-view').click();page.wait_for_timeout(1700);check('Mobile shortcut reveals campus and fits screen',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'));page.screenshot(path=str(OUT/'campus-mobile.png'))
    check('No runtime or WebGL errors',not errors);(OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds,'metrics':page.evaluate('cityApp.metrics()')},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks),flush=True);browser.close()
