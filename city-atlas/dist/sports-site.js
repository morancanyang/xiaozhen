import * as THREE from 'three';
import {createSportsField} from './sports-model.js';

export const SPORTS_SITE=Object.freeze({blockId:'BLK-7',x:-252,z:70,size:112,groundY:.34});

export function installSports(city){
  const site=SPORTS_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
  if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-7 位置与青禾运动场配置不一致');
  const model=createSportsField({THREE,blockSize:site.size,quality:'medium'});
  const id='QINGHE-SPORTS',record={id,name:'青禾运动场',type:'社区田径跑道 · 足球场',x:site.x,z:site.z,width:112,depth:112,height:14.1,floors:0,groundY:site.groundY,blockId:site.blockId,moduleId:'qinghe-sports-field'};
  model.root.name=id;model.root.position.set(site.x,site.groundY,site.z);model.root.userData={...record,cityModule:true};
  model.groups.forEach((g,component)=>g.userData={...g.userData,id,component,moduleId:record.moduleId});
  city.root.add(model.root);city.groups.set(id,model.root);city.plan.buildings.push(record);
  Object.assign(block,{name:record.name,type:'sports-field',moduleId:record.moduleId});

  const connections=new THREE.Group();connections.name='Qinghe road connections';connections.userData={id,component:'connections'};model.root.add(connections);
  const paving=city.materials.paving.clone();paving.name='Qinghe city pedestrian connection';
  const geometries=[];
  function grade(name,x,width,side){
    const a=x-width/2,b=x+width/2,inner=side*56,outer=side*70,y=.085-site.groundY;
    const points=side>0?[[a,.006,inner],[b,.006,inner],[b,y,outer],[a,y,outer]]:[[a,y,outer],[b,y,outer],[b,.006,inner],[a,.006,inner]];
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));g.setIndex([0,2,1,0,3,2]);g.computeVertexNormals();geometries.push(g);
    const mesh=new THREE.Mesh(g,paving);mesh.name=name;mesh.receiveShadow=true;connections.add(mesh);
  }
  grade('Qinghe public road connection',40,6,1);
  grade('Qinghe service road connection',-40,5,-1);

  const lighting=new THREE.Group();lighting.name='Qinghe city lighting';model.root.add(lighting);
  const spots=model.manifest.lightFixtures.map(f=>{
    const light=new THREE.SpotLight(0xffedcf,0,130,.65,.65,2);light.position.fromArray(f.position);light.target.position.fromArray(f.target);light.castShadow=false;lighting.add(light,light.target);return light;
  });
  const setTimeOfDay=model.setTimeOfDay;
  model.setTimeOfDay=value=>{const n=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:0;setTimeOfDay(n);spots.forEach(l=>l.intensity=3600*n);};

  // Export the complete parcel even when city architecture view hides this root.
  const exportScene=model.exportScene;
  model.exportScene=()=>{const visible=model.root.visible,quality=model.quality;model.root.visible=true;model.setQuality('high');try{return exportScene();}finally{model.root.visible=visible;model.setQuality(quality);}};
  const dispose=model.dispose;
  model.dispose=()=>{if(model.disposed)return;city.groups.delete(id);geometries.forEach(g=>g.dispose());paving.dispose();spots.forEach(l=>l.dispose());dispose();};
  city.root.updateMatrixWorld(true);
  return {model,site,block,record,connections,lighting,spots};
}
