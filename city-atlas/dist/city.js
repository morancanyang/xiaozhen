import * as THREE from 'three';

export const PLAN={seed:1101,units:'meters',corridor:{minX:-32,maxX:32,minZ:-300,maxZ:300,width:64},blockSize:112,blocks:[],buildings:[]};
let seed=PLAN.seed;
const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
const choose=a=>a[Math.floor(rand()*a.length)];
const windShaders={},materials={},buckets=new Map(),geometries={box:new THREE.BoxGeometry(1,1,1),cylinder:new THREE.CylinderGeometry(.5,.5,1,8),sphere:new THREE.IcosahedronGeometry(.5,1),plane:new THREE.PlaneGeometry(1,1)};
const matrix=new THREE.Matrix4(),q=new THREE.Quaternion(),position=new THREE.Vector3(),scale=new THREE.Vector3();
let root,trees,nightMaterials=[],activeBlock=null;
const CUSTOM_BLOCKS=new Set(['BLK-13','BLK-2','BLK-10','BLK-11','BLK-8','BLK-4','BLK-16','BLK-5','BLK-15','BLK-7','BLK-12','BLK-6','BLK-9','BLK-14','BLK-3']);
const RIVER_CUT={minX:-32,maxX:32,minZ:-300,maxZ:300};
const GARAGE_CUTS=[{minX:67.4,maxX:72.6,minZ:-225.1,maxZ:-191.9},{minX:210,maxX:224,minZ:-250,maxZ:-230},{minX:-159,maxX:-147,minZ:-109,maxZ:-82}];
function texture(kind){const c=document.createElement('canvas');c.width=c.height=256;const ctx=c.getContext('2d');ctx.fillStyle=kind==='asphalt'?'#082742':'#dddad0';ctx.fillRect(0,0,256,256);for(let i=0;i<18000;i++){const k=rand();ctx.fillStyle=kind==='asphalt'?`rgba(${k>.5?'95,122,151':'6,13,24'},${rand()*.025})`:`rgba(105,101,87,${rand()*.1})`;ctx.fillRect(rand()*256,rand()*256,1+rand(),1+rand());}if(kind==='paving'){ctx.strokeStyle='#bfbfb3';ctx.lineWidth=1;for(let a=0;a<=256;a+=32){ctx.beginPath();ctx.moveTo(a,0);ctx.lineTo(a,256);ctx.stroke();ctx.beginPath();ctx.moveTo(0,a);ctx.lineTo(256,a);ctx.stroke();}}const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(kind==='asphalt'?26:18,kind==='asphalt'?26:18);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t;}
function mat(name,color,extra={}){materials[name]=new THREE.MeshStandardMaterial({color,roughness:.82,...extra});materials[name].name=name;return name;}
function add(type,material,x,y,z,sx,sy,sz,rotation=0,owner='world'){const key=`${owner}|${type}|${material}`;if(!buckets.has(key))buckets.set(key,{type,material,owner,items:[]});buckets.get(key).items.push({p:[x,y,z],s:[sx,sy,sz],r:rotation,blockId:activeBlock});}
const box=(m,x,y,z,sx,sy,sz,r=0,owner='world')=>add('box',m,x,y,z,sx,sy,sz,r,owner);
const cyl=(m,x,y,z,sx,sy,sz,owner='world')=>add('cylinder',m,x,y,z,sx,sy,sz,0,owner);
function sign(text,x,y,z,rotation=0,width=8,owner=null){const c=document.createElement('canvas');c.width=512;c.height=128;const ctx=c.getContext('2d');ctx.fillStyle='#35564b';ctx.fillRect(0,0,512,128);ctx.fillStyle='#e3dec7';ctx.font='500 48px "Microsoft YaHei",sans-serif';ctx.textAlign='center';ctx.fillText(text,256,80);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;const mesh=new THREE.Mesh(new THREE.PlaneGeometry(width,2),new THREE.MeshStandardMaterial({map:t,roughness:.65,emissive:0x938b67,emissiveIntensity:.12}));mesh.position.set(x,y,z);mesh.rotation.y=rotation;mesh.name='storefront-sign';mesh.userData={owner,text};root.add(mesh);}
function tree(x,z,size=1){cyl('bark',x,2.3*size,z,.45*size,4.6*size,.45*size);box('treepit',x,.34,z,3.5,.18,3.5);for(let i=0;i<3;i++){const y=(5+i*.8)*size;add('sphere',i%2?'leaf2':'leaf1',x+(rand()-.5)*1.5*size,y,z+(rand()-.5)*1.5*size,(4.3-i*.35)*size,(4.8-i*.4)*size,(4.3-i*.35)*size,0,'trees');}}
function lamp(x,z,rot=0){cyl('metal',x,4.6,z,.19,9,.19);const dx=Math.cos(rot),dz=Math.sin(rot);box('metal',x+dx*.85,9,z+dz*.85,2,.14,.18, -rot);box('lamp',x+dx*1.65,8.94,z+dz*1.65,.85,.14,.65);}
function crosswalk(x,z,axis){for(let i=-4;i<=4;i++){if(axis==='x')box('paint',x+i*1.9,.075,z,1.05,.025,4);else box('paint',x,.075,z+i*1.9,4,.025,1.05);}}
function furnishings(x,z){box('bench',x,.95,z,3.3,.22,.72);box('metal',x-1.1,.5,z,.12,1,.6);box('metal',x+1.1,.5,z,.12,1,.6);box('bench',x,1.4,z+.33,3.3,.7,.12);box('metal',x+4,.7,z,.8,1.35,.8);cyl('hydrant',x-4,.7,z,.4,1,.4);}
function makeBuilding(x,z,index,block){const id=`QR-${String(index+1).padStart(3,'0')}`,floors=10+Math.floor(rand()*12),width=22+Math.floor(rand()*6),depth=23+Math.floor(rand()*5),height=5+floors*3.15;const wall=choose(['ivory','sand','stone','warm']);const owner=id;const building={id,name:`${choose(['梧桐','云栖','晨曦','青禾','望舒','棠里'])}${String(index+1).padStart(2,'0')}号`,type:index%4===0?'退台住宅 · 底层商业':'现代住宅 · 底层商业',x,z,width,depth,height,floors,blockId:block.id,material:wall};PLAN.buildings.push(building);
  box(wall,x,height/2,z,width,height,depth,0,owner);box('podium',x,2.3,z,width+1,4.6,depth+1,0,owner);box('ledge',x,4.8,z,width+1.5,.45,depth+1.5,0,owner);
  // Repeated facade components remain instances inside each independent building group.
  for(let floor=0;floor<floors;floor++){const y=6.5+floor*3.15;for(let side=0;side<4;side++){const count=4;for(let j=0;j<count;j++){const offset=(j-1.5)*4.8;const lit=rand()>.91;const m=lit?'litglass':'glass';if(side<2){const zz=z+(side===0?1:-1)*(depth/2+.055);box(m,x+offset,y,zz,2.2,1.95,.12,0,owner);box('frame',x+offset,y,zz+(side===0?.075:-.075),.07,1.95,.12,0,owner);box('ledge',x+offset,y-1.04,zz,2.5,.11,.45,0,owner);if(j===0||j===3){const zz2=zz+(side===0?.75:-.75);box('ledge',x+offset,y-1.14,zz2,3.2,.16,1.65,0,owner);box('rail',x+offset,y-.67,zz2+(side===0?.7:-.7),3.2,.8,.075,0,owner);box('dark',x+offset+1.05,y-.4,zz,.65,.65,.6,0,owner);}}else{const xx=x+(side===2?1:-1)*(width/2+.06);box(m,xx,y,z+offset,.12,1.95,2.2,0,owner);box('frame',xx+(side===2?.075:-.075),y,z+offset,.12,1.95,.07,0,owner);box('ledge',xx,y-1.04,z+offset,.45,.11,2.5,0,owner);}}}
    if(floor%3===2)box('ledge',x,y+1.52,z,width+.28,.12,depth+.28,0,owner);
  }
  for(const dx of [-width/2+.15,width/2-.15])box('frame',x+dx,height/2,z+depth/2+.1,.12,height,.15,0,owner);
  box('roof',x,height+.15,z,width,.3,depth,0,owner);for(const dz of [-depth/2,depth/2])box('ledge',x,height+.65,z+dz,width+.3,1,.25,0,owner);for(const dx of [-width/2,width/2])box('ledge',x+dx,height+.65,z,.25,1,depth,0,owner);
  box(wall,x+2,height+2,z-2,7,4,6,0,owner);for(let i=0;i<3;i++){box('equipment',x-7+i*3.8,height+.8,z+5,2.7,1.3,2.2,0,owner);cyl('dark',x-7+i*3.8,height+1.48,z+5,1.5,.12,1.5,owner);}if(index%4===0)box('solar',x-4,height+.45,z-6,9,.24,4,0,owner);
  for(let j=-1;j<=1;j++){box('shopglass',x+j*7.2,2.2,z+depth/2+.61,6.5,3.5,.12,0,owner);box('frame',x+j*7.2,2.2,z+depth/2+.73,.1,3.5,.12,0,owner);box('awning',x+j*7.2,4.15,z+depth/2+1.7,6.7,.15,2.5,0,owner);box('storewarm',x+j*7.2,2,z+depth/2-.4,5.8,3.1,.08,0,owner);}
  box('ledge',x,0.18,z+depth/2+1.5,8,.3,2.5,0,owner);sign(choose(['青禾咖啡','街角面包','晨光便利','小镇书屋','四季花店','邻里生活']),x,3.9,z+depth/2+.78,0,9,owner);
}

