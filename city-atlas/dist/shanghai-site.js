import * as THREE from 'three';
import {createShanghaiTower} from './shanghai-model.js';

export const SHANGHAI_SITE=Object.freeze({blockId:'BLK-11',x:112,z:70,size:112,groundY:.3});

export function installShanghai(city){
  const site=SHANGHAI_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
  if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-11 地块位置与上海中心配置不一致');
  const landmark=createShanghaiTower({THREE,footprint:112,displayHeight:96,seed:632,quality:'medium',includeLandscape:true});
  const id='SHANGHAI-TOWER',record={id,name:'上海中心大厦',type:'螺旋超高层地标 · 双层玻璃幕墙',x:site.x,z:site.z,width:104,depth:104,height:96,floors:124,blockId:site.blockId,moduleId:'shanghai-tower',groundY:site.groundY,nominalHeight:632};
  landmark.model.name=id;landmark.model.position.set(site.x,site.groundY,site.z);landmark.model.userData={...landmark.model.userData,...record,cityModule:true};
  city.root.add(landmark.model);city.groups.set(id,landmark.model);city.plan.buildings.push(record);Object.assign(block,{name:'上海中心',type:'landmark',moduleId:'shanghai-tower'});
  // Extend the thin plaza down to the soil and fill its 4 m perimeter to the city's grade.
  const connections=new THREE.Group();connections.name='Shanghai_Plaza_Connections';connections.position.copy(landmark.model.position);connections.userData={moduleId:'shanghai-tower',blockId:site.blockId,cityModule:true};city.root.add(connections);
  const geo=new THREE.BoxGeometry(1,1,1),material=city.materials.paving.clone();material.name='Shanghai city sidewalk connection';
  const add=(name,x,y,z,w,h,d)=>{const object=new THREE.Mesh(geo,material);object.name=name;object.position.set(x,y,z);object.scale.set(w,h,d);object.receiveShadow=true;connections.add(object);};
  add('Shanghai foundation to soil',0,-.33,0,112,.3,112);
  add('Shanghai west pedestrian seam',-54,-.09,0,4,.18,112);
  add('Shanghai east pedestrian seam',54,-.09,0,4,.18,112);
  add('Shanghai north pedestrian seam',0,-.09,-54,104,.18,4);
  add('Shanghai south pedestrian seam',0,-.09,54,104,.18,4);
  landmark.exportScene=()=>snapshot(landmark,connections,id);
  const dispose=landmark.dispose;landmark.dispose=()=>{city.groups.delete(id);geo.dispose();material.dispose();connections.removeFromParent();dispose();};
  city.root.updateMatrixWorld(true);return {landmark,site,block,connections,record};
}

function snapshot(landmark,connections,id){
  const geometries={},materials={},objects=[],matrix=new THREE.Matrix4();
  const visible=landmark.model.visible;landmark.model.visible=true;
  try{for(const root of [landmark.model,connections]){root.updateWorldMatrix(true,true);root.traverseVisible(object=>{
    if(!object.isMesh)return;const g=object.geometry,m=object.material;
    if(!geometries[g.uuid])geometries[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null};
    if(!materials[m.uuid])materials[m.uuid]={name:m.name||object.name,color:m.color.toArray(),roughness:m.roughness??.8,metalness:m.metalness??0,emissive:m.emissive?.toArray()||[0,0,0],emissiveIntensity:m.emissiveIntensity??0,opacity:m.opacity,transparent:m.transparent,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};
    for(let i=0;i<(object.isInstancedMesh?object.count:1);i++){const world=object.matrixWorld.clone();if(object.isInstancedMesh){object.getMatrixAt(i,matrix);world.multiply(matrix);}objects.push({g:g.uuid,m:m.uuid,matrix:world.toArray(),owner:id});}
  });}}finally{landmark.model.visible=visible;}
  return {format:'shanghai-tower-v1',snapshotSpace:'world',manifest:landmark.metadata,geometries,materials,objects};
}
