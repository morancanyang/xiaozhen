import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/hospital-integration';OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1700,'height':1050},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready');page.wait_for_timeout(1300)
    page.screenshot(path=str(OUT/'town-overview.png'))
    # Match the reference's north-up, steep aerial angle to verify the marked parcel.
    page.evaluate('''()=>{let a=cityApp,c=a.camera(),v=a.controls();c.position.set(0,1000,450);v.target.set(0,0,0);v.update();}''');page.wait_for_timeout(200);page.screenshot(path=str(OUT/'north-up-marked-parcel.png'))
    page.locator('#hospital-view').click();page.wait_for_timeout(2300);page.screenshot(path=str(OUT/'hospital-context.png'))
    page.evaluate('''()=>{let a=cityApp,s=a.hospitalSite,c=a.camera(),v=a.controls();c.position.set(s.x-90,70,s.z+40);v.target.set(s.x-35,-1,s.z-28);v.update();}''');page.wait_for_timeout(200);page.screenshot(path=str(OUT/'hospital-garage.png'))
    result={'errors':errors,'metrics':page.evaluate('cityApp.metrics()'),'site':page.evaluate('cityApp.hospitalSite'),'hospital_buildings':page.evaluate("cityApp.plan.buildings.filter(b=>b.moduleId==='hospital-campus')"),'hospital_bounds':page.evaluate('(()=>{const h=cityApp.hospital,b=new h.root.position.constructor();let min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];h.root.updateMatrixWorld(true);return {position:h.root.position.toArray(),scale:h.root.scale.toArray(),manifest:h.manifest.bounds}})()')}
    (OUT/'inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True));browser.close()
