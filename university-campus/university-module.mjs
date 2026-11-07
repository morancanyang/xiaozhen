/** Qianren university campus. No renderer, lights or animation loop is owned here. */
export function createUniversityCampus(options={}){
  const T=options.THREE;if(!T?.Group)throw new Error('请传入宿主 THREE');
  const footprint=options.footprint??112;if(!Number.isFinite(footprint)||footprint<56)throw new Error('footprint 至少为 56 米');
  const coarse=!!options.coarse,includeLandscape=options.includeLandscape!==false;
  const model=new T.Group();model.name='University_Main_Teaching_Building';
  const parts={};for(const name of ['architecture','landscape','detail','flags','lighting']){parts[name]=new T.Group();parts[name].name=name;model.add(parts[name]);}
  const {architecture,landscape,detail,flags,lighting}=parts,materials={},geometries=new Set(),textures=new Set(),batches=new Map(),cloth=[],trees=[],localLights=[];
  let simTime=0,windTime=0,quality=options.quality??'high',night=0,disposed=false;
  let seed=options.seed??2026;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const own=g=>(geometries.add(g),g);
  const mat=(name,color,roughness=.7,metalness=0,extra={})=>{const {physical,...rest}=extra;const Material=physical?T.MeshPhysicalMaterial:T.MeshStandardMaterial;const m=new Material({name,color,roughness,metalness,...rest});materials[name]=m;return m;};
  function canvasTexture(w,h,paint){if(typeof document==='undefined')return null;const c=document.createElement('canvas');c.width=w;c.height=h;paint(c.getContext('2d'),w,h);const tx=new T.CanvasTexture(c);tx.colorSpace=T.SRGBColorSpace;tx.anisotropy=4;textures.add(tx);return tx;}
  const concreteMap=canvasTexture(256,256,(c,w,h)=>{c.fillStyle='#e8e9e6';c.fillRect(0,0,w,h);for(let i=0;i<18000;i++){const k=Math.floor(192+random()*60);c.fillStyle=`rgba(${k},${k},${k},.20)`;c.fillRect(random()*w,random()*h,1+random(),1);}});
  const concrete=mat('Light grey architectural concrete',0xc8cbc9,.91,0,{map:concreteMap}),edge=mat('Precast edge and sill',0xd9dcd8,.81),joint=mat('Recessed concrete joint',0x7d898a,.92),stone=mat('Fine grey granite',0xb6bdbb,.86),paving=mat('Grey plaza paving',0xb9beba,.92),paving2=mat('Alternate paving',0xc3c7c1,.92),grout=mat('Paving joints',0x8d9693,.95),roof=mat('Roof membrane',0x8d9999,.95),metal=mat('Silver anodised aluminium',0xaab8bc,.3,.8),dark=mat('Dark window reveal',0x30454d,.68,.25),glass=mat('Blue grey glazing',0x7e98a5,.16,.24,{physical:true,clearcoat:1,clearcoatRoughness:.12,ior:1.46}),glassAlt=mat('Openable window glass',0x94a8af,.21,.23,{physical:true,clearcoat:.8,clearcoatRoughness:.16,ior:1.46}),interior=mat('Classroom interior',0xadb1a8,.9),grass=mat('Trimmed lawn',0x6e855a,.96),soil=mat('Planting soil',0x514f41,.99),bark=mat('Tree bark',0x746951,.96),leaf=mat('Campus leaves',0x6b835a,.9),wood=mat('Bench timber',0x9d8970,.87),glow=mat('Warm architectural light',0xffe7b6,.45,0,{emissive:0xffce87,emissiveIntensity:.05}),curtain=mat('Classroom curtains',0xc6c5b7,.98);
  const boxGeo=own(new T.BoxGeometry(1,1,1)),cylGeo=own(new T.CylinderGeometry(1,1,1,12)),leafGeo=own(new T.IcosahedronGeometry(1,1)),dummy=new T.Object3D();
  function instance(g,m,x,y,z,sx,sy,sz,parent=architecture,ry=0){const key=g.uuid+m.uuid+parent.uuid;if(!batches.has(key))batches.set(key,{g,m,parent,items:[]});dummy.position.set(x,y,z);dummy.rotation.set(0,ry,0);dummy.scale.set(sx,sy,sz);dummy.updateMatrix();batches.get(key).items.push(dummy.matrix.clone());}
  const box=(m,x,y,z,w,h,d,p=architecture,ry=0)=>instance(boxGeo,m,x,y,z,w,h,d,p,ry);
  const cylinder=(m,x,y,z,r,h,p=architecture)=>instance(cylGeo,m,x,y,z,r,h,r,p);
  function rod(m,a,b,r,parent=detail){const start=new T.Vector3(...a),end=new T.Vector3(...b),delta=end.clone().sub(start),key=cylGeo.uuid+m.uuid+parent.uuid;if(!batches.has(key))batches.set(key,{g:cylGeo,m,parent,items:[]});dummy.position.copy(start).add(end).multiplyScalar(.5);dummy.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),delta.clone().normalize());dummy.scale.set(r,delta.length(),r);dummy.updateMatrix();batches.get(key).items.push(dummy.matrix.clone());}
  const rubber=mat('Window EPDM gasket',0x2d3538,.94),brushed=mat('Brushed stainless fittings',0xb9c1c1,.25,.86),cutGrass=mat('Individual cut grass blades',0x718753,.96,0,{side:T.DoubleSide});
  function mesh(g,m,name,parent=architecture){const o=new T.Mesh(own(g),m);o.name=name;o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
  // First-pass masses remain available with ?coarse; detailed facade is added below.
  function block(name,x,z,w,d,floors){const height=floors*3.7+.8;box(concrete,x,.7+height/2,z,coarse?w:w-1.3,height,coarse?d:d-1.3);box(stone,x,.4,z,w+.5,.8,d+.5);box(roof,x,height+.75,z,w-.5,.12,d-.5);
    for(const s of [-1,1]){box(edge,x,height+1.1,z+s*d/2,w+.2,.7,.24);box(edge,x+s*w/2,height+1.1,z,.24,.7,d);}
    if(coarse)return;
    function facade(width,depth,angle){const count=Math.floor((width-3)/3.45),span=(count-1)*3.45+2.35;
      const panel=(u,y,pw,ph)=>{const c=Math.cos(angle),sn=Math.sin(angle);box(concrete,x+u*c+depth*sn,y,z-u*sn+depth*c,pw,ph,.65,architecture,angle);};
      for(let f=0;f<floors;f++){const y=2.65+f*3.7;panel(0,y-1.85,width,1.65);for(let i=0;i<count-1;i++)panel((i-(count-2)/2)*3.45,y,1.10,2.05);const end=(width-span)/2;for(const side of [-1,1])panel(side*(width/2-end/2),y,end,2.05);}
      panel(0,height+.2,width,1.8);
    }
    facade(w,d/2-.325,0);facade(w,d/2-.325,Math.PI);facade(d,w/2-.325,Math.PI/2);facade(d,w/2-.325,-Math.PI/2);
    for(let f=0;f<floors;f++){const y=2.65+f*3.7;for(const face of [-1,1]){const count=Math.floor((w-3)/3.45);for(let i=0;i<count;i++)window(x+(i-(count-1)/2)*3.45,y,z+face*(d/2+.014),2.35,2.05,face===1?0:Math.PI);}
      for(const side of [-1,1])for(let j=0;j<Math.floor((d-3)/3.45);j++)window(x+side*(w/2+.014),y,z+(j-(Math.floor((d-3)/3.45)-1)/2)*3.45,2.35,2.05,side*Math.PI/2);
      for(const s of [-1,1])box(edge,x,4.1+f*3.7,z+s*(d/2+.04),w+.16,.11,.24,detail);
    }
    for(let i=0;i<Math.floor(w/7);i++)for(const s of [-1,1])box(joint,x-w/2+3.5+i*7,height/2+.8,z+s*(d/2+.006),.025,height-.3,.02,detail);
    for(const s of [-1,1]){cylinder(metal,x+s*(w/2-.3),height/2+.4,z-d/2-.18,.07,height,detail);box(joint,x+s*(w/2-.3),height+1,z-d/2,.3,.08,.4,detail);}
    for(let i=0;i<Math.floor(w/16);i++){box(metal,x-w/2+9+i*16,height+1.25,z,3.4,1.1,2.1,detail);for(let j=-3;j<=3;j++)box(dark,x-w/2+9+i*16,height+1.82,z+j*.24,2.8,.025,.06,detail);for(const face of [-1,1])for(let slat=0;slat<6;slat++)box(dark,x-w/2+9+i*16,height+.85+slat*.14,z+face*1.06,2.85,.055,.035,detail);box(stone,x-w/2+9+i*16,height+.75,z,3.6,.12,2.3,detail);}
  }
  function window(x,y,z,w,h,angle){const local=(m,xx,yy,zz,ww,hh,dd,p=architecture)=>{const c=Math.cos(angle),s=Math.sin(angle);box(m,x+xx*c+zz*s,y+yy,z-xx*s+zz*c,ww,hh,dd,p,angle);};
    local(dark,0,0,-.35,w+.28,h+.3,.09);local(random()<.16?glassAlt:glass,0,0,-.235,w,h,.045);local(interior,0,-h*.42,-.29,w*.9,.045,.18,detail);
    for(const s of [-1,1]){local(metal,s*(w/2+.035),0,-.17,.075,h+.17,.09,detail);local(metal,0,s*(h/2+.035),-.17,w+.14,.075,.09,detail);}
    local(metal,0,0,-.15,.055,h,.09,detail);local(metal,0,.29,-.15,w,.045,.09,detail);local(edge,0,-h/2-.14,.11,w+.38,.12,.42,detail);
    for(const s of [-1,1]){local(rubber,s*(w/2-.025),0,-.211,.018,h,.015,detail);local(rubber,0,s*(h/2-.025),-.211,w,.018,.015,detail);local(edge,s*(w/2+.1),0,-.10,.14,h+.14,.40,detail);}
    // Separate sill drip groove and frame drainage slots, visible in close views.
    local(joint,0,-h/2-.205,.23,w+.12,.014,.022,detail);
    for(const s of [-1,1])local(dark,s*w*.32,-h/2+.035,-.12,.09,.02,.02,detail);
    if(random()<.18)local(curtain,w*.28,0,-.21,w*.3,h-.1,.015,detail);
    if(random()<.17)local(glow,-w*.23,.02,-.205,w*.42,h*.8,.012,lighting);
    if(random()<.1)local(metal,w*.33,-.05,-.09,.13,.035,.045,detail);
  }
  block('Main seven-storey bar',0,-32,86,16,7);block('West five-storey wing',-35,-9,16,30,5);block('East five-storey wing',35,-9,16,30,5);
  // Recessed central hall, columns and a continuous accessible entrance platform.
  box(dark,0,14.2,-22.9,17,27.3,2.5);box(glass,0,14.2,-21.58,15.6,26.7,.09);
  for(let i=-4;i<=4;i++)box(metal,i*1.85,14.2,-21.46,.065,26.7,.08,detail);
  for(let i=0;i<=7;i++)box(metal,0,1.3+i*3.7,-21.43,15.6,.07,.09,detail);
  box(edge,0,28.15,-23,19,.65,4.3);box(edge,0,5.15,-17.5,24,.45,9.4);
  for(const x of [-10.5,10.5])box(concrete,x,2.9,-14.8,.5,4.7,.5);
  box(interior,0,2.6,-22.4,11,4.2,.15);for(let i=-2;i<=2;i++){box(glass,i*1.6,2.5,-21.28,1.52,3.5,.055);box(metal,i*1.6+.78,2.5,-21.2,.05,3.6,.075,detail);box(metal,i*1.6+.57,2.4,-21.13,.025,.55,.035,detail);}
  box(stone,0,.65,-17.5,26,1.3,11);for(let i=0;i<6;i++)box(stone,0,(6-i)*.1,-11.85+i*.42,26,(6-i)*.2,.44);
  const ramp=mesh(new T.BoxGeometry(4,.16,14),stone,'Accessible_entrance_ramp');ramp.position.set(15,.65,-14);ramp.rotation.x=Math.atan(1.2/14);
  const rampSurface=z=>.73-(z+14)*1.2/14;
  for(const x of [13.1,16.9]){
    for(const level of [.55,.95])rod(brushed,[x,rampSurface(-20.7)+level,-20.7],[x,rampSurface(-7.2)+level,-7.2],.026);
    for(const z of [-20.7,-16.2,-11.7,-7.2]){const y=rampSurface(z);cylinder(brushed,x,y+.47,z,.025,.94,detail);cylinder(brushed,x,y+.025,z,.085,.05,detail);for(const s of [-1,1])cylinder(metal,x+s*.05,y+.055,z,.012,.014,detail);}
  }
  if(!coarse){
    const signMap=canvasTexture(2048,256,(c,w,h)=>{c.clearRect(0,0,w,h);c.fillStyle='#34413e';c.font='600 155px "Microsoft YaHei"';c.textAlign='center';c.textBaseline='middle';c.fillText('大学主教学楼',w/2,h*.54);});
    box(edge,0,6.6,-21.18,11.4,1.65,.14,detail);
    if(signMap){const sm=mat('Teaching building inscription',0xffffff,.48,.25,{map:signMap,transparent:true,depthWrite:false,side:T.DoubleSide});const sign=mesh(new T.PlaneGeometry(10.3,1.29),sm,'Building_inscription');sign.position.set(0,6.6,-21.098);}
    for(const x of [-5.4,5.4])for(const y of [6.0,7.2]){const screw=mesh(new T.SphereGeometry(.025,8,6),brushed,'Sign_standoff_fixing',detail);screw.position.set(x,y,-21.07);}
    for(let step=0;step<6;step++){
      const top=(6-step)*.2,z=-11.85+step*.42;
      for(let line=0;line<3;line++)box(joint,0,top+.003,z+.10+line*.025,25.7,.009,.012,detail);
      for(let x=-11;x<=11;x+=2)box(joint,x,top+.004,z,.012,.009,.38,detail);
    }
    for(const x of [-10.5,10.5]){box(stone,x,.11,-14.8,.8,.22,.8,detail);box(brushed,x,4.85,-14.8,.65,.12,.65,detail);}
    for(const x of [-7,0,7])box(glow,x,4.90,-17.7,3.2,.035,.11,lighting);
    // Corridor shades, expansion joints and tactile paving.
    for(const side of [-1,1])for(let i=0;i<11;i++)box(edge,side*35,20.15,-23+i*2.65,16.6,.13,.11,detail);
    for(const x of [17.8,18.05,18.3])box(edge,x,.035,-4,.08,.035,13,detail);
  }
  if(includeLandscape){
    box(grout,0,-.15,0,110,.3,110,landscape);
    // Large clean, individually jointed granite slabs, instanced by material.
    if(coarse)box(paving,0,.005,0,109,.02,109,landscape);
    else for(let x=-53;x<=53;x+=2)for(let z=-53;z<=53;z+=2)box(random()>.24?paving:paving2,x,.006,z,1.975,.028,1.975,landscape);
    for(const x of [-45.5,45.5])for(const z of [19,40]){box(stone,x,.16,z,13,.32,16,landscape);box(soil,x,.33,z,12.4,.05,15.4,landscape);box(grass,x,.39,z,12,.1,15,landscape);}
    for(const x of [-19,19]){box(stone,x,.15,-6,10,.3,14,landscape);box(grass,x,.34,-6,9.5,.09,13.5,landscape);}
    for(const z of [-51,51])box(stone,0,.08,z,108,.16,.25,landscape);for(const x of [-54,54])box(stone,x,.08,0,.25,.16,108,landscape);
    for(const x of [-30,30])box(grout,x,.032,28,.18,.015,40,detail);
    for(const x of [-30,30])for(let z=8;z<48;z+=.45)box(metal,x,.05,z,.16,.025,.045,detail);
    // Flag platform: three granite steps, centred on the hall axis.
    for(let i=0;i<3;i++)box(stone,0,.15+i*.3,27,8.4-i*.9,.3,6.4-i*.9,landscape);
    cylinder(metal,0,1.05,27,.27,.3,landscape);cylinder(metal,0,8.8,27,.085,15.4,landscape);
    const cap=mesh(new T.SphereGeometry(.15,12,8),metal,'Silver_flagpole_finial',landscape);cap.position.set(0,16.58,27);
    cylinder(metal,-.12,8.7,27,.009,15.1,detail);for(const x of [-.22,.22])for(const z of [26.78,27.22])cylinder(metal,x,1.22,z,.035,.06,detail);
  }
  function star(c,x,y,r,tip){c.beginPath();for(let i=0;i<10;i++){const a=tip+i*Math.PI/5,rr=i%2?r*.382:r;c.lineTo(x+Math.cos(a)*rr,y+Math.sin(a)*rr);}c.closePath();c.fill();}
  const flagMap=canvasTexture(1800,1200,(c,w,h)=>{c.scale(2,2);c.fillStyle='#de2910';c.fillRect(0,0,900,600);c.fillStyle='#ffde00';star(c,150,150,90,-Math.PI/2);for(const [x,y]of [[300,60],[360,120],[360,210],[300,270]])star(c,x,y,30,Math.atan2(150-y,150-x));c.strokeStyle='#bb2612';c.lineWidth=1.2;c.strokeRect(5,5,890,590);c.setLineDash([2,3]);c.lineWidth=.7;c.strokeRect(9,9,882,582);});
  const fabric=canvasTexture(32,32,(c,w,h)=>{c.fillStyle='#999';c.fillRect(0,0,w,h);c.strokeStyle='#888';c.lineWidth=1;for(let i=0;i<32;i+=4){c.beginPath();c.moveTo(i,0);c.lineTo(i,32);c.moveTo(0,i);c.lineTo(32,i);c.stroke();}});if(fabric){fabric.colorSpace=T.NoColorSpace;fabric.wrapS=fabric.wrapT=T.RepeatWrapping;fabric.repeat.set(28,20);}
  const red=mat('National flag red silk',0xffffff,.86,0,{map:flagMap,bumpMap:fabric,bumpScale:.012,side:T.DoubleSide});
  const smallRed=mat('Small red flag cloth',0xde2910,.88,0,{side:T.DoubleSide});
  function flag(name,x,y,z,w,h,national=false,index=0){const nx=coarse?12:national?42:20,ny=coarse?8:national?28:12;const g=new T.PlaneGeometry(w,h,nx,ny),p=g.attributes.position;for(let i=0;i<p.count;i++){p.setX(i,p.getX(i)+w/2);p.setY(i,p.getY(i)-h/2);}const o=mesh(g,national?red:smallRed,name,flags);o.position.set(x,y,z);o.rotation.y=-.24;cloth.push({mesh:o,w,h,base:p.array.slice(),phase:index*.79,national});return o;}
  if(includeLandscape){flag('Five_star_national_flag',.09,16.15,27,4.5,3,true);
    for(const x of [-29,29])for(let i=0;i<5;i++){const z=8+i*8.7;cylinder(metal,x,2.7,z,.035,5.4,landscape);flag('Small_red_flag_'+x+'_'+i,x+.04,5.3,z,1.6,1.07,false,i+(x<0?0:5));}
    for(const x of [-49,49])for(const z of [11,31,48]){cylinder(dark,x,3.1,z,.055,6.2,landscape);box(metal,x,6.2,z,1.25,.13,.5,landscape);box(glow,x,6.11,z,.95,.035,.3,lighting);}
    if(!coarse)for(const x of [-46,46])for(const z of [-46,19,40]){cylinder(bark,x,1.8,z,.16,3.6,landscape);const crown=new T.Group();crown.position.set(x,3.9,z);crown.name='Wind_swaying_campus_tree';landscape.add(crown);for(let branch=0;branch<5;branch++){const a=branch*2.4;rod(bark,[0,-.55,0],[Math.sin(a)*1.25,1+random()*.5,Math.cos(a)*1.25],.065,crown);}for(let i=0;i<240;i++){const a=i*2.4,r=Math.sqrt(random())*2.05,h=.2+random()*1.9-r*r*.11;instance(leafGeo,leaf,Math.cos(a)*r,h,Math.sin(a)*r,.37+random()*.16,.14+random()*.12,.35+random()*.18,crown,a);}trees.push({crown,phase:random()*6});}
    if(!coarse){
      const blade=own(new T.BufferGeometry());blade.setAttribute('position',new T.Float32BufferAttribute([-.035,0,0,.035,0,0,.013,.12,.025,0,0,-.035,0,0,.035,.025,.10,.006],3));blade.computeVertexNormals();
      for(const x of [-45.5,45.5])for(const z of [19,40])for(let i=0;i<1600;i++)instance(blade,cutGrass,x+(random()-.5)*11.8,.44,z+(random()-.5)*14.8,.7+random()*.6,.5+random()*.4,.8+random()*.4,detail,random()*6.28);
      for(const x of [-19,19])for(let i=0;i<1000;i++)instance(blade,cutGrass,x+(random()-.5)*9.3,.385,-6+(random()-.5)*13.3,.7+random()*.6,.5+random()*.4,.8+random()*.4,detail,random()*6.28);
      box(brushed,0,.96,27,.63,.10,.63,detail);cylinder(brushed,-.13,1.7,27.1,.032,.42,detail);
      for(const z of [27.095,27.13])rod(metal,[-.115,1.55,z],[-.115,16.30,z],.008);
      for(const x of [-49,49])for(const z of [11,31,48]){cylinder(brushed,x,.06,z,.16,.12,detail);for(const sx of [-1,1])for(const sz of [-1,1])cylinder(brushed,x+sx*.09,.13,z+sz*.09,.016,.028,detail);}
      const ringGeo=own(new T.TorusGeometry(.035,.008,6,12));const national=cloth.find(f=>f.national)?.mesh;if(national)for(const y of [-.10,-1.5,-2.9]){const ring=mesh(ringGeo,brushed,'Flag_hoist_eyelet',national);ring.position.set(.025,y,.014);}
    }
  }
  if(includeLandscape){
    for(const x of [-49,49])for(const z of [11,31,48]){const lamp=new T.PointLight(0xffdeb2,0,19,2);lamp.name='Campus_lamppost_light';lamp.position.set(x,5.95,z);lighting.add(lamp);localLights.push({light:lamp,power:70});}
    for(const x of [-7,7]){const lamp=new T.PointLight(0xffd7a0,0,24,2);lamp.name='Entrance_canopy_light';lamp.position.set(x,4.3,-16.5);lighting.add(lamp);localLights.push({light:lamp,power:95});}
    const flagLight=new T.SpotLight(0xffe1ba,0,36,.29,.65,2);flagLight.name='Flag_ceremony_uplight';flagLight.position.set(0,1,33);flagLight.target.position.set(1.8,15,27);lighting.add(flagLight,flagLight.target);localLights.push({light:flagLight,power:180});
  }
  for(const {g,m,parent,items}of batches.values()){const o=new T.InstancedMesh(g,m,items.length);o.name=m.name+'_instances';items.forEach((v,i)=>o.setMatrixAt(i,v));o.castShadow=![paving,paving2,grout,glow].includes(m);o.receiveShadow=true;o.computeBoundingSphere();parent.add(o);}batches.clear();
  model.scale.setScalar(footprint/112);
  const metadata={id:'university-campus',name:'大学主教学楼',version:'1.1.0',footprint:[footprint,footprint],units:'metres',upAxis:'Y',origin:'parcel-ground-centre',displayHeight:28.5325*footprint/112,floors:7,sideWingFloors:5,containsRoads:false,proceduralAnimations:true,flagCount:includeLandscape?11:0};model.userData.landmark=metadata;
  function setQuality(v){if(!['low','medium','high'].includes(v))throw new Error('quality: low / medium / high');quality=v;detail.visible=v!=='low';return quality;}
  function setTimeOfDay(v){night=T.MathUtils.clamp(typeof v==='number'?v:({morning:0,sunset:.55,night:1}[v]??0),0,1);}
  function update(dt=0,context={}){if(disposed)return;const elapsed=context.paused?0:Math.max(0,Math.min(Number.isFinite(dt)?dt:0,.25));simTime+=elapsed;if(context.wind!==false)windTime+=elapsed*(.5+T.MathUtils.clamp(context.windStrength??.6,0,1));if(Number.isFinite(context.nightFactor))setTimeOfDay(context.nightFactor);const strength=context.wind===false?0:T.MathUtils.clamp(context.windStrength??.6,0,1),t=windTime;
    flags.visible=context.flags!==false;
    for(const f of cloth){const p=f.mesh.geometry.attributes.position;for(let i=0;i<p.count;i++){const u=f.base[i*3]/f.w,v=-f.base[i*3+1]/f.h;const wave=Math.sin(u*7.1-t*3.2+f.phase+v*.7)*.6+Math.sin(u*15.5-t*5.2+v*4.5+f.phase)*.16;p.array[i*3]=u*f.w*(.95-.04*(1-strength))+.04*Math.sin(t*2+v*3)*u*strength;p.array[i*3+1]=-v*f.h-.13*u*u*(1-strength)+Math.sin(u*8.2-t*3.1+f.phase)*u*.075*strength;p.array[i*3+2]=wave*u*f.w*.16*(.28+strength*.72);}p.needsUpdate=true;f.mesh.geometry.computeVertexNormals();f.mesh.geometry.computeBoundingSphere();}
    for(const tree of trees){tree.crown.rotation.z=Math.sin(t*.8+tree.phase)*.018*strength;tree.crown.rotation.x=Math.cos(t*.65+tree.phase)*.012*strength;}
    const enabled=context.lights!==false;lighting.visible=enabled;glow.emissiveIntensity=enabled?.02+night*2.8:0;for(const l of localLights)l.light.intensity=enabled?night*l.power:0;detail.visible=quality!=='low'&&(!context.cameraDistance||context.cameraDistance<(quality==='high'?450:260));
  }
  function getBounds(){model.updateMatrixWorld(true);return new T.Box3().setFromObject(model);}
  function dispose(){if(disposed)return;disposed=true;model.removeFromParent();model.traverse(o=>{if(o.isInstancedMesh)o.dispose();});geometries.forEach(g=>g.dispose());Object.values(materials).forEach(m=>m.dispose());textures.forEach(t=>t.dispose());}
  setQuality(quality);update(0);
  return {model,metadata,parts,materials,update,setQuality,setTimeOfDay,getBounds,dispose,get time(){return simTime;},get quality(){return quality;},get flags(){return cloth.map(f=>f.mesh);}};
}
