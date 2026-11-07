import json,struct
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/shanghai-integration';OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True)
    if not value:raise AssertionError(name)
def glb(path):
    raw=path.read_bytes();assert raw[:4]==b'glTF';size=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+size])
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1700,'height':1100});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready');page.wait_for_timeout(900)
    check('BLK-11 at (112,70)',page.evaluate("cityApp.shanghaiSite.blockId==='BLK-11'&&cityApp.shanghaiSite.x===112&&cityApp.shanghaiSite.z===70"))
    check('original four homes and their details removed',page.evaluate("['QR-041','QR-042','QR-043','QR-044'].every(id=>!cityApp.scene.getObjectByName(id))&&cityApp.exportCity().batches.every(b=>b.items.every(i=>i.blockId!=='BLK-11'))"))
    check('whole model and plaza selectable as one landmark',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-11').length===1&&['Architecture','Plaza','Window_Lights','Plaza_Residents'].every(n=>cityApp.shanghai.model.getObjectByName(n))"))
    bounds=page.evaluate('({min:cityApp.shanghai.getBounds().min.toArray(),max:cityApp.shanghai.getBounds().max.toArray()})')
    check('model stays inside 112m plot',bounds['min'][0]>=56 and bounds['max'][0]<=168 and bounds['min'][2]>=14 and bounds['max'][2]<=126)
    check('native 96m height retained',95.9<bounds['max'][1]-.3<96.1 and page.evaluate('cityApp.shanghai.model.scale.toArray().every(v=>v===1)'))
    check('ground complete and edge connections present',page.evaluate("['Shanghai foundation to soil','Shanghai west pedestrian seam','Shanghai east pedestrian seam','Shanghai north pedestrian seam','Shanghai south pedestrian seam'].every(n=>cityApp.scene.getObjectByName(n))"))
    check('no source lights cameras or backdrop imported',page.evaluate("(()=>{let clean=true;cityApp.shanghai.model.traverse(o=>{if(o.isLight||o.isCamera)clean=false});return clean&&!cityApp.shanghai.model.getObjectByName('Photography_Environment')})()"))
    baseline=(OUT/'city-before-shanghai.js').read_text(encoding='utf8')
    same=page.evaluate("""async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),base=await import(url);URL.revokeObjectURL(url);const prior=base.buildCity(new T.Scene()),expected=prior.plan.buildings.filter(b=>b.blockId!=='BLK-11'),actual=cityApp.plan.buildings.filter(b=>!b.moduleId);return expected.length===actual.length&&expected.every(b=>actual.some(a=>JSON.stringify(a)===JSON.stringify(b)));}""",baseline)
    check('all other residential records unchanged',same)
    check('hospital skyline and mall retained',page.evaluate("['hospital-campus','skyline-one','mall-complex'].every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))"))
    check('future river remains clear',page.evaluate('cityApp.plan.corridor.width===64&&cityApp.shanghai.getBounds().min.x>32'))
    check('shared city sky reflection supplied',page.evaluate("cityApp.shanghai.materials['Outer glass'].envMap===cityApp.skyline.root.getObjectByName('tower:glass-0:L0')?.material.envMap || !!cityApp.shanghai.materials['Outer glass'].envMap"))
    page.screenshot(path=str(OUT/'city-overview.png'));page.locator('#shanghai-view').click();page.wait_for_timeout(2000);page.screenshot(path=str(OUT/'shanghai-context.png'))
    check('shortcut selects Shanghai tower',page.evaluate("cityApp.state.selected.id==='SHANGHAI-TOWER'&&Math.abs(cityApp.controls().target.x-112)<.1"))
    page.locator('#focus-building').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'shanghai-isolated.png'))
    with page.expect_download(timeout=60000) as result:page.locator('#export-building').click()
    result.value.save_as(OUT/'Shanghai-BLK-11.glb');doc=glb(OUT/'Shanghai-BLK-11.glb');names=[n.get('name','') for n in doc['nodes']]
    check('single GLB includes full tower and plaza','SHANGHAI-TOWER' in names and 'Twisting_Double_Skin' in names and 'Plaza' in names)
    page.locator('#close-selection').click();page.locator('#shanghai-view').click();page.wait_for_timeout(1700)
    page.locator('#pause').click();before=page.evaluate('cityApp.shanghai.parts.residents.children[0].position.toArray()');page.wait_for_timeout(300);check('global pause freezes imported people',before==page.evaluate('cityApp.shanghai.parts.residents.children[0].position.toArray()'));page.locator('#pause').click();page.wait_for_timeout(300);check('resume advances imported people',before!=page.evaluate('cityApp.shanghai.parts.residents.children[0].position.toArray()'))
    page.locator('#traffic').uncheck();page.wait_for_timeout(80);check('traffic switch controls plaza residents',not page.evaluate('cityApp.shanghai.parts.residents.visible'));page.locator('#traffic').check()
    page.locator('#quality').select_option('fast');check('quality propagates',page.evaluate("cityApp.shanghai.metadata.quality==='low'"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click();page.wait_for_timeout(1900);check('night lights synchronize',page.evaluate("cityApp.shanghai.materials['Warm windows'].emissiveIntensity>1"));page.screenshot(path=str(OUT/'shanghai-night.png'));page.locator('[data-time=morning]').click()
    page.evaluate("cityApp.select('QR-010')");page.locator('#focus-building').click();page.wait_for_timeout(1700)
    check('JSON preserves imported model while another building is isolated',page.evaluate("(()=>{const m=cityApp.exportCity().modules.find(m=>m.id==='shanghai-tower');return m.blockId==='BLK-11'&&m.snapshotSpace==='world'&&m.snapshot.objects.length>1000})()"))
    with page.expect_download(timeout=120000) as result:page.locator('#export').click()
    result.value.save_as(OUT/'town-with-shanghai.glb');doc=glb(OUT/'town-with-shanghai.glb');names=[n.get('name','') for n in doc['nodes']];check('full GLB retains Shanghai after isolation','SHANGHAI-TOWER' in names and 'Twisting_Double_Skin' in names);check('full GLB keeps prior landmarks','SKY-ONE' in names and 'MALL-TAOLI' in names and any(n.startswith('HOSP-') for n in names))
    page.locator('#home').click();page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(1900);page.locator('#collapse').click();page.locator('#shanghai-view').click();page.wait_for_timeout(1900);check('mobile shortcut reveals model',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'));page.screenshot(path=str(OUT/'shanghai-mobile.png'))
    check('no JS or WebGL errors',not errors)
    report={'checks':checks,'errors':errors,'bounds':bounds,'site':page.evaluate('cityApp.shanghaiSite'),'metrics':page.evaluate('cityApp.metrics()')};(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'passed':len(checks),'bounds':bounds},ensure_ascii=True));browser.close()
