"""Actual GPU render of the tower, using the city architecture camera and native renderer.

Full-city day renders are saved by verify_office_integration.py. Here the initial
frame is delayed until the architecture view is selected, avoiding recompilation
of every unrelated building merely to check the new parcel's night/mobile views.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/office-integration'
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1500,'height':1000});page.set_default_timeout(180000);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 source=(ROOT/'dist/main.js').read_text(encoding='utf8').replace("$('#viewport').appendChild(renderer.domElement);","$('#viewport').appendChild(renderer.domElement);window.officeNativeRender=renderer.render.bind(renderer);renderer.render=()=>{};",1)
 page.route('**/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source))
 page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',polling=100)
 page.evaluate("cityApp.select('JIHENG-ONE');document.querySelector('#focus-building').click()")
 page.wait_for_function('Math.abs(cityApp.controls().target.x-112)<.005&&Math.abs(cityApp.controls().target.z+210)<.005',polling=100)
 page.evaluate('()=>{cityApp.renderer.render=officeNativeRender}');page.wait_for_timeout(1800)
 page.screenshot(path=str(OUT/'office-isolated.png'));print('Actual GPU architecture view rendered',flush=True)
 page.locator('[data-time=night]').click();page.wait_for_function("cityApp.office.materials['office-lit'].emissiveIntensity>1.3",polling=100)
 page.screenshot(path=str(OUT/'office-night.png'));print('Actual GPU night rendered',flush=True)
 page.locator('[data-time=morning]').click();page.wait_for_function('cityApp.officeLights.every(l=>l.intensity===0)',polling=100)
 page.set_viewport_size({'width':390,'height':844})
 if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
 page.evaluate('''()=>{cityApp.renderer.render=()=>{};document.querySelector('#office-view').click();const ids=new Set(cityApp.plan.buildings.map(b=>b.id));cityApp.scene.getObjectByName('Qianren-City').traverse(o=>{if(ids.has(o.userData.id)&&o.userData.id!=='JIHENG-ONE')o.visible=false});cityApp.renderer.render=officeNativeRender}''');page.wait_for_timeout(2800)
 page.screenshot(path=str(OUT/'office-mobile.png'))
 report={'actual_gpu_render':True,'views':['architecture','night','mobile'],'errors':errors,'metrics':page.evaluate('cityApp.metrics()'),'visible_point_lights':page.evaluate('cityApp.officeLights.filter(l=>l.visible).length'),'mobile_card_hidden':page.locator('#selection').evaluate("e=>e.classList.contains('hidden')")}
 (OUT/'render-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True);b.close()
 if errors:raise AssertionError('Render errors')
