"""Offline inspection, coarse-to-fine evidence and exact model snapshot."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
with sync_playwright() as p:
    ctx=p.chromium.launch_persistent_context(str(OUT/'browser-profile'),channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'],viewport={'width':1600,'height':1050},device_scale_factor=1,accept_downloads=True)
    ctx.set_offline(True);page=ctx.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url))
    for coarse in [True,False]:
        page.goto((ROOT/'澄序住区.html').as_uri()+('?coarse' if coarse else ''),wait_until='networkidle')
        page.wait_for_function('window.courtyardApp?.ready',polling=100,timeout=120000);page.wait_for_function('courtyardApp.metrics().frames>8',polling=100,timeout=120000)
        page.screenshot(path=str(OUT/('01-blockout.png' if coarse else '02-overview.png')))
        print('Captured coarse' if coarse else 'Captured detailed',flush=True)
    page.click('#pause')
    for name in ['top','front','entrance','garden','roof','A','B','C','D']:
        page.evaluate('(n)=>courtyardApp.view(n)',name);page.wait_for_timeout(500);page.screenshot(path=str(OUT/('02-'+name+'.png')))
    page.evaluate("courtyardApp.view('overview')");page.wait_for_timeout(300)
    snapshot=page.evaluate('courtyardApp.exportScene()')
    (OUT/'courtyard-scene.json').write_text(json.dumps(snapshot,separators=(',',':')),encoding='utf8');(ROOT/'courtyard-manifest.json').write_text(json.dumps(snapshot['manifest'],ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'viewer-views.json').write_text(json.dumps(page.evaluate('courtyardApp.views')),encoding='utf8')
    with page.expect_download(timeout=180000) as dl:page.click('#export')
    dl.value.save_as(ROOT/'chengxu-residential-courtyard.glb')
    report={'errors':errors,'external_requests':[r for r in requests if r.startswith(('http:','https:'))],'bounds':page.evaluate('(()=>{const a=courtyardApp,b=new a.THREE.Box3().setFromObject(a.model.root);return{min:b.min.toArray(),max:b.max.toArray()}})()'),'metrics':page.evaluate('courtyardApp.metrics()'),'objects':len(snapshot['objects']),'owners':sorted(set(o['owner'] for o in snapshot['objects'])),'glb_bytes':(ROOT/'chengxu-residential-courtyard.glb').stat().st_size}
    (OUT/'inspection.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True);ctx.close()
    assert not errors and not report['external_requests']
