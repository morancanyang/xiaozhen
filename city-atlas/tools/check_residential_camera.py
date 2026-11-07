import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/residential-integration'
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1700,'height':1100});page.goto('http://127.0.0.1:5173');page.wait_for_function('window.cityApp?.ready');page.wait_for_timeout(800);page.click('#residential-view');page.wait_for_timeout(2100);page.screenshot(path=str(OUT/'residential-context.png'))
 result=page.evaluate("""async()=>{const T=await import('three'),p=cityApp.camera().position,t=cityApp.controls().target,ray=new T.Raycaster(p,t.clone().sub(p).normalize());const hit=ray.intersectObjects(cityApp.scene.children,true).find(h=>h.object.isMesh);let o=hit?.object;while(o?.parent&&!o.userData.id)o=o.parent;return {camera:p.toArray(),target:t.toArray(),firstVisibleId:o?.userData.id,clearApproach:p.x<-336}}""")
 assert result['clearApproach'] and result.get('firstVisibleId','').startswith('LINXU-'),result
 page.set_viewport_size({'width':420,'height':880});page.wait_for_timeout(200)
 if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
 page.click('#residential-view');page.wait_for_timeout(2000);page.screenshot(path=str(OUT/'residential-mobile.png'))
 (OUT/'camera-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result));b.close()
