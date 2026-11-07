/** 棕屿里 / host-owned THREE, metres, +Y up, +Z frontage. */
export function createMixedUseResidential({THREE:T,footprint=112,seed=1105,quality='high',coarse=false}={}){
 if(!T?.Group||!Number.isFinite(footprint)||footprint<=0)throw new Error('Supply THREE and positive footprint');
 const root=new T.Group();root.name='ZONGYU-RESIDENCES';root.scale.setScalar(footprint/112);root.userData={moduleId:'zongyu-mixeduse',id:'ZONGYU-RESIDENCES'};
 const groups=new Map(),G=new Set(),M=new Set(),X=new Set(),batches=new Map(),detail=[],windShaders=[],doors=[];
 for(const id of ['structure','facade','balconies','roof','lobby','landscape',...Array.from({length:6},(_,i)=>'SHOP-'+(i+1))]){const g=new T.Group();g.name=id;g.userData={owner:id};groups.set(id,g);root.add(g);}
 let time=0,windTime=0,night=0,level=quality,disposed=false,windStrength=.45;
 const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const geo={box:ownG(new T.BoxGeometry(1,1,1)),cyl:ownG(new T.CylinderGeometry(.5,.5,1,12)),sphere:ownG(new T.SphereGeometry(.5,16,10)),leaf:ownG(new T.IcosahedronGeometry(1,2))};
 function ownG(g){G.add(g);return g;}function ownM(m){M.add(m);return m;}
 function texture(name,base,grain,grid=false){const canvas=document.createElement('canvas');canvas.width=canvas.height=256;const c=canvas.getContext('2d');c.fillStyle=base;c.fillRect(0,0,256,256);const p=c.getImageData(0,0,256,256);for(let i=0;i<p.data.length;i+=4){const v=(rand()-.5)*grain;for(let k=0;k<3;k++)p.data[i+k]+=v;}c.putImageData(p,0,0);if(grid){c.strokeStyle='#c8c6bf';c.lineWidth=.6;for(let i=0;i<=4;i++){c.beginPath();c.moveTo(i*64,0);c.lineTo(i*64,256);c.moveTo(0,i*64);c.lineTo(256,i*64);c.stroke();}}const t=new T.CanvasTexture(canvas);t.name=name;t.colorSpace=T.SRGBColorSpace;t.wrapS=t.wrapT=T.RepeatWrapping;X.add(t);return t;}
 const materials={};function mat(name,color,extra={}){const m=ownM(new T.MeshStandardMaterial({name,color,roughness:.8,...extra}));materials[name]=m;return m;}
 const cream=mat('Cream mineral plaster',0xffffff,{map:texture('Fine ivory plaster','#eeeadf',5)}),brown=mat('Light brown stone render',0xffffff,{map:texture('Granular natural stone coating','#b6a18a',21),bumpScale:.008}),trim=mat('Warm grey precast trim',0xcac8bf),stone=mat('Commercial limestone plinth',0xb9ad9a),paving=mat('Warm white paving',0xffffff,{map:texture('Cut limestone paving','#dddcd4',9,true)}),frame=mat('Bronze grey aluminium',0x4d504c,{metalness:.68,roughness:.31}),metal=mat('Brushed equipment metal',0x9baca7,{metalness:.65,roughness:.38}),glass=mat('Residential silver blue glazing',0x849e9f,{metalness:.2,roughness:.16,transparent:true,opacity:.63,depthWrite:false}),clear=mat('Storefront clear glass',0xb3c7c5,{metalness:.08,roughness:.12,transparent:true,opacity:.32,depthWrite:false}),dark=mat('Shadow and ventilation',0x354441),interior=mat('Shop interior warm plaster',0xd7c8b2),wood=mat('Oak furnishings',0xa28761),soil=mat('Planting soil',0x7d7765),grass=mat('Trimmed garden lawn',0x8e9e7b),bark=mat('Fine tree bark',0x766b56),leaf=mat('Evergreen foliage',0x507351),cloth=mat('Awning canvas',0x8f9782,{side:T.DoubleSide}),lamp=mat('Warm entrance diffuser',0xf1dfbc,{emissive:0xffcf8b,emissiveIntensity:.08});
 brown.bumpMap=brown.map;
 const curtain=[0xcac5b7,0xb7bfb5,0xd8d0c1,0xa4b3ad].map((c,i)=>mat('Curtain fabric '+i,c,{side:T.DoubleSide}));
 const apartments=Array.from({length:10},(_,i)=>mat('Apartment interior '+i,[0xb5afa1,0xc3b59d,0xa1b4af,0xbdb8a9][i%4],{emissive:0xffca87,emissiveIntensity:0}));
 const shopLights=Array.from({length:6},(_,i)=>mat('Shop luminous interior '+i,0xe6d1ad,{emissive:0xffcc8c,emissiveIntensity:.08}));
 const matrix=new T.Matrix4(),pos=new T.Vector3(),scale=new T.Vector3(),q=new T.Quaternion(),euler=new T.Euler(),color=new T.Color();
 function add(type,m,x,y,z,w,h,d,owner='structure',tier=0,rot=[0,0,0],tint=null){const key=type+':'+m.uuid+':'+owner+':'+tier;if(!batches.has(key))batches.set(key,{type,m,owner,tier,items:[]});batches.get(key).items.push({p:[x,y,z],s:[w,h,d],rot,tint});}
 const box=(m,x,y,z,w,h,d,o='structure',tier=0)=>add('box',m,x,y,z,w,h,d,o,tier);
 const cyl=(m,x,y,z,r,h,o='structure',tier=0)=>add('cyl',m,x,y,z,r,h,r,o,tier);
 function rod(m,a,b,r,o='roof',tier=1){const aa=new T.Vector3(...a),bb=new T.Vector3(...b),mid=aa.clone().add(bb).multiplyScalar(.5),rot=new T.Euler().setFromQuaternion(new T.Quaternion().setFromUnitVectors(new T.Vector3(0,1,0),bb.clone().sub(aa).normalize()));add('cyl',m,...mid.toArray(),r,aa.distanceTo(bb),r,o,tier,[rot.x,rot.y,rot.z]);}
 function sign(text,x,y,z,w,h,o='lobby',base='#777460',ink='#f5f0e1'){
  const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=256;const c=canvas.getContext('2d');c.fillStyle=base;c.fillRect(0,0,1024,256);c.strokeStyle='#c9bfa8';c.lineWidth=2;c.strokeRect(12,12,1000,232);c.textAlign='center';c.textBaseline='middle';c.fillStyle=ink;c.font='500 108px Microsoft YaHei';c.fillText(text,512,132,970);const t=new T.CanvasTexture(canvas);t.colorSpace=T.SRGBColorSpace;X.add(t);const m=ownM(new T.MeshStandardMaterial({name:'Sign / '+text,map:t,roughness:.6})),mesh=new T.Mesh(ownG(new T.PlaneGeometry(w,h)),m);mesh.name='Sign '+text;mesh.position.set(x,y,z);groups.get(o).add(mesh);
 }
 // A closed solid ramp has its high end at -Z and low end at +Z.
 const rg=ownG(new T.BufferGeometry()),rp=[-.5,0,-.5,.5,0,-.5,.5,1,-.5,-.5,1,-.5,-.5,0,.5,.5,0,.5],ri=[0,2,1,0,3,2,0,1,5,0,5,4,3,4,5,3,5,2,0,4,3,1,2,5];rg.setAttribute('position',new T.Float32BufferAttribute(rp,3));rg.setIndex(ri);geo.ramp=ownG(rg.toNonIndexed());geo.ramp.computeVertexNormals();geo.ramp.setAttribute('uv',new T.Float32BufferAttribute(Array.from(geo.ramp.attributes.position.array).flatMap((v,i)=>i%3===0?[v,geo.ramp.attributes.position.array[i+2]]:[]),2));
 box(paving,0,-.22,0,112,.44,112);for(const x of [-55.7,55.7])box(trim,x,.025,0,.6,.05,112);for(const z of [-55.7,55.7])box(trim,0,.025,z,110.8,.05,.6);
 const base=4.6,floors=22,story=3.05,bodyTop=base+floors*story,totalHeight=bodyTop+4.2;
 const buildings=[{id:'ZONGYU-TOWER',name:'棕屿里住宅',width:78,depth:18,x:0,z:24,floors:23,residentialFloors:22,height:totalHeight,units:3}];
 // Roughing mode is deliberately distinct from the final perforated facade.
 if(coarse){box(cream,0,base+(bodyTop-base)/2,24,78,bodyTop-base,18);box(stone,0,2.3,25,84,4.6,28);for(let f=0;f<floors;f++)box(glass,0,base+f*story+1.5,33.03,75,2,.05,'facade');}
 else{
  box(dark,0,(bodyTop+base)/2,24,76,bodyTop-base,14.8);
  for(let f=0;f<=floors;f++){const y=base+f*story;box(trim,0,y+.08,24,78,.16,18);for(const side of [-1,1]){box(cream,0,y+.38,24+side*8.9,78,.60,.35,'facade');box(trim,0,y+.12,24+side*9.03,78,.10,.22,'facade',1);}}
  for(const x of [-39,39])box(cream,x,(bodyTop+base)/2,24,.5,bodyTop-base,18,'facade');
  for(let i=0;i<=15;i++){const x=-36+i*4.8;for(const side of [-1,1])box(i%5===0?brown:cream,x,(bodyTop+base)/2,24+side*8.88,i%5===0?.85:.62,bodyTop-base,.66,'facade');}
  for(const x of [-38,-12,12,38])box(brown,x,(bodyTop+base)/2,33.18,1.0,bodyTop-base,.20,'facade');
  for(const side of [-1,1])for(const x of [-37.25,37.25])box(side===1?brown:cream,x,(bodyTop+base)/2,24+side*8.95,3.5,bodyTop-base,.45,'facade');
  for(let f=0;f<floors;f++)for(const side of [-1,1])for(let i=0;i<15;i++){
   const x=-33.6+i*4.8,y=base+f*story+1.72,z=24+side*9.02,room=apartments[Math.floor(rand()*10)],cur=curtain[(f+i)%4],isBalcony=side===1&&i%5===2,isBay=side===1&&!isBalcony&&(i%5===0||i%5===4);
   box(room,x,y,z-side*.28,3.74,2.12,.09,'facade');
   const width=.45+rand()*.85;for(const a of [-1,1])box(cur,x+a*(1.76-width/2),y,z-side*.14,width,2.12,.025,'facade',1);
   for(const a of [-1,1])box(trim,x+a*1.98,y,z-side*.12,.13,2.42,.35,'facade');
   for(const a of [-1,1])box(trim,x,y+a*1.17,z-side*.12,4.08,.12,.35,'facade');
   if(isBalcony||isBay){
    const depth=isBalcony?1.9:1.15,front=z+depth,w=isBalcony?4.15:4.03;
    for(const yy of [base+f*story+.16,base+(f+1)*story-.06])box(isBay?brown:trim,x,yy,z+depth/2,w,.16,depth+.12,'balconies');
    for(const a of [-1,1]){box(isBay?brown:cream,x+a*w/2,y,z+depth/2,.13,2.78,depth,'balconies');box(frame,x+a*(w/2-.07),y,front,.065,2.78,.10,'balconies');}
    box(glass,x,y,front, w-.22,2.65,.035,'balconies');
    for(const yy of [y-1.34,y+1.34,y-.35])box(frame,x,yy,front+.035,w,.06,.08,'balconies',1);
    for(const dx of [-.65,.65])box(frame,x+dx,y,front+.04,.055,2.7,.08,'balconies',1);
    if(isBay){for(const a of [-1,1]){box(glass,x+a*(w/2-.075),y,z+depth/2,.025,2.52,depth-.16,'balconies');}box(trim,x,base+f*story+.34,front,4.08,.18,.25,'balconies',1);}
    else{box(trim,x,base+f*story+.46,front,4.15,.30,.16,'balconies');box(dark,x+1.6,base+f*story+.32,z+1.4,.16,.05,.18,'balconies',2);}
   }else{
    box(glass,x,y,z+.02*side,3.84,2.22,.04,'facade');for(const a of [-1,1]){box(frame,x+a*1.94,y,z+.07*side,.075,2.36,.10,'facade');box(frame,x,y+a*1.16,z+.07*side,3.94,.065,.10,'facade');}
    box(frame,x+.35,y,z+.08*side,.055,2.25,.10,'facade',1);box(frame,x,y+.45,z+.08*side,3.84,.045,.10,'facade',1);
    box(trim,x,y-1.25,z+.09*side,4.13,.14,.40,'facade',1);
    if(side===-1&&i%5===1){box(dark,x+1.5,y-.2,z-.25,.7,.9,.5,'facade',1);for(let a=0;a<6;a++)box(metal,x+1.5,y-.55+a*.14,z-.52,.68,.04,.06,'facade',2);}
   }
  }
  for(const x of [-39.28,39.28])for(let f=0;f<floors;f++)for(const z of [19.5,27.7]){const y=base+f*story+1.65;box(frame,x,y,z,.10,1.9,1.65,'facade');box(glass,x+(x<0?-.06:.06),y,z,.035,1.74,1.48,'facade');box(trim,x,y-1.01,z,.33,.12,1.85,'facade',1);}
 }
 // Commercial podium: floor/roof/back wall, six real shop interiors and central lobby.
 box(stone,0,.17,25,84,.34,28);box(trim,0,4.46,25,84,.28,28);box(brown,0,4.75,38.9,84,.48,.24);box(stone,0,2.25,11.1,84,4.5,.30);
 for(const x of [-41.8,41.8])box(stone,x,2.25,25,.4,4.5,28);
 for(const x of [-40,-30.5,-21.5,-12,12,21.5,30.5,40])box(stone,x,2.25,38.85,.42,4.5,.55);
 for(let x=-41;x<=41;x+=4)box(frame,x,5.2,38.75,.065,1.05,.065,'roof',1);box(frame,0,5.75,38.75,83,.065,.065,'roof',1);box(glass,0,5.15,38.75,82.6,.95,.025,'roof',1);
 const goods=[0xc4a278,0xb5835e,0x71866f,0x9d705b,0xc2b98f,0x6d858b].map((c,i)=>mat('Store product '+i,c,{roughness:.8}));
 const shopNames=['棕屿咖啡','禾麦面包','邻里便利','花间日记','一页书屋','浅棕茶事'],shopXs=[-35,-26,-17,17,26,35];
 for(let i=0;i<6;i++){
  const x=shopXs[i],o='SHOP-'+(i+1),z=39.1;
  box(interior,x,2.13,31.5,8.4,3.9,.18,o);box(wood,x,.26,35.2,8.4,.16,7.6,o);box(interior,x,4.21,35.2,8.4,.12,7.6,o);
  for(const a of [-1,1])box(interior,x+a*4.25,2.2,35.2,.16,4,7.6,o);
  box(clear,x-1.0,2.20,z,5.5,3.70,.04,o);for(const dx of [-3.8,1.8,3.8])box(frame,x+dx,2.2,z+.07,.085,3.85,.1,o);
  for(const y of [.35,4.10])box(frame,x,y,z+.07,7.8,.10,.12,o);
  const door=new T.Group();door.name='Animated shop door '+(i+1);door.position.set(x+3.8,.38,z+.08);groups.get(o).add(door);doors.push(door);
  function dm(m,px,py,pz,w,h,d){const mesh=new T.Mesh(geo.box,m);mesh.position.set(px,py,pz);mesh.scale.set(w,h,d);door.add(mesh);}
  dm(clear,-.95,1.82,0,1.85,3.55,.045);for(const a of [0,-1.9])dm(frame,a,1.82,.03,.07,3.65,.10);for(const y of [0,3.64])dm(frame,-.95,y,.03,1.95,.07,.10);dm(metal,-1.72,1.5,.12,.035,.65,.07);
  box(frame,x,4.10,39.5,8.35,.54,.8,o);sign(shopNames[i],x,4.11,39.915,7.35,.45,o,i%2?'#8d7b63':'#687365');
  // The awning is cloth fixed between two rigid rails.
  add('box',cloth,x,3.67,40.02,7.8,.045,1.6,o,1,[-.07,0,0]);for(const zz of [39.24,40.82])box(frame,x,3.68+(zz-40)*.07,zz,8,.045,.045,o,1);
  for(const xx of [x-3.6,x+3.6])rod(frame,[xx,3.9,39.2],[xx,3.65,40.8],.045,o,1);
  for(let shelf=0;shelf<3;shelf++){box(wood,x,1.0+shelf*.64,32.2,5.7,.10,.65,o,1);for(let j=0;j<7;j++){const gx=x-2.4+j*.8,gy=1.2+shelf*.64,m=goods[(j+shelf)%6];if(i===1){add('sphere',m,gx,gy-.04,32.25,.55,.22,.32,o,2);}else if(i===3){cyl(stone,gx,gy-.04,32.25,.30,.22,o,2);add('leaf',leaf,gx,gy+.22,32.25,.23,.3,.23,o,2);}else if(i===4){for(let k=0;k<3;k++)box(goods[(j+k)%6],gx+(k-1)*.13,gy+.06,32.25,.10,.42+rand()*.08,.28,o,2);}else{cyl(m,gx,gy,32.25,.19,.35,o,2);cyl(dark,gx,gy+.20,32.25,.11,.05,o,2);}}}
  box(wood,x-1.5,.8,36.7,2.7,1.05,.78,o);box(stone,x-1.5,1.36,36.7,2.85,.12,.9,o);box(shopLights[i],x,4.1,35.6,5.5,.025,.8,o);
  for(const a of [-1,1]){cyl(frame,x+a*2.4,3.85,35.5,.055,.6,o,1);cyl(lamp,x+a*2.4,3.52,35.5,.36,.08,o,1);}
  if(i===0||i===5){for(const xx of [x-2.5,x+1.2]){cyl(wood,xx,.83,37.2,.7,.08,o,1);cyl(frame,xx,.44,37.2,.08,.8,o,1);for(const a of [-1,1]){cyl(wood,xx+a*.9,.48,37.2,.4,.08,o,1);cyl(frame,xx+a*.9,.25,37.2,.06,.45,o,1);}}}
 }
 box(stone,0,.15,40.1,11,.30,4,'lobby');box(interior,0,1.9,37.5,11,3.8,.20,'lobby');box(clear,0,1.70,39.3,5.2,2.8,.05,'lobby');
 for(const x of [-2.7,0,2.7])box(frame,x,1.70,39.36,.09,2.95,.12,'lobby');for(const a of [-1,1])box(metal,a*.24,1.55,39.45,.04,.65,.08,'lobby',1);
 box(frame,0,3.35,40.8,11.5,.24,3.5,'lobby');box(lamp,0,3.20,40.9,9.4,.035,.7,'lobby');sign('棕屿里 · 住宅入口',0,3.39,42.57,9.5,.23,'lobby');
 for(const x of [-5.1,5.1]){box(stone,x,1.0,39.7,.70,1.8,.60,'lobby');box(dark,x,1.32,40.02,.45,.5,.03,'lobby');}
 for(let i=0;i<9;i++){box(metal,4.5+(i%3)*.28,.7+Math.floor(i/3)*.25,39.42,.24,.20,.15,'lobby',1);}
 for(const z of [42.3,42.7])box(trim,0,z===42.3?.10:.035,z,11.6,z===42.3?.20:.07,.4,'lobby');
 box(stone,6.4,.15,40.1,1.8,.30,4,'lobby');add('ramp',paving,6.4,0,45.25,1.8,.3,6.3,'lobby');
 // Roof equipment rooms align with the three residential units.
 box(trim,0,bodyTop+.10,24,78,.20,18,'roof');for(const z of [15.1,32.9])box(cream,0,bodyTop+.72,z,78,1.24,.25,'roof');for(const x of [-38.9,38.9])box(cream,x,bodyTop+.72,24,.25,1.24,18,'roof');
 for(const x of [-24,0,24]){
  box(brown,x,bodyTop+1.68,23,6,3.2,5.8,'roof');box(trim,x,bodyTop+3.38,23,6.4,.20,6.2,'roof');box(frame,x,bodyTop+1.3,25.98,1.3,2.3,.10,'roof');
  for(const a of [-1,1]){box(trim,x+a*6,bodyTop+.3,23,3.4,.4,3.5,'roof',1);box(metal,x+a*6,bodyTop+1.05,23,3.0,1.1,3.0,'roof');cyl(dark,x+a*6,bodyTop+1.65,23,1.6,.10,'roof',1);for(let j=0;j<7;j++)box(dark,x+a*6,bodyTop+.64+j*.13,24.52,2.6,.04,.04,'roof',2);}
  cyl(metal,x+1.6,bodyTop+3.8,21.2,.18,.75,'roof',1);cyl(metal,x+1.6,bodyTop+4.18,21.2,.45,.06,'roof',1);
 }
 for(const x of [-37,37])rod(metal,[x,bodyTop+.5,16],[x,bodyTop+.5,32],.10,'roof');
 for(const z of [17,31]){rod(metal,[-36,bodyTop+.38,z],[36,bodyTop+.38,z],.07,'roof',1);for(let x=-34;x<=34;x+=8)box(stone,x,bodyTop+.23,z,.45,.30,.45,'roof',2);}
 for(const x of [-37,37])rod(metal,[x,.4,14.6],[x,bodyTop,14.6],.09,'facade',1);
 // Quiet rear garden and a clear commercial forecourt.
 for(const x of [-26,26])for(const z of [-33,-5]){box(grass,x,.025,z,36,.05,18,'landscape');for(const zz of [z-9,z+9])box(trim,x,.045,zz,36,.09,.22,'landscape');}
 const treeSites=[[-49,-40],[49,-40],[-49,-7],[49,-7],[-49,43],[49,43]];
 if(!coarse){for(const [x,z] of treeSites){box(soil,x,.025,z,3.6,.05,3.6,'landscape');cyl(bark,x,1.8,z,.23,3.6,'landscape');for(let j=0;j<32;j++){const a=j*2.4,r=Math.sqrt(rand())*1.8;add('leaf',leaf,x+Math.sin(a)*r,4.1+rand()*1.5,z+Math.cos(a)*r,.65+rand()*.6,.75+rand()*.5,.65+rand()*.6,'landscape',j<12?0:2,[rand(),rand(),rand()]);}}
  for(const x of [-39,39])for(const z of [-33,-5])for(let i=0;i<10;i++)add('leaf',leaf,x+(rand()-.5)*3,.55,z+(rand()-.5)*5,.65,.55,.65,'landscape',1);
  for(const x of [-13,13]){for(let i=0;i<6;i++)box(wood,x,.5,-19+(i-2.5)*.14,3.6,.07,.10,'landscape',1);for(let i=0;i<3;i++)box(wood,x,.75+i*.16,-19.5,3.6,.12,.075,'landscape',1);for(const a of [-1,1])box(frame,x+a*1.3,.26,-19,.11,.45,.8,'landscape');}
 }
 for(const x of [-46,46])for(const z of [-24,10,46]){cyl(frame,x,2.4,z,.11,4.8,'landscape');box(frame,x,4.84,z,.9,.14,.42,'landscape');box(lamp,x,4.75,z,.8,.035,.32,'landscape');}
 for(let x=-40;x<=40;x+=5){box(dark,x,.02,50,.8,.025,.12,'landscape',2);}
 sign('棕 屿 里',-22,.75,51,13,1.1,'landscape','#9c8b73');box(stone,-22,.65,50.8,14,1.3,.40,'landscape');
 for(const batch of batches.values()){
  const mesh=new T.InstancedMesh(geo[batch.type],batch.m,batch.items.length);mesh.name=batch.owner+' / '+batch.m.name+' / L'+batch.tier;mesh.userData={owner:batch.owner,tier:batch.tier};mesh.castShadow=!batch.m.transparent&&batch.m!==lamp;mesh.receiveShadow=true;
  batch.items.forEach((item,i)=>{pos.fromArray(item.p);scale.fromArray(item.s);q.setFromEuler(euler.set(...item.rot));matrix.compose(pos,q,scale);mesh.setMatrixAt(i,matrix);});mesh.computeBoundingBox();mesh.computeBoundingSphere();groups.get(batch.owner).add(mesh);detail.push(mesh);
 }
 function windMat(m,amplitude,awning=false){m.customProgramCacheKey=()=>m.name+'-wind';m.onBeforeCompile=shader=>{shader.uniforms.uWindTime={value:windTime};shader.uniforms.uWindStrength={value:windStrength};windShaders.push(shader);shader.vertexShader='uniform float uWindTime,uWindStrength;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>\n#ifdef USE_INSTANCING\nfloat phase=instanceMatrix[3].x*.3+instanceMatrix[3].y*.23+instanceMatrix[3].z*.17;transformed.${awning?'y':'x'}+=sin(uWindTime*.9+phase)*${amplitude}*uWindStrength*${awning?'max(0.,position.z+.5)':'max(0.,position.y+.5)'};\n#endif`);};}
 windMat(leaf,'.10');curtain.forEach(m=>windMat(m,'.035'));windMat(cloth,'.06',true);
 function setTimeOfDay(v){night=typeof v==='number'?T.MathUtils.clamp(v,0,1):v==='night'?1:v==='evening'?.5:0;apartments.forEach((m,i)=>m.emissiveIntensity=i%4===0?.01*night:T.MathUtils.smoothstep(night,.12+i*.06,.30+i*.06)*(.65+i*.06));shopLights.forEach((m,i)=>m.emissiveIntensity=.08+night*(1.3+i*.08));lamp.emissiveIntensity=.06+night*2.6;}
 function update(delta=0,state={}){if(disposed)return;const dt=state.paused?0:Number.isFinite(delta)?T.MathUtils.clamp(delta,0,.25):0;time+=dt;if(state.wind!==false)windTime+=dt;windStrength=state.windStrength??windStrength;for(const s of windShaders){s.uniforms.uWindTime.value=windTime;s.uniforms.uWindStrength.value=state.wind===false?0:windStrength;}if(state.nightFactor!==undefined)setTimeOfDay(state.nightFactor);else if(state.timeOfDay!==undefined)setTimeOfDay(state.timeOfDay);doors.forEach((door,i)=>{door.rotation.y=state.doors===false?0:-.72*T.MathUtils.smoothstep(Math.sin(time*.21+i*1.9),.55,.92);});}
 function setQuality(v){if(!['high','medium','low'].includes(v))throw new Error('Unknown quality');level=v;detail.forEach(m=>m.visible=m.userData.tier===0||v==='high'||v==='medium'&&m.userData.tier<2);}
 function getBounds(){root.updateWorldMatrix(true,true);return new T.Box3().setFromObject(root);}
 const metadata={id:'zongyu-mixeduse',name:'棕屿里',version:'1.0.0',units:'m',upAxis:'Y',front:'+Z',footprint:{width:footprint,depth:footprint},connectionLevel:0,buildings,shops:shopNames.map((name,i)=>({id:'SHOP-'+(i+1),name,x:shopXs[i],z:39.1})),treeSites,residentialFloors:22,commercialFloors:1,unitsCount:3,containsRoads:false,containsPeople:false};
 function exportScene(){const quality=level,visible=root.visible;root.visible=true;setQuality('high');root.updateWorldMatrix(true,true);const geometries={},mats={},objects=[];try{root.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry,m=o.material;if(!geometries[g.uuid])geometries[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null,colors:null};if(!mats[m.uuid])mats[m.uuid]={name:m.name,color:m.color.toArray(),roughness:m.roughness,metalness:m.metalness,opacity:m.opacity,transparent:m.transparent,emissive:m.emissive.toArray(),emissiveIntensity:m.emissiveIntensity,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,matrix);matrix.premultiply(o.matrixWorld);}else matrix.copy(o.matrixWorld);let owner=o;while(owner!==root&&!owner.userData.owner)owner=owner.parent;objects.push({g:g.uuid,m:m.uuid,matrix:matrix.toArray(),tint:null,owner:owner.userData.owner||'structure'});}});return{format:'zongyu-mixeduse-v1',snapshotSpace:'world',metadata,manifest:metadata,state:{time,windTime,night},geometries,materials:mats,objects};}finally{setQuality(quality);root.visible=visible;}}
 function makeExportClone(){const v=root.visible,q=level;setQuality('high');root.visible=true;const copy=root.clone(true);setQuality(q);root.visible=v;return copy;}
 async function exportGLB({GLTFExporter}={}){if(!GLTFExporter)throw new Error('Pass host GLTFExporter');const clone=makeExportClone();try{return await new GLTFExporter().parseAsync(clone,{binary:true});}finally{clone.traverse(o=>{if(o.isInstancedMesh)o.dispose();});clone.clear();}}
 function dispose(){if(disposed)return;disposed=true;root.removeFromParent();root.traverse(o=>{if(o.isInstancedMesh)o.dispose();});G.forEach(g=>g.dispose());M.forEach(m=>m.dispose());X.forEach(t=>t.dispose());root.clear();groups.clear();}
 setQuality(quality);setTimeOfDay(0);update(0);return{root,groups,metadata,buildings,materials,doors,update,setQuality,setTimeOfDay,getBounds,exportScene,exportGLB,makeExportClone,dispose,get quality(){return level;},get simulationTime(){return time;},get windTime(){return windTime;},get nightFactor(){return night;},get disposed(){return disposed;}};
}
export default createMixedUseResidential;
