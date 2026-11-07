/** Host-injected Three.js factory. Metres, Y up, +Z front, no renderer or RAF. */
export function createSkylineTower({THREE,blockSize=112,quality='high',embedded=true,seed=1101,coarse=false}={}){
  if(!THREE?.Group)throw new Error('Pass the host THREE instance');
  if(!Number.isFinite(blockSize)||blockSize<=0)throw new Error('blockSize must be positive');
  const root=new THREE.Group();root.name='SKYLINE-ONE';
  const groups=new Map(),buckets=new Map(),materials={},geometries=new Set(),materialSet=new Set(),textures=new Set(),details=[],windShaders=[],people=[],cars=[],fans=[],doors=[],flags=[],birds=[];
  const manifest={id:'skyline-one',name:'云际中心',version:'1.0.0',units:'m',upAxis:'Y',front:'+Z',pivot:'ground-center',footprint:{width:blockSize,depth:blockSize},nativeFootprint:112,scale:blockSize/112,height:224*blockSize/112,floors:55,embedded,coordinateSpace:'native-local-metres; multiply by scale for host metres',bounds:{min:[-56,-4.5,-56],max:[56,224,56]},animatedBounds:{min:[-56,-4.5,-56],max:[56,251,56]},excavations:[{id:'garage',min:[-47,-4.5,-39],max:[-35,0,-12]}],entrances:{public:{position:[0,0,56],direction:[0,0,1],width:10},vehicle:{position:[56,0,39],direction:[1,0,0],width:7},service:{position:[-56,0,-44],direction:[-1,0,0],width:7}},buildingIds:['tower','podium'],buildings:[{id:'tower',name:'云际塔楼',x:0,z:-6,w:38,d:36,height:224,floors:52},{id:'podium',name:'云际商业裙房',x:0,z:-6,w:64,d:56,height:18,floors:3}],components:[{id:'tower',name:'超高层塔楼'},{id:'podium',name:'商业与双层大堂'},{id:'landscape',name:'云际广场与退台花园'},{id:'roof',name:'停机坪与机电层'},{id:'site',name:'道路与地下车库'}]};
  for(const id of ['site','tower','podium','landscape','roof','life']){const g=new THREE.Group();g.name=id;g.userData={id,semantic:'skyline-component',name:manifest.components.find(c=>c.id===id)?.name||'院内动态'};root.add(g);groups.set(id,g);}
  root.scale.setScalar(blockSize/112);
  let disposed=false,dynamics=true,level=quality,time=0,windTime=0,night=0,traffic=true,wind=true,flight=true;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const ownG=g=>(geometries.add(g),g),ownM=m=>(materialSet.add(m),m);
  const geo={box:ownG(new THREE.BoxGeometry(1,1,1)),cylinder:ownG(new THREE.CylinderGeometry(.5,.5,1,12)),sphere:ownG(new THREE.SphereGeometry(.5,12,8)),leaf:ownG(new THREE.IcosahedronGeometry(.5,0)),torus:ownG(new THREE.TorusGeometry(.5,.045,6,32))};
  function grain(color,amount=9){const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d');x.fillStyle=color;x.fillRect(0,0,128,128);const im=x.getImageData(0,0,128,128);for(let i=0;i<im.data.length;i+=4){let n=(random()-.5)*amount;for(let k=0;k<3;k++)im.data[i+k]+=n;}x.putImageData(im,0,0);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(8,8);t.anisotropy=4;textures.add(t);return t;}
  function mat(name,color,options={}){const Type=name.startsWith('glass-')||name.startsWith('office-lit-')?THREE.MeshPhysicalMaterial:THREE.MeshStandardMaterial;const m=ownM(new Type({color,roughness:.65,...(Type===THREE.MeshPhysicalMaterial?{clearcoat:1,clearcoatRoughness:.07}:{}),...options}));m.name=name;materials[name]=m;return m;}
  mat('bronze',0x9c7750,{metalness:.8,roughness:.28});mat('bronze-light',0xcfac78,{metalness:.75,roughness:.29});mat('steel',0x50656a,{metalness:.85,roughness:.31});mat('stone',0xffffff,{map:grain('#c2bcb0'),roughness:.87});mat('paving',0xffffff,{map:grain('#d7d1c4',5),roughness:.84});mat('asphalt',0xffffff,{map:grain('#233944',8),roughness:.95});mat('core',0x16313a,{roughness:.7});
  for(const [i,c] of [0x3c6472,0x416a77,0x355d6b,0x47717e].entries())mat('glass-'+i,c,{metalness:.68,roughness:.12,envMapIntensity:1.7});
  mat('spandrel',0x233f49,{metalness:.56,roughness:.28});mat('clear-glass',0x7eafb3,{transparent:true,opacity:.38,metalness:.28,roughness:.1,depthWrite:false});mat('interior',0xafa18a);mat('black',0x182a30);mat('paint',0xe8e0c5);mat('yellow',0xcba05d);mat('wood',0x71513c,{roughness:.87});mat('soil',0x4b4a40);mat('leaf',0x74394b,{roughness:.94});mat('leaf-light',0xa16068,{roughness:.92});mat('sage',0x738a7f,{roughness:.92});mat('grass',0x627a61);mat('lamp',0xffe6b2,{emissive:0xffc87d,emissiveIntensity:.1});mat('beacon',0xc84d33,{emissive:0xff4428,emissiveIntensity:.1});mat('skin',0xc3a287);mat('suit',0x344e58);mat('coat',0xb2a187);mat('rubber',0x16252b);mat('car-pearl',0xc7cfca,{metalness:.65,roughness:.24});mat('car-copper',0x885d43,{metalness:.7,roughness:.23});mat('car-dark',0x253b43,{metalness:.7,roughness:.22});mat('water',0x577d7d,{metalness:.55,roughness:.13});
  for(let i=0;i<4;i++)mat('office-lit-'+i,0x466c76,{emissive:0xffcf8d,emissiveIntensity:.025,roughness:.17,metalness:.45,envMapIntensity:1.6});
  const matrix=new THREE.Matrix4(),position=new THREE.Vector3(),quaternion=new THREE.Quaternion(),scale=new THREE.Vector3();
  function part(type,m,p,s,r=0,owner='site',tier=0){const key=[owner,type,m,tier].join('|');if(!buckets.has(key))buckets.set(key,{type,m,owner,tier,items:[]});buckets.get(key).items.push({p,s,r:Array.isArray(r)?r:[0,r,0]});}
  const box=(m,x,y,z,w,h,d,r=0,o='site',t=0)=>part('box',m,[x,y,z],[w,h,d],r,o,t);
  const cyl=(m,x,y,z,w,h,d,o='site',t=0)=>part('cylinder',m,[x,y,z],[w,h,d],0,o,t);
  function beam(m,a,b,r,owner='tower',tier=1){const va=new THREE.Vector3(...a),vb=new THREE.Vector3(...b),mid=va.clone().add(vb).multiplyScalar(.5);const q=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),vb.sub(va).normalize());part('cylinder',m,mid.toArray(),[r,new THREE.Vector3(...a).distanceTo(new THREE.Vector3(...b)),r],new THREE.Euler().setFromQuaternion(q).toArray().slice(0,3),owner,tier);}
  function mesh(type,m,p,s,parent,r=[0,0,0]){const obj=new THREE.Mesh(geo[type],materials[m]);obj.position.fromArray(p);obj.scale.fromArray(s);obj.rotation.set(...r);obj.castShadow=!['clear-glass','water'].includes(m);obj.receiveShadow=true;parent.add(obj);return obj;}
  function sign(text,p,w,h,owner='podium',rotation=0,{bg='#233b43',fg='#dfbd87',font=70}={}){const c=document.createElement('canvas');c.width=1024;c.height=256;const ctx=c.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,1024,256);ctx.fillStyle=fg;ctx.font=`500 ${font}px "Microsoft YaHei",sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,512,134,980);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;textures.add(t);const m=ownM(new THREE.MeshStandardMaterial({map:t,roughness:.5,emissive:0xd7b67f,emissiveIntensity:.08}));m.name='sign:'+text;const obj=new THREE.Mesh(ownG(new THREE.PlaneGeometry(w,h)),m);obj.position.fromArray(p);obj.rotation.y=rotation;obj.name=text;groups.get(owner).add(obj);return obj;}
  // PHASE A — metric blockout. Cut the site and display floor around the garage.
  for(const [x,z,w,d] of [[-51.5,0,9,112],[10.5,0,91,112],[-41,-47.5,12,17],[-41,22,12,68]])box('paving',x,-.18,z,w,.36,d);
  const tiers=[{bottom:18,n:20,w:38,d:36},{bottom:92,n:17,w:32,d:30},{bottom:154.9,n:15,w:26,d:24}];
  box('core',0,9,-6,60,18,52,0,'podium');
  for(const t of tiers)box('core',0,t.bottom+t.n*3.7/2,-6,t.w-3,t.n*3.7,t.d-3,0,'tower');
  box('steel',0,213.4,-6,24,6,22,0,'roof');box('steel',0,218.5,-6,27,.8,27,0,'roof');
  // PHASE B — facade, steelwork, interior depth, terraces and technical equipment.
  function railing(x,z,w,d,y,owner){for(const s of [-1,1]){box('clear-glass',x,y+.65,z+s*d/2,w,1.15,.055,0,owner,1);box('bronze',x,y+1.25,z+s*d/2,w,.08,.1,0,owner);box('clear-glass',x+s*w/2,y+.65,z,.055,1.15,d,0,owner,1);box('bronze',x+s*w/2,y+1.25,z,.1,.08,d,0,owner);for(let a=-w/2;a<=w/2;a+=2)box('bronze',x+a,y+.63,z+s*d/2,.055,1.2,.08,0,owner,2);}}
  function tree(x,z,s=1,y=0,owner='landscape',sage=false){cyl('wood',x,y+2.2*s,z,.25*s,4.2*s,.25*s,owner);cyl('soil',x,y+.16,z,2.4*s,.1,2.4*s,owner);for(let b=0;b<4;b++){const a=b*1.57;beam('wood',[x,y+2.8*s,z],[x+Math.cos(a)*1.2*s,y+4.5*s,z+Math.sin(a)*1.2*s],.1*s,owner);}
    for(let i=0;i<(coarse?5:140);i++){const a=i*2.39996,r=Math.sqrt(random())*2.45*s;part('leaf',sage?'sage':i%3?'leaf':'leaf-light',[x+Math.cos(a)*r,y+(4.9+random()*1.4)*s-r*r*.07,z+Math.sin(a)*r],[.85*s,.38*s,.95*s],[random(),a,random()],owner,1);}part('sphere',sage?'sage':'leaf',[x,y+5*s,z],[4.5*s,3.5*s,4.4*s],0,owner,-1);}
  if(!coarse){
    let floor=0;
    for(const t of tiers){const nx=Math.round(t.w/3.2),nz=Math.round(t.d/3.2),sx=t.w/nx,sz=t.d/nz;
      for(let f=0;f<t.n;f++,floor++){const y=t.bottom+f*3.7;
        for(const side of [-1,1]){
          box('spandrel',0,y+.45,-6+side*(t.d/2+.025),t.w,.9,.12,0,'tower');box('bronze',0,y+.04,-6+side*(t.d/2+.12),t.w+.12,.11,.18,0,'tower');
          box('spandrel',side*(t.w/2+.025),y+.45,-6,.12,.9,t.d,0,'tower');box('bronze',side*(t.w/2+.12),y+.04,-6,.18,.11,t.d+.12,0,'tower');
          for(let c=0;c<nx;c++){const x=-t.w/2+sx*(c+.5),z=-6+side*(t.d/2+.045),lit=random()<.18;box(lit?'office-lit-'+(floor%4):'glass-'+Math.floor(random()*4),x,y+2.18,z,sx-.13,2.6,.13,0,'tower');box('bronze',x-sx/2,y+1.85,z+side*.12,.11,3.7,.24,0,'tower');box('steel',x,y+3.35,z+side*.08,sx-.1,.045,.12,0,'tower',2);
            if(lit){box('office-lit-'+(floor%4),x,y+2.05,z-side*.75,sx-.35,2.35,.06,0,'tower',1);box('interior',x,y+.98,z-side*1.3,sx-.35,.08,1.1,0,'tower',2);if(c%3===0)box('interior',x,y+1.85,z-side*.38,sx-.3,1.25,.045,0,'tower',2);}
          }
          for(let c=0;c<nz;c++){const z=-6-t.d/2+sz*(c+.5),x=side*(t.w/2+.045),lit=random()<.15;box(lit?'office-lit-'+(floor%4):'glass-'+Math.floor(random()*4),x,y+2.18,z,.13,2.6,sz-.13,0,'tower');box('bronze',x+side*.12,y+1.85,z-sz/2,.24,3.7,.11,0,'tower');if(lit)box('office-lit-'+(floor%4),x-side*.75,y+2.05,z,.06,2.35,sz-.35,0,'tower',1);}
        }
      }
      for(const s of [-1,1])for(const a of [-1,1])box('bronze-light',s*(t.w/2+.17),t.bottom+t.n*3.7/2,-6+a*(t.d/2+.17),.38,t.n*3.7,.38,0,'tower');
      // Expressed corner diagonals resolve into five-storey structural bays.
      for(let k=0;k<t.n-4;k+=5)for(const s of [-1,1]){beam('bronze',[s*t.w/2,t.bottom+k*3.7,-6+t.d/2+.22],[s*(t.w/2-5.7),t.bottom+(k+5)*3.7,-6+t.d/2+.22],.22,'tower');}
    }
    // Three-level podium with a readable double-height lobby and shopfront bays.
    for(const s of [-1,1]){
      for(let x=-30;x<=30;x+=4){box('clear-glass',x,5.5,-6+s*28.07,3.85,10.6,.18,0,'podium');box('bronze',x-2,8.8,-6+s*28.25,.18,17.6,.32,0,'podium');box('glass-0',x,14.5,-6+s*28.07,3.85,6.5,.18,0,'podium');}
      for(let z=-32;z<=20;z+=4){box('clear-glass',s*32.07,5.5,z,.18,10.6,3.85,0,'podium');box('bronze',s*32.25,8.8,z-2,.32,17.6,.18,0,'podium');box('glass-0',s*32.07,14.5,z,.18,6.5,3.85,0,'podium');}
      for(const y of [0.5,10.8,17.9]){box('bronze-light',0,y,-6+s*28.3,64.6,.25,.38,0,'podium');box('bronze-light',s*32.3,y,-6,.38,.25,56.6,0,'podium');}
      // Structure and interior rooms are behind the glass rather than painted on it.
      for(let x=-28;x<=28;x+=8){box('steel',x,5.2,20.9,.55,10.4,.55,0,'podium');box('interior',x,2.1,20.3,6.3,3.8,.12,0,'podium',1);}
    }
    box('black',0,5.2,22.18,13,10.4,.3,0,'podium');box('clear-glass',0,5.2,22.45,12.7,10.1,.1,0,'podium');box('bronze-light',0,7.5,27,20,.35,10,0,'podium');
    for(const x of [-9,9]){box('bronze',x,3.7,30,.28,7.4,.28,0,'podium');beam('bronze',[x,7.3,30],[x,10.5,22.3],.16,'podium');}
    for(const side of [-1,1]){const door=mesh('box','clear-glass',[side*.8,2,22.6],[1.55,3.8,.11],groups.get('podium'));door.name='automatic-lobby-door';doors.push({mesh:door,side,base:side*.8});box('bronze-light',side*1.58,2,22.7,.05,3.8,.08,0,'podium',1);}
    sign('云 际 中 心',[0,9.4,22.6],14,2.7);sign('SKYLINE ONE',[0,6.9,32.06],14,1.5);sign('ATELIER CAFÉ',[-21,4.7,22.3],9,1.25);sign('GALLERY 01',[21,4.7,22.3],9,1.25);
    for(const x of [-23,-16,16,23]){cyl('bronze',x,.9,26,1,.09,1,'landscape',1);cyl('bronze',x,.5,26,.1,.8,.1,'landscape',1);for(const dz of [-.8,.8])box('wood',x,.6,26+dz,.75,.1,.65,0,'landscape',1);}
    // Habitable roofs and two generous setbacks with parapets, drainage and planting.
    box('stone',0,18.12,-6,64,.24,56,0,'podium');railing(0,-6,63,55,18.2,'podium');
    for(const [y,w,d,nw,nd] of [[92,38,36,32,30],[154.9,32,30,26,24]]){box('stone',0,y+.06,-6,w,.12,d,0,'tower');railing(0,-6,w-.4,d-.4,y+.15,'tower');for(const s of [-1,1]){box('stone',s*(w/2-1.2),y+.7,-6,1.3,1.1,d-3,0,'tower');box('sage',s*(w/2-1.2),y+1.35,-6,1.05,.5,d-3,0,'tower');box('wood',0,y+.7,-6+s*(d/2-1.2),nw-2,.15,.6,0,'tower',1);}for(let x=-nw/2+2;x<nw/2;x+=3)box('bronze',x,y+.2,-6+d/2-.3,2.6,.025,.08,0,'tower',2);}
    for(const [x,z] of [[-26,-26],[26,-26],[-26,14],[26,14]]){box('stone',x,18.7,z,6,1,6,0,'podium');tree(x,z,.65,19.2,'podium',true);}
    for(let x=-24;x<=24;x+=4){box('wood',x,18.8,17,2.7,.15,.7,0,'podium');box('bronze',x,18.45,17,.15,.6,.7,0,'podium',1);}
    // Crown, roof access and screened mechanical plant below the elevated helipad.
    for(const s of [-1,1]){for(let y=211;y<216;y+=.36){box('bronze',0,y,-6+s*11.1,24,.1,.18,0,'roof',1);box('bronze',s*12.1,y,-6,.18,.1,22,0,'roof',1);}for(let x=-11;x<=11;x+=2)box('steel',x,217,-6+s*11,.18,4,.18,0,'roof');}
    for(const x of [-7,0,7]){box('steel',x,212,-7,5,2.4,5,0,'roof');for(const z of [-8.3,-5.7]){cyl('black',x,213.25,z,1.9,.15,1.9,'roof');const f=new THREE.Group();f.position.set(x,213.36,z);groups.get('roof').add(f);for(let j=0;j<4;j++){const b=mesh('box','steel',[.44,0,0],[.9,.045,.16],f);b.rotation.y=j*Math.PI/2;b.position.set(Math.cos(j*Math.PI/2)*.44,0,Math.sin(j*Math.PI/2)*.44);}fans.push(f);}}
    box('stone',-8,213.1,1,4,5.3,4,0,'roof');box('black',-8,212.7,3.05,1.3,2.4,.08,0,'roof');box('steel',5,212.3,1,8,.7,.8,0,'roof');box('steel',8.6,213,1,.8,2,.8,0,'roof');
    for(let i=0;i<12;i++)box('steel',-10.4,211+i*.35,1,.12,.07,1.3,0,'roof',2);
    // Circular safety edge with a square pad, avoiding a fabricated scale helipad.
    const padCanvas=document.createElement('canvas');padCanvas.width=padCanvas.height=1024;const pc=padCanvas.getContext('2d');pc.fillStyle='#374e52';pc.fillRect(0,0,1024,1024);pc.strokeStyle='#e2cf99';pc.lineWidth=12;pc.strokeRect(40,40,944,944);pc.beginPath();pc.arc(512,512,350,0,Math.PI*2);pc.stroke();pc.fillStyle='#e9dfbc';pc.font='500 440px sans-serif';pc.textAlign='center';pc.textBaseline='middle';pc.fillText('H',512,530);pc.font='34px sans-serif';pc.fillText('SKYLINE  •  22 t',512,930);const pt=new THREE.CanvasTexture(padCanvas);pt.colorSpace=THREE.SRGBColorSpace;textures.add(pt);const pm=ownM(new THREE.MeshStandardMaterial({map:pt,roughness:.85}));pm.name='Helipad markings';const pad=new THREE.Mesh(ownG(new THREE.PlaneGeometry(26,26)),pm);pad.rotation.x=-Math.PI/2;pad.position.set(0,218.92,-6);pad.receiveShadow=true;groups.get('roof').add(pad);
    for(const s of [-1,1]){box('steel',0,218.7,-6+s*14.1,28.2,.06,.06,0,'roof');box('steel',s*14.1,218.7,-6,.06,.06,28.2,0,'roof');for(let a=-14;a<=14;a+=.4){box('steel',a,218.4,-6+s*13.8,.015,.015,1.8,0,'roof',2);box('steel',s*13.8,218.4,-6+a,1.8,.015,.015,0,'roof',2);}}
    for(let a=0;a<24;a++){const angle=a/24*Math.PI*2,x=Math.cos(angle)*13,z=-6+Math.sin(angle)*13;cyl('steel',x,218.4,z,.05,.4,.05,'roof',1);if(a%2===0)cyl('lamp',Math.cos(angle)*12.6,219.08,-6+Math.sin(angle)*12.6,.23,.15,.23,'roof');}
    cyl('steel',-11.7,220.4,-17,.1,7,.1,'roof');cyl('beacon',-11.7,223.8,-17,.28,.3,.28,'roof');box('yellow',10,219.2,-16.5,1,.35,1,0,'roof');
  }
  // Site circulation: internal ring, generous front plaza and genuine garage opening.
  for(const z of [-44,39])box('asphalt',0,.055,z,104,.11,7);
  for(const x of [-51,51])box('asphalt',x,.055,-2.5,7,.11,90);
  box('asphalt',0,.055,50,10,.11,12);box('paving',0,.13,30.5,40,.18,9);
  for(const z of [-44,39])for(let x=-43;x<46;x+=8)box('paint',x,.12,z,2.6,.02,.1);
  for(const x of [-51,51])for(let z=-35;z<34;z+=9)box('paint',x,.12,z,.1,.02,3);
  for(let i=0;i<8;i++)box('paint',-4.2+i*1.2,.13,39,.55,.02,6.5);
  box('asphalt',-41,-4.25,-36,12,.24,6);box('black',-41,-2.1,-39,12,4.5,.1);
  const rampG=ownG(new THREE.BufferGeometry());rampG.setAttribute('position',new THREE.Float32BufferAttribute([-46,.12,-12,-36,.12,-12,-36,-4.1,-36,-46,-4.1,-36],3));rampG.setIndex([0,1,2,0,2,3]);rampG.computeVertexNormals();const ramp=new THREE.Mesh(rampG,materials.asphalt);ramp.name='garage-ramp';ramp.receiveShadow=true;groups.get('site').add(ramp);
  for(const x of [-46.6,-35.4])box('stone',x,-1.85,-25.5,.8,4.7,27);
  for(const x of [-46.5,-35.5]){cyl('steel',x,1.8,-12,.12,3.5,.12);box('yellow',x,1.7,-12,.18,.2,.2);}
  box('yellow',-41,3.5,-12,11,.2,.2);sign('P  地下车库  ↓',[-41,4.25,-11.85],9,.9,'site');
  for(let z=-35;z<=-13;z+=4)box('paint',-41,.15+(z+12)*4.22/24,z,.13,.02,1.5,[-Math.atan(4.22/24),0,0]);
  for(let i=0;i<15;i++)box('steel',-41,.15,-11.7+i*.04,9,.02,.02,0,'site',2);
  const gate=new THREE.Group();gate.name='garage-barrier';gate.position.set(-45,1.15,-12);groups.get('site').add(gate);mesh('box','paint',[3.8,0,0],[7.6,.12,.16],gate);box('bronze',-45,.65,-12,.5,1.3,.5);
  if(!coarse){
    // Square reflecting basin, copings and four vertical jets.
    box('stone',25,.43,49,27,.7,8,0,'landscape');box('black',25,.8,49,25,.12,6,0,'landscape');
    for(let x=13;x<=37;x+=6){cyl('steel',x,.86,49,.18,.12,.18,'landscape',1);}
    // Paving joints and fine service fixtures are batched for a modest draw count.
    for(let x=-54;x<=54;x+=3){if(Math.abs(x)>6)box('stone',x,.012,49,.024,.012,12,0,'site',2);}
    for(let z=-54;z<=54;z+=3)box('stone',54,.012,z,4,.012,.024,0,'site',2);
    for(const [x,z] of [[-24,49],[-12,49],[45,49],[-54,20],[54,-25]]){box('black',x,.03,z,1.4,.04,.6,0,'site');for(let i=0;i<9;i++)box('steel',x-.6+i*.15,.065,z,.035,.015,.5,0,'site',2);}
    for(const [x,z] of [[-43,32],[-43,18],[43,-22],[43,6],[-25,-36],[25,-36],[-17,32],[17,32]]){box('stone',x,.45,z,7,.8,4,0,'landscape');box('soil',x,.88,z,6.6,.06,3.6,0,'landscape');tree(x,z,.9,.9,'landscape',x>0);}
    for(let x=-44;x<=44;x+=11){tree(x,-53,.8,0,'landscape',x>0);if(x<-8)tree(x,52,.8);}
    for(let z=-30;z<=25;z+=13)for(const x of [-53.4,53.4])tree(x,z,.7,0,'landscape',x>0);
    function bench(x,z,r=0){box('wood',x,.7,z,3,.12,.7,r,'landscape');box('wood',x,1.02,z-.32,3,.6,.1,r,'landscape');for(const a of [-1.1,1.1])box('bronze',x+a,.39,z,.12,.62,.6,r,'landscape',1);}
    for(const x of [-29,-17,15,27,39])bench(x,44);
    for(const [x,z] of [[-40,42],[41,33],[-43,-3],[43,-32]]){box('black',x,.65,z,.65,1.3,.65,0,'site');box('bronze',x,1.27,z,.7,.08,.7,0,'site',1);}
    for(const [x,z] of [[-54,-39],[54,-39],[-54,36],[54,36],[-13,48],[43,45],[-44,5],[44,5]]){cyl('bronze',x,3.3,z,.12,6.6,.12);box('bronze',x,6.6,z,1.6,.15,.4);box('lamp',x,6.5,z,1.3,.06,.3);}
    for(let i=0;i<6;i++)part('torus','steel',[-26+i*1.4,.55,30],[.85,1.1,.85],0,'site',1);
    for(const [x,z] of [[-45,45],[45,-39]]){cyl('bronze',x,.55,z,.25,1.1,.25);box('beacon',x,1.05,z,.4,.22,.4);}
    sign('SKYLINE ONE  →',[40,2.6,35],8,1.1,'site');box('bronze',40,1.3,35,.12,2.6,.12);sign('云际中心',[8,1.5,53],9,1.4,'site');box('stone',8,1.4,52.9,10,2.8,.5);
    for(const x of [-15,-8,0,8,15])cyl('bronze',x,.55,34,.17,1.1,.17,'site');
    for(let i=0;i<3;i++){const f=new THREE.Group();f.position.set(-11-i*2.4,0,47);groups.get('landscape').add(f);mesh('cylinder','bronze',[0,4,0],[.1,8,.1],f);const flag=mesh('box',i%2?'sage':'bronze-light',[.8,7.1,0],[1.5,1.3,.025],f);flags.push(flag);}
  }
  // Batch repeated architecture; high/medium/low are actual detail selections.
  for(const b of buckets.values()){const im=new THREE.InstancedMesh(geo[b.type],materials[b.m],b.items.length);im.name=`${b.owner}:${b.m}:L${b.tier}`;im.userData={tier:b.tier,component:b.owner};im.castShadow=!['clear-glass','paint','water','asphalt','paving'].includes(b.m)&&!b.m.startsWith('glass');im.receiveShadow=true;
    b.items.forEach((it,i)=>{position.fromArray(it.p);scale.fromArray(it.s);quaternion.setFromEuler(new THREE.Euler(...it.r));matrix.compose(position,quaternion,scale);im.setMatrixAt(i,matrix);});im.computeBoundingSphere();groups.get(b.owner).add(im);if(b.tier)details.push({mesh:im,tier:b.tier});}
  // GPU foliage and water use the same accumulated simulation time as every actor.
  for(const key of ['leaf','leaf-light','sage'])materials[key].onBeforeCompile=shader=>{shader.uniforms.windClock={value:windTime};windShaders.push(shader);shader.vertexShader='uniform float windClock;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n#ifdef USE_INSTANCING\ntransformed.x+=sin(windClock*1.6+instanceMatrix[3].x*.3+instanceMatrix[3].z*.2)*.095*(position.y+.6);\n#endif');};
  const waterUniform={value:0};materials.water.onBeforeCompile=shader=>{shader.uniforms.waterClock=waterUniform;shader.fragmentShader='uniform float waterClock;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>','#include <normal_fragment_maps>\nnormal=normalize(normal+vec3(sin(vViewPosition.x*2.+waterClock*1.7)*.07,cos(vViewPosition.z*1.7+waterClock)*.04,0.));');};
  const water=mesh('box','water',[25,.895,49],[24.5,.04,5.5],groups.get('landscape'));water.name='reflecting-pool';
  const jets=[];for(let x=13;x<=37;x+=6){const j=mesh('cylinder','clear-glass',[x,1.8,49],[.09,2,.09],groups.get('landscape'));j.name='fountain-jet';jets.push(j);}
  const life=groups.get('life');const wheelG=ownG(new THREE.CylinderGeometry(.3,.3,.18,12));wheelG.rotateZ(Math.PI/2);
  function car(i,parked=false){const g=new THREE.Group();g.name=parked?'parked-EV':'moving-EV';life.add(g);mesh('box',['car-pearl','car-copper','car-dark'][i%3],[0,.67,0],[1.85,.65,4.3],g);mesh('box','glass-2',[0,1.18,-.2],[1.65,.65,2.3],g);mesh('box','bronze',[0,.83,2.13],[1.75,.12,.06],g);for(const x of [-.6,.6]){mesh('box','lamp',[x,.77,2.17],[.4,.13,.05],g);mesh('box','beacon',[x,.77,-2.17],[.35,.12,.05],g);}const wheels=[];for(const x of [-.92,.92])for(const z of [-1.35,1.35]){const w=new THREE.Mesh(wheelG,materials.rubber);w.position.set(x,.3,z);g.add(w);wheels.push(w);}return {group:g,wheels,i,parked,clock:0};}
  for(let i=0;i<4;i++)cars.push(car(i));for(let i=0;i<3;i++){const c=car(i,true);c.group.position.set(40,.12,-26+i*7);c.group.rotation.y=Math.PI;}
  for(let i=0;i<32;i++){const g=new THREE.Group();g.name='plaza-person-'+i;life.add(g);mesh('sphere','skin',[0,1.64,0],[.32,.38,.32],g);mesh('box',i%3?'suit':'coat',[0,1.09,0],[.42,.65,.27],g);const legs=[],arms=[];for(const side of [-1,1]){const p=new THREE.Group();p.position.set(side*.12,.79,0);g.add(p);mesh('box','black',[0,-.36,0],[.15,.7,.18],p);legs.push(p);const a=new THREE.Group();a.position.set(side*.28,1.36,0);g.add(a);mesh('box',i%3?'suit':'coat',[0,-.27,0],[.13,.55,.15],a);arms.push(a);}if(i%6===0)mesh('box','coat',[.43,.65,0],[.25,.38,.18],g);people.push({group:g,legs,arms,i});}
  const birdG=ownG(new THREE.BufferGeometry());birdG.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,-.8,.14,.2,-.2,0,.4,0,0,0,.2,0,.4,.8,.14,.2],3));birdG.computeVertexNormals();const bm=ownM(new THREE.MeshStandardMaterial({color:0x44555a,side:THREE.DoubleSide}));for(let i=0;i<6;i++){const b=new THREE.Mesh(birdG,bm);b.name='bird';life.add(b);birds.push(b);}
  // Compact helicopter: compound fuselage, rotor pivots, skids, tail and navigation lamps.
  const heli=new THREE.Group();heli.name='skyline-helicopter';groups.get('roof').add(heli);
  mesh('sphere','car-pearl',[0,1.8,0],[2.3,2.1,4.7],heli);mesh('sphere','glass-2',[0,1.9,1.2],[2.15,1.8,2.6],heli);mesh('box','car-dark',[0,2.1,-3.7],[.55,.65,5.3],heli);mesh('box','car-pearl',[0,3,-6],[.15,2.2,1.3],heli);mesh('box','car-pearl',[0,2,-5],[3,.12,.8],heli);
  for(const x of [-1,1]){mesh('cylinder','steel',[x,.22,0],[.09,4.4,.09],heli,[Math.PI/2,0,0]);for(const z of [-1,1])mesh('box','steel',[x,.7,z],[.08,1,.08],heli);}
  mesh('cylinder','steel',[0,3.3,-.3],[.14,1.2,.14],heli);const rotor=new THREE.Group();rotor.position.set(0,3.85,-.3);heli.add(rotor);for(let i=0;i<4;i++){const a=i*Math.PI/2;mesh('box','black',[Math.cos(a)*2.3,0,Math.sin(a)*2.3],[4.6,.045,.22],rotor,[0,-a,0]);}
  const tailRotor=new THREE.Group();tailRotor.position.set(.38,2.8,-6);heli.add(tailRotor);mesh('box','black',[0,0,0],[.06,2.4,.13],tailRotor);mesh('box','black',[0,0,0],[.06,.13,2.4],tailRotor);mesh('sphere','beacon',[-1.17,2,0],[.13,.13,.13],heli);mesh('sphere','lamp',[1.17,2,0],[.13,.13,.13],heli);
  const routes=[[[43,39],[-43,39],[-51,31],[-51,-36],[-43,-44],[43,-44],[51,-36],[51,31],[43,39]],[[52,39],[22,39],[9,39],[-12,39],[-43,39],[-51,31],[-51,-36],[-43,-44],[43,-44],[51,-36],[51,31],[52,39]]];
  function polyline(points,u){let total=0;const lengths=[];for(let i=1;i<points.length;i++){const n=Math.hypot(points[i][0]-points[i-1][0],points[i][1]-points[i-1][1]);lengths.push(n);total+=n;}let d=u*total;for(let i=0;i<lengths.length;i++){if(d<=lengths[i]||i===lengths.length-1){const a=points[i],b=points[i+1],v=Math.min(1,d/lengths[i]);return {x:a[0]+(b[0]-a[0])*v,z:a[1]+(b[1]-a[1])*v,heading:Math.atan2(b[0]-a[0],b[1]-a[1])};}d-=lengths[i];}}
  function setQuality(value){if(!['low','medium','high'].includes(value))throw new Error('Unknown quality');level=value;details.forEach(d=>d.mesh.visible=d.tier<0?value==='low'||coarse:!coarse&&(value==='high'||value==='medium'&&d.tier<2));syncVisibility();}
  function syncVisibility(){people.forEach(p=>p.group.visible=traffic&&!coarse&&(level==='high'||p.i<(level==='medium'?20:8)));cars.forEach(c=>c.group.visible=traffic&&!coarse);birds.forEach((b,i)=>b.visible=wind&&!coarse&&(level==='high'||i<2));heli.visible=!coarse;}
  function setActivity(options={}){if('traffic'in options)traffic=!!options.traffic;if('wind'in options)wind=!!options.wind;if('flight'in options)flight=!!options.flight;syncVisibility();}
  function setDynamicsEnabled(value){dynamics=!!value;}
  function setTimeOfDay(value){night=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.4:0;materials.lamp.emissiveIntensity=.06+night*3.4;for(let i=0;i<4;i++)materials['office-lit-'+i].emissiveIntensity=.025+night*(.8+i*.25);materials.beacon.emissiveIntensity=.1+night*2;}
  function update(delta=0){if(disposed||!Number.isFinite(delta))return;const dt=dynamics?Math.max(0,Math.min(delta,.25)):0;time+=dt;if(wind)windTime+=dt;windShaders.forEach(s=>s.uniforms.windClock.value=windTime);waterUniform.value=time;
    if(traffic){
      cars.forEach(c=>{let p,y=.12,moving=true;const ct=c.clock+dt;
        if(c.i===3){const f=ct%64,travel=f<20?f/20:f<32?1:f<52?1-(f-32)/20:0;p=polyline([[-51,0],[-51,-7],[-41,-7],[-41,-35]],travel);y=p.z<-12&&Math.abs(p.x+41)<.5?.12+(p.z+12)*4.22/24:.12;c.group.visible=!(f>=20&&f<32);if(f>=32&&f<52)p.heading+=Math.PI;moving=f<20||f>=32&&f<52;
        }else if(c.i===0){const f=ct%90;let u=f<20?f/20*.16:f<32?.16:.16+(f-32)/58*.84;p=polyline(routes[1],u);moving=!(f>=20&&f<32);}else p=polyline(routes[0],(ct/105+c.i*.35)%1);
        const current=c.group.position;const blocked=dt>0&&c.i<3&&cars.some(other=>other!==c&&other.i<3&&Math.hypot(other.group.position.x-p.x,other.group.position.z-p.z)<7&&Math.hypot(other.group.position.x-p.x,other.group.position.z-p.z)<Math.hypot(other.group.position.x-current.x,other.group.position.z-current.z));if(!blocked){c.clock=ct;c.group.position.set(p.x,y,p.z);c.group.rotation.y=p.heading;if(moving)c.wheels.forEach(w=>w.rotation.x+=dt*7);}
      });
      people.forEach(p=>{const phase=(time*.006+p.i/32)%1,wait=phase>.43&&phase<.52,u=phase<.43?phase/.43*.5:phase<.52?.5:.5+(phase-.52)/.48*.5;let route;
        if(p.i%3===0)route=[[-7,53],[-7,43],[-7,31],[0,31],[0,23],[0,31],[-7,31],[-7,43],[-7,53]];
        else if(p.i%3===1)route=[[-32,33],[32,33],[42,43],[42,54],[-32,54],[-32,33]];
        else route=[[-44,25],[-34,25],[-34,-37],[34,-37],[42,25],[34,33],[-44,33],[-44,25]];
        const q=polyline(route,u);p.group.position.set(q.x,.18,q.z);p.group.rotation.y=q.heading;p.legs.forEach((l,i)=>l.rotation.x=wait?0:Math.sin(time*5+p.i+i*Math.PI)*.4);p.arms.forEach((a,i)=>a.rotation.x=wait?0:-Math.sin(time*5+p.i+i*Math.PI)*.3);
      });
    }
    const near=traffic&&people.some(p=>Math.hypot(p.group.position.x,p.group.position.z-23)<4);doors.forEach(d=>{d.mesh.position.x+=(d.base+d.side*(near?1.4:0)-d.mesh.position.x)*Math.min(1,dt*5);});
    const garageNear=traffic&&cars.some(c=>Math.hypot(c.group.position.x+41,c.group.position.z+12)<10);gate.rotation.z+=((garageNear?Math.PI*.47:0)-gate.rotation.z)*Math.min(1,dt*3);
    fans.forEach((f,i)=>f.rotation.y+=dt*(4+i*.2));flags.forEach((f,i)=>{f.rotation.y=Math.sin(windTime*1.8+i)*.15;f.rotation.z=Math.sin(windTime*2+i)*.025;});birds.forEach((b,i)=>{const a=windTime*.045+i*1.1;b.position.set(Math.cos(a)*37,80+i*17+Math.sin(a*2)*3,-6+Math.sin(a)*37);b.rotation.set(Math.sin(windTime*5+i)*.25,-a,Math.sin(a)*.15);});
    jets.forEach((j,i)=>{const h=1.8+Math.sin(time*1.5+i)*.35;j.scale.y=h;j.position.y=.92+h/2;});
    const f=flight?time%100:0;let h=0,x=0,z=-6;if(f>12&&f<27)h=(f-12)/15*24;else if(f>=27&&f<72){const a=(f-27)/45*Math.PI*2;h=24+Math.sin(a)*3;x=Math.sin(a)*28;z=-6+(1-Math.cos(a))*15;}else if(f>=72&&f<88)h=(88-f)/16*24;heli.position.set(x,219.0+h,z);heli.rotation.y=f>=27&&f<72?-(f-27)/45*Math.PI*2:0;rotor.rotation.y+=dt*(f>6&&f<94?45:2);tailRotor.rotation.x+=dt*(f>6&&f<94?70:3);
    materials.beacon.emissiveIntensity=(.1+night*2)*(Math.sin(time*5)>.3?1:.25);for(let i=0;i<4;i++)materials['office-lit-'+i].emissiveIntensity=.025+night*(.8+i*.25)*(.93+.07*Math.sin(time*.045+i*2));
  }
  function exportScene(){root.updateMatrixWorld(true);const gs={},ms={},objects=[];root.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry,m=o.material;if(!gs[g.uuid])gs[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null};if(!ms[m.uuid])ms[m.uuid]={name:m.name||o.name,color:m.color.toArray(),roughness:m.roughness??.8,metalness:m.metalness??0,emissive:m.emissive?.toArray()||[0,0,0],emissiveIntensity:m.emissiveIntensity||0,opacity:m.opacity,transparent:m.transparent,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};let p=o;while(p!==root&&!p.userData?.id)p=p.parent;const owner=p.userData?.id||'site';if(o.isInstancedMesh){for(let i=0;i<o.count;i++){o.getMatrixAt(i,matrix);objects.push({g:g.uuid,m:m.uuid,matrix:new THREE.Matrix4().multiplyMatrices(o.matrixWorld,matrix).toArray(),owner});}}else objects.push({g:g.uuid,m:m.uuid,matrix:o.matrixWorld.toArray(),owner});});return {format:'skyline-one-v1',snapshotSpace:'world',manifest,geometries:gs,materials:ms,objects};}
  function dispose(){if(disposed)return;disposed=true;root.removeFromParent();geometries.forEach(g=>g.dispose());materialSet.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());root.clear();groups.clear();buckets.clear();details.length=windShaders.length=people.length=cars.length=fans.length=doors.length=flags.length=birds.length=0;geometries.clear();materialSet.clear();textures.clear();}
  setQuality(quality);update(0);
  return {root,groups,manifest,update,setQuality,setActivity,setDynamicsEnabled,setTimeOfDay,exportScene,dispose,get disposed(){return disposed;},get quality(){return level;},get simulationTime(){return time;},get actorCount(){return people.length+cars.length+birds.length+1;}};
}
export default createSkylineTower;
