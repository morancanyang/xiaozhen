import * as THREE from 'three';

/** Bound GPU work without changing source meshes, animation state or exported assets. */
export function createRenderBudget({scene,renderer,sun,state,bloom,ssao,onResolutionChange}){
 const sources=new Map(),glazing=new Map(),poolRoot=new THREE.Group();poolRoot.name='Adaptive city lighting';poolRoot.userData.performanceOnly=true;scene.add(poolRoot);
 const pool=Array.from({length:12},(_,i)=>{const l=new THREE.PointLight(0xffffff,0,16,2);l.name='City light budget '+i;l.castShadow=false;l.layers.set(31);poolRoot.add(l);return{light:l,source:null};});
 const position=new THREE.Vector3(),previousPosition=new THREE.Vector3(1e9,1e9,1e9),previousRotation=new THREE.Quaternion();
 let meshes=[],hidden=[],matrixPolicy=null,deferredShadow=false;
 const stats={frames:0,shadowUpdates:0,lightSources:0,activeLightBudget:8,moving:false,pixelRatio:renderer.getPixelRatio(),enabled:true,glazingMaterials:0,culledMeshes:0};
 const originalRatio=renderer.getPixelRatio(),originalTransmission=renderer.transmissionResolutionScale;
 let enabled=true,disposed=false,quality=state.quality,lastMotion=-1e6,lastShadow=-1e6,lastScan=-1e6,lastSelection=-1e6,lastResize=-1e6,lastTime=0,frameEMA=16.7,adaptiveScale=1,lastAdapt=0,forceShadow=true;
 const visible=o=>{if(!o?.parent)return false;for(let p=o;p;p=p.parent){if(!p.visible)return false;if(p===scene)return true}return false};
 function registerLights(){const found=new Set();meshes=[];scene.traverse(o=>{
  if(o.isMesh&&!o.isInstancedMesh&&!o.isSkinnedMesh&&!o.morphTargetInfluences?.length){if(!o.geometry.boundingSphere)o.geometry.computeBoundingSphere();meshes.push(o);}
  if(o.material)for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m.isMeshPhysicalMaterial&&m.transmission>0){found.add(m);if(!glazing.has(m))glazing.set(m,{applied:false,cheap:undefined});}
  if(!o.isPointLight||o.parent===poolRoot||sources.has(o))return;sources.set(o,{mask:o.layers.mask,position:new THREE.Vector3()});if(enabled)o.layers.set(31)
 });for(const [o,data] of sources){let attached=false;for(let p=o;p;p=p.parent)if(p===scene){attached=true;break}if(!attached){o.layers.mask=data.mask;sources.delete(o);}}for(const [m] of glazing)if(!found.has(m))glazing.delete(m);stats.lightSources=sources.size;stats.glazingMaterials=glazing.size;}
 function beforeGlazing(){const cheap=state.quality!=='cinema'||stats.moving;for(const [m,data] of glazing){
  if(data.cheap!==cheap){m.needsUpdate=true;data.cheap=cheap;}
  if(!cheap||m.transmission<=0)continue;
  data.transmission=m.transmission;data.transparent=m.transparent;data.opacity=m.opacity;data.depthWrite=m.depthWrite;data.forceSinglePass=m.forceSinglePass;data.applied=true;
  // Flat architectural glazing needs sky reflection and alpha transparency. Full
  // screen-space refraction is reserved for a stationary cinema view.
  m.transmission=0;m.transparent=true;m.opacity=Math.min(m.opacity,Math.max(.32,1-data.transmission*.6));m.depthWrite=false;m.forceSinglePass=true;
 }}
 function afterFrame(){for(const [m,data] of glazing)if(data.applied){m.transmission=data.transmission;m.transparent=data.transparent;m.opacity=data.opacity;m.depthWrite=data.depthWrite;m.forceSinglePass=data.forceSinglePass;data.applied=false;}for(const o of hidden)o.visible=true;hidden.length=0;if(matrixPolicy!==null){scene.matrixWorldAutoUpdate=matrixPolicy;matrixPolicy=null;}}
 function cacheFrame(camera){
  // All model animation has already run. Share these world matrices between the
  // main image, shadow map, river reflection and refraction for this frame.
  scene.updateMatrixWorld();camera.updateMatrixWorld();matrixPolicy=scene.matrixWorldAutoUpdate;scene.matrixWorldAutoUpdate=false;
  const focal=camera.isPerspectiveCamera?innerHeight*renderer.getPixelRatio()/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov*.5))):innerHeight*renderer.getPixelRatio()*camera.zoom/(camera.top-camera.bottom);
  const threshold=state.quality==='cinema'&&!stats.moving?.25:stats.moving?1.15:.65;
  for(const o of meshes){if(!visible(o))continue;const sphere=o.geometry.boundingSphere;if(!sphere)continue;const m=o.matrixWorld.elements;const s=Math.sqrt(Math.max(m[0]*m[0]+m[1]*m[1]+m[2]*m[2],m[4]*m[4]+m[5]*m[5]+m[6]*m[6],m[8]*m[8]+m[9]*m[9]+m[10]*m[10]));position.copy(sphere.center).applyMatrix4(o.matrixWorld).applyMatrix4(camera.matrixWorldInverse);const depth=Math.max(.1,-position.z),pixels=(sphere.radius*s*1.1+.03)*2*focal/(camera.isPerspectiveCamera?depth:1);if(pixels<threshold){o.visible=false;hidden.push(o);}}
  stats.culledMeshes=hidden.length;
 }
 function capacity(){return state.quality==='cinema'?12:state.quality==='fast'?4:8;}
 function configure(){quality=state.quality;const cap=capacity();stats.activeLightBudget=cap;pool.forEach(({light},i)=>light.layers.set(enabled&&i<cap?0:31));forceShadow=true;lastSelection=-1e6;}
 function restoreSources(){for(const [source,data] of sources)source.layers.mask=data.mask;}
 function updateLights(now,target,dt){
  if(now-lastScan>2000){registerLights();lastScan=now;}
  if(now-lastSelection>180){
   const current=new Set(pool.map(p=>p.source)),candidates=[];
   for(const [source,data] of sources){if(!visible(source))continue;source.updateWorldMatrix(true,false);source.getWorldPosition(data.position);const d=data.position;const score=(Math.hypot(d.x-target.x,d.z-target.z)+Math.abs(d.y-target.y)*.15)*(current.has(source)?.82:1);candidates.push({source,data,score})}
   candidates.sort((a,b)=>a.score-b.score);const chosen=candidates.slice(0,capacity()),chosenSet=new Set(chosen.map(c=>c.source));
   // Keep a fixture in the same slot whenever possible to avoid positional flashes.
   const kept=new Set(pool.slice(0,capacity()).filter(e=>e.source&&chosenSet.has(e.source)).map(e=>e.source));
   const remaining=chosen.filter(c=>!kept.has(c.source));
   pool.forEach((entry,i)=>{if(i>=capacity()){entry.source=null;entry.light.intensity=0;return}const keep=entry.source&&chosenSet.has(entry.source),next=keep?chosen.find(c=>c.source===entry.source):remaining.shift();if(!next){entry.source=null;entry.light.intensity=0;return}if(entry.source!==next.source)entry.light.intensity=0;entry.source=next.source;entry.light.position.copy(next.data.position);});
   lastSelection=now;
  }
  for(const entry of pool){const source=entry.source,l=entry.light;if(!source||!visible(source)){l.intensity=0;continue}l.color.copy(source.color);l.decay=source.decay;source.getWorldPosition(l.position);l.distance=source.distance;l.intensity=THREE.MathUtils.lerp(l.intensity,source.intensity,Math.min(1,dt*12));if(source.intensity===0)l.intensity=0;}
 }
 function setEnabled(value){if(disposed||enabled===!!value)return;afterFrame();enabled=!!value;stats.enabled=enabled;
  if(enabled){for(const [s] of sources)s.layers.set(31);renderer.shadowMap.autoUpdate=false;configure();}
  else{restoreSources();pool.forEach(({light})=>light.layers.set(31));renderer.shadowMap.autoUpdate=true;renderer.shadowMap.needsUpdate=true;renderer.transmissionResolutionScale=originalTransmission;renderer.setPixelRatio(originalRatio);onResolutionChange();bloom.enabled=state.quality!=='fast';ssao.enabled=state.quality==='cinema';}
 }
 function beforeFrame(now,camera,target){
  if(disposed)return;stats.frames++;if(!enabled)return;
  const dt=lastTime?Math.min(.1,(now-lastTime)/1000):1/60,elapsed=lastTime?now-lastTime:16.7;lastTime=now;
  if(elapsed<1000)frameEMA=frameEMA*.94+Math.min(elapsed,100)*.06;
  if(quality!==state.quality)configure();
  const changed=camera.position.distanceToSquared(previousPosition)>.0001||Math.abs(camera.quaternion.dot(previousRotation))<.9999999;
  previousPosition.copy(camera.position);previousRotation.copy(camera.quaternion);if(changed)lastMotion=now;
  stats.moving=now-lastMotion<220;
  if(now-lastAdapt>1500){if(frameEMA>28)adaptiveScale=Math.max(.65,adaptiveScale-.08);else if(frameEMA<19)adaptiveScale=Math.min(1,adaptiveScale+.04);lastAdapt=now;}
  const cap=state.quality==='cinema'?2:state.quality==='fast'?1:1.4,pixels=innerWidth*innerHeight,maxPixels=state.quality==='cinema'?6000000:state.quality==='fast'?1400000:2800000;
  const base=Math.min(devicePixelRatio,cap,Math.sqrt(maxPixels/pixels)),motion=stats.moving?(state.quality==='cinema'?.85:.75):1;
  const ratio=Math.max(.5,Math.round(base*(stats.moving?adaptiveScale:1)*motion*20)/20);
  if(Math.abs(renderer.getPixelRatio()-ratio)>.045&&now-lastResize>450){renderer.setPixelRatio(ratio);onResolutionChange();lastResize=now;}
  stats.pixelRatio=renderer.getPixelRatio();renderer.transmissionResolutionScale=state.quality==='cinema'?(stats.moving?.5:.75):state.quality==='fast'?.3:stats.moving?.35:.5;
  bloom.enabled=state.quality!=='fast'&&!stats.moving;ssao.enabled=state.quality==='cinema'&&!stats.moving;
  renderer.shadowMap.autoUpdate=false;const interval=state.quality==='cinema'?150:state.quality==='fast'?600:stats.moving?450:280;
  if(deferredShadow||forceShadow&&now-lastShadow>=80||now-lastShadow>=interval){renderer.shadowMap.needsUpdate=true;sun.shadow.needsUpdate=true;lastShadow=now;forceShadow=false;deferredShadow=false;stats.shadowUpdates++;}
  updateLights(now,target,dt);beforeGlazing();cacheFrame(camera);
 }
 function dispose(){if(disposed)return;afterFrame();setEnabled(false);disposed=true;restoreSources();poolRoot.removeFromParent();pool.forEach(({light})=>light.dispose());sources.clear();glazing.clear();}
 registerLights();configure();renderer.shadowMap.autoUpdate=false;
 return{beforeFrame,afterFrame,registerLights,setEnabled,markShadowDirty:()=>forceShadow=true,deferShadow(){if(enabled&&sun.shadow.map&&renderer.shadowMap.needsUpdate){renderer.shadowMap.needsUpdate=false;deferredShadow=true;stats.shadowUpdates--;}},dispose,get enabled(){return enabled},get moving(){return enabled&&stats.moving},get metrics(){return{...stats,frameEMA,adaptiveScale}},get pool(){return pool.map(p=>p.light)},get sources(){return [...sources.keys()]}};
}
