import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);context=browser.new_context(viewport={'width':1600,'height':1050},device_scale_factor=1,accept_downloads=True);context.set_offline(True)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    for coarse in [True,False]:
        page.goto((ROOT/'青岚河.html').as_uri()+('?coarse' if coarse else ''));page.wait_for_function('window.riverApp?.ready',timeout=60000);page.wait_for_timeout(1800);page.screenshot(path=str(OUT/('01-blockout.png' if coarse else '02-overview.png')))
    page.click('#pause')
    for view in ['bend','bank','fish','length']:
        page.evaluate('(name)=>riverApp.view(name)',view);page.wait_for_timeout(1000);page.screenshot(path=str(OUT/('02-'+view+'.png')))
    data=page.evaluate('riverApp.exportScene()');(OUT/'river-scene.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8');(ROOT/'river-manifest.json').write_text(json.dumps(data['manifest'],ensure_ascii=False,indent=2),encoding='utf8')
    with page.expect_download(timeout=120000) as download:page.click('#export')
    download.value.save_as(ROOT/'qinglan-river.glb')
    result={'errors':errors,'metrics':page.evaluate('riverApp.metrics()'),'bounds':page.evaluate('(()=>{const a=riverApp,b=new a.THREE.Box3().setFromObject(a.river.root);return {min:b.min.toArray(),max:b.max.toArray()}})()'),'glb_bytes':(ROOT/'qinglan-river.glb').stat().st_size}
    (OUT/'inspection.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True));browser.close()
