import json,struct
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/residential-integration';checks=[]
def check(name,v):
 checks.append({'check':name,'passed':bool(v)});print(('PASS ' if v else 'FAIL ')+name,flush=True)
 if not v:raise AssertionError(name)
def glb(path):
 raw=path.read_bytes();assert raw[:4]==b'glTF';size=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+size])
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1700,'height':1100},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',timeout=60000);page.wait_for_timeout(900)
 check('BLK-5 at (-252,-210)',page.evaluate("cityApp.residentialSite.blockId==='BLK-5'&&cityApp.residentialSite.x===-252&&cityApp.residentialSite.z===-210"))
 check('original four homes removed',page.evaluate("['QR-017','QR-018','QR-019','QR-020'].every(id=>!cityApp.scene.getObjectByName(id))"))
 check('four independently selectable new buildings',page.evaluate("cityApp.plan.buildings.filter(b=>b.blockId==='BLK-5').length===4&&['A','B','C','D'].every(id=>cityApp.scene.getObjectByName('LINXU-'+id))"))
 baseline=(OUT/'city-before-residential.js').read_text(encoding='utf8')
 same=page.evaluate("""async source=>{const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),m=await import(url);URL.revokeObjectURL(url);const expected=m.buildCity(new T.Scene()).plan.buildings.filter(b=>b.blockId!=='BLK-5'),actual=cityApp.plan.buildings.filter(b=>!b.moduleId);return expected.length===actual.length&&expected.every(b=>actual.some(a=>JSON.stringify(a)===JSON.stringify(b)))}""",baseline)
 check('other residential records unchanged',same)
 check('prior landmarks and river retained',page.evaluate("['hospital-campus','skyline-one','mall-complex','shanghai-tower','university-campus','dome-arena','amusement-park'].every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))&&cityApp.river.manifest.id==='qinglan-river'"))
 data=page.evaluate('cityApp.exportCity()');check('old site furniture removed from batches',all(i.get('blockId')!='BLK-5' for bucket in data['batches'] for i in bucket['items']))
 mod=next(m for m in data['modules'] if m['id']=='linxu-residential');check('JSON includes complete residential module',mod['blockId']=='BLK-5' and mod['snapshotSpace']=='world' and len(mod['snapshot']['objects'])>1000)
 bounds=page.evaluate("async()=>{const T=await import('three'),box=new T.Box3();for(const g of cityApp.residential.root.children)if(g.name!=='Linxu road connections')box.expandByObject(g);return{min:box.min.toArray(),max:box.max.toArray()}}")
 check('model stays in square plot',bounds['min'][0]>=-308.001 and bounds['max'][0]<=-195.999 and bounds['min'][2]>=-266.001 and bounds['max'][2]<=-153.999)
 check('three approaches connect town roads',page.evaluate("['Linxu pedestrian entrance','Linxu vehicle entrance','Linxu service entrance'].every(n=>cityApp.residential.root.getObjectByName(n))"))
 page.screenshot(path=str(OUT/'city-overview.png'));page.locator('#residential-view').click();page.wait_for_timeout(2100);check('shortcut frames complete BLK-5',page.evaluate('Math.abs(cityApp.controls().target.x+252)<.1&&Math.abs(cityApp.controls().target.z+210)<.1'));page.screenshot(path=str(OUT/'residential-context.png'))
 for id in ['A','B','C','D']:
  page.evaluate('(id)=>cityApp.select("LINXU-"+id)',id);check('building '+id+' is selectable',page.evaluate('(id)=>cityApp.state.selected.id==="LINXU-"+id',id))
 page.locator('#focus-building').click();page.wait_for_timeout(1900);page.screenshot(path=str(OUT/'building-D.png'))
 with page.expect_download(timeout=120000) as dl:page.locator('#export-building').click()
 dl.value.save_as(OUT/'LINXU-D.glb');doc=glb(OUT/'LINXU-D.glb');names=[n.get('name','') for n in doc['nodes']];check('single GLB contains only selected residential building','LINXU-D' in names and 'LINXU-A' not in names and 'LINXU-B' not in names)
 snap=page.evaluate("(()=>{const m=cityApp.exportCity('LINXU-D').modules.find(m=>m.id==='linxu-residential');return[...new Set(m.snapshot.objects.map(o=>o.owner))]})()");check('single JSON filters building ownership',snap==['LINXU-D'])
 page.locator('#residential-view').click();page.wait_for_timeout(1800);page.locator('#pause').click();t=page.evaluate('cityApp.residential.simulationTime');page.wait_for_timeout(250);check('pause freezes residential animation',t==page.evaluate('cityApp.residential.simulationTime'));page.locator('#pause').click();page.wait_for_timeout(250);check('resume advances residential animation',t<page.evaluate('cityApp.residential.simulationTime'))
 page.locator('#traffic').uncheck();page.wait_for_timeout(120);check('traffic switch controls residents and cars',page.evaluate("!cityApp.residential.root.getObjectByName('Resident 0').visible&&!cityApp.residential.root.getObjectByName('Moving EV 0').visible"));page.locator('#traffic').check()
 page.locator('#quality').select_option('fast');check('low quality propagates',page.evaluate("cityApp.residential.quality==='low'"));page.locator('#quality').select_option('balanced')
 page.locator('[data-time=night]').click();page.wait_for_timeout(1800);check('night lights synchronize',page.evaluate("(()=>{let lit=false;cityApp.residential.root.traverse(o=>{if(o.material?.name==='window-lit'&&o.material.emissiveIntensity>1)lit=true});return lit})()"));page.screenshot(path=str(OUT/'residential-night.png'));page.locator('[data-time=morning]').click();page.wait_for_timeout(1700)
 page.evaluate("cityApp.select('SKY-ONE')");page.locator('#focus-building').click();page.wait_for_timeout(1800)
 with page.expect_download(timeout=180000) as dl:page.locator('#export').click()
 dl.value.save_as(OUT/'town-with-residential.glb');doc=glb(OUT/'town-with-residential.glb');names=[n.get('name','') for n in doc['nodes']];check('full GLB retains four homes and prior landmarks',all(n in names for n in ['LINXU-A','LINXU-B','LINXU-C','LINXU-D','SKY-ONE','ARENA-DOME','RIVER-QINGLAN','SKYDAY-PARK']))
 page.locator('#home').click();page.wait_for_timeout(1700);page.locator('[data-view=free]').click();page.wait_for_timeout(150);check('free view still works',page.evaluate('cityApp.state.freeView'));page.keyboard.press('Escape');page.wait_for_timeout(150)
 page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(250)
 if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
 page.locator('#residential-view').click();page.wait_for_timeout(1900);check('mobile shortcut works without overflow',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'));page.screenshot(path=str(OUT/'residential-mobile.png'))
 check('no JavaScript or WebGL errors',not errors);(OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds,'metrics':page.evaluate('cityApp.metrics()')},indent=2),encoding='utf8');print(json.dumps({'passed':len(checks)}));b.close()
