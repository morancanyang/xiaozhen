"""Record an actual browser orbit and check portrait framing, without a live service."""
import base64,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':960},device_scale_factor=1)
    page.goto((ROOT/'商城综合体.html').as_uri(),wait_until='networkidle');page.wait_for_function('mallApp.ready');page.wait_for_timeout(1000)
    data=page.evaluate('''async()=>{const a=mallApp;a.view('overview',true);a.state.paused=false;a.state.orbit=true;const stream=a.renderer.domElement.captureStream(30);const mime=MediaRecorder.isTypeSupported('video/webm;codecs=vp9')?'video/webm;codecs=vp9':'video/webm';const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:6500000});const chunks=[];const done=new Promise(resolve=>{recorder.onstop=async()=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.readAsDataURL(new Blob(chunks,{type:mime}));};});recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};recorder.start();await new Promise(r=>setTimeout(r,9000));recorder.stop();const result=await done;stream.getTracks().forEach(t=>t.stop());a.state.orbit=false;return result;}''')
    path=OUT/'商城动态巡游.webm';path.write_bytes(base64.b64decode(data));print('Actual browser orbit bytes:',path.stat().st_size,flush=True)
    page.set_viewport_size({'width':390,'height':844});page.evaluate("mallApp.view('overview',true);mallApp.state.paused=true;document.querySelector('#toast').classList.remove('show')");page.wait_for_timeout(800);page.screenshot(path=str(OUT/'final-mobile.png'))
    fit=page.evaluate('''()=>{const b=mallApp.mall.getBounds(),p=mallApp.camera;const C=p.position.constructor;const pts=[];for(const x of [b.min.x,b.max.x])for(const z of [b.min.z,b.max.z]){const v=new C(x,0,z).project(p);pts.push([v.x,v.y]);}return pts;}''')
    assert all(abs(v[0])<=1 for v in fit),'Mobile overview clips parcel horizontally'
    page.locator('[data-time=night]').evaluate('(e)=>e.click()');page.wait_for_timeout(1700);page.set_viewport_size({'width':1600,'height':1080});page.evaluate("mallApp.view('overview',true)");page.wait_for_timeout(700);page.screenshot(path=str(OUT/'final-night.png'))
    print('Portrait parcel fit verified:',json.dumps(fit));browser.close()
