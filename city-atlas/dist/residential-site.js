import * as THREE from 'three';
import {createResidential} from './residential-model.js';
export const RESIDENTIAL_SITE=Object.freeze({blockId:'BLK-5',x:-252,z:-210,size:112,groundY:.34});
export function installResidential(city){
 const site=RESIDENTIAL_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
 if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-5 位置与林序住区配置不一致');
 const model=createResidential({THREE,blockSize:112,quality:'medium'});model.root.position.set(site.x,site.groundY,site.z);model.root.name='LINXU-BLK-5';model.root.userData={moduleId:'linxu-residential',blockId:site.blockId,cityModule:true};city.root.add(model.root);
 const buildings=new Map(),records=[];
 for(const b of model.manifest.buildings){
  const id='LINXU-'+b.id,g=model.groups.get(b.id),wrapper=new THREE.Group();wrapper.name=id;wrapper.position.set(b.x,0,b.z);model.root.add(wrapper);model.root.updateWorldMatrix(true,true);wrapper.attach(g);
  const record={id,name:'林序住区 · '+b.name,type:'现代高层住宅',x:site.x+b.x,z:site.z+b.z,width:b.w+2,depth:b.d+4,height:b.height+3.45,floors:b.floors,groundY:site.groundY,blockId:site.blockId,moduleId:'linxu-residential',localId:b.id};
  wrapper.userData={...record};g.userData={...g.userData,id,component:b.id};city.groups.set(id,wrapper);buildings.set(id,wrapper);city.plan.buildings.push(record);records.push(record);
 }
 Object.assign(block,{type:'residential-complex',name:'林序住区',moduleId:'linxu-residential'});
 const connections=new THREE.Group();connections.name='Linxu road connections';model.root.add(connections);const gs=[],ms=[];
 const road=model.root.getObjectByName('site:asphalt:0').material.clone(),paving=city.materials.paving.clone();road.name='Linxu asphalt approach';paving.name='Linxu pedestrian approach';ms.push(road,paving);
 function grade(name,points,material){const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));geometry.setIndex([0,2,1,0,3,2]);geometry.computeVertexNormals();gs.push(geometry);const mesh=new THREE.Mesh(geometry,material);mesh.name=name;mesh.receiveShadow=true;connections.add(mesh);}
 const y=.085-site.groundY;
 grade('Linxu pedestrian entrance',[[-5,.252,56],[5,.252,56],[5,y,70],[-5,y,70]],paving);
 grade('Linxu vehicle entrance',[[43,.082,56],[49,.082,56],[49,y,70],[43,y,70]],road);
 grade('Linxu service entrance',[[-49,y,-70],[-43,y,-70],[-43,.082,-56],[-49,.082,-56]],road);
 const originalExport=model.exportScene;model.exportScene=(onlyId=null)=>{const visible=model.root.visible,quality=model.quality,states=[...buildings].map(([id,g])=>[id,g.visible]);model.root.visible=true;buildings.forEach(g=>g.visible=true);model.setQuality('high');try{const snapshot=originalExport();if(onlyId)snapshot.objects=snapshot.objects.filter(o=>o.owner===onlyId);return snapshot;}finally{model.root.visible=visible;model.setQuality(quality);states.forEach(([id,v])=>buildings.get(id).visible=v);}};
 const originalDispose=model.dispose;model.dispose=()=>{if(model.disposed)return;buildings.forEach((g,id)=>city.groups.delete(id));gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());originalDispose();};
 city.root.updateMatrixWorld(true);return {model,site,block,buildings,records,connections};
}
