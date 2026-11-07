"""Native GPU mouse drag, stationary clarity, free camera and high-DPI mobile checks."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/performance'
with sync_playwright() as p:
 context=p.chromium.launch_persistent_context(str(OUT/'browser-profile'),channel='msedge',headless=True,viewport={'width':1280,'height':800},args=['--enable-webgl','--enable-unsafe-swiftshader'])
 page=context.pages[0];page.set_default_timeout(120000);errors=[];checks={}
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',polling=100)
 page.wait_for_function('cityApp.performance.metrics.frames>10&&!cityApp.performance.moving&&document.elementFromPoint(640,560)?.tagName==="CANVAS"',polling=100)
 before=page.evaluate('cityApp.camera().position.toArray()');page.mouse.move(640,560);page.mouse.down();page.mouse.move(870,592,steps=18)
 checks['actual_mouse_drag_rotates']=before!=page.evaluate('cityApp.camera().position.toArray()')
 checks['motion_budget_engages']=page.evaluate('cityApp.performance.moving&&cityApp.renderer.getPixelRatio()<1')
 page.mouse.up();page.wait_for_function('!cityApp.performance.moving&&cityApp.renderer.getPixelRatio()>=.99',polling=100)
 checks['idle_clarity_restored']=page.evaluate('cityApp.renderer.getPixelRatio()>=.99')
 checks['source_material_restored_between_frames']=page.evaluate("cityApp.office.materials['vision-glass'].transmission===.55&&cityApp.scene.matrixWorldAutoUpdate")
 page.locator('[data-view=free]').click();before=page.evaluate('cityApp.camera().position.toArray()');page.locator('canvas').click(position={'x':650,'y':450});page.keyboard.down('w');page.wait_for_timeout(300);page.keyboard.up('w')
 checks['free_camera_moves']=page.evaluate('cityApp.state.freeView') and before!=page.evaluate('cityApp.camera().position.toArray()');page.locator('#free-view-exit').click()
 page.locator('#pause').click();water=page.evaluate('cityApp.river.waterTime');page.wait_for_timeout(180);checks['water_pause_preserved']=water==page.evaluate('cityApp.river.waterTime');page.locator('#pause').click()
 page.locator('[data-time=night]').click();page.wait_for_function('cityApp.performance.pool.some(l=>l.intensity>1)',polling=100);checks['night_pool_lights']=page.evaluate('cityApp.performance.pool.filter(l=>l.layers.isEnabled(0)).length===8')
 page.screenshot(path=str(OUT/'ui-night.png'));page.locator('[data-time=morning]').click()
 cdp=page.context.new_cdp_session(page);cdp.send('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':2,'mobile':True})
 page.wait_for_function('innerWidth===390&&Math.abs(cityApp.camera().aspect-390/844)<.001',polling=100);page.locator('#home').click();page.wait_for_timeout(2500)
 checks['mobile_no_overflow']=page.evaluate('document.documentElement.scrollWidth===390')
 checks['mobile_pixel_budget']=page.evaluate('cityApp.renderer.getPixelRatio()<=1.45')
 checks['all_models_retained']=page.evaluate("cityApp.plan.buildings.length===34&&cityApp.plan.blocks.length===16&&!!cityApp.office&&!!cityApp.mixed&&!!cityApp.garden&&!!cityApp.river")
 checks['no_js_or_shader_errors']=not errors;page.screenshot(path=str(OUT/'ui-mobile.png'))
 report={'checks':checks,'errors':errors,'mobile':page.evaluate('({ratio:cityApp.renderer.getPixelRatio(),performance:cityApp.performance.metrics})')};(OUT/'ui-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True);context.close()
 if not all(checks.values()):raise RuntimeError('Performance UI validation failed')
