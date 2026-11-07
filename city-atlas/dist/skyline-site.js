import * as THREE from 'three';
import {createSkylineTower} from './skyline-model.js';

// The marked parcel is the second northern row, on the west bank's inner column.
export const SKYLINE_SITE=Object.freeze({blockId:'BLK-2',x:-112,z:-70,size:112,groundY:.3});

export function installSkyline(city){
  const site=SKYLINE_SITE,tower=createSkylineTower({THREE,blockSize:site.size,quality:'medium',embedded:true,seed:1101});
  tower.root.position.set(site.x,site.groundY,site.z);
  tower.root.name='Skyline-One-BLK-2';tower.root.userData={moduleId:'skyline-one',blockId:site.blockId,cityModule:true};
  city.root.add(tower.root);
  const block=city.plan.blocks.find(b=>b.id===site.blockId);Object.assign(block,{name:'云际中心',type:'skyscraper',moduleId:'skyline-one'});
  // Tower, podium and rooftop form one selectable building with a ground-level pivot.
  const id='SKY-ONE',building=new THREE.Group();building.name=id;building.position.z=-6;tower.root.add(building);tower.root.updateMatrixWorld(true);
  for(const component of ['tower','podium','roof']){const group=tower.groups.get(component);building.attach(group);group.userData={...group.userData,id,component};}
  const record={id,name:'云际中心 · SKYLINE ONE',type:'超高层地标 · 商业与办公',x:site.x,z:site.z-6,width:64,depth:56,height:224,floors:55,blockId:site.blockId,moduleId:'skyline-one',groundY:site.groundY};
  building.userData={...record};city.groups.set(id,building);city.plan.buildings.push(record);
  addConnections(tower,site);
  // A module owns its connecting geometry, too; all resources are released together.
  const originalDispose=tower.dispose,resources=tower.root.getObjectByName('Skyline road connections');
  tower.dispose=()=>{if(!tower.disposed){const gs=new Set(),ms=new Set();resources.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material)ms.add(o.material);});gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());}originalDispose();};
  city.root.updateMatrixWorld(true);return {tower,site,block,building};
}

function addConnections(tower,site){
  const group=new THREE.Group();group.name='Skyline road connections';tower.root.add(group);
  const native=tower.root.getObjectByName('site:asphalt:L0').material,material=native.clone();material.name='Skyline road connection';
  function grade(name,points){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));g.setIndex([0,2,1,0,3,2]);g.computeVertexNormals();const m=new THREE.Mesh(g,material);m.name=name;m.receiveShadow=true;group.add(m);}
  const roadY=.08-site.groundY;
  grade('Skyline public entrance connection',[[-5,.115,56],[5,.115,56],[5,roadY,70],[-5,roadY,70]]);
  grade('Skyline vehicle entrance connection',[[52,.115,35.5],[70,roadY,35.5],[70,roadY,42.5],[52,.115,42.5]]);
  grade('Skyline service entrance connection',[[-70,roadY,-47.5],[-52,.115,-47.5],[-52,.115,-40.5],[-70,roadY,-40.5]]);
}
