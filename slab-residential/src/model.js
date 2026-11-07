/** Host-owned Three.js. Metres, Y up, ground-centre pivot. No renderer or loop. */
export function createResidentialBlock({THREE:T,footprint=112,quality='high',seed=1104,coarse=false}={}){
 if(!T?.Group||!Number.isFinite(footprint)||footprint<=0)throw new Error('Supply THREE and a positive footprint');
 const root=new T.Group();root.name='浅序住区';root.scale.setScalar(footprint/112);
 root.userData={moduleId:'qianxu-slab-residential',cityModule:true,front:'+Z'};
 const groups=new Map(),anchors=new Map(),ownedG=new Set(),ownedM=new Set(),ownedTex=new Set(),batches=new Map(),detail=[],windShaders=[],curtainShaders=[],windowLights=[];
 const treeSites=[],buildingSpecs=[['SLAB-A','A 栋',-33,16],['SLAB-B','B 栋',0,18],['SLAB-C','C 栋',33,20]],buildings=[];
 let disposed=false,time=0,windTime=0,level=quality,night=0,windEnabled=true,windStrength=.5;
 const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 for(const [id,z] of [['site',0],['landscape',0],...buildingSpecs.map(s=>[s[0],s[2]])]){const g=new T.Group();g.name=id;g.position.z=z;g.userData={id,owner:id};root.add(g);groups.set(id,g);anchors.set(id,new T.Vector3(0,0,z));}
 const G=g=>(ownedG.add(g),g),M=m=>(ownedM.add(m),m);
 const geo={box:G(new T.BoxGeometry(1,1,1)),cyl:G(new T.CylinderGeometry(.5,.5,1,12)),sphere:G(new T.SphereGeometry(.5,12,8)),leaf:G(new T.IcosahedronGeometry(1,1))};
 // Solid access-ramp wedge: near (negative Z) top Y=1, far (+Z) tip Y=0.
 // Duplicate face vertices retain crisp side edges and independent paving UVs.
 const rampPositions=[],rampUV=[];
 function rampTriangle(a,b,c,uv=[[0,0],[1,0],[0,1]]){rampPositions.push(...a,...b,...c);rampUV.push(...uv[0],...uv[1],...uv[2]);}
 const nl=[-.5,0,-.5],nr=[.5,0,-.5],tl=[-.5,1,-.5],tr=[.5,1,-.5],fl=[-.5,0,.5],fr=[.5,0,.5];
 rampTriangle(tl,fl,tr,[[0,0],[0,1],[1,0]]);rampTriangle(tr,fl,fr,[[1,0],[0,1],[1,1]]);
 rampTriangle(nl,tl,nr,[[0,0],[0,1],[1,0]]);rampTriangle(nr,tl,tr,[[1,0],[0,1],[1,1]]);
 rampTriangle(nl,nr,fl,[[0,0],[1,0],[0,1]]);rampTriangle(nr,fr,fl,[[1,0],[1,1],[0,1]]);
 rampTriangle(nl,fl,tl);rampTriangle(nr,tr,fr);
 geo.ramp=G(new T.BufferGeometry());geo.ramp.setAttribute('position',new T.Float32BufferAttribute(rampPositions,3));geo.ramp.setAttribute('uv',new T.Float32BufferAttribute(rampUV,2));geo.ramp.computeVertexNormals();
 function tex(name,size,paint){if(typeof document==='undefined')return null;const c=document.createElement('canvas');c.width=c.height=size;paint(c.getContext('2d'),size);const t=new T.CanvasTexture(c);t.name=name;t.colorSpace=T.SRGBColorSpace;t.wrapS=t.wrapT=T.RepeatWrapping;t.anisotropy=8;ownedTex.add(t);return t;}
 const wallTex=tex('Fine cream mineral render',256,(c,n)=>{c.fillStyle='#eeebe2';c.fillRect(0,0,n,n);const p=c.getImageData(0,0,n,n);for(let i=0;i<p.data.length;i+=4){const v=(rnd()-.5)*7;for(let k=0;k<3;k++)p.data[i+k]+=v;}c.putImageData(p,0,0);});
 const pavingTex=tex('Fine cut grey limestone',256,(c,n)=>{c.fillStyle='#b6bbb7';c.fillRect(0,0,n,n);for(let i=0;i<5000;i++){const v=Math.floor(140+rnd()*55);c.fillStyle=`rgba(${v},${v+2},${v},.2)`;c.fillRect(rnd()*n,rnd()*n,1,1);}c.strokeStyle='#999f9b';c.lineWidth=1;for(let i=0;i<=4;i++){c.beginPath();c.moveTo(i*n/4,0);c.lineTo(i*n/4,n);c.stroke();for(let j=0;j<4;j++){c.beginPath();c.moveTo(0,j*n/4);c.lineTo(n,j*n/4);c.stroke();}}});
 const woodTex=tex('Oiled timber grain',128,(c,n)=>{c.fillStyle='#927555';c.fillRect(0,0,n,n);for(let i=0;i<300;i++){const y=rnd()*n;c.strokeStyle=rnd()>.5?'#80664e':'#a18562';c.beginPath();c.moveTo(0,y);c.bezierCurveTo(45,y+rnd()*2,85,y-rnd()*2,n,y+rnd());c.stroke();}});
 const materials={};
 function mat(name,color,extra={}){const m=M(new T.MeshStandardMaterial({name,color,roughness:.78,...extra}));materials[name]=m;return m;}
 const wall=mat('Cream mineral render',0xffffff,{map:wallTex}),trim=mat('Light grey facade trim',0xb5bcb8),stone=mat('Warm limestone plinth',0xb9b5a8),roof=mat('Warm grey roof waterproofing',0xa8ada7),frame=mat('Graphite aluminium window frames',0x46585b,{metalness:.68,roughness:.32}),glass=mat('Silver blue residential glazing',0x638b94,{metalness:.35,roughness:.16,transparent:true,opacity:.74,depthWrite:false}),balconyGlass=mat('Clear enclosed balcony glass',0x9ab4b5,{metalness:.18,roughness:.14,transparent:true,opacity:.48,depthWrite:false}),reveal=mat('Inset window reveal',0xd8d7ce),interior=mat('Quiet interior shadow',0x536663),paving=mat('Grey stone paving',0xffffff,{map:pavingTex}),curb=mat('Pale kerbstone',0xc8cdc4),metal=mat('Satin galvanized fittings',0x8e9d99,{metalness:.72,roughness:.32}),dark=mat('Ventilation grille shadow',0x3e4b4c),wood=mat('Timber bench slats',0xffffff,{map:woodTex}),grass=mat('Clipped courtyard grass',0x7c956a),soil=mat('Planting soil',0x777865),leaf=mat('Olive evergreen foliage',0x46694b),leafLight=mat('Sunlit foliage',0x64815a),bark=mat('Tree bark',0x746c58),lamp=mat('Warm entrance diffuser',0xece5cf,{emissive:0xffd09a,emissiveIntensity:.03}),whitePaint=mat('Subtle service marking',0xe3e2d5);
 const curtains=[0xd5cdb8,0xb8c0b8,0xd4d4ca,0x9eafa9].map((v,i)=>mat('Curtain fabric '+i,v,{side:T.DoubleSide,roughness:.97}));
 for(let i=0;i<8;i++){const m=mat('Apartment interior '+i,[0xa6aaa0,0xb8aa8e,0x98a8a4,0xb6b7a3,0xa5a99b,0xa29b8a,0xa8b6b0,0xc1b39a][i],{emissive:0xffcb8a,emissiveIntensity:0,roughness:1});windowLights.push({material:m,threshold:.12+i*.085,occupancy:i%3!==0});}
 const mx=new T.Matrix4(),pos=new T.Vector3(),scl=new T.Vector3(),quat=new T.Quaternion(),euler=new T.Euler(),tint=new T.Color();
 function part(type,m,x,y,z,w,h,d,owner='site',tier=0,rotation=[0,0,0],color=null){
  const key=[type,m.uuid,owner,tier].join(':');if(!batches.has(key))batches.set(key,{type,m,owner,tier,items:[]});
  const a=anchors.get(owner);batches.get(key).items.push({p:[x-a.x,y-a.y,z-a.z],s:[w,h,d],r:rotation,color});
 }
 const box=(m,x,y,z,w,h,d,owner='site',tier=0)=>part('box',m,x,y,z,w,h,d,owner,tier);
 const cyl=(m,x,y,z,r,h,owner='site',tier=0)=>part('cyl',m,x,y,z,r,h,r,owner,tier);
 function rod(m,a,b,r,owner='site',tier=1){const aa=new T.Vector3(...a),bb=new T.Vector3(...b),p=aa.clone().add(bb).multiplyScalar(.5),q=new T.Quaternion().setFromUnitVectors(new T.Vector3(0,1,0),bb.clone().sub(aa).normalize());part('cyl',m,p.x,p.y,p.z,r,aa.distanceTo(bb),r,owner,tier,new T.Euler().setFromQuaternion(q).toArray().slice(0,3));}
 function sign(text,x,y,z,w,h,owner='site',background='#596c65',foreground='#f0ecdf'){
  if(typeof document==='undefined')return;const c=document.createElement('canvas');c.width=1024;c.height=256;const ctx=c.getContext('2d');ctx.fillStyle=background;ctx.fillRect(0,0,1024,256);ctx.strokeStyle='#9da99a';ctx.lineWidth=3;ctx.strokeRect(16,16,992,224);ctx.fillStyle=foreground;ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='500 105px Microsoft YaHei, sans-serif';ctx.fillText(text,512,132,930);const t=new T.CanvasTexture(c);t.colorSpace=T.SRGBColorSpace;ownedTex.add(t);const m=M(new T.MeshStandardMaterial({name:'Wayfinding '+text,map:t,roughness:.7}));const mesh=new T.Mesh(G(new T.PlaneGeometry(w,h)),m);mesh.name='Sign '+text;mesh.position.set(x,y,z-anchors.get(owner).z);groups.get(owner).add(mesh);
 }
 // The paving top is exactly Y=0 so the asset meets an arbitrary town parcel.
 box(paving,0,-.22,0,112,.44,112);for(const x of [-55.7,55.7])box(curb,x,.025,0,.6,.05,112);for(const z of [-55.7,55.7])box(curb,0,.025,z,110.8,.05,.6);
 for(const x of [-45,45])box(paving,x,.015,0,5,.03,109);
 for(const z of [-22,11,44])box(paving,0,.02,z,91,.04,4);
 for(const z of [-16.5,16.5]){box(grass,0,.025,z,74,.05,8.5,'landscape');for(const zz of [z-4.45,z+4.45])box(curb,0,.04,zz,74,.08,.25,'landscape');}
 for(const x of [-51,51])for(const z of [-34,-1,32])box(grass,x,.025,z,5.5,.05,22,'landscape');
 function entrance(id,label,x,z){
  box(stone,x,.15,z+8.55,8,.3,3.1,id);box(trim,x,.075,z+10.0,8.6,.15,.5,id);box(trim,x,.035,z+10.5,9.2,.07,.5,id);
  box(stone,x+5.75,.15,z+8.55,3.5,.3,3.1,id);
  part('ramp',paving,x+6,0,z+13.25,3,.3,6.3,id);
  // Keep the portal completely inside the first 3.1 m storey. The unit sign
  // sits on the front canopy fascia, ahead of the projecting balcony glazing.
  const bayLeft=x===-21?-24:x===21?16:-4,bayRight=bayLeft+8,doorLeft=x-2.3,doorRight=x+2.3;
  box(stone,(bayLeft+doorLeft)/2,1.66,z+6.94,doorLeft-bayLeft,2.72,.4,id);
  box(stone,(doorRight+bayRight)/2,1.66,z+6.94,bayRight-doorRight,2.72,.4,id);
  box(stone,(bayLeft+bayRight)/2,3.015,z+6.94,8,.17,.4,id);
  box(frame,x,1.69,z+7.12,4.6,2.78,.16,id);box(interior,x,1.66,z+7.05,4.35,2.65,.1,id);box(glass,x,1.65,z+7.28,4.25,2.62,.065,id);
  for(const xx of [x-2.15,x,x+2.15])box(frame,xx,1.69,z+7.34,.065,2.78,.09,id);
  for(const xx of [x-.18,x+.18])box(metal,xx,1.5,z+7.40,.04,.60,.06,id,1);
  box(trim,x,3.14,z+8.0,7.2,.20,4.0,id);box(metal,x,3.27,z+8.0,7.25,.045,4.05,id,1);box(lamp,x,3.02,z+8.4,5.8,.035,.4,id);
  box(frame,x,3.08,z+10.04,7.2,.38,.10,id);
  for(const xx of [x-3.15,x+3.15])box(metal,xx,1.66,z+8.5,.075,2.72,.075,id,1);
  sign(label,x,3.08,z+10.095,5.65,.30,id);
  box(stone,x-4.6,1,z+7.35,1.05,1.8,.5,id);box(dark,x-4.6,1.4,z+7.62,.7,.6,.07,id,1);
  for(let j=0;j<6;j++){box(metal,x+4.3+(j%2)*.48,.85+Math.floor(j/2)*.32,z+7.36,.44,.27,.2,id,1);box(dark,x+4.3+(j%2)*.48,.90+Math.floor(j/2)*.32,z+7.48,.27,.018,.025,id,2);}
  for(const xx of [x-3.5,x+3.5]){box(frame,xx,2.5,z+7.4,.16,.65,.18,id,1);box(lamp,xx,2.5,z+7.51,.10,.4,.045,id,1);}
 }
 function roofDetails(id,z,h){
  box(roof,0,h+.15,z,64,.3,14,id);for(const x of [-31.9,31.9]){box(trim,x,h+.72,z,.24,1.2,14,id);box(metal,x,h+1.34,z,.32,.055,14.1,id,1);}for(const zz of [z-6.9,z+6.9]){box(trim,0,h+.72,zz,64,1.2,.24,id);box(metal,0,h+1.34,zz,64.1,.055,.32,id,1);}
  for(const x of [-21,0,21]){
   box(wall,x,h+1.65,z-1,5.4,3,5.3,id);box(trim,x,h+3.25,z-1,5.75,.2,5.65,id);box(frame,x,h+1.25,z+1.70,1.2,2.1,.10,id);box(metal,x+.35,h+1.24,z+1.78,.045,.24,.04,id,2);
   box(dark,x-1.4,h+2.2,z+1.72,1.05,.65,.1,id,1);for(let j=0;j<5;j++)box(metal,x-1.4,h+1.95+j*.115,z+1.80,1.1,.04,.08,id,2);
   for(const xx of [x-4.5,x+4.5]){box(trim,xx,h+.36,z-1,2.7,.28,2.8,id,1);box(metal,xx,h+1.0,z-1,2.35,1.0,2.45,id);cyl(dark,xx,h+1.54,z-1,1.35,.08,id,1);for(const side of [-1,1])for(let j=0;j<6;j++)box(dark,xx,h+.66+j*.12,z-1+side*1.24,1.8,.04,.03,id,2);}
   cyl(metal,x+1.45,h+3.7,z-2.1,.18,.8,id,1);cyl(metal,x+1.45,h+4.15,z-2.1,.4,.10,id,1);
  }
  for(const x of [-27,-14,13,27]){cyl(metal,x,h+.7,z-4.5,.12,1,id,1);cyl(metal,x,h+1.23,z-4.5,.3,.07,id,1);}
  for(const side of [-1,1]){rod(metal,[-30,h+.43,z+side*4],[30,h+.43,z+side*4],.09,id,1);for(let x=-29;x<=29;x+=4)box(trim,x,h+.30,z+side*4,.3,.3,.5,id,2);}
  for(const x of [-31,31]){rod(metal,[x,h+.9,z-6],[x,h+2.4,z-6],.035,id,1);for(const side of [-1,1])box(dark,x,h+.3,z+side*6.1,.4,.045,.45,id,2);}
 }
 for(const [id,name,z,floors] of buildingSpecs){
  const h=floors*3.1;const building={id,name,x:0,z,width:64,depth:14,floors,height:h+4.2,front:'+Z',units:3};buildings.push(building);groups.get(id).userData={...groups.get(id).userData,...building,moduleId:'qianxu-slab-residential'};
  if(coarse){box(wall,0,h/2,z,64,h,14,id);for(const side of [-1,1])for(let f=0;f<floors;f++)box(glass,0,f*3.1+1.65,z+side*7.02,61,1.8,.06,id);roofDetails(id,z,h);continue;}
  // Slab edges, piers and spandrels surround real recessed window bays.
  box(stone,0,.4,z,64,.8,14,id);box(interior,0,h/2,z,62,h,10.6,id);
  for(let f=0;f<=floors;f++){const y=f*3.1;box(trim,0,y+.08,z,64,.16,14,id);for(const side of [-1,1]){box(wall,0,y+.43,z+side*6.9,64,.70,.38,id);box(trim,0,y+.10,z+side*7.04,64,.16,.30,id);}}
  for(let i=0;i<=16;i++){const x=-32+i*4;for(const side of [-1,1]){const entryPier=side===1&&[-21,0,21].some(cx=>Math.abs(x-cx)<4),bottom=entryPier?3.1:0,ph=h-bottom,py=(h+bottom)/2;box(wall,x,py,z+side*6.84,.66,ph,.65,id);if(i%4===0)box(trim,x,py,z+side*7.10,.16,ph,.12,id,1);}}
  for(const x of [-32,32]){box(wall,x,h/2,z,.48,h,14,id);box(trim,x,h/2,z-4,.15,h,.32,id,1);box(trim,x,h/2,z+4,.15,h,.32,id,1);}
  for(const x of [-21.3,0,21.3])box(trim,x,h/2,z-7.1,.28,h,.14,id);
  for(let f=0;f<floors;f++){
   const y=f*3.1+1.91;
   for(const side of [-1,1])for(let i=0;i<16;i++){
    const x=-30+i*4,occupied=rnd(),m=windowLights[Math.floor(rnd()*8)].material,balcony=side===1&&(i%4===0||i%4===1),front=z+side*7.02,curtainWidth=occupied>.30?.50+rnd()*.7:0;
    // Consume the same seeded choices while reserving clean ground-floor
    // entrance bays. No apartment windows, curtains or balcony frame cross it.
    if(f===0&&side===1&&[-21,0,21].some(cx=>Math.abs(x-cx)<4))continue;
    // Recessed glazing has a visible sill, head, jamb thickness and interior.
    for(const xx of [x-1.62,x+1.62])box(reveal,xx,y,front-side*.13,.12,2.34,.28,id);
    for(const yy of [y-1.12,y+1.12])box(reveal,x,yy,front-side*.13,3.35,.12,.28,id);
    box(m,x,y,front-side*.25,3.13,2.11,.09,id);
    box(glass,x,y,front+side*.015,3.15,2.12,.035,id);
    for(const xx of [x-1.63,x+1.63])box(frame,xx,y,front+side*.055,.085,2.3,.10,id);
    for(const yy of [y-1.13,y+1.13])box(frame,x,yy,front+side*.055,3.34,.075,.10,id);
    box(frame,x+(i%2?.35:-.35),y,front+side*.065,.055,2.18,.09,id,1);
    box(frame,x,y+.4,front+side*.065,3.22,.045,.08,id,1);
    box(trim,x,y-1.19,front+side*.05,3.56,.14,.48,id,1);
    if(occupied>.30){for(const edge of [-1,1])box(curtains[(f+i)%4],x+edge*(1.45-curtainWidth/2),y,front-side*.13,curtainWidth,2.08,.025,id,1);}
    if(balcony){
     const bz=front+.95;box(trim,x,f*3.1+.18,bz,3.67,.20,2.1,id);box(trim,x,f*3.1+3.10,bz,3.67,.16,2.1,id);
     for(const xx of [x-1.77,x+1.77])box(wall,xx,y,bz,.15,2.78,2.0,id);
     box(balconyGlass,x,y,bz+1.0,3.40,2.68,.035,id);
     for(const xx of [x-1.72,x-1.72/3,x+1.72/3,x+1.72])box(frame,xx,y,bz+1.04,.055,2.78,.07,id,1);
     for(const yy of [f*3.1+.45,f*3.1+1.25,f*3.1+3.03])box(frame,x,yy,bz+1.04,3.5,.055,.07,id,1);
     box(trim,x,f*3.1+.38,bz+1.02,3.54,.29,.12,id);
     box(dark,x+1.25,f*3.1+.38,bz+.75,.14,.05,.16,id,2);
    }else if(side===-1&&i%4===2){
     // Integrated air-conditioner niches, screened rather than scattered boxes.
     box(trim,x+1.55,y-.2,front-.36,.8,1.1,.7,id,1);box(dark,x+1.55,y-.2,front-.75,.65,.85,.03,id,1);for(let j=0;j<5;j++)box(metal,x+1.55,y-.53+j*.16,front-.79,.69,.045,.08,id,2);
    }
   }
   for(const x of [-32.27,32.27])for(const zz of [z-3,z+3]){box(frame,x,y,zz,.12,1.8,1.5,id);box(glass,x+(x<0?-.07:.07),y,zz,.04,1.62,1.3,id);box(trim,x,y-.95,zz,.3,.12,1.7,id,1);}
  }
  for(const x of [-27,27])rod(metal,[x,.3,z-7.18],[x,h-.2,z-7.18],.075,id,1);
  for(let i=0;i<3;i++)entrance(id,`${name} · ${i+1} 单元`,-21+i*21,z);
  roofDetails(id,z,h);
 }
 // Quiet pedestrian courtyards; no municipal roads, cars or people.
 const shrubSites=[];
 if(!coarse){
  for(const x of [-51,51])for(const z of [-44,-12,20,47]){
   treeSites.push([x,z]);const h=5.4+rnd()*1.4;cyl(bark,x,h*.31,z,.23,h*.62,'landscape');
   for(let j=0;j<4;j++){const a=j*2.1;rod(bark,[x,h*.38,z],[x+Math.sin(a)*1.25,h*.77,z+Math.cos(a)*1.25],.07,'landscape');}
   for(let j=0;j<6;j++){const a=j*2.4;part('leaf',j%2?leaf:leafLight,x+Math.sin(a)*1.15,h*.72+(j%3)*.42,z+Math.cos(a)*1.15,1.55,1.9,1.55,'landscape',0,[rnd(),a,rnd()]);}
   for(let j=0;j<30;j++){const a=j*2.4,r=rnd()*1.9;part('leaf',j%2?leaf:leafLight,x+Math.sin(a)*r,h*.68+rnd()*1.4,z+Math.cos(a)*r,.45,.55,.45,'landscape',2,[rnd(),a,rnd()]);}
   box(soil,x,.03,z,3.5,.06,3.5,'landscape');
  }
  for(const z of [-16.5,16.5])for(const x of [-31,-22,22,31]){
   shrubSites.push([x,z]);box(soil,x,.035,z,5.5,.07,3.1,'landscape');for(let j=0;j<14;j++){const xx=x+(rnd()-.5)*4.5,zz=z+(rnd()-.5)*2.2;part('leaf',j%2?leaf:leafLight,xx,.60+rnd()*.15,zz,.65+rnd()*.45,.45+rnd()*.15,.65+rnd()*.45,'landscape',0,[0,rnd()*6,0]);}
  }
  for(const z of [-21.9,11.1])for(const x of [-16,16]){
   for(let j=0;j<6;j++)box(wood,x,.51,z+(j-2.5)*.14,3.2,.075,.11,'landscape',1);
   for(let j=0;j<3;j++)box(wood,x,.8+j*.16,z-.47,3.2,.12,.075,'landscape',1);
   for(const xx of [x-1.15,x+1.15]){box(frame,xx,.27,z,.10,.45,.8,'landscape');box(frame,xx,.75,z-.45,.10,1.0,.12,'landscape');}
  }
  for(const x of [-45,45])for(const z of [-49,-17,16,49]){
   cyl(frame,x,2.5,z,.12,5,'landscape');box(frame,x,5.01,z,1.2,.16,.48,'landscape');box(lamp,x,4.92,z,1.05,.035,.34,'landscape');box(stone,x,.075,z,.55,.15,.55,'landscape');
  }
  for(const z of [-22,11,44])for(let x=-38;x<=38;x+=7)box(dark,x,.025,z+2.17,.8,.028,.18,'site',2);
  for(const z of [-22,11,44])for(const x of [-40,40]){box(stone,x,.035,z-.6,.8,.06,.8);for(let j=0;j<4;j++)box(metal,x-.24+j*.16,.07,z-.6,.04,.012,.54,'site',2);}
 }
 box(stone,-8,.8,52,13,1.6,.65);sign('浅 序 住 区',-8,1.0,52.34,11.6,1.03);sign('QIANXU · RESIDENCES',-8,.27,52.35,10.8,.27,'site','#c0c4b9','#4e6159');
 box(paving,6,.015,51,11,.03,8);for(const x of [1,11]){box(stone,x,.6,51,.4,1.2,.4);box(lamp,x,1.22,51,.3,.04,.3);}
 for(const b of batches.values()){
  const o=new T.InstancedMesh(geo[b.type],b.m,b.items.length);o.name=`${b.owner} / ${b.m.name} / L${b.tier}`;o.userData={owner:b.owner,tier:b.tier,fullCount:b.items.length};o.castShadow=!b.m.transparent&&b.m!==lamp;o.receiveShadow=true;
  b.items.forEach((it,i)=>{pos.fromArray(it.p);scl.fromArray(it.s);quat.setFromEuler(euler.set(...it.r));mx.compose(pos,quat,scl);o.setMatrixAt(i,mx);if(it.color){tint.set(it.color);o.setColorAt(i,tint);}});o.computeBoundingBox();o.computeBoundingSphere();groups.get(b.owner).add(o);detail.push(o);
 }
 function windMaterial(m,amplitude,cloth=false){
  m.onBeforeCompile=shader=>{shader.uniforms.uResidentialWindTime={value:windTime};shader.uniforms.uResidentialWindStrength={value:windStrength};(cloth?curtainShaders:windShaders).push(shader);shader.vertexShader='uniform float uResidentialWindTime,uResidentialWindStrength;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>\n#ifdef USE_INSTANCING\nfloat phase=instanceMatrix[3].x*.43+instanceMatrix[3].z*.27+instanceMatrix[3].y*.19;float anchored=${cloth?'max(0.,.5-position.y)':'max(0.,position.y+.55)'};transformed.x+=sin(uResidentialWindTime*${cloth?'.65':'1.15'}+phase)*${amplitude}*uResidentialWindStrength*anchored;\n#endif`);};
  m.customProgramCacheKey=()=>`qianxu-wind-${cloth?1:0}-${amplitude}`;
 }
 windMaterial(leaf,'.10');windMaterial(leafLight,'.09');curtains.forEach(m=>windMaterial(m,'.025',true));
 const metadata={id:'qianxu-slab-residential',name:'浅序住区',version:'1.0.0',units:'m',upAxis:'Y',front:'+Z',pivot:'ground-center',footprint:{width:footprint,depth:footprint},nativeFootprint:112,connectionLevel:0,buildings,containsPeople:false,containsRoads:false,treeCount:treeSites.length,treeSites,shrubSites,entrances:[{position:[6,0,56],width:11,direction:'+Z'}],components:[...groups.keys()],nativeBounds:{min:[-56,-.44,-56],max:[56,66.2,56]}};
 function setTimeOfDay(value){
  night=typeof value==='number'?T.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'||value==='dusk'?.48:0;
  for(const w of windowLights){const t=T.MathUtils.smoothstep(night,w.threshold,Math.min(1,w.threshold+.16));w.material.emissiveIntensity=w.occupancy?t*(.60+(w.threshold*.7)):.02*t;}
  lamp.emissiveIntensity=.03+T.MathUtils.smoothstep(night,.15,.65)*2.8;
 }
 function update(delta=0,state={}){
  if(disposed)return;const dt=state.paused?0:Number.isFinite(delta)?T.MathUtils.clamp(delta,0,.25):0;time+=dt;
  if(state.wind!==undefined)windEnabled=!!state.wind;if(state.windStrength!==undefined&&Number.isFinite(state.windStrength))windStrength=T.MathUtils.clamp(state.windStrength,0,2);
  if(windEnabled)windTime+=dt;
  for(const shader of [...windShaders,...curtainShaders]){shader.uniforms.uResidentialWindTime.value=windTime;shader.uniforms.uResidentialWindStrength.value=windStrength;}
  if(state.nightFactor!==undefined)setTimeOfDay(state.nightFactor);else if(state.timeOfDay!==undefined)setTimeOfDay(state.timeOfDay);
 }
 function setQuality(value){if(!['high','medium','low'].includes(value))throw new Error('Unknown quality');level=value;for(const o of detail)o.visible=o.userData.tier===0||value==='high'||value==='medium'&&o.userData.tier<2;}
 function getBounds(){root.updateWorldMatrix(true,true);return new T.Box3().setFromObject(root);}
 function exportScene(){
  const previous=level,visibility=root.visible;setQuality('high');root.visible=true;root.updateWorldMatrix(true,true);const geometries={},mats={},objects=[];
  try{root.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry,m=o.material;if(!geometries[g.uuid])geometries[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null,colors:g.attributes.color?Array.from(g.attributes.color.array):null};if(!mats[m.uuid])mats[m.uuid]={name:m.name,color:m.color.toArray(),roughness:m.roughness,metalness:m.metalness,opacity:m.opacity,transparent:m.transparent,emissive:m.emissive?.toArray()||[0,0,0],emissiveIntensity:m.emissiveIntensity||0,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1],side:m.side};
   let owner=o;while(owner!==root&&!owner.userData.owner)owner=owner.parent;for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,mx);mx.premultiply(o.matrixWorld);}else mx.copy(o.matrixWorld);let color=null;if(o.instanceColor){o.getColorAt(i,tint);color=tint.toArray();}objects.push({g:g.uuid,m:m.uuid,matrix:mx.toArray(),tint:color,owner:owner.userData.owner||'site'});}
  });return{format:'qianxu-slab-residential-v1',snapshotSpace:'world',metadata,manifest:metadata,state:{time,windTime,night},geometries,materials:mats,objects};}finally{root.visible=visibility;setQuality(previous);}
 }
 function makeExportClone(){const previous=level,visibility=root.visible;setQuality('high');root.visible=true;const copy=root.clone(true);root.visible=visibility;setQuality(previous);return copy;}
 async function exportGLB({GLTFExporter}={}){if(typeof GLTFExporter!=='function')throw new Error('Pass GLTFExporter from the host Three.js version');const clone=makeExportClone();try{clone.updateMatrixWorld(true);return await new GLTFExporter().parseAsync(clone,{binary:true,onlyVisible:true});}finally{clone.traverse(o=>{if(o.isInstancedMesh)o.dispose();});clone.clear();}}
 function dispose(){if(disposed)return;disposed=true;root.removeFromParent();root.traverse(o=>{if(o.isInstancedMesh)o.dispose();});for(const g of ownedG)g.dispose();for(const m of ownedM)m.dispose();for(const t of ownedTex)t.dispose();root.clear();groups.clear();batches.clear();windShaders.length=curtainShaders.length=0;}
 setQuality(quality);setTimeOfDay(0);update(0);
 return{root,groups,metadata,manifest:metadata,buildings,materials,update,setQuality,setTimeOfDay,getBounds,exportScene,exportGLB,makeExportClone,dispose,get quality(){return level;},get simulationTime(){return time;},get windTime(){return windTime;},get nightFactor(){return night;},get disposed(){return disposed;}};
}
export default createResidentialBlock;
