import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/river-integration';OUT.mkdir(exist_ok=True,parents=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1700,'height':1100});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',timeout=60000);page.wait_for_timeout(1500);page.screenshot(path=str(OUT/'city-overview.png'))
    for name in ['river-view','river-fish-view']:
        page.locator('#'+name).click();page.wait_for_timeout(2200);page.screenshot(path=str(OUT/(name+'.png')))
    report={'errors':errors,'metrics':page.evaluate('cityApp.metrics()'),'riverPass':page.evaluate('cityApp.riverPass.metrics'),'blocks':page.evaluate('cityApp.plan.blocks.length'),'buildings':page.evaluate('cityApp.plan.buildings.length')};(OUT/'inspection.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report));browser.close()
