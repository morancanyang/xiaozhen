import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True)
    page=context.new_page();page.goto((ROOT/'上海中心.html').as_uri(),wait_until='load');page.wait_for_function('window.towerApp?.ready');page.wait_for_timeout(600)
    client=context.new_cdp_session(page)
    before=page.evaluate('towerApp.camera.position.toArray()')
    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':120,'y':420,'id':0}]})
    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':175,'y':450,'id':0}]})
    client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(300)
    rotate=before!=page.evaluate('towerApp.camera.position.toArray()')
    distance=page.evaluate('towerApp.camera.position.distanceTo(towerApp.controls.target)')
    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':95,'y':420,'id':0},{'x':230,'y':420,'id':1}]})
    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':55,'y':420,'id':0},{'x':270,'y':420,'id':1}]})
    client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(300)
    pinch=abs(distance-page.evaluate('towerApp.camera.position.distanceTo(towerApp.controls.target)'))>1
    checks=[{'check':'single-finger touch rotation','passed':rotate},{'check':'two-finger pinch zoom','passed':pinch}]
    assert rotate and pinch,checks
    report=json.loads((ROOT/'outputs/verification.json').read_text(encoding='utf8'));report['checks']=[item for item in report['checks'] if item['check'] not in {c['check'] for c in checks}]+checks;(ROOT/'outputs/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(checks);context.close();browser.close()
