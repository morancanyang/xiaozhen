import json,struct
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';checks=[];errors=[];requests=[]
def check(name,ok):
 print(('PASS ' if ok else 'FAIL ')+name,flush=True);checks.append({'check':name,'passed':bool(ok)});assert ok,name
with sync_playwright() as p:
 browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True);page.set_default_timeout(60000)
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
 page.goto((ROOT/'棕屿里.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.mixedApp?.ready');page.wait_for_timeout(700)
 check('Offline without external requests',not requests)
 check('Default orthographic camera has finite real position',page.evaluate('mixedApp.camera.isOrthographicCamera&&mixedApp.camera.position.toArray().every(Number.isFinite)'))
 bounds=page.evaluate('({min:mixedApp.model.getBounds().min.toArray(),max:mixedApp.model.getBounds().max.toArray()})');check('112 metre plot bounds',bounds['min'][0]>=-56.001 and bounds['max'][0]<=56.001 and bounds['min'][2]>=-56.001 and bounds['max'][2]<=56.001)
 check('22 residential floors and six independent shops',page.evaluate('mixedApp.model.metadata.residentialFloors===22&&mixedApp.model.metadata.shops.length===6&&mixedApp.model.doors.length===6'))
 geometry=page.evaluate('''()=>{let invalid=0,badNormals=0;const s=new Set();mixedApp.model.root.traverse(o=>{if(!o.isMesh||s.has(o.geometry))return;s.add(o.geometry);const g=o.geometry;invalid+=Array.from(g.attributes.position.array).filter(x=>!Number.isFinite(x)).length;for(let i=0;i<g.attributes.normal.count;i++){const n=new mixedApp.THREE.Vector3().fromBufferAttribute(g.attributes.normal,i);if(Math.abs(n.length()-1)>.01)badNormals++;}});return{invalid,badNormals};}''')
 check('Finite geometry and normalized normals',geometry['invalid']==0 and geometry['badNormals']==0)
 check('Bay projections and enclosed balconies are real geometry',page.evaluate("mixedApp.model.groups.get('balconies').children.some(o=>o.isInstancedMesh&&o.count>100)"))
 page.screenshot(path=str(OUT/'final-overview.png'));im=Image.open(OUT/'final-overview.png').convert('RGB');check('Pure white photograph background',min(im.getpixel((1200,140)))>=254)
 check('Rendered model is visible',ImageStat.Stat(im.crop((500,260,1300,900))).stddev[0]>20)
 page.locator('#pause').click();t=page.evaluate('mixedApp.model.simulationTime');page.wait_for_timeout(300);check('Pause freezes simulation',t==page.evaluate('mixedApp.model.simulationTime'))
 page.locator('#pause').click();page.wait_for_timeout(300);check('Resume advances simulation',t<page.evaluate('mixedApp.model.simulationTime'))
 page.locator('#wind').uncheck();page.wait_for_timeout(100);t=page.evaluate('mixedApp.model.windTime');page.wait_for_timeout(250);check('Wind switch stops foliage phase',t==page.evaluate('mixedApp.model.windTime'));page.locator('#wind').check()
 page.locator('#doors').uncheck();page.wait_for_timeout(150);check('Shop doors close independently',page.evaluate('mixedApp.model.doors.every(d=>d.rotation.y===0)'));page.locator('#doors').check()
 page.locator('[data-time=night]').click();page.wait_for_function('mixedApp.model.nightFactor>.999');check('Apartment and shop lights react',page.evaluate("Object.values(mixedApp.model.materials).some(m=>m.name==='Shop luminous interior 0'&&m.emissiveIntensity>1)&&Object.values(mixedApp.model.materials).some(m=>m.name==='Apartment interior 9'&&m.emissiveIntensity>.5)"));page.screenshot(path=str(OUT/'final-night.png'));page.locator('[data-time=day]').click();page.wait_for_function('mixedApp.model.nightFactor<.001')
 page.locator('#projection').click();check('Perspective switch works',page.evaluate('mixedApp.camera.isPerspectiveCamera'));page.locator('#projection').click();check('Orthographic switch restores',page.evaluate('mixedApp.camera.isOrthographicCamera'))
 before=page.evaluate('mixedApp.camera.position.toArray()');page.mouse.move(1000,500);page.mouse.down();page.mouse.move(1100,560,steps=8);page.mouse.up();page.wait_for_timeout(200);check('Mouse rotation changes camera',before!=page.evaluate('mixedApp.camera.position.toArray()'))
 before=page.evaluate('mixedApp.controls.target.toArray()');page.mouse.move(1000,500);page.mouse.down(button='right');page.mouse.move(1060,530,steps=8);page.mouse.up(button='right');page.wait_for_timeout(200);check('Right button pans model',before!=page.evaluate('mixedApp.controls.target.toArray()'))
 z=page.evaluate('mixedApp.camera.zoom');page.mouse.wheel(0,-200);page.wait_for_timeout(200);check('Wheel scales orthographic view',page.evaluate('mixedApp.camera.zoom')>z)
 page.locator('#reset').click();check('Reset restores parcel target',page.evaluate('mixedApp.controls.target.distanceTo(new mixedApp.THREE.Vector3(0,30,12))<.00001'))
 page.locator('#quality').select_option('low');low=page.evaluate('(()=>{let n=0;mixedApp.model.root.traverseVisible(o=>{if(o.isMesh)n+=o.isInstancedMesh?o.count:1});return n;})()');page.locator('#quality').select_option('high');high=page.evaluate('(()=>{let n=0;mixedApp.model.root.traverseVisible(o=>{if(o.isMesh)n+=o.isInstancedMesh?o.count:1});return n;})()');check('Quality reduces details without losing silhouette',low<high)
 lifecycle=page.evaluate('''()=>{const a=MixedUseResidentialModule.create({THREE:mixedApp.THREE,quality:'low',coarse:true}),b=MixedUseResidentialModule.create({THREE:mixedApp.THREE,quality:'low',coarse:true});const same=JSON.stringify(a.metadata.treeSites)===JSON.stringify(b.metadata.treeSites);a.dispose();b.update(.1);const ok=same&&a.disposed&&!b.disposed&&b.simulationTime>.09;b.dispose();return ok;}''');check('Seed and separate instance disposal',lifecycle)
 for view in ['facade','entrance','roof']:
  page.locator(f'[data-view={view}]').click();page.wait_for_timeout(700);page.screenshot(path=str(OUT/('final-'+view+'.png')))
 with page.expect_download(timeout=180000) as d:page.locator('#export').click()
 d.value.save_as(ROOT/'棕屿里.glb');raw=(ROOT/'棕屿里.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);names=[n.get('name','') for n in doc['nodes']]
 check('GLB includes architecture and every shop',all(n in names for n in ['facade','balconies','roof','lobby','SHOP-1','SHOP-6']))
 check('GLB excludes photography environment',not doc.get('cameras') and not any('Preview only' in n for n in names))
 check('GLB embeds PBR texture images',bool(doc.get('images')) and all('uri' not in i for i in doc['images']))
 page.set_viewport_size({'width':390,'height':844});page.locator('#reset').click();page.wait_for_timeout(700);page.screenshot(path=str(OUT/'final-mobile.png'));check('Mobile collapses controls without overflow',page.locator('#panel-body').is_hidden() and page.evaluate('document.documentElement.scrollWidth===390'))
 check('Mobile camera contains entire plot',page.evaluate('''()=>{const a=mixedApp,T=a.THREE,b=a.model.getBounds();for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new T.Vector3(x,y,z).project(a.camera);if(Math.abs(p.x)>1||Math.abs(p.y)>1)return false;}return true;}'''))
 check('No runtime or WebGL shader errors',not errors)
 (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'requests':requests,'bounds':bounds,'geometry':geometry},ensure_ascii=False,indent=2),encoding='utf8');print('COMPLETE',len(checks));browser.close()
