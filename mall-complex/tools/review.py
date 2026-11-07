import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files'])
    page=browser.new_page(viewport={'width':1600,'height':1080},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((ROOT/'商城综合体.html').as_uri()+'?coarse',wait_until='load');page.wait_for_function('window.mallApp?.ready');page.wait_for_timeout(1500);page.screenshot(path=str(OUT/'01-rough.png'))
    page.goto((ROOT/'商城综合体.html').as_uri(),wait_until='load');page.wait_for_function('window.mallApp?.ready');page.wait_for_timeout(1800)
    for name in ['overview','entry','terrace','atrium','roof']:
        page.evaluate('(v)=>mallApp.view(v,true)',name);page.wait_for_timeout(1400);page.screenshot(path=str(OUT/f'02-{name}.png'))
    page.evaluate("mallApp.view('overview',true)");page.wait_for_timeout(700)
    data=page.evaluate('mallApp.exportData()');(OUT/'scene.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    report={'errors':errors,'metrics':page.evaluate('mallApp.metrics'),'bounds':page.evaluate('({min:mallApp.mall.getBounds().min.toArray(),max:mallApp.mall.getBounds().max.toArray()})'),'objects':len(data['objects']),'materials':len(data['materials'])}
    (OUT/'review.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report));browser.close()
    if errors:sys.exit(1)
