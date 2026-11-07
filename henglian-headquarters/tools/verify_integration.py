from pathlib import Path
import json,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
# This is the project's existing Three.js r180 bundle, distinct from the viewer's r187.
shutil.copyfile(ROOT.parent/'jiheng-office/outputs/host-three-test.js',ROOT/'outputs/host-three-test.js')
with sync_playwright() as p:
    b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=b.new_page();page.context.set_offline(True)
    page.goto((ROOT/'衡联总部.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.headquartersApp?.ready',timeout=120000,polling=100)
    page.add_script_tag(path=str(ROOT/'outputs/host-three-test.js'))
    source=(ROOT/'integration-example.mjs').read_text(encoding='utf8').replace("import {createCorporateHeadquarters} from './model.mjs';",'const createCorporateHeadquarters=CorporateHeadquartersModule.create;').replace('export function','function')
    page.add_script_tag(content=source+';window.HeadquartersIntegration={mountCorporateHeadquarters,attachHeadquartersLights};')
    result=page.evaluate('''()=>{
      const T=TownTHREE,scene=new T.Scene(),m=HeadquartersIntegration.mountCorporateHeadquarters({THREE:T,scene,x:31,z:-70,groundY:.34,blockSize:84,rotationY:.4});
      const checks={host_three_180:T.REVISION==='180',host_scene_owns_root:scene.children.includes(m.root),placement:m.root.position.y===.34&&m.root.rotation.y===.4,scale:Math.abs(m.root.scale.x-.75)<1e-8,manifest:m.getManifest().id==='henglian-corporate-headquarters'};
      const adapter=HeadquartersIntegration.attachHeadquartersLights({THREE:T,scene,model:m,budget:4});adapter.setNight(.6);const f=m.manifest.lightFixtures[0],expected=m.root.localToWorld(new T.Vector3(...f.position));
      checks.real_lights=adapter.lights.length===4&&adapter.lights.every(l=>l.isPointLight);checks.light_world_transform=adapter.lights[0].position.distanceTo(expected)<1e-6;checks.light_power_scales=Math.abs(adapter.lights[0].intensity-f.power*.75*.75*.6)<1e-6;
      m.root.position.x+=5;adapter.sync();checks.move_sync=adapter.lights[0].position.distanceTo(m.root.localToWorld(new T.Vector3(...f.position)))<1e-6;adapter.setNight(0);checks.day_lights_off=adapter.lights.every(l=>l.intensity===0);
      let finite=true,unitNormals=true;m.root.traverse(o=>{if(o.isMesh){const a=o.geometry.attributes;for(const key of ['position','normal','uv'])if(a[key])finite&&=a[key].array.every(Number.isFinite);for(let i=0;i<a.normal.count;i++){const length=new T.Vector3().fromBufferAttribute(a.normal,i).length();unitNormals&&=Math.abs(length-1)<.001}}});checks.finite_geometry=finite;checks.normal_lengths=unitNormals;
      const snapshot=m.exportScene();checks.world_snapshot=snapshot.snapshotSpace==='world'&&snapshot.objects.some(o=>Math.abs(o.matrix[12])>31);adapter.dispose();adapter.dispose();m.dispose();m.dispose();checks.safe_disposal=scene.children.length===0;return checks;
    }''')
    (ROOT/'outputs/integration-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True);b.close();assert all(result.values())
