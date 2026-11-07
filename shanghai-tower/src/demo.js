import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const frame=document.createElement('iframe');frame.hidden=true;frame.src='./上海中心.html?mode=asset';document.body.appendChild(frame);
frame.addEventListener('load',()=>{
  try{
    const factory=frame.contentWindow.QianrenLandmarks?.createShanghaiTower;
    if(!factory)throw new Error('Model interface not available. Serve both HTML files from the same local HTTP origin.');
    const landmark=factory({THREE,footprint:112,displayHeight:96,quality:'high',seed:632});
    const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.toneMapping=THREE.ACESFilmicToneMapping;document.body.prepend(renderer.domElement);
    const scene=new THREE.Scene();scene.background=new THREE.Color(0xd9e3e6);scene.add(new THREE.HemisphereLight(0xe2edf4,0x7e8c7c,2));const sun=new THREE.DirectionalLight(0xffe5bd,3);sun.position.set(-50,100,70);scene.add(sun);
    const cityRoot=new THREE.Group();scene.add(cityRoot);landmark.model.position.set(112,.34,-70);cityRoot.add(landmark.model);
    const camera=new THREE.PerspectiveCamera(40,innerWidth/innerHeight,1,2000);camera.position.set(260,140,110);const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(112,38,-70);controls.enableDamping=true;
    const ground=new THREE.Mesh(new THREE.PlaneGeometry(400,300),new THREE.MeshStandardMaterial({color:0xb5c2bd}));ground.rotation.x=-Math.PI/2;ground.position.set(112,0,-70);scene.add(ground);
    const result={sameTHREE:landmark.model instanceof THREE.Group,hostGroundY:landmark.model.position.y,displayHeight:landmark.metadata.displayHeight,modelHasCamera:false,modelHasLight:false};landmark.model.traverse(o=>{if(o.isCamera)result.modelHasCamera=true;if(o.isLight)result.modelHasLight=true;});
    document.getElementById('status').textContent='同源接口已接入 · 宿主 THREE · 单一渲染循环 · 建筑与广场独立';
    window.integrationDemo={landmark,scene,renderer,result,frame};let last=performance.now(),time=0;
    function tick(now){requestAnimationFrame(tick);const dt=Math.min(.05,(now-last)/1000);last=now;time+=dt;landmark.update(dt,{time,nightFactor:.2,cameraDistance:camera.position.distanceTo(controls.target)});controls.update();renderer.render(scene,camera);}requestAnimationFrame(tick);
    window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
  }catch(e){document.getElementById('status').textContent=e.message;console.error(e);}
});
