import * as THREE from 'three';
import {createMallComplex} from './mall-model.js';

// Eastern bank, inner column, second row from the north. The public front is +Z.
export const MALL_SITE=Object.freeze({blockId:'BLK-10',x:112,z:-70,size:112,groundY:.34,rotation:0});
export function installMall(city){
  const site=MALL_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
  if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-10 地块位置与商城接入配置不一致');
  const mall=createMallComplex({THREE,footprint:site.size,quality:'medium',seed:2026,includeLandscape:true});
  mall.model.position.set(site.x,site.groundY,site.z);mall.model.rotation.y=site.rotation;
  const id='MALL-TAOLI',record={id,name:'陶里汇 · TAOLI GALLERIA',type:'商城综合体 · 退台花园与玻璃中庭',x:site.x,z:site.z,width:112,depth:112,height:mall.metadata.displayHeight,floors:6,blockId:site.blockId,moduleId:'mall-complex',groundY:site.groundY};
  mall.model.name=id;mall.model.userData={...mall.model.userData,...record,cityModule:true};city.root.add(mall.model);city.groups.set(id,mall.model);city.plan.buildings.push(record);Object.assign(block,{name:'陶里汇商城',type:'shopping-mall',moduleId:'mall-complex'});
  // Fill the thin display foundation down to the existing asphalt; the finished
  // plaza surface remains at the same .34 m height as the town's other sidewalks.
  const foundationGeometry=new THREE.BoxGeometry(111.6,.12,111.6),paving=mall.materials['Silver grey granite'];
  const foundation=new THREE.Mesh(foundationGeometry,paving);foundation.name='Mall_foundation_to_city_grade';foundation.position.y=-.24;foundation.receiveShadow=true;mall.model.add(foundation);
  const connections=new THREE.Group();connections.name='Mall_public_pedestrian_connection';connections.position.copy(mall.model.position);connections.rotation.copy(mall.model.rotation);connections.userData={moduleId:'mall-complex',blockId:site.blockId,cityModule:true};city.root.add(connections);
  const connectionGeometry=new THREE.BufferGeometry();connectionGeometry.setAttribute('position',new THREE.Float32BufferAttribute([-6,.002,55.8,6,.002,55.8,6,.08-site.groundY,61,-6,.08-site.groundY,61],3));connectionGeometry.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));connectionGeometry.setIndex([0,2,1,0,3,2]);connectionGeometry.computeVertexNormals();const ramp=new THREE.Mesh(connectionGeometry,paving);ramp.name='Mall_gently_graded_public_approach';ramp.receiveShadow=true;connections.add(ramp);
  // Medium/low use inexpensive alpha glazing instead of a second city-wide
  // transmission render. Keep the shop interiors visible at those quality levels.
  const originalQuality=mall.setQuality;mall.setQuality=value=>{originalQuality(value);const glass=mall.materials['Shop glazing'];glass.opacity=value==='high'?.91:.53;glass.color.setHex(value==='high'?0x9eb9b8:0x708f8e);glass.needsUpdate=true;return value;};mall.setQuality('medium');
  mall.exportScene=()=>{const visible=mall.model.visible;mall.model.visible=true;try{return snapshot([mall.model,connections],mall.metadata,id);}finally{mall.model.visible=visible;}};
  const originalDispose=mall.dispose;let disposed=false;mall.dispose=()=>{if(disposed)return;disposed=true;connections.removeFromParent();foundationGeometry.dispose();connectionGeometry.dispose();originalDispose();};
  city.root.updateMatrixWorld(true);return{mall,site,block,building:mall.model,connections};
}

function snapshot(roots,metadata,owner){
  const geometries={},materials={},objects=[],local=new THREE.Matrix4(),world=new THREE.Matrix4();
  for(const root of roots){root.updateMatrixWorld(true);root.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry,m=o.material;if(!geometries[g.uuid])geometries[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null};if(!materials[m.uuid])materials[m.uuid]={name:m.name,color:m.color.toArray(),roughness:m.roughness??.8,metalness:m.metalness??0,opacity:m.opacity,transparent:m.transparent,emissive:m.emissive?.toArray()||[0,0,0],emissiveIntensity:m.emissiveIntensity||0,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,local);world.multiplyMatrices(o.matrixWorld,local);}else world.copy(o.matrixWorld);objects.push({g:g.uuid,m:m.uuid,matrix:world.toArray(),owner});}});}
  return{format:'taoli-galleria-v1',snapshotSpace:'world',metadata,geometries,materials,objects};
}
