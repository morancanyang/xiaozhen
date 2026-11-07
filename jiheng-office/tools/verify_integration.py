"""Check the actual exported integration adapter against a host-owned scene."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=b.new_page()
    page.goto((ROOT/'霁衡中心.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.officeApp?.ready',timeout=120000,polling=100)
    page.add_script_tag(path=str(ROOT/'outputs/host-three-test.js'))
    source=(ROOT/'integration-example.mjs').read_text(encoding='utf8').replace("import {createLandmarkOffice} from './model.mjs';",'const createLandmarkOffice=LandmarkOfficeModule.create;').replace('export function','function')
    page.add_script_tag(content=source+';window.OfficeIntegration={mountLandmarkOffice,attachLandmarkLights};')
    result=page.evaluate('''()=>{
      const T=window.TownTHREE,scene=new T.Scene(),m=OfficeIntegration.mountLandmarkOffice({THREE:T,scene,x:31,z:-70,groundY:.34,blockSize:84,rotationY:.4});
      const checks={host_three_180:T.REVISION==='180',host_scene_owns_root:scene.children.includes(m.root),placement:Math.abs(m.root.position.y-.34)<1e-8&&Math.abs(m.root.rotation.y-.4)<1e-8,scale:Math.abs(m.root.scale.x-.75)<1e-8,manifest:m.getManifest().id==='jiheng-landmark-office'};
      const adapter=OfficeIntegration.attachLandmarkLights({THREE:T,scene,model:m});adapter.setNight(.6);const fixture=m.manifest.lightFixtures[0],expected=m.root.localToWorld(new T.Vector3(...fixture.position));
      checks.real_lights=adapter.lights.length===16&&adapter.lights.every(l=>l.isPointLight);
      checks.light_world_transform=adapter.lights[0].position.distanceTo(expected)<1e-6;
      checks.light_power_scales= Math.abs(adapter.lights[0].intensity-fixture.power*.75*.75*.6)<1e-6;
      m.root.position.x+=5;adapter.sync();checks.move_sync=adapter.lights[0].position.distanceTo(m.root.localToWorld(new T.Vector3(...fixture.position)))<1e-6;
      adapter.setNight(0);checks.day_lights_off=adapter.lights.every(l=>l.intensity===0);
      let finite=true,unitNormals=true;m.root.traverse(o=>{if(o.isMesh){const a=o.geometry.attributes;for(const key of ['position','normal','uv'])if(a[key])finite&&=a[key].array.every(Number.isFinite);for(let i=0;i<a.normal.count;i++){const length=new T.Vector3().fromBufferAttribute(a.normal,i).length();unitNormals&&=Math.abs(length-1)<.001}}});checks.finite_geometry=finite;checks.normal_lengths=unitNormals;
      const s=m.exportScene();checks.world_snapshot=s.snapshotSpace==='world'&&s.objects.some(o=>Math.abs(o.matrix[12])>31);
      adapter.dispose();adapter.dispose();m.dispose();m.dispose();checks.safe_disposal=scene.children.length===0;return checks;
    }''')
    (ROOT/'outputs/integration-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True);b.close()
    if not all(result.values()):raise RuntimeError('Integration check failed')