export function buildCity(scene){root=new THREE.Group();root.name='Qianren-City';scene.add(root);seed=PLAN.seed;
  mat('asphalt',0xffffff,{map:texture('asphalt'),roughness:.94});mat('paving',0xffffff,{map:texture('paving')});mat('base',0xc7cbbb);mat('soil',0xd6d7c7);mat('grass',0x9aa980);mat('paint',0xe9e7cf);mat('curb',0xd5d5c5);mat('ivory',0xd9d7c9);mat('sand',0xbeb19b);mat('stone',0xbcc5c1);mat('warm',0xd1c0a7);mat('ledge',0xe1e0d4);mat('podium',0x9b9d8e);mat('glass',0x5b7c83,{metalness:.48,roughness:.24});mat('litglass',0xc8b991,{metalness:.2,roughness:.25,emissive:0xffcb78,emissiveIntensity:.15});mat('frame',0x66746f,{metalness:.55,roughness:.4});mat('rail',0x83958d,{metalness:.5,roughness:.38,transparent:true,opacity:.72});mat('roof',0x8f9891);mat('dark',0x6b7773);mat('equipment',0xb4b9ad);mat('metal',0x5e6a61,{metalness:.65,roughness:.4});mat('lamp',0xeee5bd,{emissive:0xffd68d,emissiveIntensity:.12});mat('bark',0x7d7960);mat('leaf1',0x71875b);mat('leaf2',0x8e9e65);mat('treepit',0x9c9f82);mat('bench',0xa09470);mat('hydrant',0xb67353);mat('solar',0x526575,{metalness:.5,roughness:.25});mat('awning',0x647c67);mat('shopglass',0x4c6b6a,{metalness:.4,roughness:.19,transparent:true,opacity:.78});mat('storewarm',0x9c8b65,{emissive:0xffcd81,emissiveIntensity:.08});
  nightMaterials=[materials.litglass,materials.lamp,materials.storewarm];
  box('base',0,-3.8,0,680,7,620);box('soil',0,-.4,0,660,.5,600);box('soil',0,-.08,0,64,.08,600);
  // Square 112 m blocks, 28 m streets, 64 m empty central reservation.
  for(const side of [-1,1]){box('asphalt',side*184,.03,0,304,.06,588);for(const x0 of [112,252]){const x=x0*side;for(const z of [-210,-70,70,210]){const block={id:`BLK-${PLAN.blocks.length+1}`,x,z,size:112};PLAN.blocks.push(block);activeBlock=block.id;box('curb',x,.12,z,113,.24,113);box('paving',x,.27,z,112,.14,112);box('grass',x,.36,z,94,.08,94);box('paving',x,.42,z,8,.06,96);box('paving',x,.42,z,96,.06,8);
    for(const dx of [-25.5,25.5])for(const dz of [-25.5,25.5])makeBuilding(x+dx,z+dz,PLAN.buildings.length,block);
    for(let a=-42;a<=42;a+=14){tree(x+a,z-51,.85+rand()*.2);tree(x+a,z+51,.85+rand()*.2);if(Math.abs(a)>14){tree(x-51,z+a,.9);tree(x+51,z+a,.9);}}
    for(let i=0;i<4;i++){tree(x+(i-1.5)*13,z,1);tree(x,z+(i-1.5)*13,.9);}furnishings(x+7,z+5);furnishings(x-14,z-5);box('paving',x,.44,z,18,.1,18);
    for(const dx of [-46,46])for(const dz of [-46,46])lamp(x+dx,z+dz,dx>0?0:Math.PI);
    // Parking bays occupy the paved internal edge, outside pedestrian clearways.
    for(let j=0;j<5;j++){const px=x-33+j*7;box('paint',px,.36,z-43,.12,.02,5.5);if(j<4)staticCar(px+3.3,z-43,Math.PI/2,choose(['carwhite','carblue','cargray']));}
    for(const dz of [-56.7,56.7])box('curb',x,.32,z+dz,112,.2,.4);for(const dx of [-56.7,56.7])box('curb',x+dx,.32,z,.4,.2,112);
  }}
  activeBlock=null;
  for(const x of [44,182,322].map(v=>v*side)){for(let z=-278;z<=278;z+=10){if(Math.abs((z+280)%140)<19)continue;box('paint',x,.081,z,.18,.015,4.5);}for(let z=-260;z<280;z+=70){box('dark',x+8,.085,z,1.2,.025,.65);lamp(x+side*10,z,side>0?Math.PI:0);}}
  for(const z of [-280,-140,0,140,280]){for(let xx=64;xx<=308;xx+=10){if(Math.abs(xx-182)<19)continue;box('paint',xx*side,.09,z,4.5,.02,.18);}for(const x of [44,182,322].map(v=>v*side)){if(Math.abs(x)!==322){for(const dz of [-17,17])crosswalk(x,z+dz,'x');}if(z!==-280&&z!==280){for(const dx of [-17,17]){if(Math.abs(x+dx)>32)crosswalk(x+dx,z,'z');}}for(const a of [-1,1]){cyl('metal',x+a*11,2.5,z+a*11,.15,5,.15);box('metal',x+a*11,4.4,z+a*11,.55,1.8,.5);}}}
  }
  const removedIds=new Set(PLAN.buildings.filter(b=>CUSTOM_BLOCKS.has(b.blockId)).map(b=>b.id));
  PLAN.buildings=PLAN.buildings.filter(b=>!removedIds.has(b.id));
  for(const child of [...root.children])if(removedIds.has(child.userData.owner)){root.remove(child);child.geometry?.dispose();child.material?.map?.dispose();child.material?.dispose();}
  for(const [key,bucket] of [...buckets]){
    bucket.items=bucket.items.filter(item=>!CUSTOM_BLOCKS.has(item.blockId)&&!removedIds.has(bucket.owner));
    if(bucket.owner==='world'&&bucket.type==='box'&&['base','soil','asphalt'].includes(bucket.material))bucket.items=[...GARAGE_CUTS,RIVER_CUT].reduce((items,cut)=>items.flatMap(item=>cutGroundBox(item,cut)),bucket.items);
    if(!bucket.items.length)buckets.delete(key);
  }
  // The river module occupies the excavated corridor. Its boundary guide is optional.
  const guide=new THREE.Group();guide.name='future-river-boundary';for(const x of [-32,32]){const points=[new THREE.Vector3(x,.13,-300),new THREE.Vector3(x,.13,300)];const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineDashedMaterial({color:0x69896b,dashSize:6,gapSize:4}));line.computeLineDistances();guide.add(line);}guide.visible=false;root.add(guide);
  const groups=new Map();PLAN.buildings.forEach(b=>{const group=new THREE.Group();group.name=b.id;group.position.set(b.x,0,b.z);group.userData={...b};root.add(group);groups.set(b.id,group);});
  root.updateMatrixWorld(true);for(const signMesh of [...root.children]){if(signMesh.userData.owner&&groups.has(signMesh.userData.owner))groups.get(signMesh.userData.owner).attach(signMesh);}
  const signalMeshes=[];
  for(const bucket of buckets.values()){const parent=groups.get(bucket.owner)||root;const mesh=new THREE.InstancedMesh(geometries[bucket.type],materials[bucket.material],bucket.items.length);mesh.name=`${bucket.owner}:${bucket.material}`;mesh.castShadow=!['paint','asphalt','paving','glass','rail'].includes(bucket.material);mesh.receiveShadow=true;bucket.items.forEach((item,i)=>{position.fromArray(item.p);if(groups.has(bucket.owner))position.sub(parent.position);scale.fromArray(item.s);q.setFromAxisAngle(new THREE.Vector3(0,1,0),item.r);matrix.compose(position,q,scale);mesh.setMatrixAt(i,matrix);});mesh.computeBoundingSphere();if(bucket.owner==='trees'){mesh.userData.wind=true;signalMeshes.push(mesh);}parent.add(mesh);}
  trees=signalMeshes;
  // Instanced foliage deformation: a shared global wind, locally varying phases.
  for(const key of ['leaf1','leaf2']){materials[key].onBeforeCompile=shader=>{shader.uniforms.uWind={value:0};shader.uniforms.uWindStrength={value:1};windShaders[key]=shader;shader.vertexShader='uniform float uWind; uniform float uWindStrength;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n#ifdef USE_INSTANCING\nfloat phase=instanceMatrix[3].x*.23+instanceMatrix[3].z*.17;\ntransformed.x+=sin(uWind*1.2+phase)*.045*uWindStrength*(position.y+.6);\ntransformed.z+=cos(uWind*.9+phase)*.025*uWindStrength;\n#endif');};}
  return {root,guide,groups,materials,plan:PLAN,buckets};
}

