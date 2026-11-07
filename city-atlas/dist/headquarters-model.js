import {createEcology} from './headquarters-ecology.js';
import {createStairs} from './headquarters-stairs.js';
/** Metric, renderer-independent residential parcel. All texture data is generated locally. */
export function createCorporateHeadquarters({THREE,blockSize=112,quality='high',coarse=false}={}) {
 if(!THREE?.Group||!Number.isFinite(blockSize)||blockSize<=0)throw new Error('THREE and positive blockSize required');
 const root=new THREE.Group();root.name='衡联总部';root.scale.setScalar(blockSize/112);
 const groups=new Map(),buildings=new Map(),batches=new Map(),geometries=new Set(),materialSet=new Set(),textures=new Set(),origins=new Map(),shaders=[],doors=[],fans=[],people=[],birds=[],elevators=[];
 let seed=20261106,time=0,windTime=0,level=quality,enabled=true,disposed=false;
 const activity={wind:true,people:true,birds:true,mechanical:true,bridge:true};
 const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 const manifest={id:'henglian-corporate-headquarters',name:'衡联总部',version:2,units:'m',upAxis:'Y',front:'+Z',pivot:'ground-center',footprint:{width:blockSize,depth:blockSize},nativeSize:112,nativeBounds:{min:[-56,-.4,-56],max:[56,100,56]},surfacePolicy:'Stone / permeable pavers / lawn. No asphalt. External municipal roads belong to the host.',buildings:[],parts:[],entrances:{public:{position:[0,0,56],width:8},service:{position:[46,0,56],width:6}},lightFixtures:[],motion:{peopleCount:22,birdCount:5,vehicleCount:0,walkwayCenterline:41,bridgeFloor:36.8,bridgeTop:41.2},recommendedHost:{pointLightBudget:4,waterReflectionPasses:0,transmissionPasses:0}};
 function group(id,name,parent=root,origin=[0,0,0],buildingId=null){const g=new THREE.Group();g.name=id;g.userData={id,partId:id,name,buildingId};g.position.fromArray(origin);parent.add(g);groups.set(id,g);origins.set(id,buildingId?origins.get(buildingId):origin);manifest.parts.push({id,name,buildingId});return g}
 for(const [id,name] of [['site','场地与透水铺装'],['landscape','草坪与庭院绿化'],['playground','商务休憩花园'],['life','居民与飞鸟']])group(id,name);
 const G=g=>(geometries.add(g),g),M=m=>(materialSet.add(m),m),geo={box:G(new THREE.BoxGeometry(1,1,1)),cyl:G(new THREE.CylinderGeometry(.5,.5,1,12)),sphere:G(new THREE.SphereGeometry(.5,10,8)),leaf:G(new THREE.IcosahedronGeometry(.5,2))},materials={};
 function texture(color,kind,repeat=10){const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d');x.fillStyle=color;x.fillRect(0,0,128,128);const d=x.getImageData(0,0,128,128);for(let i=0;i<d.data.length;i+=4){const v=(random()-.5)*(kind==='grass'?42:kind==='wall'?16:22);for(let k=0;k<3;k++)d.data[i+k]+=v}x.putImageData(d,0,0);if(kind==='paving'||kind==='permeable'){x.strokeStyle=kind==='permeable'?'#849b82':'#aeb5b2';x.lineWidth=kind==='permeable'?2:.7;for(let y=0;y<128;y+=32){x.beginPath();x.moveTo(0,y);x.lineTo(128,y);x.stroke();for(let xx=y%64?16:0;xx<128;xx+=32){x.beginPath();x.moveTo(xx,y);x.lineTo(xx,y+32);x.stroke()}}}if(kind==='wood'){x.strokeStyle='#5c493366';for(let y=0;y<128;y+=8){x.beginPath();x.moveTo(0,y);x.bezierCurveTo(24,y+3,86,y-3,128,y);x.stroke()}}const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(repeat,repeat);t.colorSpace=THREE.SRGBColorSpace;textures.add(t);return t}
 function mat(name,color,opts={}){const m=M(new THREE.MeshStandardMaterial({color,roughness:.82,...opts}));m.name=name;materials[name]=m;return m}
 for(const [name,color,kind,repeat] of [['wall','#e4e8e6','wall',10],['stone','#bfc9c8','paving',3],['paving','#d3d8d4','paving',14],['permeable','#b2bbae','permeable',22],['grass','#275c3e','grass',18],['wood','#92724e','wood',3],['roof','#a3afad','wall',12]]){const m=mat(name,0xffffff,{map:texture(color,kind,repeat)});m.bumpMap=m.map;m.bumpScale=kind==='grass'?.035:.008}
 mat('trim',0xe2e7e2);mat('beige-panel',0xbac5cc);mat('frame',0xcedcdd,{roughness:.32,metalness:.65});mat('seal',0x354c53,{roughness:.7});
 for(const [name,color] of [['glass',0x427d9b],['glass-blue',0x6797ad],['glass-shadow',0x2a536e]]){const m=M(new THREE.MeshPhysicalMaterial({color,roughness:.19,metalness:.38,clearcoat:.7,clearcoatRoughness:.1,transmission:0}));m.name=name;materials[name]=m}
 mat('bridge-glass',0x8bb0bf,{opacity:.28,transparent:true,depthWrite:false,metalness:.2,roughness:.15});
 mat('window-lit',0x6d8b91,{emissive:0xffd5a0,emissiveIntensity:.01,metalness:.2,roughness:.3});mat('curtain',0xc8cfc8);mat('curtain-warm',0xd5cbb4);mat('metal',0x6b7d80,{metalness:.75,roughness:.32});mat('dark',0x263c43);mat('vent',0x4c6063,{metalness:.5});mat('leaf',0x356b42);mat('leaf-light',0x618149);mat('grass-blade',0x4d7c4c,{side:THREE.DoubleSide});mat('bark',0x77604c);mat('earth',0x675947);mat('flower',0xb7a8aa);mat('rubber',0xbca98d);mat('play-sage',0x7c9b94);mat('play-honey',0xc99d5e);mat('lamp',0xfff0ce,{emissive:0xffd89c,emissiveIntensity:.08});mat('skin',0xcbaa8c);mat('cloth',0x4c6c79);mat('cloth-warm',0xaf7b59);mat('bird',0x5b707b,{side:THREE.DoubleSide});
 const mx=new THREE.Matrix4(),p=new THREE.Vector3(),s=new THREE.Vector3(),q=new THREE.Quaternion(),e=new THREE.Euler();
 function part(type,m,pos,scale,rotation=0,owner='site',tier=0){const key=[type,m,owner,tier].join(':');if(!batches.has(key))batches.set(key,{type,m,owner,tier,items:[]});batches.get(key).items.push({p:pos,s:scale,r:Array.isArray(rotation)?rotation:[0,rotation,0]})}
 const box=(m,x,y,z,w,h,d,owner='site',tier=0)=>part('box',m,[x,y,z],[w,h,d],0,owner,tier);
 function beam(m,a,b,width=.07,owner='site',tier=1){const aa=new THREE.Vector3(...a),bb=new THREE.Vector3(...b),len=aa.distanceTo(bb),mid=aa.clone().add(bb).multiplyScalar(.5),rot=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),bb.sub(aa).normalize());part('cyl',m,mid.toArray(),[width,len,width],new THREE.Euler().setFromQuaternion(rot).toArray().slice(0,3),owner,tier)}
 function mesh(type,m,pos,scale,parent,name=''){const o=new THREE.Mesh(geo[type],materials[m]);o.position.fromArray(pos);o.scale.fromArray(scale);o.castShadow=!m.includes('glass');o.receiveShadow=true;o.name=name;parent.add(o);return o}
 function sign(text,pos,width,height,owner='site'){const c=document.createElement('canvas');c.width=512;c.height=128;const x=c.getContext('2d');x.fillStyle='#314e59';x.fillRect(0,0,512,128);x.textAlign='center';x.textBaseline='middle';x.fillStyle='#e4e9df';x.font='500 57px Microsoft YaHei';x.fillText(text,256,65,480);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;textures.add(t);const m=M(new THREE.MeshStandardMaterial({map:t,roughness:.7}));m.name='sign-'+text;const o=new THREE.Mesh(G(new THREE.PlaneGeometry(width,height)),m);o.position.fromArray(pos).sub(new THREE.Vector3(...origins.get(owner)));groups.get(owner).add(o)}

 function custom(name,points,indices,material,owner){const g=G(new THREE.BufferGeometry());const origin=new THREE.Vector3(...origins.get(owner));const local=points.map(p=>new THREE.Vector3(...p).sub(origin));g.setAttribute('position',new THREE.Float32BufferAttribute(local.flatMap(p=>p.toArray()),3));g.setAttribute('uv',new THREE.Float32BufferAttribute(points.flatMap(p=>[p[0]*.5,p[2]*.5]),2));g.setIndex(indices);g.computeVertexNormals();const o=new THREE.Mesh(g,materials[material]);o.name=name;o.castShadow=o.receiveShadow=true;groups.get(owner).add(o);return o}
 function slabSlope(owner,xx,base,start,dir,run,rise,width){const a=new THREE.Vector3(xx,base,start),b=new THREE.Vector3(xx,base+rise,start+dir*run),mid=a.clone().add(b).multiplyScalar(.5);part('box','stone',mid.toArray(),[width,.16,Math.hypot(run,rise)],[-Math.atan2(rise,dir*run),0,0],owner,1)}
 function floorWithWell(m,x,y,z,w,h,d,owner,tier=0){const cx=x-3,cz=z-3,hx=2.78,hz=4.25,left=x-w/2,right=x+w/2,back=z-d/2,front=z+d/2;box(m,(left+cx-hx)/2,y,z,cx-hx-left,h,d,owner,tier);box(m,(right+cx+hx)/2,y,z,right-cx-hx,h,d,owner,tier);box(m,cx,y,(back+cz-hz)/2,hx*2,h,cz-hz-back,owner,tier);box(m,cx,y,(front+cz+hz)/2,hx*2,h,front-cz-hz,owner,tier)}
 const ecology=createEcology({THREE,G,geo,materials,mat,part,box,random,coarse,textures,groups,manifest});
 const stairs=createStairs({THREE,group,part,box,beam,coarse,manifest,groups,custom,slabSlope});
 // Native metric site, with mineral paving and no host roads in the module.
 box('paving',0,-.2,0,112,.4,112);
 for(const x of [-46,46])box('permeable',x,.04,0,6,.08,98);
 for(const z of [-46,46])box('permeable',0,.04,z,98,.08,6);
 box('permeable',46,.04,52.5,6,.08,7);
 box('grass',0,.04,-17,84,.08,49,'landscape');
 box('grass',0,.04,30,84,.08,15,'landscape');
 box('paving',0,.12,39,84,.24,5);box('paving',0,.12,-41,84,.24,2);box('paving',0,.12,49,8,.24,14);
 for(const x of [-41,41])box('paving',x,.12,0,2,.24,84);
 for(const x of [-23,24])box('paving',x,.12,27,8,.24,25);
 box('paving',1.5,.13,2,12,.26,65);
 const specs=[['main',-23,-6,24,28,30],['annex',24,3,16,24,26]];
 for(const [id,x,z,floors,w,d] of specs){
  const roofY=4.8+(floors-1)*4,height=roofY+3.2;
  const g=group(id,id==='main'?'主楼 · 24层':'辅楼 · 16层',root,[x,0,z]);buildings.set(id,g);
  for(const [key,name] of [['facade','幕墙与楼板'],['roof','屋顶与机电'],['entrance','门厅与雨棚'],['interior','会议室与办公']])group(id+'-'+key,(id==='main'?'主楼':'辅楼')+' / '+name,g,[0,0,0],id);
  manifest.buildings.push({id,name:id==='main'?'总部主楼':'总部辅楼',x,z,w,d,floors,height,roofY,lobbyHeight:4.8,standardFloorHeight:4,groundY:0});
  const f=id+'-facade',r=id+'-roof',en=id+'-entrance',inside=id+'-interior';
  box('stone',x,.2,z,w+.6,.4,d+.6,f);
  if(coarse){box('glass',x,roofY/2,z,w,roofY,d,f)}else{
   const nx=id==='main'?14:12,nz=id==='main'?15:13;
   for(let fl=0;fl<floors;fl++){
    const base=fl===0?.65:4.8+(fl-1)*4,fh=fl===0?4.15:4,cy=base+fh/2;
    floorWithWell('dark',x,base+.12,z,w-.22,.24,d-.22,f);floorWithWell('trim',x,base+.03,z,w+.06,.07,d+.06,f);
    for(const side of [-1,1]){
     const front=z+side*d/2;
     for(let j=0;j<nx;j++){
      const xx=x-w/2+(j+.5)*w/nx;
      if(fl===0&&side===1&&Math.abs(xx-x)<2.5)continue;
      const lit=fl>0&&(fl*7+j+side)%13===0;
      box(lit?'window-lit':['glass','glass-blue','glass-shadow'][(fl+j*7)%3],xx,cy,front-side*.09,w/nx-.11,fh-.16,.045,f);
      box('glass-shadow',xx,base+.38,front+side*.01,w/nx-.08,.55,.075,f);
      box('frame',xx,base+fh-.03,front+side*.05,w/nx,.075,.18,f);
      if(fl>0&&j%4===0)box('curtain',xx+.55,cy,front-side*.14,.6,fh-.4,.02,f,1);
      if((fl+j)%9===0)box('frame',xx,cy+.4,front+side*.075,w/nx-.1,.04,.09,f,2);
     }
     for(let j=0;j<=nx;j++)box('frame',x-w/2+j*w/nx,cy,front+side*.06,.095,fh,.24,f);
    }
    for(const side of [-1,1]){
     const front=x+side*w/2;
     for(let j=0;j<nz;j++){
      const zz=z-d/2+(j+.5)*d/nz;
      // True aligned bridge door openings, rather than a corridor penetrating the glass.
      if(fl===9&&side===(id==='main'?1:-1)&&Math.abs(zz-3)<3.15)continue;
      box((fl+j)%11===0?'window-lit':['glass','glass-blue','glass-shadow'][(fl+j)%3],front-side*.09,cy,zz,.045,fh-.16,d/nz-.11,f);
      box('glass-shadow',front+side*.01,base+.38,zz,.075,.55,d/nz-.08,f);
      box('frame',front+side*.05,base+fh-.03,zz,.18,.075,d/nz,f);
     }
     for(let j=0;j<=nz;j++){const zz=z-d/2+j*d/nz;if(fl===9&&side===(id==='main'?1:-1)&&Math.abs(zz-3)<2.8)continue;box('frame',front+side*.06,cy,zz,.24,fh,.095,f)}
    }
    for(const sx of [-1,1])for(const sz of [-1,1])box('frame',x+sx*w/2,cy,z+sz*d/2,.28,fh,.28,f);
   }
   // Perimeter fins emphasize a slim silver corporate grid.
   for(const dx of [-w/2,-w/4,0,w/4,w/2])for(const sz of [-1,1])box('frame',x+dx,roofY/2,z+sz*(d/2+.18),.13,roofY,.45,f,1);
  }
  // Core, lift indicator, lobbies and selected furnished office floors.
  for(const dx of [-2.9,2.9])box('stone',x-3+dx,roofY/2,z-3,.2,roofY,8.7,inside);box('stone',x-3,roofY/2,z-7.25,5.6,roofY,.2,inside);box('stone',x-3,roofY/2,z+1.25,5.6,roofY,.2,inside);stairs.internal(id,x,z,floors,roofY);
  for(const side of [-1,1])box('metal',x-3+side*1.1,2,z-.44,1.7,3,.08,inside,1);
  const lift=new THREE.Group();lift.name=id+' lift indicator';lift.position.set(-5.8,2,-.3);groups.get(inside).add(lift);mesh('box','lamp',[0,0,0],[.16,.7,.08],lift);elevators.push(lift);
  const selectedFloors=coarse?[0]:[0,4,9,floors-3];
  for(const fl of selectedFloors){const y=fl===0?.69:4.8+(fl-1)*4+.27;
   for(const side of [-1,1])for(let j=0;j<4;j++){const xx=x+side*(w/2-4),zz=z-d/2+4+j*5.3;box('wood',xx,y+.8,zz,2,.1,1,inside,1);for(const sx of [-.7,.7])box('metal',xx+sx,y+.4,zz,.07,.75,.7,inside,2);box('dark',xx,y+1.15,zz-.25,.9,.52,.06,inside,1);box('dark',xx,y+.56,zz+1,.7,.12,.65,inside,1);box('metal',xx,y+.3,zz+1,.1,.5,.1,inside,2);box('dark',xx,y+.9,zz+1.28,.7,.6,.08,inside,1)}
   box('wood',x,y+.85,z+6,6,.12,2,inside,1);for(let j=0;j<4;j++)for(const side of [-1,1]){box('dark',x-2.2+j*1.5,y+.55,z+6+side*1.6,.65,.12,.65,inside,1);box('metal',x-2.2+j*1.5,y+.3,z+6+side*1.6,.08,.5,.08,inside,2)}
   box('glass-blue',x,y+1.8,z+8,9,3.1,.025,inside,1);
  }
  const front=z+d/2;
  stairs.entrance(id,x,z,front);box('metal',x,4.05,front+2.5,10,.2,6,en);box('glass-blue',x,4.18,front+2.5,9.6,.04,5.6,en);
  for(const dx of [-4.5,4.5])box('metal',x+dx,2.05,front+4.8,.12,4.1,.12,en);
  for(const side of [-1,1]){const door=mesh('box','glass-blue',[side*.8,2.3,d/2+.12],[1.55,3.25,.045],groups.get(en),id+' sensed door '+side);doors.push({object:door,base:side*.8,side,x,z:front+1});box('frame',x+side*1.62,2.3,front+.18,.08,3.4,.14,en)}
  box('stone',x+3,1,front-4,4,1.4,1.1,inside);sign(id==='main'?'衡联 · 总部门厅':'衡联 · 商务中心',[x,3.65,front+.22],4.6,.45,en);
  box('lamp',x,4.07,front+4.7,8,.06,.12,en,1);manifest.lightFixtures.push({position:[x,3.5,front+2],type:'point',power:90,distance:16});
  // Flat roof: closed parapets, cap flashings, plant screens and service routes.
  floorWithWell('roof',x,roofY,z,w,.18,d,r);
  for(const sx of [-1,1]){box('trim',x+sx*(w/2-.15),roofY+.5,z,.3,1,d,r);box('frame',x+sx*(w/2-.15),roofY+1.03,z,.42,.08,d+.2,r,1)}
  for(const sz of [-1,1]){box('trim',x,roofY+.5,z+sz*(d/2-.15),w-.3,1,.3,r);box('frame',x,roofY+1.03,z+sz*(d/2-.15),w-.2,.08,.42,r,1)}
  box('wall',x-3,roofY+1.5,z-3,6,3,9,r);box('frame',x-3,roofY+3.1,z-3,6.3,.2,9.3,r);box('vent',x-3,roofY+1.2,z+.04,1.3,2.2,.08,r,1);
  for(const rx of [3.5,8.2])for(const rz of [-5,1.5]){box('metal',x+rx,roofY+.15,z+rz,3.3,.3,4,r,1);box('trim',x+rx,roofY+.8,z+rz,3,1.3,3.7,r,1);for(const sx of [-1,1]){box('vent',x+rx+sx*1.52,roofY+.8,z+rz,.04,.95,3.4,r,1);for(let n=0;n<8;n++)box('metal',x+rx+sx*1.55,roofY+.4+n*.115,z+rz,.04,.035,3.4,r,2)}part('cyl','dark',[x+rx,roofY+1.48,z+rz],[2.2,.04,2.2],0,r,1);const fan=new THREE.Group();fan.name=id+' roof fan';fan.position.set(rx,roofY+1.52,rz);groups.get(r).add(fan);for(let n=0;n<3;n++){const blade=mesh('box','metal',[0,0,0],[1.9,.025,.16],fan);blade.rotation.y=n*Math.PI/3}fans.push(fan)}
  for(const sz of [-1,1]){beam('metal',[x-10,roofY+.45,z+sz*8],[x+10,roofY+.45,z+sz*8],.5,r,1);for(let j=0;j<6;j++)box('metal',x-9+j*3.4,roofY+.2,z+sz*8,.7,.4,.8,r,2)}
  for(let j=0;j<10;j++)box('seal',x-w/2+1+j*(w-2)/10,roofY+.101,z,.02,.012,d-1,r,2);
  for(const sx of [-1,1])for(const sz of [-1,1]){part('cyl','metal',[x+sx*(w/2-1),roofY+.14,z+sz*(d/2-1)],[.4,.06,.4],0,r,1);box('metal',x+sx*(w/2-.8),roofY+1.6,z+sz*(d/2-.8),.035,1.1,.035,r,1)}
 }
 // Freestanding, aligned bridge. Main wall x=-9; annex wall x=12; clear span 21m.
 group('bridge','空中连廊 · 第10层');
 const bridgeY=36.8;
 box('metal',1.5,bridgeY+.1,3,21.4,.2,6.5,'bridge');box('paving',1.5,bridgeY+.235,3,21,.07,6,'bridge');box('metal',1.5,41.1,3,21.4,.2,6.5,'bridge');
 for(const sz of [-1,1]){
  const zz=3+sz*3.05;box('metal',1.5,37.05,zz,21.3,.25,.16,'bridge');box('metal',1.5,40.8,zz,21.3,.3,.18,'bridge');
  for(let j=0;j<10;j++){const xx=-9+(j+.5)*2.1;box('bridge-glass',xx,39,zz,2.02,3.55,.035,'bridge');box('frame',xx-1.05,39,zz+sz*.03,.075,3.7,.12,'bridge');box('frame',xx,38.15,zz+sz*.1,2.1,.045,.08,'bridge',1);if(j%2===0){beam('metal',[xx-1,37.2,zz],[xx+1,40.7,zz],.075,'bridge',1)}}
  box('lamp',1.5,40.67,3+sz*2.4,20,.05,.1,'bridge',1);
 }
 for(const xx of [-8.8,11.8]){box('seal',xx,bridgeY+.245,3,.12,.035,6,'bridge',1);box('metal',xx,38.9,-.2,.15,4.2,.15,'bridge',2);box('metal',xx,38.9,6.2,.15,4.2,.15,'bridge',2)}
 for(let j=0;j<11;j++){const xx=-9+j*2.1;box('metal',xx,36.75,3,.12,.3,6.5,'bridge',1);for(const sz of [-1,1])box('metal',xx,36.45,3+sz*2.8,.3,.4,.35,'bridge',2)}
 // Bolted end plates and sliding bearing seats remain separate from the clear passage.
 for(const xx of [-8.7,11.7])for(const zz of [.2,5.8]){box('metal',xx,37.0,zz,.6,.12,.6,'bridge',2);for(const dx of [-.18,.18])for(const dz of [-.18,.18])part('cyl','frame',[xx+dx,37.09,zz+dz],[.07,.065,.07],0,'bridge',2)}
 // Keep the passage unobstructed; signage is above head level.
 sign('总部主楼  ←   SKY LINK   →  商务中心',[1.5,40.42,6.14],8,.35,'bridge');
 manifest.bridge={id:'bridge',floor:36.8,top:41.2,clearSpan:21,width:6,entrances:[[-9,37.07,3],[12,37.07,3]]};
 manifest.lightFixtures.push({position:[-4,40,3],type:'point',power:45,distance:10},{position:[7,40,3],type:'point',power:45,distance:10});
 // Landscape: formal square lawns, rows of trees, meeting terrace and restrained business plaza.
 const tree=ecology.tree;
 for(const x of [-52,52])for(let z=-42;z<=42;z+=12)tree(x,z,.9);
 for(const z of [-52,52])for(const x of [-38,-25,-12,12,25,38])tree(x,z,.85);
 for(const x of [-10,10])for(const z of [24,34])tree(x,z,.9);
 for(let x=-34;x<=34;x+=2.2){if(Math.abs(x)<5)continue;ecology.shrub(x,34,1.4)}
 function bench(x,z){for(const dx of [-1.1,1.1])box('metal',x+dx,.4,z,.08,.7,.6,'landscape',1);for(let j=0;j<4;j++)box('wood',x,.78,z-.3+j*.2,2.7,.09,.14,'landscape',1);for(let j=0;j<3;j++)box('wood',x,1+j*.18,z-.4,2.7,.12,.08,'landscape',1)}
 for(const x of [-12,12])for(const z of [25,31]){box('paving',x,.13,z,5,.26,3,'playground');bench(x,z)}
 box('stone',-13,1.3,51,16,2.6,.7);sign('衡 联 企 业 总 部',[-13,1.65,51.37],14,.8);sign('HENGLIAN  /  CORPORATE CAMPUS',[-13,.65,51.38],13,.28);
 box('stone',10,1.3,51,4,2.6,4);box('metal',10,2.7,51,4.5,.2,4.5);box('glass',10,1.65,53.03,3.3,1.4,.045);box('glass',12.03,1.65,51,.045,1.4,3.3);
 for(let j=0;j<8;j++){const x=24+j*1.5;beam('metal',[x,.2,51],[x,1,51],.065);beam('metal',[x,1,51],[x,1,52.3],.065);beam('metal',[x,1,52.3],[x,.2,52.3],.065)}
 for(const [x,z] of [[-41,38],[41,38],[-41,-35],[41,-35],[-5,22],[5,22],[0,49],[0,-45]]){part('cyl','metal',[x,2,z],[.09,4,.09]);box('metal',x,3.95,z,.55,.1,.55);box('lamp',x,3.8,z,.32,.2,.32);manifest.lightFixtures.push({position:[x,3.55,z],type:'point',power:60,distance:16})}
 for(const x of [-8,8])for(const z of [24,34]){box('metal',x,.4,z,.18,.8,.18,'site',1);box('lamp',x,.82,z,.25,.1,.25,'site',1)}
 for(const x of [-39,39])for(const z of [-38,38]){box('metal',x,.65,z,.5,1,.5,'site',1);box('dark',x,.98,z+.26,.35,.2,.025,'site',1)}
 for(const z of [-41,41])for(let x=-36;x<=36;x+=5){box('vent',x,.25,z,.6,.025,.4,'site',2);for(let j=0;j<5;j++)box('metal',x-.25+j*.12,.27,z,.035,.012,.35,'site',2)}
 for(const x of [-54.7,54.7])for(const y of [.4,.85,1.2])box('metal',x,y,0,.035,.035,109,'site',1);
 for(const z of [-54.7,54.7])for(const x of [-29,29])for(const y of [.4,.85,1.2])box('metal',x,y,z,50,.035,.035,'site',1);
 for(const xx of [-23,24])for(let zz=23;zz<39;zz+=1.2)box('seal',xx,.242,zz,7.9,.002,.009,'site',2);
 for(let xx=-39;xx<=39;xx+=1.2)box('seal',xx,.242,39,.009,.002,4.8,'site',2);
 ecology.grass(specs);manifest.ecology=ecology.counts;
 for(const b of batches.values()){const parent=groups.get(b.owner),o=new THREE.InstancedMesh(geo[b.type],materials[b.m],b.items.length);o.name=b.owner+':'+b.m+':'+b.tier;o.userData.tier=b.tier;o.castShadow=!['glass','glass-blue','glass-shadow','bridge-glass','window-lit','lamp','grass'].includes(b.m);o.receiveShadow=true;const origin=new THREE.Vector3(...origins.get(b.owner));for(let i=0;i<b.items.length;i++){const it=b.items[i];p.fromArray(it.p).sub(origin);s.fromArray(it.s);q.setFromEuler(e.set(...it.r));mx.compose(p,q,s);o.setMatrixAt(i,mx)}o.computeBoundingSphere();parent.add(o)}
 for(const name of ['foliage-sun','foliage-shade','foliage-young','grass-blade','curtain','curtain-warm'])materials[name].onBeforeCompile=shader=>{shader.uniforms.windTime={value:0};shaders.push(shader);shader.vertexShader='uniform float windTime;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n#ifdef USE_INSTANCING\ntransformed.x+=sin(windTime*1.15+instanceMatrix[3].x*.3+instanceMatrix[3].z*.2)*.025*(position.y+.5);\n#endif')};
 function person(i){const g=new THREE.Group();g.name='Resident '+i;groups.get('life').add(g);mesh('sphere','skin',[0,1.65,0],[.3,.36,.3],g);mesh('box',i%2?'cloth':'cloth-warm',[0,1.13,0],[.42,.65,.25],g);const limbs=[];for(const sx of [-1,1]){const leg=new THREE.Group();leg.position.set(sx*.12,.82,0);g.add(leg);mesh('box','dark',[0,-.35,0],[.14,.7,.17],leg);limbs.push(leg);const arm=new THREE.Group();arm.position.set(sx*.28,1.35,0);g.add(arm);mesh('box','skin',[0,-.25,0],[.11,.5,.13],arm);limbs.push(arm)}return{g,limbs,i}}
 for(let i=0;i<22;i++)people.push(person(i));
 const bg=G(new THREE.BufferGeometry());bg.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,-.6,.1,.25,-.15,0,.3,0,0,0,.15,0,.3,.6,.1,.25],3));bg.computeVertexNormals();for(let i=0;i<5;i++){const b=new THREE.Mesh(bg,materials.bird);b.name='Courtyard bird '+i;groups.get('life').add(b);birds.push(b)}
 function squareRoute(distance,h){const d=((distance%(8*h))+8*h)%(8*h),seg=Math.floor(d/(2*h)),t=d%(2*h);return seg===0?[h,-h+t,0]:seg===1?[h-t,h,-Math.PI/2]:seg===2?[-h,h-t,Math.PI]:[-h+t,-h,Math.PI/2]}
 function update(delta=0){if(disposed)return;const dt=enabled&&Number.isFinite(delta)?THREE.MathUtils.clamp(delta,0,.25):0;time+=dt;if(activity.wind)windTime+=dt;shaders.forEach(s=>s.uniforms.windTime.value=windTime);
  for(const a of people){let x,z,yaw,y=.23;
   if(a.i<8){const d=(time*.75+a.i*5.5)%68;x=d<34?-17+d:51-d;z=3+(a.i%2?.8:-.8);y=37.07;yaw=d<34?Math.PI/2:-Math.PI/2}
   else if(a.i<14){const d=(time*.7+a.i*13)%160;x=d<80?-40+d:120-d;z=39+(a.i%2?.6:-.6);yaw=d<80?Math.PI/2:-Math.PI/2}
   else if(a.i<20){[x,z,yaw]=squareRoute(time*.72+a.i*39,41)}
   else {x=a.i===20?-23:24;const d=(time*.55+a.i*3)%12;const front=a.i===20?9:16;z=front+1+(d<6?d:12-d);yaw=d<6?0:Math.PI;const approach=z-front;y=approach<5.2?.69:approach<5.6?.69:approach<6?.54:approach<6.4?.39:.24}
   a.g.position.set(x,y,z);a.g.rotation.y=yaw;a.g.visible=activity.people&&(a.i>=8||activity.bridge)&&(level!=='low'||a.i<4||a.i>17);a.limbs.forEach((l,j)=>l.rotation.x=Math.sin(time*4+a.i+(j===0||j===3?0:Math.PI))*(j%2?.25:.35))
  }
  for(const d of doors){const near=activity.people&&people.some(a=>a.i>=8&&a.g.visible&&Math.hypot(a.g.position.x-d.x,a.g.position.z-d.z)<4);const wanted=d.base+d.side*(near?.72:0);d.object.position.x+=(wanted-d.object.position.x)*Math.min(1,dt*4)}
  if(activity.mechanical)elevators.forEach((lift,i)=>{const b=manifest.buildings[i],height=b.roofY-5;lift.position.y=2+(.5+.5*Math.sin(time*.12+i*2))*height});
  if(activity.mechanical)fans.forEach(f=>f.rotation.y+=dt*4);
  birds.forEach((b,i)=>{const a=time*.12+i*1.256;b.position.set(Math.sin(a)*18,15+i*2+Math.sin(a*2)*.6,Math.cos(a)*18);b.rotation.y=-a;b.rotation.z=Math.sin(time*5+i)*.22;b.visible=activity.birds&&level!=='low'})
 }
 function setQuality(value){if(!['high','medium','low'].includes(value))throw new Error('Unknown quality');level=value;root.traverse(o=>{if(o.userData.tier)o.visible=value==='high'||value==='medium'&&o.userData.tier<2});for(const m of ecology.grassMeshes)m.count=m.userData[value==='high'?'highCount':value==='medium'?'mediumCount':'lowCount'];update(0)}
 function setTimeOfDay(value){const n=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.4:0;materials.lamp.emissiveIntensity=.08+n*3;materials['window-lit'].emissiveIntensity=.01+n*1.3}
 function exportScene(){root.updateWorldMatrix(true,true);const gs={},ms={},objects=[];root.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry,m=o.material;if(!gs[g.uuid])gs[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null,colors:g.attributes.color?Array.from(g.attributes.color.array):null};if(!ms[m.uuid])ms[m.uuid]={name:m.name,color:m.color.toArray(),vertexColors:m.vertexColors,roughness:m.roughness,metalness:m.metalness,opacity:m.opacity,transparent:m.transparent,transmission:m.transmission||0,emissive:m.emissive.toArray(),emissiveIntensity:m.emissiveIntensity,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};let owner=o;while(owner!==root&&!owner.userData.id)owner=owner.parent;for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,mx);mx.premultiply(o.matrixWorld)}else mx.copy(o.matrixWorld);objects.push({g:g.uuid,m:m.uuid,matrix:mx.toArray(),owner:owner.userData.id||'site'})}});return{format:'henglian-corporate-headquarters-v1',manifest,snapshotSpace:'world',geometries:gs,materials:ms,objects}}
 function dispose(){if(disposed)return;disposed=true;root.removeFromParent();root.traverse(o=>{if(o.isInstancedMesh)o.dispose()});geometries.forEach(g=>g.dispose());materialSet.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());root.clear();groups.clear();buildings.clear();batches.clear()}
 setQuality(quality);update(0);
 return{root,groups,buildings,main:buildings.get('main'),annex:buildings.get('annex'),bridge:groups.get('bridge'),manifest,getManifest:()=>JSON.parse(JSON.stringify(manifest)),update,setQuality,setTimeOfDay,setDynamicsEnabled:v=>enabled=!!v,setActivity:v=>{for(const k of Object.keys(activity))if(k in v)activity[k]=!!v[k];update(0)},exportScene,dispose,get quality(){return level},get simulationTime(){return time},get disposed(){return disposed}};
}
