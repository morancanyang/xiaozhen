import * as THREE from 'three';
import {createUniversityCampus} from './university-model.js';

export const UNIVERSITY_SITE=Object.freeze({blockId:'BLK-8',x:-252,z:210,size:112,groundY:.32});

export function installUniversity(city){
  const site=UNIVERSITY_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
  if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-8 地块位置与大学校园配置不一致');
  const landmark=createUniversityCampus({THREE,footprint:112,seed:2026,quality:'medium',includeLandscape:true});
  const id='UNIVERSITY-CAMPUS',record={id,name:'大学主教学楼',type:'现代大学主楼 · 升旗广场',x:site.x,z:site.z,width:110,depth:110,height:28.5325,floors:7,blockId:site.blockId,moduleId:'university-campus',groundY:site.groundY};
  landmark.model.name=id;landmark.model.position.set(site.x,site.groundY,site.z);landmark.model.userData={...landmark.model.userData,...record,cityModule:true};
  city.root.add(landmark.model);city.groups.set(id,landmark.model);city.plan.buildings.push(record);Object.assign(block,{name:'大学校园',type:'landmark',moduleId:'university-campus'});
  // Extend the thin plaza down to the soil and fill its 1 m perimeter to the city's grade.
  const connections=new THREE.Group();connections.name='University_Plaza_Connections';connections.position.copy(landmark.model.position);connections.userData={moduleId:'university-campus',blockId:site.blockId,cityModule:true};city.root.add(connections);
  const geo=new THREE.BoxGeometry(1,1,1),material=city.materials.paving.clone();material.name='University city sidewalk connection';
  const add=(name,x,y,z,w,h,d)=>{const object=new THREE.Mesh(geo,material);object.name=name;object.position.set(x,y,z);object.scale.set(w,h,d);object.receiveShadow=true;connections.add(object);};
  add('University foundation to soil',0,-.385,0,112,.17,112);
  add('University west pedestrian seam',-55.5,-.07,0,1,.18,112);
  add('University east pedestrian seam',55.5,-.07,0,1,.18,112);
  add('University north pedestrian seam',0,-.07,-55.5,110,.18,1);
  add('University south pedestrian seam',0,-.07,55.5,110,.18,1);
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
    if(!materials[m.uuid])materials[m.uuid]={name:m.name||object.name,color:m.color.toArray(),roughness:m.roughness??.8,metalness:m.metalness??0,clearcoat:m.clearcoat??0,emissive:m.emissive?.toArray()||[0,0,0],emissiveIntensity:m.emissiveIntensity??0,opacity:m.opacity,transparent:m.transparent,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};
    for(let i=0;i<(object.isInstancedMesh?object.count:1);i++){const world=object.matrixWorld.clone();if(object.isInstancedMesh){object.getMatrixAt(i,matrix);world.multiply(matrix);}objects.push({g:g.uuid,m:m.uuid,matrix:world.toArray(),owner:id});}
  });}}finally{landmark.model.visible=visible;}
  return {format:'university-campus-v1',snapshotSpace:'world',manifest:landmark.metadata,geometries,materials,objects};
}
