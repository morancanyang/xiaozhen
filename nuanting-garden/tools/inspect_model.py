"""Capture the real offline Three.js blockout and detailed model for visual review."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    ctx=browser.new_context(viewport={'width':1600,'height':1050},device_scale_factor=1,accept_downloads=True);ctx.set_offline(True)
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    for coarse in [True,False]:
        page.goto((ROOT/'暖庭花园.html').as_uri()+('?coarse' if coarse else ''),wait_until='networkidle')
        page.wait_for_function('window.gardenApp?.ready',timeout=60000);page.wait_for_timeout(1000)
        page.screenshot(path=str(OUT/('01-blockout.png' if coarse else '02-overview.png')))
    if not page.evaluate('gardenApp.state.paused'):page.click('#pause')
    for name in ['top','entrance','garden','roof','facade','A','B','C','D']:
        page.evaluate('(n)=>gardenApp.view(n)',name);page.wait_for_timeout(600)
        page.screenshot(path=str(OUT/('02-'+name+'.png')))
    page.evaluate("gardenApp.view('overview')");page.wait_for_timeout(300)
    snapshot=page.evaluate('gardenApp.exportScene()')
    (OUT/'garden-scene.json').write_text(json.dumps(snapshot,separators=(',',':')),encoding='utf8')
    (ROOT/'garden-manifest.json').write_text(json.dumps(snapshot['manifest'],ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'viewer-views.json').write_text(json.dumps(page.evaluate('gardenApp.views'),indent=2),encoding='utf8')
    with page.expect_download(timeout=180000) as dl:page.click('#export')
    dl.value.save_as(ROOT/'nuanting-garden-housing.glb')
    report={'errors':errors,'bounds':page.evaluate('(()=>{const a=gardenApp,b=new a.THREE.Box3().setFromObject(a.model.root);return{min:b.min.toArray(),max:b.max.toArray()}})()'),'metrics':page.evaluate('gardenApp.metrics()'),'snapshot_objects':len(snapshot['objects']),'snapshot_owners':sorted(set(o['owner'] for o in snapshot['objects'])),'glb_bytes':(ROOT/'nuanting-garden-housing.glb').stat().st_size}
    (OUT/'inspection.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True);browser.close()
    if errors:raise RuntimeError('Browser errors during visual inspection')
