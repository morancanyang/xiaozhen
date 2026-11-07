import * as THREE from 'three';
import {createGardenHousing} from './garden-model.js';

export const GARDEN_SITE=Object.freeze({blockId:'BLK-6',x:-252,z:-70,size:112,groundY:.34});

/** Mount the garden parcel into the city's existing renderer, lights and frame loop. */
export function installGarden(city){
  const site=GARDEN_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
  if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-6 位置与暖庭花园配置不一致');
  for(const letter of ['A','B','C','D'])if(city.groups.has('NUANTING-'+letter))throw new Error('暖庭花园已安装');
  const previousBlock={...block};
  const model=createGardenHousing({THREE,blockSize:site.size,quality:'medium'});
  model.root.position.set(site.x,site.groundY,site.z);
  model.root.name='NUANTING-BLK-6';
  model.root.userData={moduleId:'nuanting-garden-housing',blockId:site.blockId,cityModule:true};
  city.root.add(model.root);

  const buildings=new Map(),records=[];
  for(const b of model.manifest.buildings){
    const id='NUANTING-'+b.id,group=model.buildings.get(b.id);
    const record={id,name:'暖庭花园 · '+b.name,type:'花园洋房 · 真石漆与坡屋顶',x:site.x+b.x,z:site.z+b.z,width:28,depth:23,height:b.height,floors:b.floors,groundY:site.groundY,blockId:site.blockId,moduleId:'nuanting-garden-housing',localId:b.id};
    group.name=id;group.userData={...group.userData,...record,component:b.id};
    city.groups.set(id,group);buildings.set(id,group);city.plan.buildings.push(record);records.push(record);
  }
  Object.assign(block,{type:'garden-residential-complex',name:'暖庭花园',moduleId:'nuanting-garden-housing'});

  const connections=new THREE.Group();connections.name='Nuanting road connections';model.root.add(connections);
  const geometries=[],materials=[];
  const road=model.root.getObjectByName('site:asphalt:0').material.clone();road.name='Nuanting asphalt road approach';
  const paving=city.materials.paving.clone();paving.name='Nuanting city pedestrian approach';materials.push(road,paving);
  function grade(name,points,material){
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));geometry.setIndex([0,2,1,0,3,2]);geometry.computeVertexNormals();geometries.push(geometry);
    const mesh=new THREE.Mesh(geometry,material);mesh.name=name;mesh.receiveShadow=true;connections.add(mesh);
  }
  const roadY=.085-site.groundY;
  grade('Nuanting public entrance',[[-4,.224,56],[4,.224,56],[4,roadY,70],[-4,roadY,70]],paving);
  grade('Nuanting vehicle entrance',[[43,.054,56],[49,.054,56],[49,roadY,70],[43,roadY,70]],road);
  grade('Nuanting service entrance',[[-48.5,roadY,-70],[-43.5,roadY,-70],[-43.5,.054,-56],[-48.5,.054,-56]],road);

  const lighting=new THREE.Group();lighting.name='Nuanting city lighting';model.root.add(lighting);
  const lights=model.manifest.lightFixtures.map(f=>{
    const light=new THREE.PointLight(f.color??0xffd19b,0,f.distance??16,2);light.position.fromArray(f.position);light.castShadow=false;lighting.add(light);return light;
  });
  const originalTimeOfDay=model.setTimeOfDay;
  model.setTimeOfDay=value=>{
    const n=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.4:0;
    originalTimeOfDay(n);lights.forEach((light,i)=>light.intensity=(model.manifest.lightFixtures[i].power??28)*n);
  };

  // Full-city exports remain complete while the user observes another building.
  const originalExport=model.exportScene;
  model.exportScene=(onlyId=null)=>{
    const rootVisible=model.root.visible,quality=model.quality,states=[...buildings].map(([id,g])=>[id,g.visible]);
    model.root.visible=true;buildings.forEach(g=>g.visible=true);model.setQuality('high');
    try{const snapshot=originalExport();if(onlyId)snapshot.objects=snapshot.objects.filter(object=>object.owner===onlyId);return snapshot;}
    finally{model.root.visible=rootVisible;model.setQuality(quality);states.forEach(([id,visible])=>buildings.get(id).visible=visible);}
  };
  const originalDispose=model.dispose;
  model.dispose=()=>{
    if(model.disposed)return;
    const ids=new Set(buildings.keys());ids.forEach(id=>city.groups.delete(id));
    city.plan.buildings=city.plan.buildings.filter(record=>!ids.has(record.id));
    if(block.moduleId==='nuanting-garden-housing'){for(const key of Object.keys(block))if(!(key in previousBlock))delete block[key];Object.assign(block,previousBlock);}
    geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());lights.forEach(light=>light.dispose());buildings.clear();
    originalDispose();
  };
  city.root.updateMatrixWorld(true);
  return {model,site,block,buildings,records,connections,lighting,lights};
}
