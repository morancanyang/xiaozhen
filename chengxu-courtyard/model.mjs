/** Metric, renderer-independent residential parcel. All texture data is generated locally. */
export function createResidentialCourtyard({THREE,blockSize=112,quality='high',coarse=false}={}) {
 if(!THREE?.Group||!Number.isFinite(blockSize)||blockSize<=0)throw new Error('THREE and positive blockSize required');
 const root=new THREE.Group();root.name='澄序住区';root.scale.setScalar(blockSize/112);
 const groups=new Map(),buildings=new Map(),batches=new Map(),geometries=new Set(),materialSet=new Set(),textures=new Set(),origins=new Map(),shaders=[],doors=[],fans=[],people=[],birds=[];
 let seed=20261106,time=0,windTime=0,level=quality,enabled=true,disposed=false;
 const activity={wind:true,people:true,birds:true,mechanical:true};
 const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 const manifest={id:'chengxu-residential-courtyard',name:'澄序住区',version:1,units:'m',upAxis:'Y',front:'+Z',pivot:'ground-center',footprint:{width:blockSize,depth:blockSize},nativeSize:112,nativeBounds:{min:[-56,-.4,-56],max:[56,78,56]},surfacePolicy:'Stone / permeable pavers / lawn. No asphalt. External municipal roads belong to the host.',buildings:[],parts:[],entrances:{public:{position:[0,0,56],width:8},service:{position:[46,0,56],width:6}},lightFixtures:[],motion:{peopleCount:22,birdCount:5,vehicleCount:0,walkwayCenterline:41},recommendedHost:{pointLightBudget:4,waterReflectionPasses:0,transmissionPasses:0}};
 function group(id,name,parent=root,origin=[0,0,0],buildingId=null){const g=new THREE.Group();g.name=id;g.userData={id,partId:id,name,buildingId};g.position.fromArray(origin);parent.add(g);groups.set(id,g);origins.set(id,buildingId?origins.get(buildingId):origin);manifest.parts.push({id,name,buildingId});return g}
 for(const [id,name] of [['site','场地与透水铺装'],['landscape','草坪与庭院绿化'],['playground','儿童与休憩花园'],['life','居民与飞鸟']])group(id,name);
 const G=g=>(geometries.add(g),g),M=m=>(materialSet.add(m),m),geo={box:G(new THREE.BoxGeometry(1,1,1)),cyl:G(new THREE.CylinderGeometry(.5,.5,1,12)),sphere:G(new THREE.SphereGeometry(.5,10,8)),leaf:G(new THREE.IcosahedronGeometry(.5,2))},materials={};
 function texture(color,kind,repeat=10){const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d');x.fillStyle=color;x.fillRect(0,0,128,128);const d=x.getImageData(0,0,128,128);for(let i=0;i<d.data.length;i+=4){const v=(random()-.5)*(kind==='grass'?42:kind==='wall'?16:22);for(let k=0;k<3;k++)d.data[i+k]+=v}x.putImageData(d,0,0);if(kind==='paving'||kind==='permeable'){x.strokeStyle=kind==='permeable'?'#849b82':'#aeb5b2';x.lineWidth=kind==='permeable'?2:.7;for(let y=0;y<128;y+=32){x.beginPath();x.moveTo(0,y);x.lineTo(128,y);x.stroke();for(let xx=y%64?16:0;xx<128;xx+=32){x.beginPath();x.moveTo(xx,y);x.lineTo(xx,y+32);x.stroke()}}}if(kind==='wood'){x.strokeStyle='#5c493366';for(let y=0;y<128;y+=8){x.beginPath();x.moveTo(0,y);x.bezierCurveTo(24,y+3,86,y-3,128,y);x.stroke()}}const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(repeat,repeat);t.colorSpace=THREE.SRGBColorSpace;textures.add(t);return t}
 function mat(name,color,opts={}){const m=M(new THREE.MeshStandardMaterial({color,roughness:.82,...opts}));m.name=name;materials[name]=m;return m}
 for(const [name,color,kind,repeat] of [['wall','#e4e8e6','wall',10],['stone','#bfc9c8','paving',3],['paving','#d3d8d4','paving',14],['permeable','#b2bbae','permeable',22],['grass','#275c3e','grass',18],['wood','#92724e','wood',3],['roof','#a3afad','wall',12]]){const m=mat(name,0xffffff,{map:texture(color,kind,repeat)});m.bumpMap=m.map;m.bumpScale=kind==='grass'?.035:.008}
 mat('trim',0xe2e7e2);mat('beige-panel',0xc9c5b7);mat('frame',0xcedcdd,{roughness:.32,metalness:.65});mat('seal',0x354c53,{roughness:.7});
 for(const [name,color] of [['glass',0x527e91],['glass-blue',0x628a9a],['glass-shadow',0x375867]]){const m=M(new THREE.MeshPhysicalMaterial({color,roughness:.19,metalness:.38,clearcoat:.7,clearcoatRoughness:.1,transmission:0}));m.name=name;materials[name]=m}
 mat('window-lit',0x6d8b91,{emissive:0xffd5a0,emissiveIntensity:.01,metalness:.2,roughness:.3});mat('curtain',0xc8cfc8);mat('curtain-warm',0xd5cbb4);mat('metal',0x6b7d80,{metalness:.75,roughness:.32});mat('dark',0x263c43);mat('vent',0x4c6063,{metalness:.5});mat('leaf',0x356b42);mat('leaf-light',0x618149);mat('grass-blade',0x4d7c4c,{side:THREE.DoubleSide});mat('bark',0x77604c);mat('earth',0x675947);mat('flower',0xb7a8aa);mat('rubber',0xbca98d);mat('play-sage',0x7c9b94);mat('play-honey',0xc99d5e);mat('lamp',0xfff0ce,{emissive:0xffd89c,emissiveIntensity:.08});mat('skin',0xcbaa8c);mat('cloth',0x4c6c79);mat('cloth-warm',0xaf7b59);mat('bird',0x5b707b,{side:THREE.DoubleSide});
 const mx=new THREE.Matrix4(),p=new THREE.Vector3(),s=new THREE.Vector3(),q=new THREE.Quaternion(),e=new THREE.Euler();
 function part(type,m,pos,scale,rotation=0,owner='site',tier=0){const key=[type,m,owner,tier].join(':');if(!batches.has(key))batches.set(key,{type,m,owner,tier,items:[]});batches.get(key).items.push({p:pos,s:scale,r:Array.isArray(rotation)?rotation:[0,rotation,0]})}
 const box=(m,x,y,z,w,h,d,owner='site',tier=0)=>part('box',m,[x,y,z],[w,h,d],0,owner,tier);
 function beam(m,a,b,width=.07,owner='site',tier=1){const aa=new THREE.Vector3(...a),bb=new THREE.Vector3(...b),len=aa.distanceTo(bb),mid=aa.clone().add(bb).multiplyScalar(.5),rot=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),bb.sub(aa).normalize());part('cyl',m,mid.toArray(),[width,len,width],new THREE.Euler().setFromQuaternion(rot).toArray().slice(0,3),owner,tier)}
 function mesh(type,m,pos,scale,parent,name=''){const o=new THREE.Mesh(geo[type],materials[m]);o.position.fromArray(pos);o.scale.fromArray(scale);o.castShadow=!m.includes('glass');o.receiveShadow=true;o.name=name;parent.add(o);return o}
 function sign(text,pos,width,height,owner='site'){const c=document.createElement('canvas');c.width=512;c.height=128;const x=c.getContext('2d');x.fillStyle='#314e59';x.fillRect(0,0,512,128);x.textAlign='center';x.textBaseline='middle';x.fillStyle='#e4e9df';x.font='500 57px Microsoft YaHei';x.fillText(text,256,65,480);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;textures.add(t);const m=M(new THREE.MeshStandardMaterial({map:t,roughness:.7}));m.name='sign-'+text;const o=new THREE.Mesh(G(new THREE.PlaneGeometry(width,height)),m);o.position.fromArray(pos).sub(new THREE.Vector3(...origins.get(owner)));groups.get(owner).add(o)}
 // One square parcel; every internal circulation surface is light mineral or permeable paving.
 box('paving',0,-.2,0,112,.4,112);box('grass',0,.035,0,85,.07,85,'landscape');
 for(const x of [-46,46])box('permeable',x,.045,0,6,.09,98);for(const z of [-46,46])box('permeable',0,.045,z,98,.09,6);
 box('permeable',46,.045,52.5,6,.09,7);box('paving',0,.11,0,4,.22,112);box('paving',0,.11,0,85,.22,4);
 for(const x of [-41,41])box('paving',x,.11,0,2,.22,84);for(const z of [-41,41])box('paving',0,.11,z,80,.22,2);
 for(const x of [-26,26]){box('paving',x,.11,-7,3,.22,14);box('paving',x,.11,39,3,.22,4)}
 const specs=[['A',-26,-26,20],['B',26,-26,22],['C',-26,26,22],['D',26,26,24]];
 for(const [id,x,z,floors] of specs){
  const roofY=4.2+(floors-1)*3.1,height=roofY+2.5,g=group(id,id+'栋 · '+floors+'层',root,[x,0,z]);buildings.set(id,g);
  for(const [key,name] of [['facade','立面与窗框'],['roof','屋顶与机电'],['entrance','门厅与雨棚']])group(id+'-'+key,id+'栋 / '+name,g,[0,0,0],id);
  manifest.buildings.push({id,name:id+'栋',x,z,w:22,d:20,floors,height,roofY,groundY:0,lobbyHeight:4.2,standardFloorHeight:3.1});
  const f=id+'-facade',r=id+'-roof',en=id+'-entrance';
  box('stone',x,.19,z,22.5,.38,20.5,f);box('roof',x,roofY-.1,z,22,.2,20,r);
  if(coarse){box('wall',x,roofY/2,z,22,roofY,20,f)}else{
   // Actual floor plates and hollow infill elevations; the window recesses have geometric depth.
   for(let fl=0;fl<floors;fl++){
    const base=fl===0?.3:4.2+(fl-1)*3.1,fh=fl===0?3.9:3.1,cy=base+fh*.57;
    box('trim',x,base+.055,z,22.16,.11,20.16,f);box('dark',x,base+.15,z,21.45,.08,19.45,f,1);
    for(const side of [-1,1]){
     const zz=z+side*9.83;
     box(fl===0?'stone':'wall',x,base+.47,zz,22,.83,.34,f);box('wall',x,base+fh-.27,zz,22,.54,.34,f);
     for(let j=0;j<=8;j++)box(j===2||j===6?'beige-panel':'wall',x-10.75+j*2.6875,cy,zz,j===0||j===8?.5:.65,fh-1.3,.34,f);
     for(let j=0;j<8;j++){
      if(fl===0&&side===1&&(j===3||j===4))continue;
      const xx=x+(j-3.5)*2.6875,lit=(fl*13+j+side+id.charCodeAt(0))%9===0,front=zz+side*.02,wh=fh-1.43;
      box('seal',xx,cy,front-side*.09,2.08,wh+.12,.08,f);
      box(lit?'window-lit':['glass','glass-blue','glass-shadow'][(fl+j)%3],xx,cy,front,1.96,wh,.045,f);
      for(const dx of [-1.02,1.02])box('frame',xx+dx,cy,front+side*.06,.07,wh+.13,.14,f);
      for(const dy of [-wh/2-.04,wh/2+.04])box('frame',xx,cy+dy,front+side*.06,2.1,.07,.14,f);
      box('frame',xx,cy,front+side*.07,.045,wh,.11,f,1);box('frame',xx,cy+.25,front+side*.08,2,.045,.1,f,1);
      box('trim',xx,cy-wh/2-.14,front+side*.12,2.2,.13,.4,f,1);
      if(j%3!==0){box((fl+j)%2?'curtain':'curtain-warm',xx+.55,cy,front-side*.075,.65,wh-.08,.012,f,1)}
     }
    }
    for(const side of [-1,1]){
     const xx=x+side*10.83;box(fl===0?'stone':'wall',xx,base+.47,z,.34,.83,19.5,f);box('wall',xx,base+fh-.27,z,.34,.54,19.5,f);
     for(let j=0;j<=7;j++)box(j===3?'beige-panel':'wall',xx,cy,z-9.65+j*2.757,.34,fh-1.3,j===0||j===7?.7:.8,f);
     for(let j=0;j<7;j++){const zz=z+(j-3)*2.757,wh=fh-1.43;
      box((fl+j)%8===0?'window-lit':j%2?'glass':'glass-blue',xx+side*.02,cy,zz,.045,wh,1.9,f);
      for(const dz of [-.99,.99])box('frame',xx+side*.08,cy,zz+dz,.14,wh+.13,.07,f);
      for(const dy of [-wh/2-.04,wh/2+.04])box('frame',xx+side*.08,cy+dy,zz,.14,.07,2.06,f);
      box('frame',xx+side*.09,cy,zz,.1,wh,.045,f,1);box('trim',xx+side*.1,cy-wh/2-.14,zz,.38,.13,2.2,f,1);
      if(j===3){box('vent',xx+side*.11,base+.6,zz,.06,.65,1.6,f,1);for(let n=0;n<6;n++)box('metal',xx+side*.15,base+.33+n*.1,zz,.09,.035,1.65,f,2)}
     }
    }
    for(const sx of [-1,1])for(const sz of [-1,1])box('trim',x+sx*10.94,base+fh/2,z+sz*9.94,.24,fh,.24,f);
   }
   // Recessed balcony strips, slim rails, planters. No geometry protrudes into the circulation loop.
   for(let fl=2;fl<floors-1;fl+=3){const y=4.2+(fl-1)*3.1+.25;
    for(const sx of [-1,1]){const bx=x+sx*7.2;box('trim',bx,y,z+10.58,2.7,.16,1.25,f,1);box('glass-shadow',bx,y+.65,z+11.13,2.55,1.1,.035,f,1);beam('metal',[bx-1.3,y+1.22,z+11.15],[bx+1.3,y+1.22,z+11.15],.06,f,1);for(const dx of [-1.28,1.28])box('metal',bx+dx,y+.65,z+11.15,.045,1.15,.045,f,1);box('stone',bx+.55,y+.3,z+10.65,.8,.4,.45,f,2);part('leaf','leaf',[bx+.55,y+.62,z+10.65],[1,.5,.6],0,f,2)}
   }
  }
  // Parapets, capping and a flat roof with separately editable service plant.
  for(const dx of [-10.85,10.85]){box('wall',x+dx,roofY+.48,z,.3,.96,20.2,r);box('frame',x+dx,roofY+1,z,.42,.08,20.4,r,1)}
  for(const dz of [-9.85,9.85]){box('wall',x,roofY+.48,z+dz,21.4,.96,.3,r);box('frame',x,roofY+1,z+dz,21.5,.08,.42,r,1)}
  box('wall',x-3,roofY+1.2,z-2,5.2,2.4,4.8,r);box('trim',x-3,roofY+2.45,z-2,5.5,.1,5.1,r);
  box('vent',x-3,roofY+1.1,z+.44,1.1,2,.08,r,1);box('metal',x-2.5,roofY+1.1,z+.5,.06,.3,.08,r,2);
  for(const rx of [2.7,6.2])for(const rz of [-4,1.5]){
   box('metal',x+rx,roofY+.12,z+rz,2.7,.24,3.4,r,1);box('trim',x+rx,roofY+.65,z+rz,2.3,1,2.9,r,1);
   for(const sx of [-1,1]){box('vent',x+rx+sx*1.16,roofY+.66,z+rz,.035,.65,2.6,r,1);for(let n=0;n<7;n++)box('metal',x+rx+sx*1.2,roofY+.37+n*.085,z+rz,.04,.025,2.65,r,2)}
   part('cyl','dark',[x+rx,roofY+1.17,z+rz],[1.65,.045,1.65],0,r,1);
   const fan=new THREE.Group();fan.position.set(rx,roofY+1.2,rz);fan.name=id+' roof fan';groups.get(r).add(fan);for(let n=0;n<4;n++){const blade=mesh('box','metal',[0,0,0],[1.35,.025,.16],fan);blade.rotation.y=n*Math.PI/4}fans.push(fan);
  }
  for(const zz of [-6,6]){beam('metal',[x-8,roofY+.35,z+zz],[x+8,roofY+.35,z+zz],.35,r,1);for(let n=0;n<6;n++)box('metal',x-7+n*2.7,roofY+.17,z+zz,.6,.35,.7,r,2)}
  for(let n=0;n<10;n++)box('seal',x-9+n*2,roofY+.015,z,.025,.015,18,r,2);
  for(const sx of [-1,1])for(const sz of [-1,1]){part('cyl','metal',[x+sx*9.4,roofY+.12,z+sz*8.5],[.4,.06,.4],0,r,1);box('metal',x+sx*10.6,roofY+1.45,z+sz*9.5,.035,.85,.035,r,1)}
  // A generous lobby, sliding doors, canopy, tactile strip, handrails and mailbox bank.
  box('stone',x,.15,z+12.5,8,.3,5,en);box('paving',x+4.8,.12,z+11.9,1.7,.24,5,en);
  box('metal',x,3.75,z+11.1,5.8,.18,3,en);box('glass-blue',x,3.85,z+11.1,5.6,.035,2.8,en);
  for(const dx of [-2.6,2.6])box('metal',x+dx,1.85,z+12.25,.09,3.7,.09,en);
  box('seal',x,1.8,z+10.03,4.5,3.1,.12,en);box('glass-blue',x,1.8,z+10.12,4.3,2.95,.035,en);
  for(const side of [-1,1]){const d=mesh('box','glass',[side*.61,1.65,10.2],[1.2,2.7,.045],groups.get(en),id+' sensed door '+side);doors.push({object:d,base:side*.61,side,id,x,z});box('metal',x+side*.14,1.6,z+10.28,.04,.45,.1,en,1)}
  sign(id+'栋 · 澄序',[x,3.3,z+10.28],2.6,.42,en);sign(id,[x-8,roofY-1.15,z+10.05],1.2,1.1,f);
  for(let n=0;n<8;n++){box('metal',x+3.25+(n%2)*.6,.9+Math.floor(n/2)*.35,z+10.17,.54,.29,.28,en,1);box('seal',x+3.25+(n%2)*.6,.96+Math.floor(n/2)*.35,z+10.32,.32,.025,.025,en,2)}
  box('metal',x-2.5,1.3,z+10.18,.22,.45,.1,en,1);box('lamp',x-3.2,2.35,z+10.19,.2,.5,.12,en,1);manifest.lightFixtures.push({position:[x-3.2,2.3,z+10.6],type:'point',power:50,distance:12});
  for(const side of [-1,1])beam('metal',[x+side*4,.9,z+11],[x+side*4,.9,z+14.3],.045,en,1);
 }
 // Central square lawns and cross-shaped paths retain the four-tower reference composition.
 function tree(x,z,size=1){part('cyl','bark',[x,2.3*size,z],[.23*size,4.6*size,.23*size],0,'landscape');for(let n=0;n<(coarse?3:12);n++){const a=n*2.4,rr=(.6+random()*.65)*size,yy=(4.5+random()*1.5)*size;part('leaf',n%3?'leaf':'leaf-light',[x+Math.sin(a)*rr,yy,z+Math.cos(a)*rr],[(1.5+random()*.7)*size,(1.7+random()*.7)*size,(1.5+random()*.7)*size],0,'landscape',0);if(!coarse&&n<5)beam('bark',[x,2.9*size,z],[x+Math.sin(a)*rr,yy,z+Math.cos(a)*rr],.09*size,'landscape',1)}box('earth',x,.07,z,2,.08,2,'landscape',1);for(const dx of [-1.1,1.1])box('stone',x+dx,.13,z,.12,.12,2.2,'landscape',1)}
 for(const x of [-52,52])for(let z=-44;z<=44;z+=11)tree(x,z,.85+random()*.12);
 for(const z of [-52,52])for(const x of [-39,-26,-13,13,26,39])tree(x,z,.8);
 for(const x of [-8,8])for(const z of [-15,15])tree(x,z,1.1);
 for(const x of [-13,13])for(const z of [-4,4])tree(x,z,.85);
 for(const z of [-39,39])for(let x=-36;x<=36;x+=2.1){if(Math.abs(x)<4||Math.abs(Math.abs(x)-26)<2.5)continue;part('leaf','leaf',[x,.6,z],[1.8,1.1,1.5],0,'landscape',1)}
 for(const x of [-6,6])for(let z=-34;z<=34;z+=2.2){if(Math.abs(z)<12)continue;part('leaf','leaf-light',[x,.55,z],[1.3,.8,1.7],0,'landscape',1)}
 function bench(x,z,owner='landscape'){for(const dx of [-1.1,1.1])box('metal',x+dx,.4,z,.09,.65,.6,owner,1);for(let n=0;n<4;n++)box('wood',x,.75,z-.3+n*.2,2.8,.09,.14,owner,1);for(let n=0;n<3;n++)box('wood',x,1+n*.17,z-.4,2.8,.12,.08,owner,1)}
 for(const x of [-7,7])for(const z of [-9,9]){box('paving',x,.115,z,5,.23,3,'landscape');bench(x,z)}
 box('paving',-26,.13,0,15,.26,10,'playground');for(const x of [-31,-21])for(const z of [-3,3])box('wood',x,1.8,z,.22,3.6,.22,'playground');for(let n=0;n<17;n++)box('wood',-31.5+n*.7,3.7,0,.16,.2,7.6,'playground',1);bench(-26,-2,'playground');
 box('rubber',26,.13,0,17,.26,12,'playground');box('play-sage',26,.28,0,10,.03,9,'playground');
 for(const x of [21,24])for(const z of [-3,-.5])beam('wood',[x,.25,z],[x,2.6,z],.17,'playground');box('wood',22.5,1.6,-1.75,3.3,.14,2.8,'playground');box('play-honey',22.5,2.8,-1.75,3.7,.16,3.1,'playground');part('box','play-sage',[22.5,1,1.6],[2,.1,4.7],[.31,0,0],'playground');
 for(const x of [29,32])for(const sz of [-1,1])beam('metal',[x,.25,sz*2.2],[x,3,0],.1,'playground');beam('metal',[29,3,0],[32,3,0],.13,'playground');
 const swing=new THREE.Group();swing.name='Garden swing';swing.position.set(30.5,2.95,0);groups.get('playground').add(swing);for(const x of [-.45,.45])mesh('cyl','metal',[x,-.95,0],[.025,1.9,.025],swing);mesh('box','wood',[0,-1.95,0],[1.1,.1,.5],swing);
 // Entry pavilion, addresses, bicycle stands and permeable service access.
 box('stone',-8,1.35,51,4,2.7,4);box('trim',-8,2.8,51,4.5,.2,4.5);box('glass',-8,1.7,53.04,3.2,1.5,.045);box('glass',-5.96,1.7,51,.045,1.5,3.2);
 box('stone',12,1.1,52,14,2.2,.6);sign('澄 序 住 区',[12,1.35,52.32],12,.85);sign('CHENGXU  COURTYARD',[12,.55,52.33],10,.25);
 for(let n=0;n<8;n++){const x=26+n*1.4;beam('metal',[x,.2,51],[x,1,51],.065);beam('metal',[x,1,51],[x,1,52.2],.065);beam('metal',[x,1,52.2],[x,.2,52.2],.065)}
 for(const x of [-54.7,54.7]){for(let z=-54;z<=54;z+=6)box('metal',x,.65,z,.05,1.3,.05,'site',1);for(const y of [.45,.9,1.25])box('metal',x,y,0,.035,.035,109,'site',1)}
 for(const z of [-54.7,54.7])for(const side of [-1,1])for(const y of [.45,.9,1.25])box('metal',side*28,y,z,48,.035,.035,'site',1);
 for(const [x,z] of [[-41,-38],[41,-38],[-41,0],[41,0],[-41,38],[41,38],[-9,-10],[9,10],[0,49],[0,-49]]){part('cyl','metal',[x,2,z],[.1,4,.1]);box('metal',x,3.95,z,.55,.12,.55);box('lamp',x,3.75,z,.3,.3,.3);manifest.lightFixtures.push({position:[x,3.5,z],type:'point',power:70,distance:16})}
 for(const x of [-3,3])for(const z of [-32,-20,20,32]){box('metal',x,.4,z,.16,.8,.16,'site',1);box('lamp',x,.82,z,.22,.1,.22,'site',1);manifest.lightFixtures.push({position:[x,.95,z],type:'point',power:12,distance:7})}
 for(const z of [-41,41])for(let x=-34;x<=34;x+=5){box('vent',x,.23,z,.65,.025,.4,'site',2);for(let n=0;n<5;n++)box('metal',x-.27+n*.13,.25,z,.035,.015,.35,'site',2)}
 // Accessible paving cues, bins and actual cycle frames beside the entry.
 for(const z of [-44,-32,-20,20,32,44])for(let n=0;n<5;n++)box('beige-panel',-.6+n*.3,.235,z,.08,.025,.8,'site',2);
 for(const x of [-11,11])for(const z of [-9,9]){box('metal',x,.63,z,.5,1,.5,'landscape',1);box('dark',x,.96,z+.26,.35,.2,.02,'landscape',1);box('wood',x,1.16,z,.6,.08,.6,'landscape',1)}
 const wheelGeo=G(new THREE.TorusGeometry(.33,.028,6,18));
 if(!coarse)for(let i=0;i<4;i++){
  const x=27+i*2.8,z=51.6;for(const zz of [-.6,.6]){const w=new THREE.Mesh(wheelGeo,materials.metal);w.rotation.y=Math.PI/2;w.position.set(x,.54,z+zz);w.name='Bicycle wheel';groups.get('site').add(w)}
  const a=[x,.54,z-.6],b=[x,.54,z+.6],c=[x,1.15,z-.1],d=[x,.65,z+.03];for(const [v,w] of [[a,c],[c,b],[a,d],[b,d],[c,d]])beam('play-sage',v,w,.035,'site',1);beam('metal',[x,.7,z-.6],[x,1.22,z-.45],.035,'site',1);box('dark',x,1.22,z-.1,.22,.07,.38,'site',1);beam('metal',[x-.27,1.24,z-.45],[x+.27,1.24,z-.45],.035,'site',1)
 }
 let grassMesh;
 if(!coarse){const blade=G(new THREE.BufferGeometry());blade.setAttribute('position',new THREE.Float32BufferAttribute([-.015,0,0,.015,0,0,.01,.13,.02],3));blade.computeVertexNormals();grassMesh=new THREE.InstancedMesh(blade,materials['grass-blade'],16000);grassMesh.name='Individual grass blades';for(let i=0;i<grassMesh.count;i++){let x,z;do{x=-39+random()*78;z=-39+random()*78}while(Math.abs(x)<2.2||Math.abs(z)<2.2||specs.some(b=>Math.abs(x-b[1])<11.5&&Math.abs(z-b[2])<12)||Math.abs(Math.abs(x)-26)<1.7&&z>0||Math.abs(z)<7&&Math.abs(x)>16||Math.abs(Math.abs(x)-7)<3&&Math.abs(Math.abs(z)-9)<2);mx.makeRotationY(random()*Math.PI);mx.setPosition(x,.08,z);grassMesh.setMatrixAt(i,mx)}grassMesh.computeBoundingSphere();groups.get('landscape').add(grassMesh)}
 for(const b of batches.values()){const parent=groups.get(b.owner),o=new THREE.InstancedMesh(geo[b.type],materials[b.m],b.items.length);o.name=b.owner+':'+b.m+':'+b.tier;o.userData.tier=b.tier;o.castShadow=!['glass','glass-blue','glass-shadow','window-lit','lamp','grass'].includes(b.m);o.receiveShadow=true;const origin=new THREE.Vector3(...origins.get(b.owner));for(let i=0;i<b.items.length;i++){const it=b.items[i];p.fromArray(it.p).sub(origin);s.fromArray(it.s);q.setFromEuler(e.set(...it.r));mx.compose(p,q,s);o.setMatrixAt(i,mx)}o.computeBoundingSphere();parent.add(o)}
 for(const name of ['leaf','leaf-light','grass-blade','curtain','curtain-warm'])materials[name].onBeforeCompile=shader=>{shader.uniforms.windTime={value:0};shaders.push(shader);shader.vertexShader='uniform float windTime;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n#ifdef USE_INSTANCING\ntransformed.x+=sin(windTime*1.15+instanceMatrix[3].x*.3+instanceMatrix[3].z*.2)*.025*(position.y+.5);\n#endif')};
 function person(i){const g=new THREE.Group();g.name='Resident '+i;groups.get('life').add(g);mesh('sphere','skin',[0,1.65,0],[.3,.36,.3],g);mesh('box',i%2?'cloth':'cloth-warm',[0,1.13,0],[.42,.65,.25],g);const limbs=[];for(const sx of [-1,1]){const leg=new THREE.Group();leg.position.set(sx*.12,.82,0);g.add(leg);mesh('box','dark',[0,-.35,0],[.14,.7,.17],leg);limbs.push(leg);const arm=new THREE.Group();arm.position.set(sx*.28,1.35,0);g.add(arm);mesh('box','skin',[0,-.25,0],[.11,.5,.13],arm);limbs.push(arm)}return{g,limbs,i}}
 for(let i=0;i<22;i++)people.push(person(i));
 const bg=G(new THREE.BufferGeometry());bg.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,-.6,.1,.25,-.15,0,.3,0,0,0,.15,0,.3,.6,.1,.25],3));bg.computeVertexNormals();for(let i=0;i<5;i++){const b=new THREE.Mesh(bg,materials.bird);b.name='Courtyard bird '+i;groups.get('life').add(b);birds.push(b)}
 function squareRoute(distance,h){const d=((distance%(8*h))+8*h)%(8*h),seg=Math.floor(d/(2*h)),t=d%(2*h);return seg===0?[h,-h+t,0]:seg===1?[h-t,h,-Math.PI/2]:seg===2?[-h,h-t,Math.PI]:[-h+t,-h,Math.PI/2]}
 function update(delta=0){if(disposed)return;const dt=enabled&&Number.isFinite(delta)?THREE.MathUtils.clamp(delta,0,.25):0;time+=dt;if(activity.wind)windTime+=dt;shaders.forEach(s=>s.uniforms.windTime.value=windTime);
  for(const a of people){let x,z,yaw;if(a.i<8){const d=(time*.68+a.i*11)%168;x=(a.i%2?.65:-.65);z=d<84?-42+d:126-d;yaw=d<84?0:Math.PI}else if(a.i<12){const d=(time*.7+(a.i-8)*24)%168;x=d<84?-42+d:126-d;z=a.i%2?.6:-.6;yaw=d<84?Math.PI/2:-Math.PI/2}else if(a.i<18){[x,z,yaw]=squareRoute(time*.7+a.i*41,41)}else{const b=specs[a.i-18],d=(time*.55+a.i*3)%14;x=b[1];z=b[2]+11.8+(d<7?d:14-d)*.45;yaw=d<7?0:Math.PI}a.g.position.set(x,.23,z);a.g.rotation.y=yaw;a.g.visible=activity.people&&(level!=='low'||a.i<10);a.limbs.forEach((l,j)=>l.rotation.x=Math.sin(time*4+a.i+(j===0||j===3?0:Math.PI))*(j%2?.25:.35))}
  for(const d of doors){const near=activity.people&&people.some(a=>a.g.visible&&Math.hypot(a.g.position.x-d.x,a.g.position.z-d.z-11)<4);const wanted=d.base+d.side*(near?.68:0);d.object.position.x+=(wanted-d.object.position.x)*Math.min(1,dt*4)}
  if(activity.mechanical)fans.forEach(f=>f.rotation.y+=dt*4);swing.rotation.x=Math.sin(time*1.2)*.1;
  birds.forEach((b,i)=>{const a=time*.12+i*1.256;b.position.set(Math.sin(a)*18,15+i*2+Math.sin(a*2)*.6,Math.cos(a)*18);b.rotation.y=-a;b.rotation.z=Math.sin(time*5+i)*.22;b.visible=activity.birds&&level!=='low'})
 }
 function setQuality(value){if(!['high','medium','low'].includes(value))throw new Error('Unknown quality');level=value;root.traverse(o=>{if(o.userData.tier)o.visible=value==='high'||value==='medium'&&o.userData.tier<2});if(grassMesh)grassMesh.count=value==='high'?16000:value==='medium'?5000:1200;update(0)}
 function setTimeOfDay(value){const n=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.4:0;materials.lamp.emissiveIntensity=.08+n*3;materials['window-lit'].emissiveIntensity=.01+n*1.3}
 function exportScene(){root.updateWorldMatrix(true,true);const gs={},ms={},objects=[];root.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry,m=o.material;if(!gs[g.uuid])gs[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null};if(!ms[m.uuid])ms[m.uuid]={name:m.name,color:m.color.toArray(),roughness:m.roughness,metalness:m.metalness,opacity:m.opacity,transparent:m.transparent,transmission:m.transmission||0,emissive:m.emissive.toArray(),emissiveIntensity:m.emissiveIntensity,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};let owner=o;while(owner!==root&&!owner.userData.id)owner=owner.parent;for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,mx);mx.premultiply(o.matrixWorld)}else mx.copy(o.matrixWorld);objects.push({g:g.uuid,m:m.uuid,matrix:mx.toArray(),owner:owner.userData.id||'site'})}});return{format:'chengxu-residential-courtyard-v1',manifest,snapshotSpace:'world',geometries:gs,materials:ms,objects}}
 function dispose(){if(disposed)return;disposed=true;root.removeFromParent();root.traverse(o=>{if(o.isInstancedMesh)o.dispose()});geometries.forEach(g=>g.dispose());materialSet.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());root.clear();groups.clear();buildings.clear();batches.clear()}
 setQuality(quality);update(0);
 return{root,groups,buildings,manifest,getManifest:()=>JSON.parse(JSON.stringify(manifest)),update,setQuality,setTimeOfDay,setDynamicsEnabled:v=>enabled=!!v,setActivity:v=>{for(const k of Object.keys(activity))if(k in v)activity[k]=!!v[k];update(0)},exportScene,dispose,get quality(){return level},get simulationTime(){return time},get disposed(){return disposed}};
}
