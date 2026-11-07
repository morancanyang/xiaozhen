import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1)
    errors=[]
    logs=[]
    page.on('pageerror',lambda err: errors.append(str(err)))
    page.on('console',lambda msg: logs.append(msg.text) if msg.type in ('error','warning') else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle')
    page.wait_for_function('window.cityApp?.ready',timeout=90000)
    page.wait_for_timeout(2500)
    page.screenshot(path=str(ROOT/'outputs'/'web-overview.png'))
    page.select_option('#quality','fast')
    page.wait_for_timeout(1000)
    page.screenshot(path=str(ROOT/'outputs'/'web-fast.png'))
    data=page.evaluate('window.cityApp.exportCity()')
    (ROOT/'outputs'/'qianren-city.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    result={'errors':errors,'logs':logs[:12],'metrics':page.evaluate('window.cityApp.metrics()'),'url':page.url,'export_bytes':(ROOT/'outputs'/'qianren-city.json').stat().st_size}
    print(json.dumps(result,ensure_ascii=False))
    browser.close()
