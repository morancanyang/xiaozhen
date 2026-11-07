/** JIHENG ONE — standalone, host-owned Three.js factory. Native footprint 112m square, +Z front. */
export function createLandmarkOffice({THREE,blockSize=112,quality='high',coarse=false}={}){
 if(!THREE?.Group)throw new Error('Pass the host THREE namespace');
 if(!Number.isFinite(blockSize)||blockSize<=0)throw new Error('blockSize must be positive');
 const root=new THREE.Group();root.name='JIHENG-LANDMARK';root.scale.setScalar(blockSize/112);
 const building=new THREE.Group();building.name='JH-01';building.userData={id:'JH-01',name:'霁衡中心',selectable:true};root.add(building);
 const groups=new Map(),buildings=new Map([['JH-01',building]]),geometries=new Set(),textures=new Set(),materials={};
 const parts=[['lower','下段办公塔楼',true],['middle','中段办公塔楼',true],['upper','上段办公塔楼',true],['podium','石材商业裙楼',true],['roof','屋顶设备',true],['terraces','退台花园',true],['site','城市广场',false],['landscape','绿化与设施',false],['life','广场日常',false]];
 parts.forEach(([id,name,architecture])=>{const g=new THREE.Group();g.name=id;g.userData={partId:id,name,buildingId:architecture?'JH-01':null};(architecture?building:root).add(g);groups.set(id,g)});
 let seed=92717;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 const G=g=>(geometries.add(g),g),geo={box:G(new THREE.BoxGeometry(1,1,1)),cyl:G(new THREE.CylinderGeometry(.5,.5,1,12)),sphere:G(new THREE.SphereGeometry(.5,12,8)),leaf:G(new THREE.IcosahedronGeometry(.5,1)),cone:G(new THREE.ConeGeometry(.5,1,10))};
 function texture(kind,color){const c=document.createElement('canvas');c.width=c.height=256;const ctx=c.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,256,256);for(let i=0;i<11000;i++){const k=Math.floor(80+rand()*140);ctx.fillStyle=`rgba(${k},${k},${k},${kind==='stone'?.10:.20})`;ctx.fillRect(rand()*256,rand()*256,rand()*2+.3,rand()*2+.3)}if(kind==='stone'){ctx.strokeStyle='#ffffff12';ctx.lineWidth=.5;for(let i=0;i<11;i++){ctx.beginPath();ctx.moveTo(0,rand()*256);ctx.bezierCurveTo(80,rand()*256,180,rand()*256,256,rand()*256);ctx.stroke()}}const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=4;textures.add(t);return t}
 function mat(name,color,roughness=.6,metalness=0,extra={}){const m=new THREE.MeshStandardMaterial({color,roughness,metalness,...extra});m.name=name;materials[name]=m;return m}
 mat('limestone',0xffffff,.78,0,{map:texture('stone','#bdbbb3'),bumpScale:.018});materials.limestone.bumpMap=materials.limestone.map;
 mat('paving',0xffffff,.83,0,{map:texture('stone','#d0d1cf'),bumpScale:.012});materials.paving.bumpMap=materials.paving.map;
 mat('asphalt',0xffffff,.95,0,{map:texture('asphalt','#343f48'),bumpScale:.015});materials.asphalt.bumpMap=materials.asphalt.map;
 mat('silver',0xc5d0d4,.26,.78);mat('satin',0x8b9da5,.4,.67);mat('graphite',0x26353c,.52,.4);mat('shadow',0x152a34,.85,.08);
 mat('roofing',0x687982,.84,.12);mat('floor',0xb8b6aa,.85);mat('wood',0x8c6745,.79);mat('soil',0x474438,.95);
 mat('grass',0x335a47,.94);mat('leaf',0x35664d,.85);mat('leaf-light',0x69866b,.9);mat('silver-leaf',0x8d9e83,.88);mat('bark',0x685746,.95);
 mat('white',0xd8ddd8,.7);mat('gold',0xaa8860,.31,.64);mat('rubber',0x20272c,.97);mat('red',0x9c5146,.6);
 mat('skin',0xc99b7a,.9);mat('suit',0x344b58,.86);mat('cloth',0xb6a891,.92);mat('car-white',0xd5dedc,.25,.48);mat('car-blue',0x365b6d,.24,.52);
 mat('lamp',0xe5e2cf,.28,.15,{emissive:0xffd9a3,emissiveIntensity:.06});mat('obstruction',0xb72920,.3,0,{emissive:0xff3012,emissiveIntensity:1});
 const glassColors=[0x487e95,0x52879b,0x42758c,0x6092a4,0x4d8399,0x658f9f];
 glassColors.forEach((color,i)=>{const m=new THREE.MeshPhysicalMaterial({color,roughness:.095+i*.009,metalness:.52,clearcoat:1,clearcoatRoughness:.08,ior:1.5});m.name='glass-'+i;materials[m.name]=m});
 const vision=new THREE.MeshPhysicalMaterial({color:0xb0c8cf,roughness:.12,metalness:.08,transmission:.55,thickness:.06,ior:1.5,clearcoat:1});vision.name='vision-glass';materials[vision.name]=vision;
 mat('office-lit',0x88a4ac,.23,.2,{emissive:0xffcd8b,emissiveIntensity:.008});
 const batches=new Map(),p=new THREE.Vector3(),s=new THREE.Vector3(),q=new THREE.Quaternion(),e=new THREE.Euler(),mx=new THREE.Matrix4();
 function part(type,m,pos,scale,owner='site',tier=0,rot=[0,0,0]){const key=[owner,type,m,tier].join('|');if(!batches.has(key))batches.set(key,{type,m,owner,tier,items:[]});batches.get(key).items.push({pos,scale,rot})}
 function box(m,x,y,z,w,h,d,owner='site',tier=0){part('box',m,[x,y,z],[w,h,d],owner,tier)}
 function mesh(type,m,pos,scale,parent,name=''){const o=new THREE.Mesh(geo[type],materials[m]);o.position.fromArray(pos);o.scale.fromArray(scale);o.name=name;o.castShadow=true;o.receiveShadow=true;parent.add(o);return o}
 function beam(m,a,b,r,owner='site',tier=0){const A=new THREE.Vector3(...a),B=new THREE.Vector3(...b),dir=B.clone().sub(A);q.setFromUnitVectors(new THREE.Vector3(0,1,0),dir.clone().normalize());e.setFromQuaternion(q);part('cyl',m,A.add(B).multiplyScalar(.5).toArray(),[r,dir.length(),r],owner,tier,[e.x,e.y,e.z])}
 function sign(text,pos,w,h,owner='podium',rot=0){const c=document.createElement('canvas');c.width=1024;c.height=128;const x=c.getContext('2d');x.fillStyle='#243b45';x.fillRect(0,0,1024,128);x.textAlign='center';x.textBaseline='middle';x.fillStyle='#d8d6bb';x.font='44px Microsoft YaHei';x.fillText(text,512,66);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;textures.add(t);const m=mat('sign-'+Object.keys(materials).length,0xffffff,.5,.1,{map:t,emissive:0xffffff,emissiveMap:t,emissiveIntensity:.02});const g=G(new THREE.PlaneGeometry(w,h));const o=new THREE.Mesh(g,m);o.position.fromArray(pos);o.rotation.y=rot;o.name=text;groups.get(owner).add(o)}
 const manifest={id:'jiheng-landmark-office',name:'霁衡中心',version:'1.0.0',units:'m',upAxis:'Y',nativeBlockSize:112,blockSize,height:184,footprint:{width:112,depth:112},buildings:[{id:'JH-01',name:'霁衡中心',x:0,z:0,w:72,d:64,floors:46,officeFloors:42,height:184}],parts:parts.map(([id,name,architecture])=>({id,name,buildingId:architecture?'JH-01':null})),entrances:[{id:'public',position:[0,.16,56],width:12},{id:'vehicle',position:[48,.055,56],width:6},{id:'service',position:[-48,.055,-56],width:6}],lightFixtures:[],sections:[{id:'lower',bottom:16.8,top:68.6,w:48,d:42,floors:14},{id:'middle',bottom:68.6,top:120.4,w:40,d:36,floors:14},{id:'upper',bottom:120.4,top:172.2,w:32,d:30,floors:14}]};
 // A real basement ramp opening: the plot slab is split around its void.
 box('paving',-50.25,-.27,0,11.5,.54,112);box('paving',8.25,-.27,0,95.5,.54,112);
 box('paving',-42,-.27,-35.5,5,.54,41);box('paving',-42,-.27,37,5,.54,38);
 for(const x of [-48,48])box('asphalt',x,.027,0,6,.055,112);for(const z of [-48,48])box('asphalt',0,.027,z,90,.055,6);
 for(const x of [-51.3,51.3])box('limestone',x,.12,0,.25,.24,112);for(const z of [-51.3,51.3])box('limestone',0,.12,z,102.6,.24,.25);
 for(const x of [-44.8,44.8])for(const range of [[-56,-16],[20,56]])box('limestone',x,.12,(range[0]+range[1])/2,.25,.24,range[1]-range[0]);
 for(const z of [-44.8,44.8])box('limestone',0,.12,z,89.6,.24,.25);
 for(let z=-53;z<55;z+=6)for(const x of [-48,48])box('white',x,.065,z,.12,.018,2.7,'site',1);
 for(let x=-41;x<=41;x+=6)for(const z of [-48,48])box('white',x,.065,z,2.7,.018,.12,'site',1);
 // Public plaza paving, deliberately on both sides of the loop-road crossing.
 box('paving',0,.08,38,72,.16,12);box('paving',0,.08,53.7,14,.16,4.6);
 for(let x=-34;x<=34;x+=2.4)box('satin',x,.165,38,.025,.01,11.8,'site',2);
 for(let z=33;z<44;z+=2.4)box('satin',0,.165,z,71,.01,.025,'site',2);
 for(let x=-6;x<=6;x+=1.2)box('white',x,.07,48,.52,.025,5.7,'site');
 // Ramp from surface to a recessed basement portal, not a painted rectangle.
 const rampGeometry=G(new THREE.BufferGeometry());rampGeometry.setAttribute('position',new THREE.Float32BufferAttribute([-44.5,-2.8,-15,-44.5,.055,18,-39.5,.055,18,-39.5,-2.8,-15],3));rampGeometry.setIndex([0,1,2,0,2,3]);rampGeometry.computeVertexNormals();const ramp=new THREE.Mesh(rampGeometry,materials.asphalt);ramp.name='Basement ramp';ramp.receiveShadow=true;groups.get('site').add(ramp);
 for(const x of [-44.65,-39.35]){box('limestone',x,-1,-.5,.3,3,33);beam('satin',[x,.8,-15],[x,.8,18],.08,'site',1)}
 box('shadow',-42,-1.6,-15.1,4.9,2.4,.1);box('limestone',-42,1.3,-13,6,.4,5);sign('P  地下车库  ↓',[-42,1.12,19.2],5,.65,'site');
 for(let z=-10;z<17;z+=3)box('white',-42,-2.8+(z+15)/33*2.855+.012,z,.12,.02,1.5,'site',1);
 // Four-floor podium: continuous stone piers and recessed glazed shop bays.
 if(coarse)box('limestone',0,8.4,0,72,16.8,64,'podium');else{
  for(let f=0;f<4;f++){
   const y=.2+f*4.15;box('shadow',0,y+2,0,70.8,4,62.8,'podium');
   for(const z of [-32,32]){
    box('limestone',0,y+.22,z,72,.44,.9,'podium');box('limestone',0,y+3.95,z,72,.4,.9,'podium');
    for(let n=0;n<=12;n++){const x=-36+n*6;box('limestone',x,y+2.1,z,.65,3.5,1,'podium');}
    for(let n=0;n<12;n++){const x=-33+n*6;if(f===0&&z===32&&Math.abs(x)<7)continue;box('glass-'+((n+f)%6),x,y+2.1,z-.12*Math.sign(z),5.3,3.35,.09,'podium');box('silver',x,y+2.1,z+.08*Math.sign(z),.075,3.4,.12,'podium',1);box('gold',x,y+.65,z+.15*Math.sign(z),5.35,.06,.12,'podium',1)}
   }
   for(const x of [-36,36]){box('limestone',x,y+.22,0,.9,.44,63);box('limestone',x,y+3.95,0,.9,.4,63);for(let n=0;n<=10;n++)box('limestone',x,y+2.1,-32+n*6.4,1,3.5,.65,'podium');for(let n=0;n<10;n++)box('glass-'+((n+f+1)%6),x-.12*Math.sign(x),y+2.1,-28.8+n*6.4,.09,3.35,5.75,'podium')}
  }
  box('limestone',0,16.6,0,72.8,.4,64.8,'podium');box('roofing',0,16.84,0,71.5,.08,63.5,'podium');
  for(const z of [-32.51,32.51])for(let x=-35;x<36;x+=1.5)for(let f=0;f<4;f++)box('satin',x,.42+f*4.15,z,.018,.38,.025,'podium',2);
 }
 // Office floors share rational 3.7m spacing; each curtain-wall grid is independent geometry.
 manifest.sections.forEach((section,si)=>{
  const {id,w,d,bottom,floors}=section;
  if(coarse){box('glass-2',0,bottom+25.9,0,w,51.8,d,id);return}
  for(let f=0;f<floors;f++){
   const y=bottom+f*3.7;
   box('floor',0,y+.14,0,w-.34,.26,d-.34,id);box('shadow',0,y+1.95,0,w-5,3.35,d-5,id);
   box('satin',0,y+.4,0,w+.12,.16,d+.12,id);box('satin',0,y+3.62,0,w+.13,.11,d+.13,id);
   for(let side=0;side<4;side++){
    const isZ=side<2,sgn=side%2===0?1:-1,span=isZ?w:d,n=Math.round(span/2.65),pitch=span/n,normal=(isZ?d:w)/2*sgn;
    for(let j=0;j<n;j++){
     const u=-span/2+(j+.5)*pitch,lit=(f*17+j*7+side*3+si)%19<3,seeInside=side===0&&j%5===2&&f%4===1;
     const m=seeInside?'vision-glass':lit?'office-lit':'glass-'+((f+j+side+si)%6),a=isZ?u:normal,b=isZ?normal:u;
     box(m,a,y+2.03,b,isZ?pitch-.11:.075,2.94,isZ?.075:pitch-.11,id);
     box('graphite',a+(isZ?0:sgn*.12),y+.67,b+(isZ?sgn*.12:0),isZ?pitch-.08:.1,.55,isZ?.1:pitch-.08,id);
     const mullion=isZ?[u-pitch/2,y+2.02,normal+sgn*.08]:[normal+sgn*.08,y+2.02,u-pitch/2];
     box('silver',...mullion,isZ?.09:.2,3.35,isZ?.2:.09,id);
     if((j+f)%4===0)box('satin',a+(isZ?0:sgn*.07),y+2.45,b+(isZ?sgn*.07:0),isZ?pitch-.18:.09,.045,isZ?.09:pitch-.18,id,2);
     if(seeInside){const iz=normal-.9;box('floor',u,y+1.12,iz,1.8,.08,.8,id,1);for(const dx of [-.7,.7])box('silver',u+dx,y+.62,iz,.045,1,.045,id,2);box('graphite',u,y+1.5,iz-.2,.65,.4,.045,id,1);box('white',u+1,y+1.7,normal-1.25,.05,2.6,1.8,id,1)}
    }
   }
   // Fine facade fins at the corners carry the vertical rhythm through the stepped volumes.
   for(const x of [-w/2,w/2])for(const z of [-d/2,d/2])box('silver',x,y+1.85,z,.24,3.7,.24,id);
  }
  for(const z of [-d/2-.08,d/2+.08])box('silver',0,bottom+51.76,z,w+.3,.15,.28,id);
 });
 // Entry recess and responsive sliding doors under a wide structural canopy.
 box('floor',0,.14,30,13,.28,6,'podium');box('shadow',0,2.1,29.5,11,3.8,.2,'podium');
 box('silver',0,4.6,35,15,.28,8,'podium');box('glass-3',0,4.8,35,14.7,.08,7.7,'podium');
 for(const x of [-6.7,6.7])box('satin',x,2.3,37,.2,4.6,.2,'podium');for(const x of [-4.5,-1.5,1.5,4.5])box('lamp',x,4.42,36,1.3,.035,.12,'podium',1);
 sign('霁 衡 中 心   J I H E N G   O N E',[0,5.6,32.56],20,1.15);
 ['CORNER COFFEE','ATELIER  /  DESIGN','CITY GALLERY','JIHENG LOBBY'].forEach((t,i)=>sign(t,[-27+i*18,3.35,32.57],6.6,.45));
 const doors=[];for(const side of [-1,1]){const g=new THREE.Group();g.name='Automatic door '+side;g.position.set(side*1.1,2,32.35);groups.get('podium').add(g);mesh('box','vision-glass',[0,0,0],[2.1,3.6,.065],g);for(const x of [-1.04,1.04])mesh('box','silver',[x,0,.04],[.065,3.65,.1],g);mesh('box','gold',[side*.72,0,.13],[.06,.8,.06],g);doors.push({g,side})}
 box('paving',9,.28,35,3.2,.15,6,'site');for(let i=0;i<3;i++)box('limestone',-9,.075+i*.05,36-i*.9,3,.15+i*.1,.9,'site',1);
 for(const x of [-10.5,-7.5])beam('satin',[x,.95,38],[x,1.1,32.7],.055,'site',1);
 // Terraces at all three setbacks; garden bands stay outside the next tower footprint.
 const swaying=[];
 function tree(x,y,z,size,owner='landscape',silver=false){beam('bark',[x,y,z],[x,y+size*.65,z],size*.065,owner);for(let j=0;j<3;j++)part('leaf',silver?'silver-leaf':j%2?'leaf-light':'leaf',[x+(rand()-.5)*size*.6,y+size*.75+j*size*.07,z+(rand()-.5)*size*.6],[size*.65,size*.75,size*.65],owner,1);}
 function bench(x,y,z,owner='landscape',yaw=0){for(let k=0;k<5;k++)part('box','wood',[x,y+.5,z+(k-2)*.085],[2.6,.075,.065],owner,1,[0,yaw,0]);for(const sx of [-1,1])box('graphite',x+sx*1.05,y+.25,z,.1,.5,.5,owner,1)}
 function planter(x,y,z,w,d,owner='terraces'){box('limestone',x,y+.38,z,w,.76,d,owner);box('soil',x,y+.78,z,w-.15,.035,d-.15,owner);for(let i=0;i<Math.max(2,Math.round(w));i++)part('leaf',i%2?'leaf':'silver-leaf',[x-w*.4+i/(Math.max(2,Math.round(w))-1)*w*.8,y+1.05,z],[.7,.75,d*.8],owner,1)}
 for(const [level,w,d,nextW,nextD] of [[16.8,71,63,48,42],[68.6,48,42,40,36],[120.4,40,36,32,30]]){
  box('roofing',0,level+.045,0,w,.09,d,'terraces');
  for(const side of [-1,1]){
   const z=side*(d/2-.85);for(let x=-w/2+2;x<w/2-1;x+=5)planter(x,level,z,3,.95);
   for(const x of [-w/2+.18,w/2-.18]){box('glass-3',x,level+.7,0,.055,1.2,d,'terraces');beam('silver',[x,level+1.3,-d/2],[x,level+1.3,d/2],.05,'terraces',1)}
   box('glass-3',0,level+.7,side*(d/2-.18),w,1.2,.055,'terraces');beam('silver',[-w/2,level+1.3,side*d/2],[w/2,level+1.3,side*d/2],.05,'terraces',1);
  }
  for(const side of [-1,1]){const z=side*((nextD/2+d/2)/2);for(const x of [-w*.27,w*.27])bench(x,level,z,'terraces');}
  if(level===16.8){for(const x of [-30,30])for(const z of [-24,24]){planter(x,level,z,3,3);tree(x,level+.8,z,3.6,'terraces',true)}for(let n=0;n<12;n++)box('wood',-30+n*.75,20.5,0,.16,.15,12,'terraces',1);for(const z of [-5.5,5.5])for(const x of [-30,-22])box('silver',x,18.7,z,.12,3.8,.12,'terraces',1)}
 }
 // Rooftop screened mechanical plant, accessible walkways, ductwork and a 184m lightning mast.
 box('roofing',0,172.26,0,32,.12,30,'roof');box('graphite',0,176.25,0,24,7.9,22,'roof');
 for(const z of [-11.1,11.1])for(let y=173;y<180.2;y+=.45)box('silver',0,y,z,24,.12,.16,'roof',1);
 for(const x of [-12.1,12.1])for(let y=173;y<180.2;y+=.45)box('silver',x,y,0,.16,.12,22,'roof',1);
 geo.ring=G(new THREE.TorusGeometry(.5,.008,4,36));
 const fans=[];for(const x of [-6,1,7])for(const z of [-5,4]){
  box('satin',x,181.15,z,4.2,1.9,4.2,'roof');part('cyl','graphite',[x,182.14,z],[3.1,.08,3.1],'roof');
  const fan=new THREE.Group();fan.position.set(x,182.22,z);fan.name='Cooling fan '+fans.length;groups.get('roof').add(fan);
  for(let a=0;a<4;a++) {const blade=mesh('box','silver',[0,0,.65],[.35,.06,1.3],fan);blade.rotation.y=a*Math.PI/2;blade.position.set(Math.sin(a*Math.PI/2)*.65,0,Math.cos(a*Math.PI/2)*.65)}fans.push(fan);
  for(let r=.7;r<=3.2;r+=.5)part('ring','satin',[x,182.31,z],[r,r,r],'roof',1,[Math.PI/2,0,0]);
  part('cyl','silver',[x,182.35,z],[.4,.14,.4],'roof',1);
  for(const side of [-1,1])for(let h=180.5;h<181.9;h+=.18)box('graphite',x,h,z+side*2.11,3.75,.045,.035,'roof',2);
  for(const dx of [-1.9,1.9])for(const dz of [-1.9,1.9])part('cyl','silver',[x+dx,182.13,z+dz],[.06,.04,.06],'roof',2);
 }
 box('limestone',-8,174.6,11,5,4.7,5,'roof');box('graphite',-8,175,13.55,1.2,2.3,.08,'roof');
 for(let z=-12;z<=12;z+=2)box('paving',14,172.4,z,1.5,.18,1.6,'roof',1);
 for(const x of [-10,-7]){box('satin',x,180.8,-3,1.5,1.3,13,'roof',1);for(let z=-8;z<4;z+=1.5)box('silver',x,181.48,z,1.6,.06,.08,'roof',2)}
 beam('silver',[12,172.4,-12],[12,183.8,-12],.12,'roof');part('sphere','obstruction',[12,183.94,-12],[.16,.12,.16],'roof');
 for(const x of [-15.7,15.7])for(const z of [-14.7,14.7])part('sphere','obstruction',[x,173.5,z],[.16,.16,.16],'roof');
 // Streetscape, flower beds, visitor parking, lights, tactile paths and service objects.
 for(const x of [-52.2,52.2])for(let z=-38;z<=39;z+=11){box('soil',x,.04,z,2.8,.08,2.8,'landscape');tree(x,.08,z,5.5,'landscape')}
 for(const z of [-52.2,52.2])for(const x of [-38,-23,23,38]){box('soil',x,.04,z,2.8,.08,2.8,'landscape');tree(x,.08,z,5.8,'landscape',x<0)}
 for(const x of [-39.5,39.5])for(const z of [35,40])planter(x,.1,z,4,2,'landscape');
 for(const z of [36.5,42])for(const x of [-23,23])bench(x,.16,z);
 for(const x of [-18,18])for(let z=34;z<44;z+=.42)box('gold',x,.18,z,1,.025,.06,'site',2);
 for(const x of [-12,-9,9,12]){part('cyl','satin',[x,.6,40],[.15,.9,.15],'landscape');part('sphere','silver',[x,1.05,40],[.16,.16,.16],'landscape',1)}
 for(const x of [-30,30])for(const z of [-40,40]){box('graphite',x,.6,z,.55,1.15,.55,'landscape',1);box('silver',x,1.2,z,.62,.1,.62,'landscape',1)}
 for(let n=0;n<6;n++){const z=-26+n*5.5;box('white',40.5,.065,z,5,.025,.1,'site');box('rubber',42.1,.16,z+2.3,.18,.22,1.1,'site',1);box('graphite',37.4,.7,z+2.3,.35,1.4,.45,'landscape',1);box('lamp',37.4,1,z+2.54,.25,.28,.02,'landscape',1)}
 for(let z=-40;z<44;z+=8)for(const x of [-44.4,44.4]){box('graphite',x,.165,z,.4,.025,.8,'site',1);for(let k=0;k<6;k++)box('silver',x,.183,z-.3+k*.12,.32,.015,.025,'site',2)}
 for(const x of [-48,48])for(const z of [-36,-12,12,36]){part('cyl','graphite',[x+(x>0?3.7:-3.7),3.1,z],[.12,6.2,.12],'landscape');box('graphite',x+(x>0?3.2:-3.2),6.2,z,1.3,.18,.35,'landscape');manifest.lightFixtures.push({position:[x+(x>0?3.2:-3.2),5.95,z],power:110,distance:19,color:0xffd8ac});box('lamp',x+(x>0?3.2:-3.2),6.08,z,.8,.06,.25,'landscape')}
 for(const x of [-28,-14,14,28])for(const z of [35,42]){box('graphite',x,.6,z,.18,1,.18,'landscape');box('lamp',x,1.06,z,.23,.13,.23,'landscape');manifest.lightFixtures.push({position:[x,1.24,z],power:12,distance:7})}
 // Guard booth and loading entrance occupy the quiet north service court.
 box('limestone',-39,1.3,-40,3.4,2.6,3.6,'site');box('glass-2',-39,1.7,-38.15,2.5,1.25,.06,'site');box('silver',-39,2.7,-40,3.8,.2,4,'site');
 for(const x of [-15,15]){box('graphite',x,1.9,-32.58,4,3.4,.12,'podium');for(let y=.5;y<3.6;y+=.3)box('satin',x,y,-32.67,3.9,.04,.04,'podium',1)}
 // Instanced facade / site batches: individual transforms remain editable and exportable.
 for(const b of batches.values()){const o=new THREE.InstancedMesh(geo[b.type],materials[b.m],b.items.length);o.name=b.owner+' / '+b.m+' / '+b.tier;o.userData.tier=b.tier;o.castShadow=!b.m.includes('glass')&&!['lamp','asphalt','grass','paving'].includes(b.m);o.receiveShadow=true;b.items.forEach((it,i)=>{p.fromArray(it.pos);s.fromArray(it.scale);q.setFromEuler(e.set(...it.rot));mx.compose(p,q,s);o.setMatrixAt(i,mx)});o.computeBoundingSphere();groups.get(b.owner).add(o)}
 const windShaders=[];for(const key of ['leaf','leaf-light','silver-leaf'])materials[key].onBeforeCompile=shader=>{shader.uniforms.windTime={value:0};windShaders.push(shader);shader.vertexShader='uniform float windTime;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n#ifdef USE_INSTANCING\ntransformed.x+=sin(windTime*1.1+instanceMatrix[3].x*.3+instanceMatrix[3].z*.2)*.055*(position.y+.5);\n#endif')};
 const people=[];function person(i){const g=new THREE.Group();g.name='Office pedestrian '+i;groups.get('life').add(g);mesh('sphere','skin',[0,1.65,0],[.3,.36,.3],g);mesh('box',i%3?'suit':'cloth',[0,1.13,0],[.43,.65,.26],g);const limbs=[];for(const sx of [-1,1]){const l=new THREE.Group();l.position.set(sx*.13,.8,0);g.add(l);mesh('box','graphite',[0,-.34,0],[.15,.68,.19],l);limbs.push(l);const arm=new THREE.Group();arm.position.set(sx*.28,1.38,0);g.add(arm);mesh('box',i%3?'suit':'skin',[0,-.25,0],[.12,.5,.14],arm);limbs.push(arm)}if(i%4===0)mesh('box','graphite',[.42,.72,0],[.16,.36,.44],g);return{g,limbs,i,t:i*11}}
 for(let i=0;i<22;i++)people.push(person(i));
 const cars=[];function car(i,parked=false){const g=new THREE.Group();g.name=(parked?'Parked car ':'Office car ')+i;groups.get('life').add(g);mesh('box',i%2?'car-blue':'car-white',[0,.7,0],[1.85,.7,4.25],g);mesh('box','glass-2',[0,1.15,-.1],[1.65,.65,2.05],g);mesh('box',i%2?'car-blue':'car-white',[0,1.51,-.1],[1.7,.08,2.04],g);const wheels=[];for(const sx of [-1,1])for(const z of [-1.35,1.35]){const o=mesh('cyl','rubber',[sx*.94,.35,z],[.62,.2,.62],g);o.rotation.z=Math.PI/2;wheels.push(o);const h=mesh('cyl','silver',[sx*1.05,.35,z],[.33,.03,.33],g);h.rotation.z=Math.PI/2}for(const sx of [-1,1]){mesh('box','lamp',[sx*.62,.8,2.16],[.4,.14,.03],g);mesh('box','red',[sx*.65,.82,-2.16],[.35,.12,.03],g)}return{g,wheels,i,d:i*145,wait:0,stopped:false,parked}}
 for(let i=0;i<2;i++)cars.push(car(i));for(let i=0;i<4;i++){const c=car(i,true);c.g.position.set(40.5,.065,-23.2+i*5.5);c.g.rotation.y=Math.PI/2;cars.push(c)}
 const gate=new THREE.Group();gate.name='Vehicle barrier';gate.position.set(45,1.3,27);groups.get('site').add(gate);mesh('box','white',[3,0,0],[6,.14,.16],gate);for(let i=0;i<5;i++)mesh('box','red',[.5+i*1.1,0,.09],[.4,.15,.02],gate);mesh('box','graphite',[0,-.65,0],[.45,1.3,.5],gate);
 const elevators=[];for(const x of [-3,3]){const g=new THREE.Group();g.name='Panoramic lift '+x;groups.get('podium').add(g);mesh('box','gold',[0,0,0],[1.7,.16,1.5],g);mesh('box','vision-glass',[0,1.1,0],[1.65,2.1,1.4],g);mesh('box','lamp',[0,2.18,0],[1.7,.08,1.5],g);g.position.set(x,.3,31.6);elevators.push(g)}
 // Explicit lift guides created after batching; add their small support geometry directly.
 for(const x of [-3.94,2.06])mesh('box','silver',[x,8.4,31.6],[.08,16.3,.08],groups.get('podium'));
 const birds=[];for(let i=0;i<4;i++){const g=new THREE.Group();g.name='City bird '+i;for(const side of [-1,1]){const w=mesh('box','graphite',[side*.22,0,0],[.43,.025,.14],g);w.rotation.z=side*.15}swaying.push(g);groups.get('life').add(g);birds.push(g)}
 let enabled=true,disposed=false,time=0,windTime=0,peopleTime=0,vehicleTime=0,mechanicalTime=0,night=0,level=quality;
 const activity={wind:true,people:true,vehicles:true,mechanical:true};
 function route(distance,hx,hz,r){const lx=2*(hx-r),lz=2*(hz-r),arc=Math.PI*r/2,len=2*lx+2*lz+4*arc;let n=((distance%len)+len)%len;const list=[lz,arc,lx,arc,lz,arc,lx,arc];for(let k=0;k<8;k++){if(n<=list[k]){if(k===0)return{x:hx,z:-hz+r+n,yaw:0};if(k===2)return{x:hx-r-n,z:hz,yaw:-Math.PI/2};if(k===4)return{x:-hx,z:hz-r-n,yaw:Math.PI};if(k===6)return{x:-hx+r+n,z:-hz,yaw:Math.PI/2};const a=(k-1)/2*Math.PI/2+n/r,cx=[hx-r,-hx+r,-hx+r,hx-r][(k-1)/2],cz=[hz-r,hz-r,-hz+r,-hz+r][(k-1)/2];return{x:cx+Math.cos(a)*r,z:cz+Math.sin(a)*r,yaw:-a}}n-=list[k]}return{x:hx,z:0,yaw:0}}
 function update(delta=0){
  if(disposed)return;const dt=enabled&&Number.isFinite(delta)?THREE.MathUtils.clamp(delta,0,.25):0;time+=dt;if(activity.wind)windTime+=dt;if(activity.people)peopleTime+=dt;if(activity.vehicles)vehicleTime+=dt;
  windShaders.forEach(sh=>sh.uniforms.windTime.value=windTime);
  people.forEach(a=>{let x,z,yaw,walk=true;
   if(a.i<8){const v=route(peopleTime*.72+a.i*18,32,4,1);({x,z,yaw}=v);z+=38;}
   else if(a.i<16){x=-5.5+(a.i-8)*1.55;const cycle=(peopleTime+a.i*2)%32;z=cycle<16?42-cycle*.62:32.1+(cycle-16)*.62;yaw=cycle<16?Math.PI:0;}
   else if(a.i<20){const v=route(peopleTime*.75+a.i*23,53.5,53.5,2);({x,z,yaw}=v);}
   else{x=a.i===20?-21:21;z=36.5;yaw=a.i===20?1.5:-1.5;walk=false}
   a.g.position.set(x,.17,z);a.g.rotation.y=yaw;a.g.visible=activity.people&&(level!=='low'||a.i<10);a.limbs.forEach((l,j)=>l.rotation.x=walk?Math.sin(peopleTime*4+a.i+(j===0||j===3?0:Math.PI))*(j%2?.23:.34):0);
  });
  const doorOpen=activity.people&&people.some(a=>a.g.visible&&Math.abs(a.g.position.x)<4.5&&a.g.position.z<35.7);
  doors.forEach(a=>{const target=a.side*(1.1+(doorOpen?1.85:0));a.g.position.x+=(target-a.g.position.x)*Math.min(1,dt*4)});
  let gateOpen=false;cars.forEach(c=>{if(c.parked)return;const at=route(c.d,48,48,7);const approaching=at.x>46&&at.z>15&&at.z<33;if(approaching&&activity.vehicles)gateOpen=true;const crossing=at.z>44&&Math.abs(at.x)<11,gateStop=approaching&&at.z>23&&at.z<26&&gate.rotation.z<1.15;
   const dwell=crossing&&((vehicleTime+c.i*7)%22<3);const advance=activity.vehicles&&!gateStop&&!dwell?dt*3:0;c.d+=advance;const v=route(c.d,48,48,7);c.g.position.set(v.x,.06,v.z);c.g.rotation.y=v.yaw;c.g.visible=activity.vehicles;c.wheels.forEach(w=>w.rotation.x+=advance/.31);
  });
  gate.rotation.z+=((gateOpen?Math.PI*.47:0)-gate.rotation.z)*Math.min(1,dt*3.5);
  if(activity.mechanical){mechanicalTime+=dt;fans.forEach((f,i)=>f.rotation.y+=dt*(2.5+i*.15));elevators.forEach((g,i)=>{const phase=(mechanicalTime+i*15)%42;let h=phase<4?0:phase<20?(phase-4)/16:phase<25?1:(42-phase)/17;g.position.y=.3+Math.max(0,h)*12.1})}
  materials.obstruction.emissiveIntensity=night*(.3+Math.pow(Math.max(0,Math.sin(time*2)),8)*5)+.08;
  birds.forEach((b,i)=>{const a=peopleTime*.07+i*1.57;b.position.set(Math.cos(a)*36,42+i*9+Math.sin(a*2)*2,Math.sin(a)*35);b.rotation.y=-a;b.children.forEach((w,j)=>w.rotation.z=(j?1:-1)*(.15+Math.sin(peopleTime*5+i)*.3));b.visible=activity.people&&level!=='low'});
 }
 function setQuality(value){if(!['high','medium','low'].includes(value))throw new Error('Unknown quality');level=value;root.traverse(o=>{if(o.userData.tier)o.visible=value==='high'||value==='medium'&&o.userData.tier===1});}
 function setTimeOfDay(value){night=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.45:0;materials.lamp.emissiveIntensity=.05+night*4;materials['office-lit'].emissiveIntensity=.008+night*1.35;for(const m of Object.values(materials))if(m.name.startsWith('sign-'))m.emissiveIntensity=.02+night*.6;}
 function exportScene({partId=null}={}){root.updateWorldMatrix(true,true);const outGeometries={},outMaterials={},objects=[];root.traverseVisible(o=>{if(!o.isMesh)return;let owner=o;while(owner!==root&&!owner.userData.partId)owner=owner.parent;const id=owner.userData.partId||'site';if(partId&&partId!==id)return;const g=o.geometry,m=o.material;if(!outGeometries[g.uuid])outGeometries[g.uuid]={positions:Array.from(g.attributes.position.array),normals:Array.from(g.attributes.normal.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null};if(!outMaterials[m.uuid])outMaterials[m.uuid]={name:m.name,color:m.color.toArray(),roughness:m.roughness,metalness:m.metalness,transmission:m.transmission||0,opacity:m.opacity,transparent:m.transparent,emissive:m.emissive.toArray(),emissiveIntensity:m.emissiveIntensity,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,mx);mx.premultiply(o.matrixWorld)}else mx.copy(o.matrixWorld);objects.push({g:g.uuid,m:m.uuid,matrix:mx.toArray(),owner:id,name:o.name})}});return{format:'jiheng-landmark-office-v1',manifest,snapshotSpace:'world',geometries:outGeometries,materials:outMaterials,objects}}
 function dispose(){if(disposed)return;disposed=true;root.removeFromParent();root.traverse(o=>{if(o.isInstancedMesh)o.dispose()});geometries.forEach(g=>g.dispose());Object.values(materials).forEach(m=>m.dispose());textures.forEach(t=>t.dispose());root.clear();groups.clear();buildings.clear();batches.clear()}
 setQuality(quality);setTimeOfDay('day');update(0);
 return{root,groups,buildings,manifest,materials,update,setTimeOfDay,setQuality,setDynamicsEnabled:v=>enabled=!!v,setActivity:v=>{for(const key of Object.keys(activity))if(v[key]!==undefined)activity[key]=!!v[key]},getManifest:()=>manifest,exportScene,dispose,get quality(){return level},get simulationTime(){return time},get windTime(){return windTime},get disposed(){return disposed},get activity(){return{...activity}}};
}
