"""Exercise the actual exported city adapter in an offline browser."""
import json,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
bundle=subprocess.run(['node','-e',"let e;try{e=require('esbuild')}catch{e=require('D:/3D建模/现代居民楼/01a19528-018c-7023-86c7-cebff28a47b9/residential/node_modules/esbuild')}process.stdout.write(e.buildSync({entryPoints:['integration-example.mjs'],bundle:true,write:false,format:'iife',globalName:'SportsIntegration'}).outputFiles[0].text)"],cwd=ROOT,capture_output=True,text=True,check=True).stdout
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1500,'height':1000});page.context.set_offline(True)
    page.goto((ROOT/'青禾运动场.html').as_uri());page.wait_for_function('window.sportsApp?.ready')
    page.add_script_tag(content=bundle)
    report=page.evaluate('''()=>{
      const {THREE}=sportsApp,scene=new THREE.Scene(),initialCanvasCount=document.querySelectorAll('canvas').length;
      const model=SportsIntegration.mountSportsField({THREE,scene,x:200,z:300,groundY:2,blockSize:84,rotationY:Math.PI/2,quality:'low'});
      const box=new THREE.Box3().setFromObject(model.root);
      const adapter=SportsIntegration.attachSportsFloodlights({THREE,scene,model});adapter.setNight(true);
      const expected=model.root.localToWorld(new THREE.Vector3(-48.4,13.4,-38.4));
      const result={
        square_scaled_to_84m:Math.abs(box.max.x-box.min.x-84)<.001&&Math.abs(box.max.z-box.min.z-84)<.001,
        parcel_position_applied:Math.abs((box.min.x+box.max.x)/2-200)<.001&&Math.abs((box.min.z+box.max.z)/2-300)<.001,
        lamps_rotate_and_scale:adapter.lights[0].position.distanceTo(expected)<.001,
        light_intensity_scales:adapter.lights.every(l=>Math.abs(l.intensity-3600*.75*.75)<.001&&l.distance===130*.75),
        host_owns_canvas:document.querySelectorAll('canvas').length===initialCanvasCount,
        no_host_camera_created:!scene.children.some(o=>o.isCamera)
      };
      adapter.dispose();model.dispose();result.all_resources_unmounted=scene.children.length===0;
      return result;
    }''')
    page.click('#pause');page.screenshot(path=str(ROOT/'outputs/final-overview.png'))
    page.click('#night');page.wait_for_timeout(500)
    report['night_actual_lighting']=page.evaluate('sportsApp.scene.children.filter(o=>o.isSpotLight&&o.intensity===3600).length===4')
    page.screenshot(path=str(ROOT/'outputs/final-night.png'))
    (ROOT/'outputs/integration-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report),flush=True);browser.close()
    if not all(report.values()):raise RuntimeError('Integration check failed')
