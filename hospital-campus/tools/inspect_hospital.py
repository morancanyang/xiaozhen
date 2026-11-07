import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1)
    context.set_offline(True)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto((ROOT/'澄和医院.html').as_uri()+'?coarse',wait_until='load');page.wait_for_function('window.hospitalApp?.ready');page.wait_for_timeout(1200);page.screenshot(path=str(ROOT/'outputs/01-graybox.png'))
    page.goto((ROOT/'澄和医院.html').as_uri(),wait_until='load');page.wait_for_function('window.hospitalApp?.ready');page.wait_for_timeout(1500);page.screenshot(path=str(ROOT/'outputs/02-overview.png'))
    export=page.evaluate('hospitalApp.exportScene()');(ROOT/'outputs/hospital-scene.json').write_text(json.dumps(export,separators=(',',':')),encoding='utf-8')
    (ROOT/'hospital-manifest.json').write_text(json.dumps(export['manifest'],ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ['garden','emergency','garage','roof']:
        page.evaluate('(name)=>hospitalApp.view(name,true)',name);page.wait_for_timeout(350);page.screenshot(path=str(ROOT/'outputs'/('02-'+name+'.png')))
    print(json.dumps({'errors':errors,'metrics':page.evaluate('hospitalApp.metrics()'),'bounds':page.evaluate('(()=>{let a=hospitalApp;let b=new a.THREE.Box3().setFromObject(a.hospital.root);return {min:b.min.toArray(),max:b.max.toArray()}})()')},ensure_ascii=True))
    (ROOT/'outputs/first-inspection.json').write_text(json.dumps({'errors':errors},indent=2),encoding='utf-8')
    browser.close()
