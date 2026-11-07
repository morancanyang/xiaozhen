import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
import {createMixedUseResidential} from './model.js';

const $=s=>document.querySelector(s),coarse=new URLSearchParams(location.search).has('coarse');
const state={paused:false,wind:true,windStrength:.45,speed:1,quality:'high',time:'day',nightFactor:0,view:'overview',doors:true};
let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});}catch(error){$('#load-message').textContent='无法启动 WebGL，请启用浏览器硬件加速。';throw error;}
renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,1.8));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.98;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;$('#viewport').appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color(0xffffff);
const perspective=new THREE.PerspectiveCamera(38,innerWidth/innerHeight,.12,3200),orthographic=new THREE.OrthographicCamera(-120,120,90,-90,.12,3200);let camera=orthographic;let controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.075;controls.minDistance=4;controls.maxDistance=650;controls.maxPolarAngle=Math.PI*.485;controls.minPolarAngle=.08;controls.screenSpacePanning=true;controls.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:THREE.MOUSE.PAN};
const hemi=new THREE.HemisphereLight(0xd9edf0,0xa6aa8f,1.4);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xfff0d4,3);sun.position.set(-80,115,100);sun.castShadow=true;sun.shadow.mapSize.set(4096,4096);Object.assign(sun.shadow.camera,{left:-115,right:115,top:115,bottom:-115,near:1,far:500});sun.shadow.camera.updateProjectionMatrix();sun.shadow.normalBias=.035;sun.shadow.bias=-.000045;sun.shadow.radius=2;scene.add(sun,sun.target);
const fill=new THREE.DirectionalLight(0xd0e6f4,.35);fill.position.set(70,40,-60);scene.add(fill);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(7000,7000),new THREE.ShadowMaterial({color:0x545043,opacity:.14}));ground.rotation.x=-Math.PI/2;ground.position.y=-.72;ground.receiveShadow=true;ground.name='Preview only / studio ground';scene.add(ground);

