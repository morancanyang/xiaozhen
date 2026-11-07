import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)});print(('PASS ' if v else 'FAIL ')+n,flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1500,'height':1000},accept_downloads=True);ctx.set_offline(True);page=ctx.new_page();errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url));page.goto((ROOT/'林序住区.html').as_uri());page.wait_for_function('window.residentialApp?.ready');page.wait_for_timeout(800)
 check('offline HTML without network',not any(x.startswith(('http:','https:')) for x in requests));check('four independent building IDs',page.evaluate("['A','B','C','D'].every(id=>residentialApp.model.groups.get(id).children.length>0)&&residentialApp.model.manifest.buildings.length===4"))
 bounds=page.evaluate('(()=>{const a=residentialApp,b=new a.THREE.Box3().setFromObject(a.model.root);return {min:b.min.toArray(),max:b.max.toArray()}})()');check('all geometry inside 112m square',bounds['min'][0]>=-56.01 and bounds['max'][0]<=56.01 and bounds['min'][2]>=-56.01 and bounds['max'][2]<=56.01)
 page.click('#pause');t=page.evaluate('residentialApp.model.simulationTime');page.wait_for_timeout(200);check('pause freezes animations',page.evaluate('residentialApp.model.simulationTime')==t);page.click('#pause');page.wait_for_timeout(200);check('resume advances animations',page.evaluate('residentialApp.model.simulationTime')>t)
 before=page.evaluate('residentialApp.camera.position.toArray()');page.mouse.move(800,500);page.mouse.down();page.mouse.move(950,540,steps=8);page.mouse.up();page.wait_for_timeout(250);check('drag rotates camera',before!=page.evaluate('residentialApp.camera.position.toArray()'))
 before=page.evaluate('residentialApp.controls.target.toArray()');page.mouse.down(button='right');page.mouse.move(1000,600,steps=6);page.mouse.up(button='right');page.wait_for_timeout(200);check('right drag pans camera',before!=page.evaluate('residentialApp.controls.target.toArray()'))
 before=page.evaluate('residentialApp.camera.position.distanceTo(residentialApp.controls.target)');page.mouse.wheel(0,-250);page.wait_for_timeout(200);check('wheel zoom works',page.evaluate('residentialApp.camera.position.distanceTo(residentialApp.controls.target)')<before)
 for name in ['A','B','C','D']:
  page.click('[data-building='+name+']');check('focus building '+name,page.evaluate('residentialApp.camera.position.toArray().every(Number.isFinite)'))
 page.uncheck('#fish');page.wait_for_timeout(120);check('people and cars can be disabled',page.evaluate("!residentialApp.model.root.getObjectByName('Resident 0').visible&&!residentialApp.model.root.getObjectByName('Moving EV 0').visible"));page.check('#fish')
 page.select_option('#quality','low');check('low quality applies',page.evaluate("residentialApp.model.quality==='low'"));page.select_option('#quality','high')
 page.click('#night');check('night window lamps activate',page.evaluate("(()=>{let lit=false;residentialApp.model.root.traverse(o=>{if(o.material?.name==='window-lit'&&o.material.emissiveIntensity>1)lit=true});return lit})()"));page.click('#night')
 state=page.evaluate('''()=>{const a=residentialApp,m=ResidentialModule.create({THREE:a.THREE,blockSize:84,coarse:true});const box=new a.THREE.Box3().setFromObject(m.root);let light=false;m.root.traverse(o=>{if(o.isLight||o.isCamera)light=true});const swing=m.root.getObjectByName('Swing');m.update(.2);const moving=Math.abs(swing.rotation.x)>0;m.dispose();m.dispose();return{scaled:Math.abs(box.max.x-box.min.x-84)<.01,pure:!light,moving,disposed:m.disposed&&m.root.children.length===0}}''')
 for k in ['scaled','pure','moving','disposed']:check('factory '+k,state[k])
 with page.expect_download(timeout=120000) as d:page.click('#export')
 d.value.save_as(ROOT/'linxu-residential.glb');check('GLB binary valid',(ROOT/'linxu-residential.glb').read_bytes()[:4]==b'glTF')
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(200);check('mobile has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth===390'));page.screenshot(path=str(ROOT/'outputs/final-mobile.png'))
 check('no JS or WebGL errors',not errors);(ROOT/'outputs/verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds},indent=2),encoding='utf8');b.close()
 if not all(c['passed'] for c in checks):raise SystemExit('Verification failed')
