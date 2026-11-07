import * as THREE from 'three';
import {createHospital} from './hospital-model.js';

// North is -Z. The red-circled northeastern 112 m parcel is BLK-13.
export const HOSPITAL_SITE=Object.freeze({blockId:'BLK-13',x:252,z:-210,size:112,groundY:.3});

export function installHospital(city){
  const site=HOSPITAL_SITE;
  const hospital=createHospital({THREE,embedded:true,quality:'medium'});
  hospital.root.position.set(site.x,site.groundY,site.z);
  hospital.root.name='CH-Hospital-BLK-13';
  hospital.root.userData={moduleId:'hospital-campus',blockId:site.blockId,cityModule:true};
  city.root.add(hospital.root);
  const block=city.plan.blocks.find(b=>b.id===site.blockId);
  Object.assign(block,{type:'hospital',name:'澄和医院',moduleId:'hospital-campus'});
  hospital.buildings.forEach((group,localId)=>{
    const b=hospital.manifest.buildings.find(b=>b.id===localId),id='HOSP-'+localId;
    const record={id,name:'澄和医院 · '+b.name,type:'医疗院区 · '+b.name,x:site.x+b.x,z:site.z+b.z,width:b.w,depth:b.d,height:b.height,floors:b.floors,blockId:site.blockId,moduleId:'hospital-campus',localId,groundY:site.groundY};
    group.name=id;group.userData={...record,hospitalBuilding:true};city.groups.set(id,group);city.plan.buildings.push(record);
  });
  openCurbs(hospital);
  addConnections(hospital,site);
  city.root.updateMatrixWorld(true);
  return {hospital,site,block};
}

function openCurbs(hospital){
  const replacements=[];const transform=new THREE.Matrix4(),p=new THREE.Vector3(),s=new THREE.Vector3(),q=new THREE.Quaternion();
  hospital.root.traverse(mesh=>{if(!mesh.isInstancedMesh||mesh.material.name!=='concrete')return;const kept=[];
    for(let i=0;i<mesh.count;i++){mesh.getMatrixAt(i,transform);transform.decompose(p,q,s);let segments=null;
      if(Math.abs(s.x-112)<.01&&Math.abs(s.z-.3)<.01&&p.z===53)segments=[[-56,-5.5],[5.5,56]].map(([a,b])=>({p:[(a+b)/2,p.y,53],s:[b-a,s.y,s.z]}));
      if(Math.abs(s.z-112)<.01&&Math.abs(s.x-.3)<.01&&p.x===53)segments=[[-56,39],[47,56]].map(([a,b])=>({p:[53,p.y,(a+b)/2],s:[s.x,s.y,b-a]}));
      if(Math.abs(s.z-112)<.01&&Math.abs(s.x-.3)<.01&&p.x===-53)segments=[[-56,-46],[-40,56]].map(([a,b])=>({p:[-53,p.y,(a+b)/2],s:[s.x,s.y,b-a]}));
      if(segments)replacements.push(...segments.map(segment=>({...segment,material:mesh.material,geometry:mesh.geometry})));
      else kept.push(transform.clone());
    }mesh.count=kept.length;kept.forEach((m,i)=>mesh.setMatrixAt(i,m));mesh.instanceMatrix.needsUpdate=true;mesh.computeBoundingSphere();
  });
  for(const item of replacements){const mesh=new THREE.Mesh(item.geometry,item.material);mesh.name='Hospital gate curb';mesh.position.fromArray(item.p);mesh.scale.fromArray(item.s);mesh.castShadow=true;mesh.receiveShadow=true;hospital.root.add(mesh);}
}

function addConnections(hospital,site){
  const material=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.96});
  const road=hospital.root.getObjectByName('site:asphalt:L0');
  if(road?.material){material.copy(road.material);material.name='Hospital connecting road';}
  const connectors=new THREE.Group();connectors.name='Hospital public and emergency access';hospital.root.add(connectors);
  // Grade from the raised campus paving to the existing town road. No new lights or backdrop.
  function ramp(name,points){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));g.setIndex([0,2,1,0,3,2]);g.computeVertexNormals();const m=new THREE.Mesh(g,material);m.name=name;m.receiveShadow=true;connectors.add(m);return m;}
  const roadY=.068-site.groundY;
  ramp('Public entrance graded connection',[[-4.5,.265,56],[4.5,.265,56],[4.5,roadY,70],[-4.5,roadY,70]]);
  ramp('Emergency entrance graded connection',[[52,.185,39.5],[70,roadY,39.5],[70,roadY,46.5],[52,.185,46.5]]);
  ramp('Service entrance graded connection',[[-70,roadY,-46],[-52,.14,-46],[-52,.14,-40],[-70,roadY,-40]]);
  // Portal pedestrian continuity beside the public driveway.
  const pathMat=new THREE.MeshStandardMaterial({color:0xcbd0c4,roughness:.9});
  const geometry=new THREE.BoxGeometry(1,1,1);
  for(const x of [-6,6]){const mesh=new THREE.Mesh(geometry,pathMat);mesh.position.set(x,.13,55);mesh.scale.set(2,.15,2);mesh.receiveShadow=true;mesh.name='Hospital entrance footpath';connectors.add(mesh);}
}
