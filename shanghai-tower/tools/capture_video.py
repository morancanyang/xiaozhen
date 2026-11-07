from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1280,'height':960},device_scale_factor=1)
    page.goto((ROOT/'上海中心.html').as_uri(),wait_until='load');page.wait_for_function('window.towerApp?.ready');page.wait_for_timeout(700)
    with page.expect_download(timeout=30000) as downloaded:
        info=page.evaluate("""async()=>{towerApp.view('overview',true);towerApp.state.orbit=true;const canvas=towerApp.renderer.domElement,stream=canvas.captureStream(30),mime=MediaRecorder.isTypeSupported('video/webm;codecs=vp9')?'video/webm;codecs=vp9':'video/webm';const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:4500000}),chunks=[];recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};const blob=await new Promise(resolve=>{recorder.onstop=()=>resolve(new Blob(chunks,{type:mime}));recorder.start(200);setTimeout(()=>recorder.stop(),8000);});stream.getTracks().forEach(t=>t.stop());const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='ShanghaiTower-8s.webm';a.click();return {bytes:blob.size,mime,width:canvas.width,height:canvas.height,seconds:8};}""")
    downloaded.value.save_as(ROOT/'outputs/上海中心-实时巡游.webm');print(info);browser.close()
