/** Procedural 112 m garden housing parcel. Browser DOM is used only for packed textures. */
export function createGardenHousing({THREE,blockSize=112,quality='high',coarse=false}={}){
 if(!THREE?.Group||!Number.isFinite(blockSize)||blockSize<=0)throw new Error('THREE and positive blockSize required');
 const root=new THREE.Group();root.name='暖庭花园';root.scale.setScalar(blockSize/112);
 const groups=new Map(),buildings=new Map(),batches=new Map(),geometries=new Set(),materialSet=new Set(),textures=new Set(),people=[],cars=[],curtains=[],windShaders=[];
 let time=0,windTime=0,enabled=true,wind=true,peopleEnabled=true,vehiclesEnabled=true,disposed=false,level=quality,night=0;
 let seed=41124;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const manifest={id:'nuanting-garden-housing',name:'暖庭花园',units:'m',upAxis:'Y',front:'+Z',pivot:'ground-center',footprint:{width:blockSize,depth:blockSize},nativeBounds:{min:[-56,-.4,-56],max:[56,23,56]},buildings:[],entrances:{public:{position:[0,0,56],width:8},vehicle:{position:[46,0,56],width:6},service:{position:[-46,0,-56],width:5}},lightFixtures:[],motion:{roadCenterline:46,roadCornerRadius:6,walkwayCenterline:40.5,peopleCount:16,vehicleCount:2}};
 for(const id of ['site','landscape','playground','life','A','B','C','D']){const g=new THREE.Group();g.name=id;g.userData={id};groups.set(id,g);root.add(g);if(id.length===1)buildings.set(id,g);}
 const G=g=>(geometries.add(g),g),M=m=>(materialSet.add(m),m),geo={box:G(new THREE.BoxGeometry(1,1,1)),cyl:G(new THREE.CylinderGeometry(.5,.5,1,10)),sphere:G(new THREE.SphereGeometry(.5,10,7)),leaf:G(new THREE.IcosahedronGeometry(.5,1))},materials={};
 function grain(color,kind='fine',repeat=8){const canvas=document.createElement('canvas');canvas.width=canvas.height=128;const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,128,128);const d=ctx.getImageData(0,0,128,128);for(let i=0;i<d.data.length;i+=4){const n=(random()-.5)*(kind==='wall'?28:kind==='grass'?35:18);for(let k=0;k<3;k++)d.data[i+k]+=n;}ctx.putImageData(d,0,0);if(kind==='paving'){ctx.strokeStyle='#acaa99';ctx.lineWidth=.6;for(let n=0;n<128;n+=32){ctx.beginPath();ctx.moveTo(n,0);ctx.lineTo(n,128);ctx.moveTo(0,n);ctx.lineTo(128,n);ctx.stroke();}}if(kind==='wood'){ctx.strokeStyle='#6f5b4240';for(let n=0;n<15;n++){ctx.beginPath();ctx.moveTo(0,n*9);ctx.bezierCurveTo(30,n*9+5,80,n*9-4,128,n*9);ctx.stroke();}}const t=new THREE.CanvasTexture(canvas);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(repeat,repeat);t.colorSpace=THREE.SRGBColorSpace;textures.add(t);return t;}
 function mat(name,color,options={}){const m=M(new THREE.MeshStandardMaterial({color,roughness:.82,...options}));m.name=name;materials[name]=m;return m;}
 mat('warm-stucco',0xffffff,{map:grain('#ddbc7b','wall',12),roughness:.93});materials['warm-stucco'].bumpMap=materials['warm-stucco'].map;materials['warm-stucco'].bumpScale=.012;
 mat('sunlit-stucco',0xffffff,{map:grain('#d6b783','wall',12)});mat('cream-trim',0xe7d7af);mat('stone-base',0xffffff,{map:grain('#a79a7f','paving',5),roughness:.9});mat('paving',0xffffff,{map:grain('#c4bba3','paving',9)});mat('asphalt',0xffffff,{map:grain('#424947','fine',18),roughness:.97});mat('grass',0xffffff,{map:grain('#386341','grass',16),roughness:1});mat('grass-blade',0x4e7946,{side:THREE.DoubleSide});
 mat('roof-base',0x665e54);mat('roof-tile-0',0x75695a);mat('roof-tile-1',0x82735f);mat('roof-tile-2',0x6c6257);mat('roof-tile-3',0x8a7966);mat('roof-tile-4',0x71675d);mat('roof-edge',0x9a8970);
 mat('window-frame',0x53483b,{metalness:.5,roughness:.37});mat('glass',0x547d81,{metalness:.32,roughness:.15});mat('window-lit',0x667b70,{emissive:0xffca7e,emissiveIntensity:.015,roughness:.35});mat('curtain',0xd9c8a1,{side:THREE.DoubleSide});mat('curtain-light',0xede0bf,{side:THREE.DoubleSide});mat('room-shadow',0x514d42);mat('wood',0xffffff,{map:grain('#9e8057','wood',2)});mat('metal',0x655f50,{metalness:.7,roughness:.36});mat('lamp',0xe9d7a3,{emissive:0xffc97b,emissiveIntensity:.08});mat('paint',0xe7dfc3);mat('dark',0x303b36);mat('leaf',0x476841);mat('leaf-light',0x799052);mat('flower',0xc49b67);mat('bark',0x74634b);mat('earth',0x6b5c43);mat('terracotta',0xa87852);mat('rubber',0x987f58);mat('play-sage',0x7c9b7e);mat('play-honey',0xc7a363);mat('skin',0xc6aa88);mat('cloth',0x5a7269);mat('cloth-warm',0xb48560);mat('car-ivory',0xcfcabe,{metalness:.45,roughness:.28});mat('car-green',0x526b63,{metalness:.5,roughness:.3});mat('tire',0x272e2a);mat('bird',0x726957,{side:THREE.DoubleSide});
 const mx=new THREE.Matrix4(),p=new THREE.Vector3(),s=new THREE.Vector3(),q=new THREE.Quaternion(),e=new THREE.Euler();
 function part(type,m,pos,scale,rotation=0,owner='site',tier=0){const key=[type,m,owner,tier].join(':');if(!batches.has(key))batches.set(key,{type,m,owner,tier,items:[]});batches.get(key).items.push({p:pos,s:scale,r:Array.isArray(rotation)?rotation:[0,rotation,0]});}
 const box=(m,x,y,z,w,h,d,owner='site',tier=0)=>part('box',m,[x,y,z],[w,h,d],0,owner,tier);
 function mesh(type,m,pos,scale,parent,name=''){const o=new THREE.Mesh(geo[type],materials[m]);o.position.fromArray(pos);if(buildings.has(parent.userData?.id))o.position.sub(parent.position);o.scale.fromArray(scale);o.castShadow=!['glass','lamp','paint'].includes(m);o.receiveShadow=true;o.name=name;parent.add(o);return o;}
 function beam(m,a,b,width=.07,owner='site',tier=0){const aa=new THREE.Vector3(...a),bb=new THREE.Vector3(...b),length=aa.distanceTo(bb),mid=aa.clone().add(bb).multiplyScalar(.5),quat=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),bb.sub(aa).normalize());part('cyl',m,mid.toArray(),[width,length,width],new THREE.Euler().setFromQuaternion(quat).toArray().slice(0,3),owner,tier);}
 function sign(text,pos,width,height,owner='site'){const c=document.createElement('canvas');c.width=512;c.height=128;const x=c.getContext('2d');x.fillStyle='#4d5846';x.fillRect(0,0,512,128);x.fillStyle='#f3dfb2';x.textAlign='center';x.textBaseline='middle';x.font='500 60px Microsoft YaHei';x.fillText(text,256,67,480);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;textures.add(t);const m=M(new THREE.MeshStandardMaterial({map:t,roughness:.8}));m.name='sign '+text;const o=new THREE.Mesh(G(new THREE.PlaneGeometry(width,height)),m);o.position.fromArray(pos);const parent=groups.get(owner);if(buildings.has(owner))o.position.sub(parent.position);parent.add(o);return o;}
 function patch(name,points,material,owner='site'){const g=G(new THREE.BufferGeometry());g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,1,1,0,1],2));g.setIndex([0,2,1,0,3,2]);g.computeVertexNormals();const o=new THREE.Mesh(g,materials[material]);o.name=name;o.receiveShadow=true;groups.get(owner).add(o);return o;}
 function arcRoad(cx,cz,start,end){const n=24,v=[],uv=[],ix=[];for(let i=0;i<=n;i++){const a=start+(end-start)*i/n;for(const r of [3,9]){v.push(cx+Math.cos(a)*r,.052,cz+Math.sin(a)*r);uv.push(i/n, r/6);}}for(let i=0;i<n;i++){let a=i*2;ix.push(a,a+2,a+1,a+1,a+2,a+3);}const g=G(new THREE.BufferGeometry());g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();const o=new THREE.Mesh(g,materials.asphalt);o.receiveShadow=true;groups.get('site').add(o);}
 box('paving',0,-.2,0,112,.4,112);
 box('grass',0,.035,0,83,.07,83,'landscape');
 for(const x of [-46,46])box('asphalt',x,.025,0,6,.05,80);for(const z of [-46,46])box('asphalt',0,.025,z,80,.05,6);
 arcRoad(40,40,0,Math.PI/2);arcRoad(-40,40,Math.PI/2,Math.PI);arcRoad(-40,-40,Math.PI,Math.PI*1.5);arcRoad(40,-40,Math.PI*1.5,Math.PI*2);
 box('asphalt',46,.025,48,6,.05,16);box('asphalt',-46,.025,-48,5,.05,16);
 box('paving',0,.105,0,4,.21,112);box('paving',0,.105,0,81,.21,4);
 for(const x of [-40.5,40.5])box('paving',x,.105,0,3,.21,83);for(const z of [-40.5,40.5])box('paving',0,.105,z,81,.21,3);
 for(const x of [-8,8])box('paving',x,.115,0,1.8,.23,20);for(const z of [-9,9])box('paving',0,.115,z,17.8,.23,1.8);
 for(const x of [-25,25]){box('paving',x,.12,-7,2.5,.24,14);box('paving',x,.12,39,2.5,.24,4);}
 // Build four independently centered, hollow, genuinely fenestrated houses.
 const specs=[['A',-25,-25,4],['B',25,-25,5],['C',-25,25,5],['D',25,25,6]];
 for(const [id,x,z,floors] of specs){
  const w=26,d=16,eave=.3+floors*3.1,rise=3.35,height=eave+rise+.38,group=groups.get(id);group.position.set(x,0,z);
  manifest.buildings.push({id,name:id+'栋',x,z,w,d,floors,height,groundY:.3});
  box('stone-base',x,.27,z,26.5,.54,16.5,id);box('room-shadow',x,.38,z,25.4,.15,15.4,id);
  if(coarse){box('warm-stucco',x,eave/2,z,w,eave,d,id);}else{
   for(let floor=0;floor<floors;floor++){
    const base=.3+floor*3.1;
    box('cream-trim',x,base+.09,z,26.2,.18,16.2,id,1);box('room-shadow',x,base+.19,z,25.35,.08,15.35,id);
    // Interior partitions terminate in the facade piers, leaving windows with depth.
    box('room-shadow',x,base+1.6,z,.16,2.9,15.2,id,1);box('room-shadow',x,base+1.6,z-1,25.2,2.9,.12,id,1);
    for(const side of [-1,1]){
     const zz=z+side*7.82;
     if(floor===0&&side===1){for(const sx of [-1,1])box('warm-stucco',x+sx*6.98,base+.48,zz,12.04,.96,.36,id);}else box('warm-stucco',x,base+.48,zz,26,.96,.36,id);
     box('warm-stucco',x,base+2.85,zz,26,.5,.36,id);
     for(let j=0;j<7;j++){const edge=j===0||j===6,xx=x+(edge?Math.sign(j-3)*12.3:(j-3)*4.2);if(j===3&&floor===0&&side===1)continue;box('warm-stucco',xx,base+1.75,zz,edge?1.4:2,1.7,.36,id);}
     for(let j=0;j<6;j++){
      const xx=x+(j-2.5)*4.2,cy=base+1.76,normal=z+side*7.91,bay=(j===0||j===5)&&floor>0&&floor<floors-1,lit=(floor*9+j+id.charCodeAt(0)+side)%7===0;
      // Frames, recessed glazing, mullions and deep stone sills.
      const front=normal+side*(bay?.86:-.08),frameWidth=2.2;
      box('room-shadow',xx,cy,normal-side*.29,2.16,1.72,.07,id);
      box(lit?'window-lit':'glass',xx,cy,front,2.06,1.65,.045,id);
      for(const dx of [-1.08,1.08])box('window-frame',xx+dx,cy,front+side*.02,.085,1.84,.1,id);
      for(const dy of [-.88,.88])box('window-frame',xx,cy+dy,front+side*.025,frameWidth,.085,.1,id);
      box('window-frame',xx,cy,front+side*.08,.055,1.7,.07,id,1);box('window-frame',xx,cy+.2,front+side*.08,2.12,.045,.07,id,1);
      box('cream-trim',xx,base+.84,normal+side*.14,2.45,.14,bay?1.05:.45,id,1);box('cream-trim',xx,base+2.72,normal+side*.14,2.5,.12,bay?1.05:.35,id,1);
      if(bay){for(const sx of [-1,1]){box('glass',xx+sx*1.07,cy,normal+side*.4,.045,1.65,.78,id);box('window-frame',xx+sx*1.09,cy,normal+side*.06,.09,1.8,.1,id);}}
      // Varied drawn curtains sit behind the glass, not in front of the facade.
      if((floor+j)%3!==0){const sideCurtain=j%2?1:-1,c=mesh('box',(j+floor)%2?'curtain':'curtain-light',[xx+sideCurtain*.63,cy,normal-side*.2],[.55,1.62,.04],group,'Curtain '+id+' '+floor+' '+side+' '+j);curtains.push({object:c,base:c.position.x,phase:random()*6});}
      if(side===1&&(j===1||j===4)&&floor>0){
       const bz=z+9.03,y=base+.18;
       box('cream-trim',xx,y,bz,3.2,.22,2.1,id);box('wood',xx,y+.13,bz,2.9,.045,1.85,id,1);
       beam('metal',[xx-1.5,y+1.16,z+10],[xx+1.5,y+1.16,z+10],.065,id,1);
       for(let k=0;k<=12;k++)box('metal',xx-1.5+k*.25,y+.65,z+10,.035,1,.035,id,1);
       for(const sx of [-1,1]){beam('metal',[xx+sx*1.5,y+1.16,z+8],[xx+sx*1.5,y+1.16,z+10],.06,id,1);for(let k=0;k<7;k++)box('metal',xx+sx*1.5,y+.65,z+8.2+k*.28,.035,1,.035,id,1);}
       if((floor+j)%2===0){box('terracotta',xx+.8,y+.35,bz+.3,.65,.45,.4,id,1);part('leaf','leaf',[xx+.8,y+.7,bz+.3],[.85,.65,.65],0,id,1);}
      }
     }
    }
    // Side elevations: four windows cut into the walls, with quoins at corners.
    for(const side of [-1,1]){
     const xx=x+side*12.82;box('warm-stucco',xx,base+.48,z,.36,.96,15.3,id);box('warm-stucco',xx,base+2.85,z,.36,.5,15.3,id);
     for(let j=0;j<5;j++){const edge=j===0||j===4,zz=z+(edge?Math.sign(j-2)*7.1:(j-2)*3.6);box('warm-stucco',xx,base+1.75,zz,.36,1.7,edge?1.8:2,id);}
     for(let j=0;j<4;j++){const zz=z+(j-1.5)*3.6,front=x+side*12.74;box('glass',front,base+1.76,zz,.045,1.65,1.52,id);for(const dz of [-.81,.81])box('window-frame',front+side*.07,base+1.76,zz+dz,.1,1.8,.075,id);for(const dy of [-.88,.88])box('window-frame',front+side*.07,base+1.76+dy,zz,.1,.075,1.7,id);box('cream-trim',front+side*.17,base+.84,zz,.4,.14,1.9,id,1);box('window-frame',front+side*.1,base+1.76,zz,.09,1.7,.05,id,1);}
    }
    for(const sx of [-1,1])for(const sz of [-1,1]){box('cream-trim',x+sx*12.9,base+1.55,z+sz*7.91,.22,3.0,.22,id,1);for(let k=0;k<5;k++)box('cream-trim',x+sx*12.82,base+.4+k*.56,z+sz*7.84,.38,.22,.4,id,2);}
   }
  }
  // Warm plaster gable: a closed triangular prism; separate roof planes above it.
  const gv=[[-13,0,-8],[13,0,-8],[-13,0,8],[13,0,8],[-13,rise,0],[13,rise,0]],gi=[0,4,2,1,3,5,0,1,5,0,5,4,2,4,5,2,5,3,0,2,3,0,3,1];
  const gg=G(new THREE.BufferGeometry());gg.setAttribute('position',new THREE.Float32BufferAttribute(gv.flat(),3));gg.setIndex(gi.reverse());gg.computeVertexNormals();const gable=new THREE.Mesh(gg,materials['warm-stucco']);gable.position.set(0,eave,0);gable.name='Plastered gable '+id;gable.castShadow=true;group.add(gable);
  const slope=Math.atan(rise/8.75),slopeLength=Math.hypot(8.75,rise);
  for(const side of [-1,1]){
   part('box','roof-base',[x,eave+rise/2,z+side*4.375],[27.4,.18,slopeLength+.15],[side*slope,0,0],id);
   beam('roof-edge',[x-13.75,eave-.04,z+side*8.79],[x+13.75,eave-.04,z+side*8.79],.18,id);
   // Gutters have two lips and an inner channel, plus end drops and pipe clips.
   box('metal',x,eave-.17,z+side*8.88,27.6,.12,.23,id,1);
   for(const edge of [-.12,.12])box('metal',x,eave-.06,z+side*8.88+edge,27.6,.15,.035,id,1);
   for(const sx of [-1,1]){const px=x+sx*12.55,pz=z+side*8.32;beam('metal',[px,.38,pz],[px,eave-.12,pz],.12,id,1);beam('metal',[px,eave-.12,pz],[px,eave-.12,z+side*8.9],.12,id,1);for(let k=1;k<floors;k++)box('metal',px,.7+k*3.1,pz,.24,.07,.2,id,2);}
   if(!coarse){for(let row=0;row<17;row++)for(let col=0;col<34;col++){const zz=(row+.5)*8.75/17,xx=(col-16.5)*.8+(row%2?.12:0);part('box','roof-tile-'+((row+col*3+id.charCodeAt(0))%5),[x+xx,eave+rise-zz*rise/8.75+.15,z+side*zz],[.78,.075,.62],[side*slope,0,0],id,1);}}
  }
  for(const sx of [-1,1])for(const side of [-1,1])beam('roof-edge',[x+sx*13.7,eave+.06,z+side*8.8],[x+sx*13.7,eave+rise+.12,z],.16,id,1);
  for(let k=0;k<34;k++)part('cyl','roof-edge',[x+(k-16.5)*.8,eave+rise+.18,z],[.4,.82,.4],[0,0,Math.PI/2],id,1);
  // Small roof vents, weather caps and a discreet skylight.
  box('stone-base',x+8,eave+rise-1.5,z-4,1.1,1.5,.9,id,1);box('metal',x+8,eave+rise-.7,z-4,1.35,.12,1.15,id,1);
  part('box','window-frame',[x-4,eave+rise-1.15,z+3.4],[2.25,.2,2.0],[slope,0,0],id,1);part('box','glass',[x-4,eave+rise-1.03,z+3.4],[1.95,.045,1.7],[slope,0,0],id,1);
  // Gable attic fan-light window sits below ridge on both end walls.
  for(const sx of [-1,1]){box('window-frame',x+sx*13.03,eave+1.2,z,.09,1.2,1.4,id,1);box('glass',x+sx*13.09,eave+1.2,z,.045,1,1.2,id,1);box('window-frame',x+sx*13.13,eave+1.2,z,.06,1.05,.055,id,1);}
  box('paving',x,.17,z+10.5,8,.34,5,id);box('cream-trim',x,.27,z+11.6,3.6,.12,1.1,id);box('cream-trim',x,.36,z+10.8,3.6,.12,1.1,id);
  box('window-frame',x,1.55,z+8.01,1.95,2.5,.16,id);box('glass',x,1.55,z+8.12,1.72,2.3,.065,id);box('window-frame',x,1.55,z+8.18,.055,2.3,.055,id);
  for(const sx of [-1,1])box('metal',x+sx*.17,1.48,z+8.25,.035,.4,.09,id,1);
  box('metal',x,3.01,z+9.1,4.6,.14,2.5,id);box('wood',x,2.9,z+9.1,4.4,.08,2.3,id,1);sign(id+'栋 · 暖庭',[x,2.63,z+8.25],1.6,.28,id);
  box('metal',x+1.35,1.4,z+8.15,.22,.35,.1,id,1);box('lamp',x-1.5,2.3,z+8.2,.22,.45,.18,id,1);manifest.lightFixtures.push({position:[x-1.5,2.1,z+8.5],type:'point',power:45});
  // A ground-floor private terrace occupies the corner between house and inner path.
  const tx=x-7;box('wood',tx,.21,z+11.5,7,.22,3.6,id,1);
  for(const xx of [tx-3.5,tx+3.5])box('stone-base',xx,.65,z+11.5,.45,1,4.0,id,1);
  box('terracotta',tx,.55,z+13.25,6.4,.5,.5,id,1);for(let n=0;n<8;n++)part('leaf','leaf',[tx-2.8+n*.8,.95,z+13.25],[.9,.7,.6],0,id,1);
  part('cyl','wood',[tx,1.0,z+11.3],[1.2,.08,1.2],0,id,1);part('cyl','metal',[tx,.6,z+11.3],[.08,.8,.08],0,id,1);
  for(const sx of [-1,1]){box('wood',tx+sx*1.1,.62,z+11.3,.6,.12,.6,id,1);box('wood',tx+sx*1.4,.98,z+11.3,.1,.6,.65,id,1);}
 }
 // Planned perimeter parking: ten bays, five parked cars, two electric chargers.
 for(let i=0;i<10;i++){const x=-32+i*3.4;for(const dx of [-1.65,1.65])box('paint',x+dx,.065,-51.6,.07,.025,5.0,'site',1);box('paint',x,.065,-54.1,3.3,.025,.07,'site',1);if(i%2===0){box(i%4?'car-green':'car-ivory',x,.7,-51.3,1.9,.9,4.2,'site',1);box('glass',x,1.35,-51.4,1.65,.65,2.0,'site',1);for(const sx of [-1,1])for(const zz of [-1.3,1.3])box('tire',x+sx*.94,.38,-51.3+zz,.18,.6,.6,'site',1);}}
 for(const x of [-32,-25.2]){box('metal',x,1.0,-54.5,.45,1.5,.28,'site',1);box('play-sage',x,1.4,-54.33,.3,.4,.04,'site',1);beam('dark',[x+.2,1.1,-54.3],[x+.45,.3,-53.6],.045,'site',1);}
 // Trees are deliberately small enough that the complete canopy fits the plot.
 function tree(x,z,size=1){part('cyl','bark',[x,1.9*size,z],[.19*size,3.8*size,.19*size],0,'landscape');for(let j=0;j<(coarse?3:9);j++){const a=j*2.4,r=.7*Math.sqrt(random())*size;part('leaf',j%3?'leaf':'leaf-light',[x+Math.sin(a)*r,(3.9+random()*1.7)*size,z+Math.cos(a)*r],[2.1*size,2.5*size,2.1*size],0,'landscape',coarse?0:1);}if(!coarse){box('earth',x,.075,z,2,.08,2,'landscape',1);box('stone-base',x,.12,z,2.2,.08,.12,'landscape',1);}}
 for(const x of [-52.5,52.5])for(let z=-38;z<=38;z+=12.6)tree(x,z,.85+random()*.12);
 for(const x of [-15,15])for(const z of [-6,6])tree(x,z,1.05);
 for(const x of [-39,39])for(const z of [-37,37])tree(x,z,.8);
 if(!coarse){for(let i=0;i<56;i++){let x=(i%2?1:-1)*(12+random()*25),z=(i%4<2?-1:1)*(36+random()*2);part('leaf',i%3?'leaf':'leaf-light',[x,.65,z],[1.3,1.05,1.3],0,'landscape',1);}for(const z of [-15,15])for(let x=-7;x<=7;x+=1.4){part('leaf','leaf',[x,.55,z],[1.3,.8,1.1],0,'landscape',1);part('leaf','flower',[x,.98,z],[.45,.25,.45],0,'landscape',2);}}
 function bench(x,z,owner='landscape'){box('metal',x,.37,z,2.5,.1,.65,owner,1);for(const dx of [-1.1,1.1])box('metal',x+dx,.32,z,.08,.6,.55,owner,1);for(let n=0;n<4;n++)box('wood',x,.7,z-.3+n*.2,2.7,.09,.13,owner,1);for(let n=0;n<3;n++)box('wood',x,.9+n*.18,z-.35,2.7,.12,.08,owner,1);}
 for(const x of [-5,5])for(const z of [-12,12])bench(x,z);
 // A slatted pergola and a restrained children's corner occupy opposite garden wings.
 for(const x of [-28,-20])for(const z of [-3,3])box('wood',x,1.7,z,.24,3.4,.24,'landscape');box('paving',-24,.11,0,11,.22,9,'landscape');for(let j=0;j<15;j++)box('wood',-28.7+j*.67,3.5,0,.18,.22,7.5,'landscape',1);for(const z of [-3,3])box('wood',-24,3.35,z,9.5,.25,.18,'landscape');bench(-24,-2);
 box('rubber',25,.15,0,16,.2,12,'playground');box('play-sage',25,.27,0,8,.035,9,'playground',1);
 for(const x of [21.5,24.5])for(const z of [-3,-.5])beam('wood',[x,.25,z],[x,2.7,z],.16,'playground');box('wood',23,1.7,-1.75,3.3,.15,2.7,'playground');box('play-honey',23,2.85,-1.75,3.7,.16,3,'playground');part('box','play-sage',[23,1.0,1.7],[2.25,.09,5.0],[.32,0,0],'playground');for(let j=0;j<5;j++)box('wood',23,.4+j*.29,-4+j*.32,1.5,.1,.4,'playground',1);
 for(const x of [29,32]){beam('metal',[x,.3,-3],[x,3.0,0],.11,'playground');beam('metal',[x,.3,3],[x,3,0],.11,'playground');}beam('metal',[29,3,0],[32,3,0],.14,'playground');
 const swing=new THREE.Group();swing.name='Garden swing';swing.position.set(30.5,2.95,0);groups.get('playground').add(swing);for(const x of [-.45,.45])mesh('cyl','metal',[x,-.95,0],[.025,1.9,.025],swing);mesh('box','wood',[0,-1.95,0],[1.15,.13,.55],swing);
 // Public entry pavilion, mailboxes, bicycle rack and entrance barrier.
 box('stone-base',-7,1.3,51,4,2.6,4);box('cream-trim',-7,2.7,51,4.4,.2,4.4);box('glass',-7,1.6,53.04,3.2,1.3,.06);box('glass',-4.96,1.6,51,.06,1.3,3.2);box('metal',-6.8,.8,53.1,1,.6,.1,'site',1);
 box('stone-base',11,1.25,52,13,2.5,.4);sign('暖 庭 花 园',[11,1.6,52.25],11,1.1);sign('NUANTING  GARDEN',[11,.7,52.26],8,.3);box('paving',0,.11,52,8,.22,8);
 for(let n=0;n<8;n++){box('metal',-13+n*.62,1.2,51.8,.56,.48,.4,'site',1);box('dark',-13+n*.62,1.2,52.01,.35,.045,.025,'site',1);}
 for(let n=0;n<5;n++){const xx=26+n*1.3;beam('metal',[xx,.2,51],[xx,.9,51],.07,'site',1);beam('metal',[xx,.9,51],[xx,.9,52.4],.07,'site',1);beam('metal',[xx,.9,52.4],[xx,.2,52.4],.07,'site',1);}
 box('metal',43, .7,30,.5,1.4,.6);const gatePivot=new THREE.Group();gatePivot.position.set(43,1.3,30);gatePivot.name='Gate barrier';groups.get('site').add(gatePivot);mesh('box','paint',[3,0,0],[6,.13,.15],gatePivot);for(let i=0;i<5;i++)mesh('box','play-honey',[.5+i*1.1,0,.09],[.4,.14,.03],gatePivot);
 for(const x of [-54.6,54.6]){for(let z=-54;z<=54;z+=6)beam('metal',[x,.05,z],[x,1.2,z],.05,'site',1);for(const y of [.4,.8,1.15])beam('metal',[x,y,-54.6],[x,y,54.6],.035,'site',1);}
 for(const z of [-54.6,54.6])for(const range of z<0?[[-54.6,-49],[-43,-5],[5,54.6]]:[[-54.6,-5],[5,41],[50,54.6]]){for(const y of [.4,.8,1.15])beam('metal',[range[0],y,z],[range[1],y,z],.035,'site',1);}
 const lampLocations=[[-40,0],[40,0],[-40,-37],[40,-37],[-40,37],[40,37],[-9,-11],[9,11],[0,49],[0,-49]];
 for(const [x,z] of lampLocations){part('cyl','metal',[x,1.85,z],[.1,3.7,.1]);box('metal',x,3.6,z,.5,.12,.5);box('lamp',x,3.42,z,.32,.25,.32);manifest.lightFixtures.push({position:[x+.4,3.25,z],type:'point',power:70});}
 for(const x of [-3,3])for(const z of [-32,-20,20,32]){box('metal',x,.4,z,.16,.8,.16,'site',1);box('lamp',x,.79,z,.21,.12,.21,'site',1);manifest.lightFixtures.push({position:[x,.92,z],type:'point',power:12});}
 for(let z=-36;z<=36;z+=6)for(const x of [-42,42]){box('dark',x,.12,z,.5,.035,.4,'site',2);for(let n=0;n<5;n++)box('metal',x-.2+n*.1,.14,z,.025,.025,.35,'site',2);}
 // Keep grass away from buildings, paved paths, playground and the pergola.
 let grassMesh=null;
 if(!coarse){const blade=G(new THREE.BufferGeometry());blade.setAttribute('position',new THREE.Float32BufferAttribute([-.018,0,0,.018,0,0,.014,.12,.025],3));blade.computeVertexNormals();grassMesh=new THREE.InstancedMesh(blade,materials['grass-blade'],12000);grassMesh.name='Individual grass blades';for(let i=0;i<grassMesh.count;i++){let x,z;do{x=-39+random()*78;z=-39+random()*78;}while(Math.abs(x)<2.2||Math.abs(z)<2.2||specs.some(b=>Math.abs(x-b[1])<14&&Math.abs(z-b[2])<10)||Math.abs(Math.abs(x)-8)<1.1&&Math.abs(z)<10||Math.abs(Math.abs(z)-9)<1.1&&Math.abs(x)<9||Math.abs(x+24)<6&&Math.abs(z)<5||Math.abs(x-25)<9&&Math.abs(z)<7||Math.abs(Math.abs(x)-25)<1.6&&z<-9||Math.abs(Math.abs(x)-25)<1.6&&z>35);mx.makeRotationY(random()*Math.PI);mx.setPosition(x,.075,z);grassMesh.setMatrixAt(i,mx);}grassMesh.computeBoundingSphere();groups.get('landscape').add(grassMesh);}
 // One instance batch per component/material/detail tier.
 for(const b of batches.values()){const parent=groups.get(b.owner),o=new THREE.InstancedMesh(geo[b.type],materials[b.m],b.items.length);o.name=b.owner+':'+b.m+':'+b.tier;o.userData.tier=b.tier;o.castShadow=!['glass','paint','lamp','grass','asphalt'].includes(b.m);o.receiveShadow=true;for(let i=0;i<b.items.length;i++){const it=b.items[i];p.fromArray(it.p).sub(parent.position);s.fromArray(it.s);q.setFromEuler(e.set(...it.r));mx.compose(p,q,s);o.setMatrixAt(i,mx);}o.computeBoundingSphere();parent.add(o);}
 for(const name of ['leaf','leaf-light','grass-blade'])materials[name].onBeforeCompile=shader=>{shader.uniforms.windTime={value:0};windShaders.push(shader);shader.vertexShader='uniform float windTime;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n#ifdef USE_INSTANCING\nfloat phase=instanceMatrix[3].x*.23+instanceMatrix[3].z*.18;\ntransformed.x+=sin(windTime*1.3+phase)*.045*(position.y+.6);\n#endif');};
 function roundedRoute(distance,hx,hz,r){const lx=2*(hx-r),lz=2*(hz-r),arc=Math.PI*r/2,length=2*lx+2*lz+4*arc;let d=((distance%length)+length)%length;const segments=[lz,arc,lx,arc,lz,arc,lx,arc];for(let i=0;i<segments.length;i++){if(d<=segments[i]){if(i===0)return {x:hx,z:-hz+r+d,yaw:0,length};if(i===2)return{x:hx-r-d,z:hz,yaw:-Math.PI/2,length};if(i===4)return{x:-hx,z:hz-r-d,yaw:Math.PI,length};if(i===6)return{x:-hx+r+d,z:-hz,yaw:Math.PI/2,length};const a=(i-1)/2*Math.PI/2+d/r,cx=[hx-r,-hx+r,-hx+r,hx-r][(i-1)/2],cz=[hz-r,hz-r,-hz+r,-hz+r][(i-1)/2];return{x:cx+Math.cos(a)*r,z:cz+Math.sin(a)*r,yaw:-a,length};}d-=segments[i];}return{x:hx,z:-hz+r,yaw:0,length};}
 function makePerson(i){const g=new THREE.Group();g.name='Resident '+i;groups.get('life').add(g);mesh('sphere','skin',[0,1.65,0],[.32,.38,.32],g);mesh('box',i%2?'cloth':'cloth-warm',[0,1.1,0],[.43,.65,.26],g);const limbs=[];for(const sx of [-1,1]){const pivot=new THREE.Group();pivot.position.set(sx*.13,.8,0);g.add(pivot);mesh('box','dark',[0,-.35,0],[.15,.7,.17],pivot);limbs.push(pivot);const arm=new THREE.Group();arm.position.set(sx*.29,1.35,0);g.add(arm);mesh('box','skin',[0,-.24,0],[.12,.48,.14],arm);limbs.push(arm);}return {g,limbs,i};}
 for(let i=0;i<16;i++)people.push(makePerson(i));
 function makeCar(i){const g=new THREE.Group();g.name='Moving car '+i;groups.get('life').add(g);mesh('box',i?'car-green':'car-ivory',[0,.72,0],[1.9,.78,4.15],g);mesh('box','glass',[0,1.27,-.18],[1.65,.68,2.1],g);mesh('box',i?'car-green':'car-ivory',[0,1.65,-.18],[1.7,.08,2.0],g);for(const sx of [-1,1]){mesh('box','lamp',[sx*.6,.8,2.1],[.48,.17,.045],g);mesh('box','terracotta',[sx*.65,.8,-2.1],[.4,.12,.045],g);}const wheels=[];for(const sx of [-1,1])for(const zz of [-1.32,1.32]){const w=mesh('cyl','tire',[sx*.96,.4,zz],[.66,.22,.66],g);w.rotation.z=Math.PI/2;wheels.push(w);}return{g,wheels,distance:i?205:28,speed:2.6,gateWait:0,waitStarted:false};}
 for(let i=0;i<2;i++)cars.push(makeCar(i));
 const birdGeometry=G(new THREE.BufferGeometry());birdGeometry.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,-.5,.08,.2,-.15,0,.35,0,0,0,.15,0,.35,.5,.08,.2],3));birdGeometry.computeVertexNormals();const birds=[];for(let i=0;i<3;i++){const bird=new THREE.Mesh(birdGeometry,materials.bird);bird.name='Garden bird '+i;groups.get('life').add(bird);birds.push(bird);}
 function update(delta=0){
  if(disposed)return;const dt=enabled&&Number.isFinite(delta)?THREE.MathUtils.clamp(delta,0,.25):0;time+=dt;if(wind)windTime+=dt;windShaders.forEach(shader=>shader.uniforms.windTime.value=windTime);curtains.forEach(c=>c.object.position.x=c.base+Math.sin(windTime*.6+c.phase)*.018);
  for(const a of people){let route;if(a.i<8)route=roundedRoute(time*.65+a.i*8,8,9,1.5);else if(a.i<12)route=roundedRoute(time*.62+(a.i-8)*38,.7,38,.6);else route=roundedRoute(time*.7+(a.i-12)*72,40.5,40.5,4);a.g.position.set(route.x,.23,route.z);a.g.rotation.y=route.yaw;a.g.visible=peopleEnabled&&(level!=='low'||a.i<8);a.limbs.forEach((l,j)=>l.rotation.x=Math.sin(time*4+a.i+(j===0||j===3?0:Math.PI))*(j%2?.28:.36));}
  let openGate=false;
  for(const a of cars){const route=roundedRoute(a.distance,46,46,6),nearBarrier=route.x>44&&route.z>25&&route.z<29;if(vehiclesEnabled&&route.x>44&&route.z>14&&route.z<35)openGate=true;if(vehiclesEnabled&&nearBarrier&&!a.waitStarted){a.waitStarted=true;a.gateWait=1.2;}if(route.x<44||route.z>36||route.z<10)a.waitStarted=false;const stop=nearBarrier&&(gatePivot.rotation.z<.95||a.gateWait>0);if(vehiclesEnabled)a.gateWait=Math.max(0,a.gateWait-dt);const advance=vehiclesEnabled&&!stop?dt*a.speed:0;a.distance+=advance;const next=roundedRoute(a.distance,46,46,6);a.g.position.set(next.x,.075,next.z);a.g.rotation.y=next.yaw;a.g.visible=vehiclesEnabled;a.wheels.forEach(w=>w.rotation.x+=advance/.33);}
  const desired=openGate?Math.PI*.47:0;gatePivot.rotation.z+=(desired-gatePivot.rotation.z)*Math.min(1,dt*3);swing.rotation.x=Math.sin(time*1.05)*.1;
  birds.forEach((b,i)=>{const angle=time*.15+i*2.1;b.position.set(Math.sin(angle)*10,8+i*1.2+Math.sin(angle*2)*.4,Math.cos(angle)*10);b.rotation.y=-angle;b.rotation.z=Math.sin(time*4+i)*.16;b.visible=peopleEnabled&&level!=='low';});
 }
 function setQuality(value){if(!['high','medium','low'].includes(value))throw new Error('Unknown quality');level=value;root.traverse(o=>{if(o.userData.tier)o.visible=value==='high'||value==='medium'&&o.userData.tier<2;});if(grassMesh)grassMesh.count=value==='high'?12000:value==='medium'?5000:1000;}
 function setTimeOfDay(value){night=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value==='night'?1:value==='evening'?.4:0;materials.lamp.emissiveIntensity=.08+night*3;materials['window-lit'].emissiveIntensity=.015+night*1.4;}
 function exportScene(){root.updateWorldMatrix(true,true);const outGeometries={},outMaterials={},objects=[];root.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry,m=o.material;if(!outGeometries[g.uuid])outGeometries[g.uuid]={positions:Array.from(g.attributes.position.array),indices:g.index?Array.from(g.index.array):null,uv:g.attributes.uv?Array.from(g.attributes.uv.array):null};if(!outMaterials[m.uuid])outMaterials[m.uuid]={name:m.name,color:m.color.toArray(),roughness:m.roughness,metalness:m.metalness,opacity:m.opacity,transparent:m.transparent,emissive:m.emissive.toArray(),emissiveIntensity:m.emissiveIntensity,texture:m.map?.image?.toDataURL?m.map.image.toDataURL():null,repeat:m.map?.repeat.toArray()||[1,1]};let owner=o;while(owner!==root&&!owner.userData.id)owner=owner.parent;for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,mx);mx.premultiply(o.matrixWorld);}else mx.copy(o.matrixWorld);objects.push({g:g.uuid,m:m.uuid,matrix:mx.toArray(),owner:owner.userData.id||'site'});}});return {format:'nuanting-garden-housing-v1',manifest,snapshotSpace:'world',geometries:outGeometries,materials:outMaterials,objects};}
 function dispose(){if(disposed)return;disposed=true;root.removeFromParent();root.traverse(o=>{if(o.isInstancedMesh)o.dispose();});geometries.forEach(g=>g.dispose());materialSet.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());root.clear();groups.clear();buildings.clear();batches.clear();}
 setQuality(quality);update(0);
 return {root,groups,buildings,manifest,update,setQuality,setTimeOfDay,setDynamicsEnabled:value=>enabled=!!value,setActivity:value=>{if(value.wind!==undefined)wind=!!value.wind;if(value.traffic!==undefined)peopleEnabled=vehiclesEnabled=!!value.traffic;if(value.people!==undefined)peopleEnabled=!!value.people;if(value.vehicles!==undefined)vehiclesEnabled=!!value.vehicles;},exportScene,dispose,get quality(){return level;},get simulationTime(){return time;},get disposed(){return disposed;}};
}
