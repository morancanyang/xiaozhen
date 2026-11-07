import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    ctx=browser.new_context(viewport={'width':1600,'height':1100},device_scale_factor=1,accept_downloads=True)
    ctx.set_offline(True)
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    for coarse in [True,False]:
        page.goto((ROOT/'云际中心.html').as_uri()+('?coarse' if coarse else ''),wait_until='load')
        page.wait_for_function('window.skylineApp?.ready',timeout=60000)
        page.wait_for_timeout(1600)
        page.screenshot(path=str(OUT/('01-graybox.png' if coarse else '02-overview.png')))
    page.click('#pause')
    for name in ['low','entrance','terrace','roof','garage','top']:
        page.evaluate('(name)=>skylineApp.view(name,true)',name);page.wait_for_timeout(350)
        page.screenshot(path=str(OUT/('02-'+name+'.png')))
    data=page.evaluate('skylineApp.exportScene()')
    (OUT/'skyline-scene.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    (ROOT/'skyline-manifest.json').write_text(json.dumps(data['manifest'],ensure_ascii=False,indent=2),encoding='utf8')
    page.evaluate("skylineApp.view('overview',true);skylineApp.timeOfDay('night')");page.wait_for_timeout(400)
    page.screenshot(path=str(OUT/'02-night.png'))
    page.evaluate("skylineApp.timeOfDay('morning')");page.wait_for_timeout(250)
    with page.expect_download(timeout=120000) as d:page.click('#export-glb')
    d.value.save_as(ROOT/'skyline-one.glb')
    result={'errors':errors,'metrics':page.evaluate('skylineApp.metrics()'),'bounds':page.evaluate('(()=>{const a=skylineApp,b=new a.THREE.Box3().setFromObject(a.tower.root);return {min:b.min.toArray(),max:b.max.toArray()}})()'),'glb_bytes':(ROOT/'skyline-one.glb').stat().st_size}
    (OUT/'inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=True))
    browser.close()