function cutGroundBox(item,cut){
  const [x,y,z]=item.p,[w,h,d]=item.s;
  const x0=x-w/2,x1=x+w/2,z0=z-d/2,z1=z+d/2;
  if(x1<=cut.minX||x0>=cut.maxX||z1<=cut.minZ||z0>=cut.maxZ)return [item];
  const left=Math.max(x0,cut.minX),right=Math.min(x1,cut.maxX),back=Math.max(z0,cut.minZ),front=Math.min(z1,cut.maxZ);
  const rectangles=[[x0,left,z0,z1],[right,x1,z0,z1],[left,right,z0,back],[left,right,front,z1]];
  return rectangles.filter(([a,b,c,d])=>b-a>.001&&d-c>.001).map(([a,b,c,d])=>({...item,p:[(a+b)/2,y,(c+d)/2],s:[b-a,h,d-c]}));
}

function ensureCarMaterials(){if(materials.carwhite)return;mat('carwhite',0xdadbd1,{metalness:.3,roughness:.32});mat('carblue',0x63818b,{metalness:.4,roughness:.3});mat('cargray',0x707a74,{metalness:.4,roughness:.3});mat('carred',0xa47560,{metalness:.3,roughness:.35});mat('tire',0x333d39);}
function staticCar(x,z,r,color){ensureCarMaterials();const p=(lx,lz)=>[x+Math.cos(r)*lx+Math.sin(r)*lz,z-Math.sin(r)*lx+Math.cos(r)*lz];let [xx,zz]=p(0,0);box(color,xx,.85,zz,2,1.05,4.5,r);[xx,zz]=p(0,-.15);box('glass',xx,1.6,zz,1.75,.8,2.4,r);for(const dx of [-1,1])for(const dz of [-1.45,1.45]){[xx,zz]=p(dx,dz);box('tire',xx,.52,zz,.25,.7,.7,r);}}

