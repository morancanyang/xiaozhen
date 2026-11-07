import * as THREE from 'three';
import {createQuietCityPark} from './forest-model.js';

export const FOREST_SITE=Object.freeze({blockId:'BLK-15',x:252,z:70,size:112,groundY:.16});

export function installForest(city){
  const site=FOREST_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
  if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-15 地块位置与森隐公园配置不一致');
  const landmark=createQuietCityPark({THREE,footprint:112,seed:71103,quality:'medium',includeLandscape:true});
  const id='SENYIN-PARK',record={id,name:'森隐公园',type:'森林公园 · 湖泊与林间小径',x:site.x,z:site.z,width:110,depth:110,height:18,floors:0,blockId:site.blockId,moduleId:'quiet-city-park',groundY:site.groundY};
  landmark.model.name=id;landmark.model.position.set(site.x,site.groundY,site.z);landmark.model.userData={...landmark.model.userData,...record,cityModule:true};
  city.root.add(landmark.model);city.groups.set(id,landmark.model);city.plan.buildings.push(record);Object.assign(block,{name:'森隐公园',type:'landmark',moduleId:'quiet-city-park'});
  // Extend the thin plaza down to the soil and fill its 1 m perimeter to the city's grade.
  const connections=new THREE.Group();connections.name='Forest_Plaza_Connections';connections.position.copy(landmark.model.position);connections.userData={moduleId:'quiet-city-park',blockId:site.blockId,cityModule:true};city.root.add(connections);
  const geo=new THREE.BoxGeometry(1,1,1),material=city.materials.paving.clone();material.name='Forest city sidewalk connection';
  const add=(name,x,y,z,w,h,d)=>{const object=new THREE.Mesh(geo,material);object.name=name;object.position.set(x,y,z);object.scale.set(w,h,d);object.receiveShadow=true;connections.add(object);};
  add('Forest foundation below basin',0,-2.7,0,112,.8,112);
  add('Forest west pedestrian seam',-55.5,-.07,0,1,.5,112);
  add('Forest east pedestrian seam',55.5,-.07,0,1,.5,112);
  add('Forest north pedestrian seam',0,-.07,-55.5,110,.5,1);
  add('Forest south pedestrian seam',0,-.07,55.5,110,.5,1);
  landmark.exportScene=()=>snapshot(landmark,connections,id);
  const dispose=landmark.dispose;landmark.dispose=()=>{city.groups.delete(id);geo.dispose();material.dispose();connections.removeFromParent();dispose();};
  city.root.updateMatrixWorld(true);return {landmark,site,block,connections,record};
}

function snapshot(landmark,connections,id){
  const geometries={},materials={},objects=[],matrix=new THREE.Matrix4();
  const visible=landmark.model.visible;landmark.model.visible=true;
  try{for(const root of [landmark.model,connections]){root.updateWorldMatrix(true,true);root.traverseVisible(object=>{
    if(!object.isMesh)return;const g=object.geometry,m=object.material;
    if(!geometries[g.uuid])geometries[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null,colors:g.attributes.color?Array.from(g.attributes.color.array):null};
    if(!materials[m.uuid])materials[m.uuid]={name:m.name||object.name,color:m.color.toArray(),roughness:m.roughness??.8,metalness:m.metalness??0,clearcoat:m.clearcoat??0,transmission:m.transmission??0,thickness:m.thickness??0,emissive:m.emissive?.toArray()||[0,0,0],emissiveIntensity:m.emissiveIntensity??0,opacity:m.opacity,transparent:m.transparent,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};
    for(let i=0;i<(object.isInstancedMesh?object.count:1);i++){const world=object.matrixWorld.clone();if(object.isInstancedMesh){object.getMatrixAt(i,matrix);world.multiply(matrix);}objects.push({g:g.uuid,m:m.uuid,matrix:world.toArray(),owner:id});}
  });}}finally{landmark.model.visible=visible;}
  return {format:'quiet-city-park-v1',snapshotSpace:'world',manifest:landmark.metadata,geometries,materials,objects};
}
