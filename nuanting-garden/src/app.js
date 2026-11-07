import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {createGardenHousing} from './model.js';

const $=selector=>document.querySelector(selector);
const coarse=new URLSearchParams(location.search).has('coarse');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.9;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;$('#viewport').appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color(0xd8d8c6);scene.fog=new THREE.FogExp2(0xd8d8c6,.0007);
const camera=new THREE.PerspectiveCamera(43,innerWidth/innerHeight,.08,2200);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.065;
controls.minDistance=2;controls.maxDistance=900;controls.maxPolarAngle=Math.PI*.495;
const model=createGardenHousing({THREE,quality:'high',coarse});scene.add(model.root);
const buildings=model.buildings instanceof Map?model.buildings:new Map(model.manifest.buildings.map(b=>[b.id,model.groups.get(b.id)]));
const hemi=new THREE.HemisphereLight(0xdde6de,0x7d744e,1.15);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffdfad,2.5);sun.position.set(-100,90,100);sun.castShadow=true;
sun.shadow.mapSize.set(4096,4096);Object.assign(sun.shadow.camera,{left:-90,right:90,top:110,bottom:-110,near:1,far:500});
sun.shadow.camera.updateProjectionMatrix();sun.shadow.normalBias=.025;sun.shadow.bias=-.00008;scene.add(sun,sun.target);
const environment=new RoomEnvironment(),pmrem=new THREE.PMREMGenerator(renderer),env=pmrem.fromScene(environment,.04);
scene.environment=env.texture;scene.environmentIntensity=.35;environment.dispose();pmrem.dispose();
const sky=new THREE.Mesh(new THREE.SphereGeometry(1300,32,20),new THREE.ShaderMaterial({
 side:THREE.BackSide,uniforms:{time:{value:0},night:{value:0},warm:{value:.25}},
 vertexShader:'varying vec3 direction;void main(){direction=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
 fragmentShader:`varying vec3 direction;uniform float time,night,warm;float noise(vec2 p){return sin(p.x*.4+sin(p.y*.6))*cos(p.y*.3+sin(p.x*.4));}void main(){vec3 d=normalize(direction);vec3 c=mix(vec3(.83,.84,.75),vec3(.40,.61,.68),pow(max(d.y,0.),.55));c=mix(c,vec3(.91,.66,.42),warm*max(0.,1.-d.y)*.35);if(d.y>.02){vec2 p=d.xz/max(d.y,.035)*2.+vec2(time*.012,0.);float cloud=smoothstep(.12,.73,noise(p)+noise(p*2.1)*.3);c=mix(c,vec3(.96,.94,.84),cloud*.7);}c=mix(c,vec3(.018,.031,.052),night);gl_FragColor=vec4(c,1.);}`
}));sky.name='Presentation sky';scene.add(sky);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(4000,4000),new THREE.MeshStandardMaterial({color:0xd8d7c7,roughness:1}));
floor.name='Presentation ground outside export';floor.rotation.x=-Math.PI/2;floor.position.y=-.43;floor.receiveShadow=true;scene.add(floor);
const localLights=(model.manifest.lightFixtures||[]).map(f=>{
 const light=new THREE.PointLight(0xffce8f,0,f.distance||18,2);light.position.fromArray(f.position);light.name='Garden night light';scene.add(light);
 return {light,power:f.intensity??f.power??65};
});
const outline=new THREE.Box3Helper(new THREE.Box3(),0x96774f);outline.visible=false;scene.add(outline);
const views={
 overview:{p:[128,105,146],q:[0,5,0]},top:{p:[0,185,.01],q:[0,0,0]},
 entrance:{p:[20,9,76],q:[0,3,46]},garden:{p:[8,8,12],q:[0,2,-6]},
 roof:{p:[11,40,4],q:[-25,17,-25]},facade:{p:[-25,10,4],q:[-25,7,-25]}
};
const state={paused:false,speed:1,time:'afternoon',night:false,selected:null,isolated:null,wind:true,people:true,vehicles:true};
let currentView='overview',mobileLayout=innerWidth<700;
function fitParcel(preset){
 const sphere=new THREE.Box3().setFromObject(model.root).getBoundingSphere(new THREE.Sphere());
 const vertical=THREE.MathUtils.degToRad(camera.fov/2),angle=Math.min(vertical,Math.atan(Math.tan(vertical)*camera.aspect));
 const direction=new THREE.Vector3(...preset.p).sub(new THREE.Vector3(...preset.q)).normalize();
 controls.target.copy(sphere.center);camera.position.copy(sphere.center).add(direction.multiplyScalar(sphere.radius/Math.sin(angle)*1.07));
}
for(const b of model.manifest.buildings){const option=document.createElement('option');option.value=b.id;option.textContent=`${b.id} 栋 · ${b.floors} 层`;$('#building').appendChild(option);}
function showAll(){buildings.forEach(g=>g.visible=true);state.isolated=null;}
function select(id=null){
 const record=model.manifest.buildings.find(b=>b.id===id),group=buildings.get(id);
 state.selected=record?.id||null;$('#building').value=state.selected||'';
 $('#inspect').disabled=!record;$('#export-selected').disabled=!record;
 $('#selection-note').textContent=record?`${record.id} 栋 / ${record.floors} 层 · ${record.height.toFixed(1)} m`:'轻触建筑，查看一栋家的细节';
 outline.visible=!!group;if(group)outline.box.setFromObject(group);
 return group;
}
function frameBuilding(id){
 const group=buildings.get(id);if(!group)return;
 buildings.forEach((g,key)=>g.visible=key===id);state.isolated=id;select(id);
 const bounds=new THREE.Box3().setFromObject(group),center=bounds.getCenter(new THREE.Vector3()),radius=bounds.getBoundingSphere(new THREE.Sphere()).radius;
 const vertical=THREE.MathUtils.degToRad(camera.fov/2),angle=Math.min(vertical,Math.atan(Math.tan(vertical)*camera.aspect));
 camera.position.copy(center).add(new THREE.Vector3(1,.65,1.2).normalize().multiplyScalar(radius/Math.sin(angle)*1.13));controls.target.copy(center);
}
function view(name='overview'){
 currentView=name;
 if(buildings.has(name))frameBuilding(name);else{
  showAll();const preset=views[name]||views.overview;camera.position.fromArray(preset.p);controls.target.fromArray(preset.q);
  if(innerWidth<700&&['overview','top'].includes(name))fitParcel(preset);
  select(null);
 }
 controls.update();$('.intro').classList.toggle('hidden',name!=='overview');
 document.querySelectorAll('[data-view]').forEach(button=>button.classList.toggle('active',button.dataset.view===name));
 return name;
}
document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>view(button.dataset.view));
$('#building').onchange=e=>{showAll();select(e.target.value||null);};
$('#inspect').onclick=()=>state.selected&&view(state.selected);
$('#reset').onclick=()=>view('overview');
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let pointerDown={x:0,y:0};
renderer.domElement.addEventListener('pointerdown',event=>pointerDown={x:event.clientX,y:event.clientY});
renderer.domElement.addEventListener('click',event=>{
 if(Math.hypot(event.clientX-pointerDown.x,event.clientY-pointerDown.y)>5)return;
 pointer.set(event.clientX/innerWidth*2-1,-event.clientY/innerHeight*2+1);raycaster.setFromCamera(pointer,camera);
 const hit=raycaster.intersectObjects([...buildings.values()].filter(g=>g.visible),true)[0];if(!hit){select(null);return;}
 let object=hit.object;while(object&&!([...buildings.values()].includes(object)))object=object.parent;
 const id=[...buildings].find(([,group])=>group===object)?.[0];if(id)select(id);
});
$('#pause').onclick=()=>{state.paused=!state.paused;model.setDynamicsEnabled(!state.paused);$('#pause').textContent=state.paused?'继续日常':'暂停日常';$('#pause').setAttribute('aria-pressed',String(state.paused));};
$('#speed').oninput=e=>{state.speed=+e.target.value;$('#speed-value').textContent=state.speed.toFixed(2)+'×';};
for(const id of ['wind','people','vehicles'])$('#'+id).onchange=e=>{state[id]=e.target.checked;model.setActivity({[id]:e.target.checked});};
$('#quality').onchange=e=>{
 const quality=e.target.value;model.setQuality(quality);renderer.setPixelRatio(Math.min(devicePixelRatio,quality==='low'?1:1.5));
 sun.shadow.mapSize.set(quality==='high'?4096:quality==='medium'?3072:2048,quality==='high'?4096:quality==='medium'?3072:2048);
 if(sun.shadow.map){sun.shadow.map.dispose();sun.shadow.map=null;}
 renderer.setSize(innerWidth,innerHeight);
};
const timePresets={
 afternoon:{night:0,color:0xffdfad,sun:2.5,hemi:1.15,env:.35,sky:0xd8d8c6,ground:0xd8d7c7,position:[-100,90,100],warm:.25,exposure:.9,clock:'15:30'},
 evening:{night:.4,color:0xffb57a,sun:1.8,hemi:.7,env:.2,sky:0xc4b49f,ground:0xb3aa93,position:[-150,45,-70],warm:1,exposure:.95,clock:'17:40'},
 night:{night:1,color:0xa5c6df,sun:.08,hemi:.17,env:.035,sky:0x233341,ground:0x59625b,position:[-100,180,100],warm:0,exposure:1,clock:'20:30'}
};
function setTime(name){
 const preset=timePresets[name]||timePresets.afternoon;state.time=name;state.night=preset.night===1;
 sun.color.setHex(preset.color);sun.intensity=preset.sun;sun.position.fromArray(preset.position);hemi.intensity=preset.hemi;
 scene.environmentIntensity=preset.env;scene.fog.color.setHex(preset.sky);scene.background.copy(scene.fog.color);floor.material.color.setHex(preset.ground);
 renderer.toneMappingExposure=preset.exposure;sky.material.uniforms.night.value=preset.night;sky.material.uniforms.warm.value=preset.warm;
 localLights.forEach(({light,power})=>light.intensity=power*preset.night);model.setTimeOfDay(preset.night);
 $('#clock').textContent=preset.clock;$('#time').value=name;document.body.classList.toggle('night',preset.night>.7);
}
$('#time').onchange=e=>setTime(e.target.value);
function download(blob,name){const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),5000);}
async function exportGLB(onlyId=null){
 const selected=typeof onlyId==='string'?buildings.get(onlyId):null;let copy;
 if(selected){copy=selected.clone(true);copy.position.set(0,0,0);}else{
  const visibility=[...buildings].map(([id,g])=>[id,g.visible]),quality=model.quality,visible=model.root.visible;
  try{buildings.forEach(g=>g.visible=true);model.root.visible=true;model.setQuality('high');copy=model.root.clone(true);}
  finally{visibility.forEach(([id,v])=>buildings.get(id).visible=v);model.setQuality(quality);model.root.visible=visible;}
 }
 try{copy.updateMatrixWorld(true);const binary=await new GLTFExporter().parseAsync(copy,{binary:true});download(new Blob([binary]),selected?`nuanting-${onlyId}.glb`:'nuanting-garden-housing.glb');}
 catch(error){$('#selection-note').textContent='导出失败：'+error.message;throw error;}
}
$('#export').onclick=()=>exportGLB();$('#export-selected').onclick=()=>state.selected&&exportGLB(state.selected);
$('#capture').onclick=()=>{renderer.render(scene,camera);renderer.domElement.toBlob(blob=>blob&&download(blob,'暖庭花园.png'));};
$('#collapse').onclick=()=>{const hidden=!$('#panel-body').hidden;$('#panel-body').hidden=hidden;$('#collapse').setAttribute('aria-expanded',String(!hidden));$('#collapse-icon').textContent=hidden?'+':'−';};
window.addEventListener('resize',()=>{
 camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);
 const mobile=innerWidth<700;
 if(mobile&&!mobileLayout){$('#panel-body').hidden=true;$('#collapse').setAttribute('aria-expanded','false');$('#collapse-icon').textContent='+';}
 if(mobile&&['overview','top'].includes(currentView)){fitParcel(views[currentView]);controls.update();}
 mobileLayout=mobile;
});
let last=performance.now(),frames=0,fps=0,stamp=last,cloudTime=0;
function tick(now){
 requestAnimationFrame(tick);const delta=Math.min(.08,Math.max(0,(now-last)/1000));last=now;model.update(delta*state.speed);
 if(state.wind&&!state.paused)cloudTime+=delta*state.speed;sky.material.uniforms.time.value=cloudTime;controls.update();camera.updateMatrixWorld();sky.position.copy(camera.position);renderer.render(scene,camera);
 frames++;if(now-stamp>1000){fps=frames*1000/(now-stamp);stamp=now;frames=0;$('#stats').textContent=Math.round(fps)+' FPS';}
}
view('overview');setTime('afternoon');
window.GardenHousingModule={create:createGardenHousing};
window.gardenApp={THREE,model,renderer,scene,camera,controls,state,views,view,select,setTime,exportGLB,exportScene:()=>model.exportScene(),ready:true,metrics:()=>({fps,triangles:renderer.info.render.triangles,calls:renderer.info.render.calls})};
if(innerWidth<700){$('#panel-body').hidden=true;$('#collapse').setAttribute('aria-expanded','false');$('#collapse-icon').textContent='+';}
$('#loading').remove();requestAnimationFrame(tick);