export function createLife(scene){ensureCarMaterials();const moving=new THREE.Group();moving.name='City life';scene.add(moving);const cars=[],walkers=[],signals=[],birds=[];
  const carGeo=new THREE.BoxGeometry(1,1,1),wheelGeo=new THREE.CylinderGeometry(.34,.34,.22,8);wheelGeo.rotateZ(Math.PI/2);
  function car(){const g=new THREE.Group();const body=new THREE.Mesh(carGeo,materials[choose(['carwhite','carblue','cargray','carred'])]);body.scale.set(1.9,.8,4.4);body.position.y=.8;body.castShadow=true;g.add(body);const glass=new THREE.Mesh(carGeo,materials.glass);glass.scale.set(1.65,.8,2.2);glass.position.set(0,1.5,-.2);g.add(glass);const roof=new THREE.Mesh(carGeo,body.material);roof.scale.set(1.7,.08,2.1);roof.position.set(0,1.94,-.2);g.add(roof);const wheels=[];for(const x of [-.96,.96])for(const z of [-1.35,1.35]){const w=new THREE.Mesh(wheelGeo,materials.tire);w.position.set(x,.45,z);g.add(w);wheels.push(w);}for(const x of [-.6,.6]){const head=new THREE.Mesh(carGeo,materials.lamp);head.scale.set(.5,.18,.08);head.position.set(x,.92,2.22);g.add(head);}moving.add(g);return {g,wheels};}
  // Rounded rectangular routes occupy one lane; all route members share a speed.
  for(const side of [-1,1])for(const bx of [112,252])for(const bz of [-210,-70,70,210]){const left=side===1?bx-64:-bx-64,right=left+128,top=bz-64,bottom=bz+64,r=12;const coords=[[left+r,top],[right-r,top],[right,top+r],[right,bottom-r],[right-r,bottom],[left+r,bottom],[left,bottom-r],[left,top+r]];const curve=new THREE.CatmullRomCurve3(coords.map(([x,z])=>new THREE.Vector3(x,.12,z)),true,'centripetal',.12),length=curve.getLength();for(let i=0;i<3;i++){const c=car();cars.push({...c,curve,length,t:(i/3+rand()*.025)%1,route:cars.length/3|0,speed:7.5});}
    const path=new THREE.CatmullRomCurve3([[left+9,top+9],[right-9,top+9],[right-9,bottom-9],[left+9,bottom-9]].map(([x,z])=>new THREE.Vector3(x,.48,z)),true,'catmullrom',0);for(let i=0;i<(side*bx===252&&bz===-210?0:7);i++){const person=new THREE.Group(),cloth=new THREE.MeshStandardMaterial({color:choose([0x606f68,0x9e8e72,0xb6b9aa,0x6d8890,0xa38372]),roughness:.9}),skin=new THREE.MeshStandardMaterial({color:0xc6ab8e});const body=new THREE.Mesh(new THREE.BoxGeometry(.5,.8,.29),cloth);body.position.y=1.03;person.add(body);const head=new THREE.Mesh(new THREE.SphereGeometry(.19,6,5),skin);head.position.y=1.66;person.add(head);const legs=[];for(const x of [-.14,.14]){const leg=new THREE.Mesh(new THREE.BoxGeometry(.16,.68,.19),materials.dark);leg.position.set(x,.4,0);person.add(leg);legs.push(leg);}moving.add(person);const walker={g:person,legs,curve:path,length:path.getLength(),t:rand(),speed:.8+rand()*.5};if(side*bx===112&&[-210,210].includes(bz)||side*bx===-252&&[-210,-70,70].includes(bz)||side*bx===-112&&[-70,70,210].includes(bz)||side*bx===252&&[-70,70,210].includes(bz)){person.removeFromParent();person.traverse(o=>{o.geometry?.dispose();});cloth.dispose();skin.dispose();}else walkers.push(walker);}}
  for(const side of [-1,1])for(const x of [44,182,322])for(const z of [-280,-140,0,140,280]){const g=new THREE.Group();g.position.set(side*x+11,4.8,z+11);const lights=[];for(let j=0;j<3;j++){const material=new THREE.MeshBasicMaterial({color:j===0?0xc56b51:j===1?0xc7ad65:0x82a577});const m=new THREE.Mesh(new THREE.SphereGeometry(.18,6,5),material);m.position.set(0,-j*.43,.3);g.add(m);lights.push(m);}moving.add(g);signals.push({lights,z});}
  const birdmat=new THREE.MeshStandardMaterial({color:0x667668,side:THREE.DoubleSide});const birdgeo=new THREE.BufferGeometry();birdgeo.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,-2,.4,.4,-.4,0,1,0,0,0,.4,0,1,2,.4,.4],3));for(let i=0;i<9;i++){const b=new THREE.Mesh(birdgeo,birdmat);moving.add(b);birds.push(b);}
  return {moving,cars,walkers,signals,birds};
}

