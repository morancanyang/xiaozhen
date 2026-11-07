import * as THREE from 'three';
import {createCorporateHeadquarters} from './headquarters-model.js';
export const HEADQUARTERS_SITE=Object.freeze({blockId:'BLK-3',x:-112,z:70,size:112,groundY:.34});
export function installHeadquarters(city){
 const site=HEADQUARTERS_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
 if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-3 与衡联总部坐标不一致');
 if(city.groups.has('HENGLIAN-MAIN'))throw new Error('衡联总部已安装');
 const previousBlock={...block},model=createCorporateHeadquarters({THREE,blockSize:site.size,quality:'medium'});
 model.root.position.set(site.x,site.groundY,site.z);model.root.name='HENGLIAN-BLK-3';
 Object.assign(model.root.userData,{moduleId:model.manifest.id,blockId:site.blockId,cityModule:true});city.root.add(model.root);
 const buildings=new Map(),records=[];
 for(const b of [...model.manifest.buildings,{id:'bridge',name:'空中连廊',x:1.5,z:3,w:21,d:6,height:4.4,floors:1}]){
  const id='HENGLIAN-'+b.id.toUpperCase(),g=model.groups.get(b.id),record={id,name:'衡联总部 · '+b.name,type:'企业总部 · 银灰幕墙与空中连廊',x:site.x+b.x,z:site.z+b.z,width:b.w,depth:b.d,height:b.height,floors:b.floors,groundY:site.groundY+(b.id==='bridge'?36.8:0),blockId:site.blockId,moduleId:model.manifest.id,localId:b.id};
  g.name=id;Object.assign(g.userData,record);city.groups.set(id,g);city.plan.buildings.push(record);buildings.set(id,g);records.push(record);
 }
 Object.assign(block,{name:'衡联总部',type:'corporate-headquarters',moduleId:model.manifest.id});
 const connections=new THREE.Group();connections.name='Henglian pedestrian connections';connections.userData.id='site';model.root.add(connections);
 const paving=city.materials.paving.clone(),geometries=[];paving.name='Henglian stone approach';
 function grade(name,x,width,y){const end=.085-site.groundY,g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([x-width/2,y,56,x+width/2,y,56,x+width/2,end,70,x-width/2,end,70],3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));g.setIndex([0,2,1,0,3,2]);g.computeVertexNormals();geometries.push(g);const o=new THREE.Mesh(g,paving);o.name=name;o.receiveShadow=true;connections.add(o)}
 grade('Henglian public entrance',0,8,.224);grade('Henglian permeable service entrance',46,6,.094);
 const lighting=new THREE.Group();lighting.name='Henglian fixture lights';model.root.add(lighting);
 // The city render budget pools these sources; no additional renderer or lighting pass.
 const lights=model.manifest.lightFixtures.map(f=>{const l=new THREE.PointLight(0xffd8aa,0,f.distance||15,2);l.position.fromArray(f.position);lighting.add(l);return l});
 const originalTime=model.setTimeOfDay;model.setTimeOfDay=v=>{const n=typeof v==='number'?THREE.MathUtils.clamp(v,0,1):v==='night'?1:v==='evening'?.4:0;originalTime(n);lights.forEach((l,i)=>l.intensity=model.manifest.lightFixtures[i].power*n)};
 const originalExport=model.exportScene;model.exportScene=(onlyId=null)=>{const vis=[...model.groups].map(([id,g])=>[id,g.visible]),rootVisible=model.root.visible,quality=model.quality;try{model.root.visible=true;model.groups.forEach(g=>g.visible=true);model.setQuality('high');const out=originalExport();if(onlyId){const local=onlyId.replace('HENGLIAN-','').toLowerCase();out.objects=out.objects.filter(o=>o.owner===onlyId||o.owner.startsWith(local+'-'))}return out}finally{model.setQuality(quality);vis.forEach(([id,v])=>model.groups.get(id).visible=v);model.root.visible=rootVisible}};
 const originalDispose=model.dispose;model.dispose=()=>{if(model.disposed)return;const ids=new Set(buildings.keys());ids.forEach(id=>city.groups.delete(id));city.plan.buildings=city.plan.buildings.filter(b=>!ids.has(b.id));if(block.moduleId===model.manifest.id){for(const key of Object.keys(block))if(!(key in previousBlock))delete block[key];Object.assign(block,previousBlock)}geometries.forEach(g=>g.dispose());paving.dispose();lights.forEach(l=>l.dispose());buildings.clear();originalDispose()};
 city.root.updateMatrixWorld(true);return{model,site,block,records,buildings,lights,connections};
}
