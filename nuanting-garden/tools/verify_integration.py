"""Verify the delivered adapter in an actual offline browser with a transformed parcel."""
import json,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
bundle=subprocess.run(['node','-e',"let e;try{e=require('esbuild')}catch{e=require('D:/3D建模/现代居民楼/01a19528-018c-7023-86c7-cebff28a47b9/residential/node_modules/esbuild')}process.stdout.write(e.buildSync({entryPoints:['integration-example.mjs'],bundle:true,write:false,format:'iife',globalName:'GardenIntegration'}).outputFiles[0].text)"],cwd=ROOT,capture_output=True,text=True,check=True).stdout
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1200,'height':900});page.context.set_offline(True)
    page.goto((ROOT/'暖庭花园.html').as_uri(),wait_until='networkidle');page.wait_for_function('gardenApp?.ready',timeout=60000);page.add_script_tag(content=bundle)
    result=page.evaluate('''()=>{
      const {THREE}=gardenApp,scene=new THREE.Scene(),n=document.querySelectorAll('canvas').length;
      const model=GardenIntegration.mountGardenHousing({THREE,scene,x:200,z:300,groundY:2,blockSize:84,rotationY:Math.PI/2,quality:'low'}),box=new THREE.Box3().setFromObject(model.root);
      const lighting=GardenIntegration.attachGardenLights({THREE,scene,model});lighting.setNight(1);
      const expected=model.root.localToWorld(new THREE.Vector3(...model.manifest.lightFixtures[0].position));
      const result={
        scaled_84m_square:Math.abs(box.max.x-box.min.x-84)<.001&&Math.abs(box.max.z-box.min.z-84)<.001,
        positioned_at_requested_parcel:Math.abs((box.min.x+box.max.x)/2-200)<.001&&Math.abs((box.min.z+box.max.z)/2-300)<.001,
        lights_follow_scale_and_rotation:lighting.lights[0].position.distanceTo(expected)<.001,
        lamp_intensity_scales_with_parcel:Math.abs(lighting.lights[0].intensity-model.manifest.lightFixtures[0].power*.75*.75)<.001,
        no_extra_canvas:document.querySelectorAll('canvas').length===n,
        four_independent_houses:model.buildings.size===4,
        no_extra_camera:!scene.children.some(o=>o.isCamera)
      };
      model.root.position.x+=20;lighting.sync();result.lights_follow_later_moves=lighting.lights[0].position.distanceTo(expected.clone().add(new THREE.Vector3(20,0,0)))<.001;
      lighting.dispose();lighting.dispose();model.dispose();result.clean_unmount=scene.children.length===0;return result;
    }''')
    (ROOT/'outputs/integration-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True);browser.close()
    if not all(result.values()):raise RuntimeError('Integration adapter validation failed')
