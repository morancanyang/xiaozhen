"""Deterministic render scheduling, material/export and layer/visibility contracts."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/performance'
imports=re.search(r'<script type="importmap">.*?</script>',(ROOT/'dist/index.html').read_text(encoding='utf8'),re.S).group(0)
fixture=ROOT/'dist/__performance-test.html';fixture.write_text('<!doctype html>'+imports,encoding='utf8')
try:
 with sync_playwright() as p:
  b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page(viewport={'width':1280,'height':800});page.goto('http://127.0.0.1:5173/__performance-test.html')
  result=page.evaluate('''async()=>{
   const T=await import('three'),{createRenderBudget}=await import('./render-budget.js'),{createRiver}=await import('./river-model.js'),{createRiverPass}=await import('./river-pass.js'),{GLTFExporter}=await import('three/addons/exporters/GLTFExporter.js');
   const checks={},scene=new T.Scene(),root=new T.Group();root.name='Source building';root.scale.setScalar(2);scene.add(root);const sun=new T.DirectionalLight();scene.add(sun);const state={quality:'balanced'};
   const lights=Array.from({length:48},(_,i)=>{const l=new T.PointLight(0xffccaa,50+i,16,2);l.position.set(i%8*8,3,Math.floor(i/8)*8);root.add(l);return l});
   const mat=new T.MeshPhysicalMaterial({color:0x557788,transmission:.6,roughness:.15}),mesh=new T.Mesh(new T.BoxGeometry(10,40,10),mat);mesh.position.set(0,20,0);root.add(mesh);
   const tiny=new T.Mesh(new T.BoxGeometry(.01,.01,.01),new T.MeshStandardMaterial());tiny.position.set(0,20,0);root.add(tiny);
   const manualHidden=tiny.clone();manualHidden.visible=false;root.add(manualHidden);
   let ratio=1,resize=0;const renderer={shadowMap:{autoUpdate:true,needsUpdate:false},transmissionResolutionScale:1,getPixelRatio:()=>ratio,setPixelRatio:r=>ratio=r};
   const budget=createRenderBudget({scene,renderer,sun,state,bloom:{enabled:true},ssao:{enabled:false},onResolutionChange:()=>resize++});
   checks.source_visibility_preserved=lights.every(l=>l.visible);checks.original_lights_excluded_from_camera=lights.every(l=>!l.layers.test(new T.Layers()));
   const camera=new T.PerspectiveCamera(36,1.6,.1,4000);camera.position.set(0,120,200);camera.lookAt(0,20,0);camera.updateMatrixWorld();const target=new T.Vector3(0,20,0);
   budget.beforeFrame(1000,camera,target);checks.fixed_medium_light_budget=budget.pool.filter(l=>l.layers.mask===1).length===8;checks.light_range_preserves_original_units=budget.pool.filter(l=>l.layers.mask===1).every(l=>l.distance===16);checks.cheap_glass_only_inside_frame=mat.transmission===0&&mat.transparent;checks.static_world_matrices_shared=!scene.matrixWorldAutoUpdate;checks.subpixel_mesh_skipped=!tiny.visible;
   budget.afterFrame();checks.frame_restores_source_material=mat.transmission===.6&&!mat.transparent&&mat.opacity===1&&mat.depthWrite;checks.frame_restores_visibility=tiny.visible&&!manualHidden.visible;checks.world_update_policy_restored=scene.matrixWorldAutoUpdate;
   const json=await new GLTFExporter().parseAsync(root,{binary:false});checks.glb_keeps_original_glass=json.materials.some(m=>m.extensions?.KHR_materials_transmission?.transmissionFactor===.6);checks.glb_keeps_original_lights=json.extensions.KHR_lights_punctual.lights.length===48;
   state.quality='cinema';budget.beforeFrame(1300,camera,target);checks.cinema_light_budget=budget.pool.filter(l=>l.layers.mask===1).length===12;checks.cinema_idle_uses_full_glass=mat.transmission===.6;budget.afterFrame();camera.position.x+=1;budget.beforeFrame(1400,camera,target);checks.cinema_motion_uses_light_glass=mat.transmission===0;budget.afterFrame();
   state.quality='fast';budget.beforeFrame(1600,camera,target);checks.fast_light_budget=budget.pool.filter(l=>l.layers.mask===1).length===4;budget.afterFrame();
   state.quality='balanced';for(let now=2000;now<3000;now+=16){camera.position.x+=.2;budget.beforeFrame(now,camera,target);budget.afterFrame();}const movingRatio=ratio;budget.beforeFrame(3400,camera,target);budget.afterFrame();checks.sharpness_recovers_after_motion=ratio>movingRatio;
   budget.setEnabled(false);checks.legacy_switch_restores_all_lights=lights.every(l=>l.layers.mask===1)&&renderer.shadowMap.autoUpdate;budget.setEnabled(true);budget.dispose();checks.dispose_restores_scene=lights.every(l=>l.layers.mask===1)&&!scene.getObjectByName('Adaptive city lighting')&&mat.transmission===.6&&tiny.visible&&!manualHidden.visible;
   const river=createRiver({THREE:T,quality:'medium',coarse:true}),pass=createRiverPass({THREE:T,river});const waterScene=new T.Scene();waterScene.add(river.root);const waterCamera=new T.PerspectiveCamera(45,1.6,.1,2000);waterCamera.position.set(0,130,180);waterCamera.lookAt(0,-3.2,0);waterCamera.updateMatrixWorld();
   let calls=0,validState=true,current=null;const planes=[];const fake={clippingPlanes:planes,shadowMap:{autoUpdate:false,needsUpdate:true},xr:{enabled:true},getRenderTarget:()=>current,setRenderTarget:t=>current=t,clear(){},render(){calls++;validState&&=!this.shadowMap.autoUpdate&&!this.shadowMap.needsUpdate;}};
   const perFrame=[];for(let now=0;now<=1000;now+=16){waterCamera.position.x+=.1;waterCamera.lookAt(0,-3.2,0);pass.beforeRender(fake,waterScene,waterCamera,{optimized:true,moving:true,now});perFrame.push(pass.metrics.passesThisFrame)}
   checks.camera_motion_cannot_bypass_river_budget=calls<20&&calls>5;checks.expensive_water_passes_split=perFrame.slice(1).every(n=>n<=1)&&perFrame[0]===2;checks.shadow_updates_never_run_in_river=validState&&fake.shadowMap.needsUpdate&&fake.shadowMap.autoUpdate===false;checks.render_target_and_clip_restored=current===null&&fake.clippingPlanes===planes&&fake.xr.enabled;
   const before=calls;waterCamera.position.set(0,20,700);waterCamera.lookAt(0,20,1200);waterCamera.updateMatrixWorld();pass.beforeRender(fake,waterScene,waterCamera,{optimized:true,moving:true,now:2000});checks.offscreen_river_skipped=calls===before&&pass.metrics.passesThisFrame===0;
   river.root.visible=false;pass.beforeRender(fake,waterScene,waterCamera,{now:3000});checks.hidden_river_has_no_stale_pass_count=pass.metrics.passesThisFrame===0;river.root.visible=true;
   waterCamera.position.set(0,130,180);waterCamera.lookAt(0,-3.2,0);waterCamera.updateMatrixWorld();const legacyStart=calls;for(let n=0;n<12;n++){waterCamera.position.x++;pass.beforeRender(fake,waterScene,waterCamera,{optimized:false,now:4000+n*16});}checks.legacy_comparison_uses_original_updates=calls-legacyStart===24;
   pass.dispose();river.dispose();return{checks,legacy_gpu_passes_12_frames:calls-legacyStart,optimized_gpu_passes_1_second:perFrame.reduce((a,b)=>a+b,0),source_lights:48};
  }''')
  (OUT/'contracts.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True);b.close()
  if not all(result['checks'].values()):raise RuntimeError('Render budget contracts failed')
finally:fixture.unlink(missing_ok=True)
