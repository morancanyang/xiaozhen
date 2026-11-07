"""Real GPU frame-pacing comparison in a fixed viewport, same camera path and browser."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/performance';OUT.mkdir(parents=True,exist_ok=True)
sample='''async({moving,seconds})=>{
 const a=cityApp,c=a.camera(),target=a.controls().target;target.set(0,15,0);c.position.set(650,610,790);a.controls().update();
 const times=[],calls=[],triangles=[],start=performance.now();let last=start;
 return await new Promise(resolve=>{function frame(now){const elapsed=(now-start)/1000;if(elapsed>.5){times.push(now-last);calls.push(a.renderer.info.render.calls);triangles.push(a.renderer.info.render.triangles)}last=now;
  if(moving){const angle=Math.atan2(650,790)+elapsed*.15;c.position.set(Math.sin(angle)*Math.hypot(650,790),610,Math.cos(angle)*Math.hypot(650,790));}
  if(elapsed<seconds){requestAnimationFrame(frame);return}const sorted=[...times].sort((a,b)=>a-b),avg=v=>v.reduce((a,b)=>a+b,0)/v.length;resolve({frames:times.length,fps:1000/avg(times),median_ms:sorted[Math.floor(sorted.length*.5)],p95_ms:sorted[Math.floor(sorted.length*.95)],average_calls:avg(calls),average_triangles:avg(triangles),performance:a.performance.metrics,river:a.riverPass.metrics});}requestAnimationFrame(frame)});
}'''
with sync_playwright() as p:
 context=p.chromium.launch_persistent_context(str(OUT/'browser-profile'),channel='msedge',headless=True,viewport={'width':1280,'height':800},device_scale_factor=1,args=['--enable-webgl','--enable-unsafe-swiftshader'])
 page=context.pages[0];page.set_default_timeout(240000);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',timeout=360000,polling=100)
 inventory=page.evaluate('''()=>{const a=cityApp,r=a.renderer,gl=r.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return{renderer:gl.getParameter(ext.UNMASKED_RENDERER_WEBGL),buildings:a.plan.buildings.length,sources:a.performance.metrics.lightSources,lights:a.performance.pool.length,viewport:[innerWidth,innerHeight],dpr:devicePixelRatio}}''');print('INVENTORY '+json.dumps(inventory),flush=True)
 results={'inventory':inventory,'errors':errors,'samples':{}}
 for name,enabled,moving in [('optimized_idle',True,False),('optimized_drag',True,True),('legacy_drag',False,True),('optimized_drag_repeat',True,True)]:
  page.evaluate('(enabled)=>cityApp.performance.setEnabled(enabled)',enabled);page.wait_for_timeout(2500)
  print('MEASURING '+name,flush=True);data=page.evaluate(sample,{'moving':moving,'seconds':6});results['samples'][name]=data;print(name+' '+json.dumps(data),flush=True)
  (OUT/'benchmark.json').write_text(json.dumps(results,indent=2),encoding='utf8')
 page.evaluate('cityApp.performance.setEnabled(true)');page.locator('#home').click();page.wait_for_timeout(2500);page.screenshot(path=str(OUT/'optimized-city.png'))
 page.locator('[data-time=night]').click();page.wait_for_function("cityApp.performance.pool.some(l=>l.intensity>0)",polling=100);page.wait_for_timeout(1700);page.screenshot(path=str(OUT/'optimized-night.png'))
 results['night']=page.evaluate('({lit:cityApp.performance.pool.filter(l=>l.intensity>0).length,budget:cityApp.performance.metrics.activeLightBudget})');results['errors']=errors
 (OUT/'benchmark.json').write_text(json.dumps(results,indent=2),encoding='utf8');context.close()
 if errors:raise RuntimeError('Browser errors; see benchmark.json')