const skyUniforms={uTime:{value:0},uNight:{value:0},uWarm:{value:0},uSun:{value:sun.position.clone().normalize()}};
const skyMaterial=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms:skyUniforms,vertexShader:'varying vec3 vDirection;void main(){vDirection=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:`
varying vec3 vDirection;uniform float uTime,uNight,uWarm;uniform vec3 uSun;
float h(vec3 p){p=fract(p*.3183099+.1);p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}
float noise(vec3 p){vec3 a=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(mix(h(a),h(a+vec3(1,0,0)),f.x),mix(h(a+vec3(0,1,0)),h(a+vec3(1,1,0)),f.x),f.y),mix(mix(h(a+vec3(0,0,1)),h(a+vec3(1,0,1)),f.x),mix(h(a+vec3(0,1,1)),h(a+vec3(1,1,1)),f.x),f.y),f.z);}
void main(){vec3 d=normalize(vDirection);vec3 horizon=mix(vec3(.68,.79,.81),vec3(.90,.64,.43),uWarm),zenith=vec3(.26,.49,.66);vec3 col=mix(horizon,zenith,pow(max(d.y,0.),.5));
if(d.y>.025){float trans=1.;vec3 clouds=vec3(0.);for(int i=0;i<8;i++){float height=160.+float(i)*6.;vec3 p=d*height/max(d.y,.025);p.x+=uTime*.85;float n=noise(p*.006)*.65+noise(p*.012)*.25+noise(p*.024)*.1;float den=smoothstep(.55,.73,n)*sin(float(i)/8.*3.14159)*.18;clouds+=trans*den*mix(vec3(.66,.74,.77),vec3(1.,.98,.91),float(i)/8.);trans*=1.-den;}col=col*trans+clouds;}
col+=vec3(1.,.8,.57)*pow(max(dot(d,uSun),0.),100.)*.3;col=mix(col,vec3(.013,.024,.045)+col*.025,uNight);gl_FragColor=vec4(col,1.);
#include <tonemapping_fragment>
#include <colorspace_fragment>
}`});
const sky=new THREE.Mesh(new THREE.SphereGeometry(1800,24,12),skyMaterial);sky.name='Preview only / moving cloud sky';// Invisible lighting environment keeps the photography background white.
const probeScene=new THREE.Scene(),probeSky=new THREE.Mesh(sky.geometry,skyMaterial);probeScene.add(probeSky);
const pmrem=new THREE.PMREMGenerator(renderer);let environment=null,reflectionUpdates=0,environmentWait=0;
function refreshEnvironment(){const previous=environment;environment=pmrem.fromScene(probeScene,.025,.1,2500);scene.environment=environment.texture;scene.environmentIntensity=.4;previous?.dispose();reflectionUpdates++;}
refreshEnvironment();

let model;
try{model=createMixedUseResidential({THREE,footprint:112,quality:'high',seed:1104,coarse});scene.add(model.root);}catch(error){$('#load-message').textContent='模型构建失败：'+error.message;throw error;}

const views={side:{p:[150,38,24],q:[0,38,24]},lobby:{p:[12,6,61],q:[0,2.5,40]},overview:{p:[135,105,155],q:[0,30,12]},facade:{p:[0,38,180],q:[0,38,24]},entrance:{p:[-35,7.5,65],q:[-24,2.8,38]},roof:{p:[95,120,105],q:[0,69,24]}};
function view(name='overview'){
 controls.enableDamping=false;controls.update();const v=views[name]||views.overview;state.view=name;camera.position.fromArray(v.p);controls.target.fromArray(v.q);
 if(name==='overview'||name==='roof'||innerWidth<700&&name==='facade'){
  const box=model.getBounds(),sphere=box.getBoundingSphere(new THREE.Sphere()),half=THREE.MathUtils.degToRad(perspective.fov/2),angle=Math.min(half,Math.atan(Math.tan(half)*innerWidth/innerHeight));
  const fit=sphere.radius/Math.sin(angle)*(innerWidth<700?1.13:1.04);const offset=camera.position.clone().sub(controls.target).normalize().multiplyScalar(fit);camera.position.copy(controls.target).add(offset);
  // A modest lens shift gives the desktop introduction and controls breathing room.
  camera.filmOffset=innerWidth>1100&&name==='overview'?-2:0;
 }else camera.filmOffset=0;
 if(camera.isOrthographicCamera){const sphere=model.getBounds().getBoundingSphere(new THREE.Sphere()),aspect=innerWidth/innerHeight,h=name==='lobby'?7:name==='side'?48:name==='entrance'?8:name==='roof'?58:name==='facade'?48:sphere.radius*1.08;Object.assign(camera,{left:-h*aspect,right:h*aspect,top:h,bottom:-h,zoom:name==='overview'?Math.min(1,aspect):1});}camera.updateProjectionMatrix();controls.update();controls.enableDamping=true;$('.intro').classList.toggle('hidden',name!=='overview');document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
}
const presets={morning:{label:'07:30',description:'晨光 · 清晰长影',sun:[-100,65,110],color:0xffddb2,power:2.8,ambient:1.2,night:0,warm:.15,ground:0xdde0d1},day:{label:'10:30',description:'晴日 · 柔和阴影',sun:[-80,115,100],color:0xfff0d4,power:3,ambient:1.4,night:0,warm:0,ground:0xe0e3d8},evening:{label:'18:10',description:'暮色 · 窗里的暖光',sun:[-130,32,-40],color:0xffc080,power:1.8,ambient:.75,night:.48,warm:.9,ground:0xc7c9bd},night:{label:'20:30',description:'蓝调 · 万家灯火',sun:[-80,95,-100],color:0xa6c8f0,power:.24,ambient:.38,night:1,warm:0,ground:0x606f73}};
let lightTransition=null;
function setTime(name){const p=presets[name];if(!p)return;state.time=name;$('#time-label').textContent=p.label;$('#light-description').textContent=p.description;document.querySelectorAll('[data-time]').forEach(b=>b.classList.toggle('active',b.dataset.time===name));lightTransition={elapsed:0,from:{pos:sun.position.clone(),color:sun.color.clone(),power:sun.intensity,ambient:hemi.intensity,night:state.nightFactor,warm:skyUniforms.uWarm.value,ground:ground.material.color.clone()},to:p};}
function updateLight(dt){if(!lightTransition)return;const t=lightTransition;t.elapsed+=dt;const x=Math.min(1,t.elapsed/1.8),s=x*x*(3-2*x),a=t.from,b=t.to;sun.position.copy(a.pos).lerp(new THREE.Vector3(...b.sun),s);sun.color.copy(a.color).lerp(new THREE.Color(b.color),s);sun.intensity=THREE.MathUtils.lerp(a.power,b.power,s);hemi.intensity=THREE.MathUtils.lerp(a.ambient,b.ambient,s);state.nightFactor=THREE.MathUtils.lerp(a.night,b.night,s);skyUniforms.uNight.value=state.nightFactor;skyUniforms.uWarm.value=THREE.MathUtils.lerp(a.warm,b.warm,s);skyUniforms.uSun.value.copy(sun.position).normalize();ground.material.color.set(0x545043);model.setTimeOfDay(state.nightFactor);if(x===1){lightTransition=null;refreshEnvironment();}}

function toast(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').classList.remove('show'),3000);}
function download(blob,name){const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);}
async function exportGLB(){const data=await model.exportGLB({GLTFExporter});return data;}
$('#export').onclick=async()=>{try{toast('正在整理完整建筑模型…');const data=await exportGLB();download(new Blob([data],{type:'model/gltf-binary'}),'zongyu-mixeduse.glb');toast('完整住宅模型已导出');}catch(error){toast('导出失败：'+error.message);throw error;}};
$('#capture').onclick=()=>renderer.domElement.toBlob(blob=>{if(blob)download(blob,'棕屿里.png');});
$('#pause').onclick=()=>{state.paused=!state.paused;$('#pause').textContent=state.paused?'▷ 继续动态':'Ⅱ 暂停动态';};
$('#doors').onchange=e=>state.doors=e.target.checked;
$('#projection').onclick=()=>{const position=camera.position.clone(),target=controls.target.clone();controls.dispose();camera=camera.isOrthographicCamera?perspective:orthographic;camera.position.copy(position);controls=new OrbitControls(camera,renderer.domElement);controls.target.copy(target);controls.enableDamping=true;controls.minDistance=4;controls.maxDistance=650;controls.maxPolarAngle=Math.PI*.485;$('#projection').textContent=camera.isOrthographicCamera?'切换为透视观察 ↗':'切换为正交观察 ↗';view(state.view);};
$('#wind').onchange=e=>state.wind=e.target.checked;
$('#wind-strength').oninput=e=>{state.windStrength=+e.target.value;$('#wind-value').textContent=state.windStrength<.1?'无风':state.windStrength<.7?'轻风':'清风';};
$('#speed').oninput=e=>{state.speed=+e.target.value;$('#speed-value').textContent=state.speed.toFixed(2)+'×';};
$('#quality').onchange=e=>{const q=e.target.value;state.quality=q;model.setQuality(q);renderer.setPixelRatio(Math.min(devicePixelRatio,q==='high'?1.8:q==='medium'?1.4:1));const n=q==='high'?4096:q==='medium'?2048:1024;sun.shadow.mapSize.set(n,n);sun.shadow.map?.dispose();sun.shadow.map=null;renderer.setSize(innerWidth,innerHeight);};
$('#collapse').onclick=()=>{const hidden=!$('#panel-body').hidden;$('#panel-body').hidden=hidden;$('#collapse').textContent=hidden?'+':'−';$('#collapse').setAttribute('aria-expanded',String(!hidden));};
$('#reset').onclick=()=>view('overview');$('#brand-home').onclick=e=>{e.preventDefault();view('overview');};
$('#zoom-in').onclick=()=>{if(camera.isOrthographicCamera){camera.zoom*=1.2;camera.updateProjectionMatrix();return;}camera.position.sub(controls.target).multiplyScalar(.82).add(controls.target);controls.update();};$('#zoom-out').onclick=()=>{if(camera.isOrthographicCamera){camera.zoom/=1.2;camera.updateProjectionMatrix();return;}camera.position.sub(controls.target).multiplyScalar(1.2).add(controls.target);controls.update();};
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>setTime(b.dataset.time));
let narrowLayout=innerWidth<700;
addEventListener('resize',()=>{const narrow=innerWidth<700;if(narrow&&!narrowLayout){$('#panel-body').hidden=true;$('#collapse').textContent='+';$('#collapse').setAttribute('aria-expanded','false');}narrowLayout=narrow;camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);if(['overview','roof'].includes(state.view))view(state.view);});
let last=performance.now(),fpsStamp=last,frames=0,fps=0,sceneTime=0;
function tick(now){requestAnimationFrame(tick);const raw=Math.max(0,Math.min((now-last)/1000,.05));last=now;const dt=state.paused?0:raw*state.speed;sceneTime+=dt;updateLight(state.paused?0:raw);model.update(dt,{paused:state.paused,wind:state.wind,windStrength:state.windStrength,nightFactor:state.nightFactor,doors:state.doors});skyUniforms.uTime.value=sceneTime;environmentWait+=dt;if(environmentWait>10){environmentWait=0;refreshEnvironment();}controls.update();camera.position.y=Math.max(.7,camera.position.y);sky.position.copy(camera.position);renderer.render(scene,camera);frames++;if(now-fpsStamp>1000){fps=frames*1000/(now-fpsStamp);frames=0;fpsStamp=now;$('#stats').textContent=Math.round(fps)+' FPS · '+(renderer.info.render.triangles/1000).toFixed(0)+'k';}}
view('overview');if(innerWidth<700){$('#panel-body').hidden=true;$('#collapse').textContent='+';$('#collapse').setAttribute('aria-expanded','false');}
window.MixedUseResidentialModule={create:options=>createMixedUseResidential(options),version:'1.0.0',footprint:112};
window.mixedApp={THREE,model,renderer,scene,get camera(){return camera;},get controls(){return controls;},state,view,setTime,exportGLB,exportScene:()=>model.exportScene(),metrics:()=>({fps,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,reflectionUpdates}),ready:true};
$('#loading').remove();requestAnimationFrame(tick);
