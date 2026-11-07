import * as THREE from 'three';
import {createLandmarkOffice} from './office-model.js';

export const OFFICE_SITE=Object.freeze({blockId:'BLK-9',x:112,z:-210,size:112,groundY:.34});

/** The city owns rendering, sky, camera and time. Only the parcel is transplanted. */
export function installOffice(city){
 const site=OFFICE_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
 if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-9 与霁衡中心配置不一致');
 if(city.groups.has('JIHENG-ONE'))throw new Error('霁衡中心已安装');
 const previousBlock={...block},model=createLandmarkOffice({THREE,blockSize:site.size,quality:'medium'});
 const record={id:'JIHENG-ONE',name:'霁衡中心',type:'地标写字楼 · 石材商业裙楼',x:site.x,z:site.z,width:112,depth:112,height:184,floors:46,groundY:site.groundY,blockId:site.blockId,moduleId:'jiheng-landmark-office'};
 // Part IDs remain editable; native building IDs must not intercept city picking.
 model.root.traverse(o=>delete o.userData.id);
 model.root.position.set(site.x,site.groundY,site.z);model.root.name=record.id;Object.assign(model.root.userData,record,{cityModule:true});
 city.root.add(model.root);city.groups.set(record.id,model.root);city.plan.buildings.push(record);
 Object.assign(block,{name:record.name,type:'landmark-office-complex',moduleId:record.moduleId});

 const connections=new THREE.Group();connections.name='Jiheng road connections';connections.userData.partId='site';model.root.add(connections);
 const road=model.materials.asphalt.clone(),paving=city.materials.paving.clone(),geometries=[];
 road.name='Jiheng asphalt approach';paving.name='Jiheng pedestrian approach';
 const roadY=.085-site.groundY;
 function grade(name,points,material){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));g.setIndex([0,2,1,0,3,2]);g.computeVertexNormals();geometries.push(g);const o=new THREE.Mesh(g,material);o.name=name;o.receiveShadow=true;connections.add(o);}
 grade('Jiheng public entrance',[[-6,.16,56],[6,.16,56],[6,roadY,70],[-6,roadY,70]],paving);
 grade('Jiheng vehicle entrance',[[45,.055,56],[51,.055,56],[51,roadY,70],[45,roadY,70]],road);
 grade('Jiheng service entrance',[[-51,roadY,-70],[-45,roadY,-70],[-45,.055,-56],[-51,.055,-56]],road);

 const lighting=new THREE.Group();lighting.name='Jiheng city lighting';model.root.add(lighting);
 const lights=model.manifest.lightFixtures.map(f=>{const o=new THREE.PointLight(f.color??0xffd8aa,0,f.distance??15,2);o.position.fromArray(f.position);o.castShadow=false;lighting.add(o);return o;});
 // Physical lights affect every city material's shader. Keep the full installation,
 // and select an appropriate light budget for each rendering quality.
 const originalQuality=model.setQuality,balancedLights=new Set([2,3,6,7,9,13]);
 model.setQuality=value=>{originalQuality(value);lights.forEach((o,i)=>o.visible=value==='high'||value==='medium'&&balancedLights.has(i));};
 model.setQuality('medium');
 const originalTime=model.setTimeOfDay;
 model.setTimeOfDay=value=>{const n=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.45:0;originalTime(n);lights.forEach((o,i)=>o.intensity=model.manifest.lightFixtures[i].power*n);};
 const originalExport=model.exportScene;
 model.exportScene=()=>{const visible=model.root.visible,quality=model.quality,states=[...model.groups].map(([id,g])=>[id,g.visible]);try{model.root.visible=true;model.groups.forEach(g=>g.visible=true);model.setQuality('high');return originalExport();}finally{model.setQuality(quality);states.forEach(([id,v])=>model.groups.get(id).visible=v);model.root.visible=visible;}};
 const originalDispose=model.dispose;
 model.dispose=()=>{if(model.disposed)return;city.groups.delete(record.id);city.plan.buildings=city.plan.buildings.filter(b=>b.id!==record.id);if(block.moduleId===record.moduleId){for(const key of Object.keys(block))if(!(key in previousBlock))delete block[key];Object.assign(block,previousBlock);}geometries.forEach(g=>g.dispose());road.dispose();paving.dispose();lights.forEach(o=>o.dispose());originalDispose();};
 city.root.updateMatrixWorld(true);return{model,record,site,block,connections,lighting,lights};
}
