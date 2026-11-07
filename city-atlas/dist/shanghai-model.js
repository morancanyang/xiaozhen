/** Shanghai Tower inspired architectural model. Geometry uses the host THREE only. */
export function createShanghaiTower(options={}){
  const T=options.THREE;if(!T?.Group)throw new Error('Supply the host THREE namespace.');
  const height=options.displayHeight??96,footprint=options.footprint??112;
  if(height<20||height>250||footprint<56)throw new Error('Invalid dimensions: height 20–250 m, footprint at least 56 m.');
  const root=new T.Group();root.name='ShanghaiTower_Landmark';
  const architecture=new T.Group(),landscape=new T.Group(),windows=new T.Group(),residents=new T.Group(),detail=new T.Group();
  architecture.name='Architecture';landscape.name='Plaza';windows.name='Window_Lights';residents.name='Plaza_Residents';detail.name='Fine_Details';root.add(architecture,landscape,windows,residents,detail);
  const scale=height/96,siteScale=Math.min(1,(footprint-8)/104),shapeScale=Math.min(scale,siteScale*2.5);
  let seed=options.seed??632;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const materials={};const mat=(name,color,extra={})=>{const m=new T.MeshStandardMaterial({color,roughness:.65,...extra});m.name=name;materials[name]=m;return m;};
  mat('Silver titanium',0xa6bbc8,{metalness:.8,roughness:.27});mat('Dark mullions',0x273e4d,{metalness:.7,roughness:.3});mat('Pale stone',0x81949e,{roughness:.88});mat('Podium roof',0x748e9d,{metalness:.5,roughness:.33});mat('Core',0x273c50,{metalness:.2,roughness:.65});mat('Landscape metal',0x526b71,{metalness:.5,roughness:.4});mat('Grass',0x4a6b59);mat('Leaves',0x477866);mat('Wood',0x8e745b);mat('Bark',0x6f6857);
  materials['Outer glass']=new T.MeshPhysicalMaterial({name:'Outer glass',color:0x9cbed2,metalness:.45,roughness:.18,clearcoat:1,clearcoatRoughness:.14,transparent:true,opacity:.24,side:T.DoubleSide,depthWrite:false});
  materials['Inner glass']=new T.MeshPhysicalMaterial({name:'Inner glass',color:0x52758b,metalness:.52,roughness:.24,clearcoat:.7});
  mat('Warm windows',0xd5a66f,{emissive:0xffa344,emissiveIntensity:1.0,roughness:.5});mat('Plaza luminaires',0xe9d3ad,{emissive:0xffc78a,emissiveIntensity:2});
  const unitBox=new T.BoxGeometry(1,1,1),unitSphere=new T.IcosahedronGeometry(1,1),unitLeaf=new T.IcosahedronGeometry(1,0),unitCylinder=new T.CylinderGeometry(1,1,1,10),batches=new Map();
  const dummy=new T.Object3D();
  function instance(kind,material,x,y,z,sx,sy,sz,rotation=0,parent=architecture){const key=parent.uuid+'|'+kind+'|'+material;if(!batches.has(key))batches.set(key,{parent,kind,material,matrices:[]});dummy.position.set(x,y,z);dummy.rotation.set(0,rotation,0);dummy.scale.set(sx,sy,sz);dummy.updateMatrix();batches.get(key).matrices.push(dummy.matrix.clone());}
  const box=(m,x,y,z,w,h,d,r=0,p=architecture)=>instance('box',m,x,y,z,w,h,d,r,p);
  const sphere=(m,x,y,z,a,b,c,p=landscape)=>instance('sphere',m,x,y,z,a,b,c,0,p);
  function section(t,a,inner=false){const theta=a+t*Math.PI*2/3;const radius=inner?6.1*(1-.51*t):8.6*(1-.55*Math.pow(t,.9))*(1+.135*Math.cos(3*a));return new T.Vector3(Math.cos(theta)*radius*shapeScale,(5.3+t*84)*scale,Math.sin(theta)*radius*shapeScale);}
  function skin(inner=false){const around=96,levels=options.coarse?18:126,positions=[],indices=[];for(let j=0;j<=levels;j++){const t=j/levels;for(let i=0;i<=around;i++)positions.push(...section(t,i/around*Math.PI*2,inner).toArray());}for(let j=0;j<levels;j++)for(let i=0;i<around;i++){const a=j*(around+1)+i,b=a+around+1;indices.push(a,b,a+1,b,b+1,a+1);}const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(positions,3));g.setIndex(indices);g.computeVertexNormals();return g;}
  const innerSkin=new T.Mesh(skin(true),materials['Inner glass']);innerSkin.name='Inner_Curtain_Wall';innerSkin.castShadow=true;innerSkin.receiveShadow=true;architecture.add(innerSkin);
  const outerSkin=new T.Mesh(skin(),materials['Outer glass']);outerSkin.name='Twisting_Double_Skin';outerSkin.renderOrder=3;architecture.add(outerSkin);
  const core=new T.Mesh(new T.CylinderGeometry(2.3*shapeScale,4.3*shapeScale,84*scale,48),materials.Core);core.name='Interior_Core';core.position.y=47.3*scale;architecture.add(core);
  function ribbon(points,width,material,parent=architecture){const pos=[],idx=[];for(let i=0;i<points.length;i++){const p=points[i];pos.push(p.x,p.y-width/2,p.z,p.x,p.y+width/2,p.z);if(i<points.length-1){const a=i*2;idx.push(a,a+1,a+2,a+1,a+3,a+2);}}const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(pos,3));geo.setIndex(idx);geo.computeVertexNormals();const m=new T.Mesh(geo,materials[material]);m.castShadow=true;parent.add(m);return m;}
  // Thin continuous curved ribs; orientation follows the actual twisted surface.
  function rib(a,from=0,to=1,w=.035){const count=64,pos=[],idx=[];for(let j=0;j<=count;j++){const t=from+(to-from)*j/count;const p=section(t,a),p2=section(t,a+.005);const v=p2.sub(p).normalize().multiplyScalar(w*shapeScale/2);pos.push(p.x-v.x,p.y,p.z-v.z,p.x+v.x,p.y,p.z+v.z);if(j<count){const k=j*2;idx.push(k,k+1,k+2,k+1,k+3,k+2);}}const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(pos,3));g.setIndex(idx);g.computeVertexNormals();const mesh=new T.Mesh(g,materials['Silver titanium']);architecture.add(mesh);}
  if(!options.coarse){
    for(let i=0;i<72;i++)rib(i/72*Math.PI*2);
    for(let floor=0;floor<=124;floor++){const t=floor/124,points=[];for(let a=0;a<=96;a++)points.push(section(t,a/96*Math.PI*2));ribbon(points,.04*scale,'Silver titanium');}
    for(let zone=1;zone<9;zone++){const t=zone/9;const points=[];for(let a=0;a<=96;a++)points.push(section(t,a/96*Math.PI*2,true));ribbon(points,.52*scale,'Dark mullions');}
  }
  const litPositions=[];
  if(!options.coarse){
    for(let floor=1;floor<123;floor++)for(let col=0;col<60;col++){
      const t=(floor+.5)/124,a=(col+.5)/60*Math.PI*2,p=section(t,a,true),theta=a+t*Math.PI*2/3,lit=rnd()<.18+(Math.sin(floor*.36)+1)*.08;
      if(lit){const width=2*Math.PI*6.1*(1-.51*t)/60*.75*shapeScale;box('Warm windows',p.x*1.008,p.y,p.z*1.008,width,.39*scale,.035*shapeScale,-theta-Math.PI/2,windows);litPositions.push({p:p.clone(),phase:rnd()*Math.PI*2});}
      if(col%3===0){box('Dark mullions',p.x*1.006,p.y,p.z*1.006,.024*shapeScale,.62*scale,.024*shapeScale,0,detail);}
    }
    for(let zone=1;zone<9;zone++){const t=zone/9;for(let i=0;i<9;i++){const a=i/9*Math.PI*2,p=section(t,a,true);sphere('Grass',p.x, p.y+.38*scale,p.z,.36*shapeScale,.35*scale,.36*shapeScale,detail);}const ring=[];for(let i=0;i<=96;i++)ring.push(section(t+.004,i/96*Math.PI*2,true));ribbon(ring,.07*scale,'Plaza luminaires',detail);}
  }
  // Open, asymmetric crown: no invented needle spire.
  const crownP=[],crownI=[];for(let j=0;j<=9;j++)for(let i=0;i<=96;i++){const a=i/96*Math.PI*2,p=section(1,a),v=j/9;const radius=1-.11*v;const top=(94.8+1.2*Math.cos(a-.4))*scale;crownP.push(p.x*radius,89.3*scale+(top-89.3*scale)*v,p.z*radius);if(j<9&&i<96){const k=j*97+i;crownI.push(k,k+97,k+1,k+97,k+98,k+1);}}
  const crownG=new T.BufferGeometry();crownG.setAttribute('position',new T.Float32BufferAttribute(crownP,3));crownG.setIndex(crownI);crownG.computeVertexNormals();const crown=new T.Mesh(crownG,materials['Outer glass']);crown.name='Asymmetric_Spiral_Crown';crown.renderOrder=4;architecture.add(crown);
  for(let i=0;i<36;i++){const a=i/36*Math.PI*2,p=section(1,a),top=(94.8+1.2*Math.cos(a-.4))*scale;box('Silver titanium',p.x*.95,(89.3*scale+top)/2,p.z*.95,.045*shapeScale,top-89.3*scale,.045*shapeScale);}
  const topPoints=[];for(let i=0;i<=96;i++){const a=i/96*Math.PI*2,p=section(1,a);p.multiplyScalar(.89);p.y=(94.8+1.2*Math.cos(a-.4))*scale;topPoints.push(p);}ribbon(topPoints,.09*scale,'Silver titanium');
  // Podium follows a gently rounded triangular plan.
  function roundedRect(w,d,r){const s=new T.Shape();s.moveTo(-w/2+r,-d/2);s.lineTo(w/2-r,-d/2);s.quadraticCurveTo(w/2,-d/2,w/2,-d/2+r);s.lineTo(w/2,d/2-r);s.quadraticCurveTo(w/2,d/2,w/2-r,d/2);s.lineTo(-w/2+r,d/2);s.quadraticCurveTo(-w/2,d/2,-w/2,d/2-r);s.lineTo(-w/2,-d/2+r);s.quadraticCurveTo(-w/2,-d/2,-w/2+r,-d/2);return s;}
  function podium(w,d,h,y,material,name){const g=new T.ExtrudeGeometry(roundedRect(w*siteScale,d*siteScale,5*siteScale),{depth:h*scale,bevelEnabled:true,bevelSize:.16*siteScale,bevelThickness:.10*scale,bevelSegments:2,curveSegments:12});g.rotateX(-Math.PI/2);const m=new T.Mesh(g,materials[material]);m.position.y=y*scale;m.name=name;m.castShadow=m.receiveShadow=true;architecture.add(m);return m;}
  podium(34,27,3.6,.25,'Inner glass','Glass_Podium');podium(35.5,28.5,.24,3.9,'Podium roof','Floating_Podium_Roof');podium(30,24,1,4.1,'Podium roof','Upper_Concourse');
  for(let i=-9;i<=9;i++){const x=i*1.45*siteScale;box('Dark mullions',x,2*scale,13.6*siteScale,.065*siteScale,3.5*scale,.09*siteScale);}
  box('Silver titanium',0,3.5*scale,15.2*siteScale,7.4*siteScale,.16*scale,4*siteScale);
  const door=new T.Group();door.name='Automatic_Entrance_Doors';door.position.set(0,0,13.68*siteScale);architecture.add(door);
  for(const side of [-1,1])box('Inner glass',side*.95*siteScale,1.65*scale,0,1.85*siteScale,2.9*scale,.06*siteScale,0,door);
  if(options.includeLandscape!==false){
    box('Pale stone',0,-.09,0,104*siteScale,.18,104*siteScale,0,landscape);
    for(let i=-8;i<=8;i++){box('Landscape metal',i*6*siteScale,.012,0,.022,.015,100*siteScale,0,landscape);box('Landscape metal',0,.013,i*6*siteScale,100*siteScale,.015,.022,0,landscape);}
    for(const r of [22,29,36]){const ring=new T.Mesh(new T.RingGeometry(r*siteScale-.04,r*siteScale+.04,128),materials['Landscape metal']);ring.rotation.x=-Math.PI/2;ring.position.y=.022;ring.name='Concentric_Paving_Joint';landscape.add(ring);}
    for(let i=0;i<16;i++){const a=i/16*Math.PI*2,x=Math.cos(a)*43*siteScale,z=Math.sin(a)*43*siteScale;if(z>33&&Math.abs(x)<15)continue;
      box('Landscape metal',x,.24,z,4.3*siteScale,.48,4.3*siteScale,0,landscape);box('Grass',x,.50,z,3.9*siteScale,.08,3.9*siteScale,0,landscape);instance('cylinder','Bark',x,2.2,z,.14,3.4,.14,0,landscape);
      for(let j=0;j<(options.coarse?7:150);j++){const angle=j*2.4,rr=options.coarse?1.1:Math.sqrt(rnd())*2.2;instance(options.coarse?'sphere':'leaf','Leaves',x+Math.sin(angle)*rr,4.8+rnd()*1.7-rr*rr*.14,z+Math.cos(angle)*rr,options.coarse?1.5:.36,options.coarse?.8:.12,options.coarse?1.4:.6,angle,landscape);}
      box('Wood',x*.88,.65,z*.88,3,.13,.7,a,landscape);box('Landscape metal',x*.88,.3,z*.88,2.5,.6,.4,a,landscape);
      box('Landscape metal',x+2.7,.48,z,.35,.95,.35,0,landscape);box('Plaza luminaires',x+2.7,.95,z,.32,.12,.32,0,landscape);
    }
    for(const x of [-9,9])for(let z=19;z<47;z+=5)box('Plaza luminaires',x*siteScale,.025,z*siteScale,.13,.025,.7,0,landscape);
    box('Landscape metal',-12*siteScale,.5,22*siteScale,5,.95,.4,0,landscape);
  }
  // Door thresholds, drainage slots, handles, glazing joints and roof equipment.
  if(!options.coarse){
    for(const x of [-3.8,3.8])box('Plaza luminaires',x*siteScale,3.35*scale,15*siteScale,.08,.08,3.4);
    for(const x of [-1.05,1.05])box('Silver titanium',x*siteScale,1.45*scale,13.8*siteScale,.035,.55*scale,.07);
    for(let i=-15;i<=15;i++)box('Dark mullions',i*1.1*siteScale,.045,18*siteScale,.35,.025,.06,0,landscape);
    for(let i=0;i<8;i++){const a=i/8*Math.PI*2,p=section(.999,a,true);box('Dark mullions',p.x*.72,89.5*scale,p.z*.72,1.2*shapeScale,.45*scale,.7*shapeScale,-a,detail);for(let j=0;j<5;j++)box('Silver titanium',p.x*.72+(j-2)*.18*shapeScale,89.74*scale,p.z*.72,.05*shapeScale,.025,.62*shapeScale,-a,detail);}
    if(typeof document!=='undefined'){const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=256;const ctx=canvas.getContext('2d');ctx.clearRect(0,0,1024,256);ctx.fillStyle='#e8d7b3';ctx.font='64px Microsoft YaHei';ctx.textAlign='center';ctx.fillText('上海中心',512,106);ctx.font='30px Georgia';ctx.fillText('SHANGHAI TOWER',512,174);const texture=new T.CanvasTexture(canvas);texture.colorSpace=T.SRGBColorSpace;const sign=new T.Mesh(new T.PlaneGeometry(5,.99),new T.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false}));sign.name='Shanghai_Tower_Entrance_Sign';sign.position.set(-12*siteScale,.63,22.22*siteScale);landscape.add(sign);}
  }
  function flush(){for(const b of batches.values()){const geometry=b.kind==='box'?unitBox:b.kind==='sphere'?unitSphere:b.kind==='leaf'?unitLeaf:unitCylinder;const mesh=new T.InstancedMesh(geometry,materials[b.material],b.matrices.length);mesh.name=b.material+' instances';b.matrices.forEach((matrix,i)=>mesh.setMatrixAt(i,matrix));mesh.castShadow=!['Warm windows','Plaza luminaires','Inner glass','Outer glass'].includes(b.material);mesh.receiveShadow=true;mesh.computeBoundingSphere();b.parent.add(mesh);}batches.clear();}
  flush();
  const people=[];
  for(let i=0;i<(options.coarse?0:18);i++){
    const person=new T.Group();person.name='Resident_'+i;const cloth=mat('Resident coat '+i,[0x667d90,0xb2a68d,0x819c9d,0x9b7a68][i%4]);const skin=mat('Resident skin '+i,0xc3a183);const body=new T.Mesh(unitBox,cloth);body.scale.set(.38,.62,.25);body.position.y=1.08;person.add(body);const head=new T.Mesh(unitSphere,skin);head.scale.set(.16,.2,.16);head.position.y=1.61;person.add(head);const legs=[];for(const x of [-.11,.11]){const leg=new T.Mesh(unitBox,materials['Dark mullions']);leg.scale.set(.13,.7,.16);leg.position.set(x,.42,0);person.add(leg);legs.push(leg);}const phase=i/18*Math.PI*2;people.push({group:person,legs,phase,radius:24+(i%4)*4.2,speed:.025+(i%3)*.006});residents.add(person);
  }
  const windShaders=[];
  materials.Leaves.onBeforeCompile=shader=>{shader.uniforms.uWind={value:0};windShaders.push(shader);shader.vertexShader='uniform float uWind;\n'+shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n#ifdef USE_INSTANCING\nfloat phase=instanceMatrix[3].x*.21+instanceMatrix[3].z*.37;transformed.x+=sin(uWind*1.3+phase)*.15*max(position.y+.5,0.);\n#endif');};
  const metadata={id:'shanghai-tower',name:'上海中心大厦',nominalHeight:632,displayHeight:height,displayScale:height/632,footprint,seed:options.seed??632,twistDegrees:120,units:'meters',upAxis:'Y',origin:'ground-center',version:'1.0.0',reference:'Architectural interpretation; not survey-grade BIM'};root.userData={...metadata};
  let disposed=false,night=.8,clock=0,windClock=0,lastWindowStep=-1,quality='high';const windowMesh=windows.children.find(o=>o.isInstancedMesh),windowColor=new T.Color();
  function update(dt,context={}){if(disposed)return;const paused=context.paused??false;if(!paused)clock=context.time??clock+Math.max(0,dt||0);night=context.nightFactor??night;materials['Warm windows'].emissiveIntensity=.08+night*1.0;materials['Plaza luminaires'].emissiveIntensity=.1+night*3;windows.visible=context.lights!==false;residents.visible=context.people!==false;
    detail.visible=quality!=='low'&&(context.cameraDistance??0)<(quality==='high'?300:190);
    if(!paused&&context.wind!==false)windClock+=Math.max(0,dt||0);for(const shader of windShaders)shader.uniforms.uWind.value=windClock;
    people.forEach((person,i)=>{const a=clock*person.speed+person.phase;person.group.position.set(Math.sin(a)*person.radius*siteScale,.03,Math.cos(a)*person.radius*siteScale);person.group.rotation.y=a+Math.PI/2;person.legs.forEach((leg,j)=>leg.rotation.x=Math.sin(clock*5+i+j*Math.PI)*.3);});
    const step=Math.floor(clock/18);if(windowMesh&&step!==lastWindowStep){lastWindowStep=step;for(let i=0;i<windowMesh.count;i++){const warm=(Math.sin(i*1.39+step*.03)+1)*.5;windowColor.setRGB(.72+warm*.28,.65+warm*.15,.45+warm*.2);windowMesh.setColorAt(i,windowColor);}if(windowMesh.instanceColor)windowMesh.instanceColor.needsUpdate=true;}
    const nearEntrance=people.some(p=>Math.abs(p.group.position.x)<5&&p.group.position.z>18&&p.group.position.z<25),open=nearEntrance?1:0;
    door.children.forEach((object,index)=>object.position.x+=( (index===0?-1:1)*(.95+open*.8)*siteScale-object.position.x)*Math.min(1,(paused?0:Math.max(0,dt||0))*3));
  }
  function setQuality(q='high'){quality=q;detail.visible=q!=='low';materials['Outer glass'].opacity=q==='low'?.2:.24;metadata.quality=q;}
  function getBounds(){root.updateWorldMatrix(true,true);return new T.Box3().setFromObject(root);}
  function dispose(){if(disposed)return;disposed=true;const gs=new Set([unitBox,unitSphere,unitCylinder,unitLeaf]),ms=new Set(Object.values(materials)),ts=new Set();root.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material])ms.add(m);});for(const g of gs)g.dispose();for(const m of ms){for(const [key,v] of Object.entries(m))if(key!=='envMap'&&v?.isTexture)ts.add(v);m.dispose();}for(const t of ts)t.dispose();root.removeFromParent();}
  setQuality(options.quality??'high');
  return {model:root,metadata,update,setQuality,getBounds,dispose,materials,parts:{architecture,landscape,windows,residents,detail,door},section};
}
