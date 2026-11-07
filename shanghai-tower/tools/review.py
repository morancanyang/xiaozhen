import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1800,'height':1100},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    uri=(ROOT/'上海中心.html').as_uri()
    page.goto(uri+'?coarse=1',wait_until='load');page.wait_for_function('window.towerApp?.ready');page.wait_for_timeout(900);page.screenshot(path=str(ROOT/'outputs/01-rough.png'))
    page.goto(uri,wait_until='load');page.wait_for_function('window.towerApp?.ready');page.wait_for_timeout(1600)
    page.screenshot(path=str(ROOT/'outputs/02-overview.png'))
    for name in ['hero','facade','entry','crown']:
        page.locator('[data-view='+name+']').click();page.wait_for_timeout(1800);page.screenshot(path=str(ROOT/f'outputs/02-{name}.png'))
    data=page.evaluate('towerApp.exportData()');(ROOT/'outputs/scene.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    result={'errors':errors,'metadata':data['metadata'],'metrics':page.evaluate('towerApp.metrics'),'bounds':page.evaluate('({min:towerApp.tower.getBounds().min.toArray(),max:towerApp.tower.getBounds().max.toArray()})')}
    (ROOT/'outputs/review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True));browser.close()
