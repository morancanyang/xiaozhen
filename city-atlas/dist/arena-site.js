import * as THREE from 'three';
import {createArenaComplex} from './arena-model.js';

// Western bank, inner column, southernmost row. Front entrance faces +Z.
export const ARENA_SITE=Object.freeze({blockId:'BLK-4',x:-112,z:210,size:112,groundY:.22,rotation:0});

export function installArena(city){
  const site=ARENA_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
  if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-4 地块位置与体育馆配置不一致');
  const arena=createArenaComplex({THREE,blockSize:site.size,quality:'medium',embedded:true});
  const id='ARENA-DOME',record={id,name:'穹光体育中心',type:'公共综合体育馆 · 银蓝穹顶',x:site.x,z:site.z,width:112,depth:112,height:arena.manifest.height,floors:3,blockId:site.blockId,moduleId:'dome-arena',groundY:site.groundY};
  arena.root.name=id;arena.root.position.set(site.x,site.groundY,site.z);arena.root.rotation.y=site.rotation;arena.root.userData={...record,cityModule:true};
  arena.groups.forEach((g,component)=>g.userData={...g.userData,id,component,moduleId:'dome-arena'});
  city.root.add(arena.root);city.groups.set(id,arena.root);city.plan.buildings.push(record);
  Object.assign(block,{name:'穹光体育中心',type:'sports-center',moduleId:'dome-arena'});
  const connections=new THREE.Group();connections.name='Arena road connections';arena.root.add(connections);
  const geometries=[],materials=[];
  const road=arena.root.getObjectByName('site:asphalt:L0').material.clone();road.name='Arena road access';materials.push(road);
  const paving=city.materials.paving.clone();paving.name='Arena public approach';materials.push(paving);
  function grade(name,points,material){
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));g.setIndex([0,2,1,0,3,2]);g.computeVertexNormals();geometries.push(g);
    const mesh=new THREE.Mesh(g,material);mesh.name=name;mesh.receiveShadow=true;connections.add(mesh);
  }
  const roadY=.085-site.groundY;
  grade('Arena public entrance connection',[[-7,.002,56],[7,.002,56],[7,roadY,70],[-7,roadY,70]],paving);
  grade('Arena dropoff road connection',[[47,.162,34],[70,roadY,34],[70,roadY,40],[47,.162,40]],road);
  grade('Arena service road connection',[[-70,roadY,-38],[-47,.162,-38],[-47,.162,-32],[-70,roadY,-32]],road);
  const lighting=new THREE.Group();lighting.name='Arena city lighting';arena.root.add(lighting);
  const spots=arena.manifest.lightFixtures.map(f=>{const light=new THREE.SpotLight(0xcbe9ff,0,150,.58,.65,2);light.position.fromArray(f.position);light.target.position.fromArray(f.target);light.castShadow=false;lighting.add(light,light.target);return light;});
  const entryLights=[-12,0,12].map(x=>{const light=new THREE.PointLight(0xffce89,0,28,2);light.position.set(x,4,31);lighting.add(light);return light;});
  const setNight=arena.setTimeOfDay;arena.setTimeOfDay=value=>{setNight(value);const n=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.4:0;spots.forEach(l=>l.intensity=2200*n);entryLights.forEach(l=>l.intensity=170*n);};
  const exportScene=arena.exportScene;arena.exportScene=()=>{
    const visible=arena.root.visible,quality=arena.quality,roof=arena.roofVisible;
    arena.root.visible=true;arena.setQuality('high');arena.setRoofVisible(true);
    try{return exportScene();}finally{arena.root.visible=visible;arena.setQuality(quality);arena.setRoofVisible(roof);}
  };
  const dispose=arena.dispose;arena.dispose=()=>{if(arena.disposed)return;geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());spots.forEach(l=>l.shadow.dispose());city.groups.delete(id);dispose();};
  city.root.updateMatrixWorld(true);return {arena,site,block,record,connections,lighting};
}