export function updateLife(life,t,dt,state){if(state.wind){for(const key of ['leaf1','leaf2']){const s=windShaders[key];if(s){s.uniforms.uWind.value=t;s.uniforms.uWindStrength.value=1;}}}else for(const key of ['leaf1','leaf2']){const s=windShaders[key];if(s)s.uniforms.uWindStrength.value=0;}
  life.cars.forEach(c=>{c.g.visible=state.traffic;if(!state.traffic)return;const phase=t%24;const tangent=c.curve.getTangentAt(c.t),horizontal=Math.abs(tangent.x)>.75;const red=horizontal?phase<11:phase>=12&&phase<23;const next=(c.t+c.speed*dt/c.length)%1;const cornerZone=Math.min(...[.125,.375,.625,.875].map(v=>Math.abs(c.t-v)))<.014;if(!(red&&cornerZone))c.t=next;const p=c.curve.getPointAt(c.t),d=c.curve.getTangentAt(c.t);c.g.position.copy(p);c.g.rotation.y=Math.atan2(d.x,d.z);if(!(red&&cornerZone))c.wheels.forEach(w=>w.rotation.x+=c.speed*dt/.34);});
  life.walkers.forEach((w,i)=>{w.g.visible=state.traffic;if(!state.traffic)return;w.t=(w.t+w.speed*dt/w.length)%1;w.g.position.copy(w.curve.getPointAt(w.t));const d=w.curve.getTangentAt(w.t);w.g.rotation.y=Math.atan2(d.x,d.z);w.legs.forEach((l,j)=>l.rotation.x=Math.sin(t*5+i+j*Math.PI)*.4);});
  life.signals.forEach(s=>s.lights.forEach((l,j)=>{const active=(t%24)<11?2:(t%24)<12?1:0;l.material.color.setHex(j===active?[0xe57b5a,0xe2c16c,0x85ba85][j]:0x36423a);}));
  life.birds.forEach((b,i)=>{b.visible=state.wind;const angle=t*.025+i*.35;b.position.set(Math.cos(angle)*150+i*8,92+Math.sin(i+t*.13)*12,Math.sin(angle)*170);b.rotation.set(Math.sin(t*4+i)*.2,-angle,Math.sin(t*3+i)*.15);});
}

export function setNight(amount){nightMaterials.forEach((m,i)=>{m.emissiveIntensity=[.15,.12,.08][i]+amount*[2.1,4,1.4][i];});}

export function exportCity(onlyId=null){const selected=onlyId?PLAN.buildings.filter(b=>b.id===onlyId):PLAN.buildings;const result={format:'qianren-city-v1',plan:{...PLAN,buildings:selected},materials:{},batches:[]};for(const [name,m] of Object.entries(materials)){result.materials[name]={color:m.color.toArray(),roughness:m.roughness,metalness:m.metalness,emissive:m.emissive.toArray(),emissiveIntensity:m.emissiveIntensity};}for(const b of buckets.values()){if(onlyId&&b.owner!==onlyId)continue;result.batches.push(b);}return result;}
