/** Independent, metre-based commercial parcel. Host owns the render loop and THREE. */
export function createMallComplex({THREE:T,footprint=112,quality='high',seed=2026,includeLandscape=true,coarse=false}={}){
  if(!T?.Group)throw new Error('请传入宿主 THREE 命名空间');
  if(!Number.isFinite(footprint)||footprint<=0)throw new Error('footprint 必须为正数');
  const model=new T.Group();model.name='Taoli_Galleria_112m';
  const architecture=new T.Group(),landscape=new T.Group(),detail=new T.Group(),people=new T.Group(),lighting=new T.Group();
  architecture.name='Architecture';landscape.name='Landscape';detail.name='Construction_Detail';people.name='Visitors';lighting.name='Architectural_Lighting';model.add(architecture,landscape,detail,people,lighting);
  const ownedG=new Set(),ownedM=new Set(),ownedTex=new Set(),batches=new Map(),boxGeo=own(new T.BoxGeometry(1,1,1)),cylinderGeo=own(new T.CylinderGeometry(1,1,1,12)),sphereGeo=own(new T.SphereGeometry(1,10,7));
  let rng=seed>>>0,simTime=0,disposed=false,activeQuality=quality,currentNight=0,lightsEnabled=true;
  const random=()=>((rng=(Math.imul(rng,1664525)+1013904223)>>>0)/4294967296),materials={};
  function own(g){ownedG.add(g);return g;}
  function mat(name,color,roughness=.65,metalness=0,more={}){const m=new T.MeshStandardMaterial({name,color,roughness,metalness,...more});ownedM.add(m);materials[name]=m;return m;}
  function texture(kind){const c=document.createElement('canvas');c.width=c.height=256;const ctx=c.getContext('2d');ctx.fillStyle=kind==='stone'?'#ddd9d3':'#eee8e1';ctx.fillRect(0,0,256,256);for(let i=0;i<14000;i++){const a=random()*.095;ctx.fillStyle=`rgba(${kind==='stone'?'76,64,54':'90,66,43'},${a})`;ctx.fillRect(random()*256,random()*256,random()*2.4+.4,random()*1.2+.3);}if(kind==='clay'){for(let i=0;i<90;i++){ctx.fillStyle='rgba(92,55,37,.025)';ctx.fillRect(0,i*3,256,.6);}}const t=new T.CanvasTexture(c);t.colorSpace=T.SRGBColorSpace;t.wrapS=t.wrapT=T.RepeatWrapping;t.anisotropy=4;ownedTex.add(t);return t;}
  const clayMap=coarse?null:texture('clay'),stoneMap=coarse?null:texture('stone');
  const clay=[mat('Terracotta warm',0x9a4f39,.82,0,{map:clayMap}),mat('Terracotta muted',0x894630,.84,0,{map:clayMap}),mat('Terracotta pale',0xa96045,.79,0,{map:clayMap}),mat('Terracotta ochre',0x945238,.83,0,{map:clayMap})];
  const stone=mat('Red brown limestone',0x9e7760,.78,0,{map:stoneMap}),pale=mat('Warm limestone coping',0xd3c5b0,.72,0,{map:stoneMap}),paving=mat('Silver grey granite',0xc9c8c0,.84,0,{map:stoneMap}),grout=mat('Paving joints',0xa6a79f,.9),bronze=mat('Coffee aluminium',0x3e302a,.34,.76),brass=mat('Brushed champagne brass',0xb89b6f,.32,.74),dark=mat('Deep interior',0x302923,.85),floor=mat('Interior terrazzo',0xd4c4aa,.57),wood=mat('Oiled oak',0x806044,.75),soil=mat('Planting soil',0x484333,.95),grass=mat('Low planting',0x707b52,.96),bark=mat('Tree bark',0x675348,.95),seat=mat('Cafe fabric',0xb4a48c,.91),leafM=[mat('Leaf sage',0x6f805b,.95),mat('Leaf olive',0x829265,.95),mat('Leaf bright',0x96a074,.95)];
  const glass=new T.MeshPhysicalMaterial({name:'Shop glazing',color:0x9eb9b8,roughness:.10,metalness:.12,transmission:.72,thickness:.08,ior:1.46,transparent:true,opacity:.91,envMapIntensity:.75});ownedM.add(glass);materials[glass.name]=glass;
  const roofGlass=new T.MeshPhysicalMaterial({name:'Atrium skylight',color:0xb1c9c9,roughness:.17,metalness:.22,transmission:.42,thickness:.14,ior:1.46,transparent:true,opacity:.72,side:T.DoubleSide});ownedM.add(roofGlass);materials[roofGlass.name]=roofGlass;
  const water=new T.MeshPhysicalMaterial({name:'Reflecting water',color:0x749995,roughness:.17,metalness:.3,transparent:true,opacity:.83});ownedM.add(water);materials[water.name]=water;
  const glow=mat('Warm architectural light',0xffdab0,.45,0,{emissive:0xffad5b,emissiveIntensity:.6}),shopGlow=mat('Shop ceiling warm light',0xffe3b9,.75,0,{emissive:0xffc17f,emissiveIntensity:.45}),jetMat=mat('Fountain water',0xb9d9d5,.22,.12,{transparent:true,opacity:.65});
  const litMaterials=[glow,shopGlow];
  if(!coarse){for(const m of [...clay,stone,pale,paving]){const bump=m.map.clone();bump.colorSpace=T.NoColorSpace;bump.needsUpdate=true;ownedTex.add(bump);m.bumpMap=bump;m.bumpScale=m===stone?.025:.014;}const ptex=stoneMap.clone();ptex.repeat.set(40,40);ptex.needsUpdate=true;ownedTex.add(ptex);paving.map=ptex;}
  const localLights=[];
  if(!coarse){for(const p of [[-27,3.7,20],[27,3.7,24],[0,9,20],[0,19,-5]]){const light=new T.PointLight(0xffbf7c,38,22,2);light.name='Warm_commercial_interior';light.position.set(...p);lighting.add(light);localLights.push(light);}}
  function batch(g,m,parent=architecture){const key=g.uuid+'|'+m.uuid+'|'+parent.uuid;if(!batches.has(key))batches.set(key,{g,m,parent,items:[]});return batches.get(key).items;}
  const dummy=new T.Object3D();
  function primitive(g,m,p,s,r=[0,0,0],parent=architecture){dummy.position.set(...p);dummy.rotation.set(...r);dummy.scale.set(...s);dummy.updateMatrix();batch(g,m,parent).push(dummy.matrix.clone());}
  function box(m,x,y,z,w,h,d,parent=architecture,ry=0){primitive(boxGeo,m,[x,y,z],[w,h,d],[0,ry,0],parent);}
  function cylinder(m,x,y,z,r,h,parent=landscape){primitive(cylinderGeo,m,[x,y,z],[r,h,r],[0,0,0],parent);}
  function ball(m,x,y,z,r,parent=landscape,squash=1){primitive(sphereGeo,m,[x,y,z],[r,r*squash,r],[0,0,0],parent);}
  function rail(x0,z0,x1,z1,y,parent=detail){const len=Math.hypot(x1-x0,z1-z0),a=Math.atan2(x1-x0,z1-z0);box(bronze,(x0+x1)/2,y+1.07,(z0+z1)/2,.055,.065,len,parent,a);box(glass,(x0+x1)/2,y+.55,(z0+z1)/2,.035,.95,len,parent,a);for(let t=0;t<=len;t+=2.2){const u=t/len;box(bronze,x0+(x1-x0)*u,y+.55,z0+(z1-z0)*u,.055,1.1,.055,parent);}}
  function label(text,w,h,bg='#332a25',fg='#f4e9d6',font=70,name='Sign',parent=detail){const c=document.createElement('canvas');c.width=1024;c.height=Math.max(128,Math.round(1024*h/w));const ctx=c.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=fg;ctx.font=`${font}px "Microsoft YaHei",sans-serif`;ctx.fillText(text,512,c.height*.51,940);const tex=new T.CanvasTexture(c);tex.colorSpace=T.SRGBColorSpace;ownedTex.add(tex);const m=mat(name+' material',0xffffff,.7,0,{map:tex,emissive:0xffffff,emissiveMap:tex,emissiveIntensity:.09});litMaterials.push(m);const mesh=new T.Mesh(own(new T.PlaneGeometry(w,h)),m);mesh.name=name;parent.add(mesh);return mesh;}
  function mesh(g,m,name,parent=architecture){const o=new T.Mesh(own(g),m);o.name=name;o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
  box(paving,0,-.09,0,111.6,.18,111.6,landscape);
  const floors=[{y:0,h:5.4,x0:-40,x1:40,b:-38,l:25,r:29},{y:5.4,h:4.6,x0:-40,x1:40,b:-38,l:25,r:29},{y:10,h:4.6,x0:-37,x1:38,b:-36,l:22,r:26},{y:14.6,h:4.6,x0:-34,x1:35,b:-34,l:13,r:22},{y:19.2,h:4.6,x0:-31,x1:32,b:-32,l:7,r:16},{y:23.8,h:4.5,x0:-28,x1:28,b:-30,l:-2,r:8}];
  const leftInner=-12,rightInner=12,backInner=-14;
  function slab(f,y,material=pale,thickness=.28){box(material,(f.x0+leftInner)/2,y,(f.b+f.l)/2,leftInner-f.x0,thickness,f.l-f.b);box(material,(rightInner+f.x1)/2,y,(f.b+f.r)/2,f.x1-rightInner,thickness,f.r-f.b);box(material,0,y,(f.b+backInner)/2,24,thickness,backInner-f.b);}
  if(coarse){floors.forEach((f,i)=>{slab(f,f.y-.1);box(clay[i%4],(f.x0-12)/2,f.y+f.h/2,(f.b+f.l)/2,-12-f.x0,f.h-.25,f.l-f.b);box(clay[i%4],(12+f.x1)/2,f.y+f.h/2,(f.b+f.r)/2,f.x1-12,f.h-.25,f.r-f.b);box(clay[i%4],0,f.y+f.h/2,(f.b-14)/2,24,f.h-.25,-14-f.b);});box(glass,0,12,30,23,24,.15);box(pale,0,5.55,32,32,.35,10);}
  const leafParts=[],residents=[],stepGroups=[],doors=[],flags=[],fountain=[];
  const routes=[[[ -45,35],[ -20,38],[ -4,38],[0,31],[0,18],[0,31],[-4,38],[-20,38]],[[45,35],[25,40],[7,37],[0,31],[0,19],[0,31],[7,37],[25,40]],[[ -49,-43],[-49,45],[48,45],[48,-43]],[[ -48,44],[40,45],[41,34],[-40,34]]];
  function facade(x0,z0,x1,z1,f,normal,interior=false){const len=Math.hypot(x1-x0,z1-z0),ux=(x1-x0)/len,uz=(z1-z0)/len,angle=-Math.atan2(uz,ux),n=Math.max(1,Math.round(len/(f.y===0?4.8:3.8))),step=len/n,wy=f.y+f.h/2;
    function at(u,depth){return[x0+ux*u+normal[0]*depth,z0+uz*u+normal[1]*depth];}
    function element(m,u,y,w,h,depth,offset=.02,parent=architecture){const p=at(u,offset);box(m,p[0],y,p[1],w,h,depth,parent,angle);}
    for(let i=0;i<n;i++){const u=(i+.5)*step,solid=!interior&&f.y>0&&((i+Math.round(f.y/4.6))%5===1),m=clay[(i+Math.round(f.y))%4];
      if(solid){const rows=4;for(let row=0;row<rows;row++)element(m,u,f.y+(row+.5)*f.h/rows,step-.028,f.h/rows-.024,.29,.01);if(i%2===0){element(bronze,u,wy,.32,f.h*.58,.07,.18);element(glass,u,wy,.23,f.h*.53,.018,.225);}}
      else{const glazingHeight=f.h-(f.y===0?.95:1.3),centerY=f.y+.35+glazingHeight/2;element(glass,u,centerY,step-.27,glazingHeight,.055,-.15);element(bronze,u-step/2+.085,centerY,.105,glazingHeight+.17,.21,.0);element(bronze,u+step/2-.085,centerY,.105,glazingHeight+.17,.21,.0);element(bronze,u,centerY-glazingHeight/2,step,.085,.2,.0);element(bronze,u,centerY+glazingHeight/2,step,.095,.2,.0);element(bronze,u,centerY+.15,step,.052,.11,-.03);element(f.y===0?stone:m,u,f.y+.15,step-.025,.3,.34,.03);element(m,u,f.y+f.h-.42,step-.025,.77,.35,.025);
        if(!interior&&f.y>0&&i%4===0){for(let j=0;j<4;j++)element(brass,u-step*.35+j*step*.23,centerY,.065,glazingHeight,.45,.28,detail);}
        const p=at(u,-1.5);box(shopGlow,p[0],f.y+f.h-.65,p[1],Math.max(.5,step-1),.045,1.6,lighting,angle);
      }
      element(f.y===0?stone:clay[(i+1)%4],u-step/2,wy,.28,f.h-.12,.52,.10);
      // Recessed lintel and sill metal trims, including the reverse faces.
      element(brass,u,f.y+f.h-.04,step-.04,.045,.46,.08,detail);
      if(f.y===0&&!interior)element(glow,u,f.y+f.h-.29,step-.34,.035,.055,.31,lighting);
    }
    element(pale,len/2,f.y+.03,len,.12,.62,.015);
  }
  function shopFront(x,z,width,name,index,ry=0){const s=label(name,width*.73,.62,'#3a2a23','#e9d2ab',66,'Shop '+name);s.position.set(x,4.52,z);s.rotation.y=ry;}
  function terracePlants(x0,x1,z,y){for(let x=x0+1.5;x<x1-1;x+=5.2){box(stone,x,y+.37,z,3.5,.74,1.4,detail);box(soil,x,y+.76,z,3.26,.035,1.16,detail);for(let k=0;k<6;k++)ball(leafM[k%3],x-1.35+k*.52,y+1.0+random()*.25,z,.43,detail,.8);}}
  if(!coarse){
    floors.forEach((f,i)=>{
      slab(f,f.y-.10);slab(f,f.y+f.h-.16);
      // Interior floors and recessed walls leave a genuine, deep central atrium.
      box(floor,(f.x0-12)/2,f.y+.065,(f.b+f.l)/2,-12-f.x0,.09,f.l-f.b);box(floor,(f.x1+12)/2,f.y+.065,(f.b+f.r)/2,f.x1-12,.09,f.r-f.b);box(floor,0,f.y+.065,(f.b-14)/2,24,.09,-14-f.b);
      facade(f.x0,f.l,-12,f.l,f,[0,1]);facade(12,f.r,f.x1,f.r,f,[0,1]);facade(f.x0,f.b,f.x0,f.l,f,[-1,0]);facade(f.x1,f.r,f.x1,f.b,f,[1,0]);facade(f.x1,f.b,f.x0,f.b,f,[0,-1]);
      facade(-12,f.l,-12,-14,f,[1,0],true);facade(12,-14,12,f.r,f,[-1,0],true);facade(-12,-14,12,-14,f,[0,1],true);
      // Shop interiors with furniture, displays, partitions and suspended fixtures.
      for(const side of [-1,1]){const xa=side<0?f.x0:12,xb=side<0?-12:f.x1,zfront=side<0?f.l:f.r;
        for(let x=xa+2;x<xb-1;x+=5.1){box(dark,x,f.y+f.h*.42,zfront-7,4.2,f.h*.8,.16);for(let r=0;r<3;r++){box(wood,x,f.y+.6+r*.69,zfront-5.6,3.6,.08,.55,detail);for(let j=0;j<4;j++){box([clay[2],pale,brass,seat][(j+r)%4],x-1.25+j*.8,f.y+.88+r*.69,zfront-5.6,.45,.45,.32,detail);}}
          if((Math.round(x)+i)%2===0){box(pale,x,f.y+.55,zfront-2.6,1.7,1.1,.8,detail);cylinder(brass,x,f.y+f.h-.9,zfront-2.5,.34,.09,detail);box(glow,x,f.y+f.h-.96,zfront-2.5,.5,.03,.5,lighting);}
          else{box(brass,x,f.y+1.9,zfront-2.5,2.1,.07,.07,detail);for(let j=0;j<5;j++)box([seat,clay[2],leafM[0]][j%3],x-.8+j*.4,f.y+1.47,zfront-2.5,.32,.72,.11,detail);}
        }
      }
      if(i<5){const next=floors[i+1],y=f.y+f.h;
        if(f.l-next.l>1){rail(f.x0+.4,f.l-.5,-12.4,f.l-.5,y);terracePlants(f.x0+.6,-13,f.l-1.5,y);}
        if(f.r-next.r>1){rail(12.4,f.r-.5,f.x1-.4,f.r-.5,y);terracePlants(13,f.x1-.6,f.r-1.5,y);}
        if(next.x0>f.x0){rail(f.x0+.35,f.b+.35,f.x0+.35,f.l-.5,y);}
        if(next.x1<f.x1){rail(f.x1-.35,f.b+.35,f.x1-.35,f.r-.5,y);}
      }
    });
    // Roof parapets and screened mechanical courts.
    const top=floors[5];for(const side of [-1,1]){const x=side*20;box(pale,x,28.37,-16,15,.24,28);box(stone,x,28.8,-29,15,1.1,.32);box(stone,side*27.4,28.8,-16,.35,1.1,26);box(soil,x,28.58,-8,10,.28,8,detail);for(let i=0;i<14;i++)ball(leafM[i%3],x+(random()-.5)*8,29,-8+(random()-.5)*6,.7,detail,.6);for(let j=0;j<3;j++){box(bronze,x-4+j*3.4,29,-23,2.5,1.1,2.7,detail);for(let k=0;k<6;k++)box(brass,x-4+j*3.4,29.58,-24+k*.34,2.2,.055,.12,detail);}}
    box(bronze,0,26.7,-22,17,.22,11);for(let i=0;i<12;i++)box(pale,-8+i*1.45,26.95,-22,.5,.25,10,detail);
    // A small roof pavilion and a furnished terrace break up the repeated setbacks.
    for(const x of [-26,-15])for(const z of [-14,-5])box(bronze,x,29.76,z,.10,2.55,.10,detail);
    for(let z=-14.5;z<=-4.5;z+=.6)box(wood,-20.5,31.08,z,12,.19,.12,detail);
    for(const x of [-24,-18]){cylinder(pale,x,15.4,18,.7,.09,detail);cylinder(bronze,x,15.0,18,.05,.8,detail);for(const z of [16.9,19.1]){box(seat,x,15.05,z,.55,.1,.55,detail);box(wood,x,15.4,z+.23,.55,.65,.07,detail);}}
    for(let i=0;i<4;i++){box(bronze,19+i*1.6,28.6,-17,1.3,.12,5.5,detail);box(glass,19+i*1.6,28.7,-17,1.2,.03,5.3,detail);}
    // Tall glazed galleria with a sloping clerestory roof and visible structural ribs.
    box(floor,0,.08,7.7,23.7,.15,44);
    box(glass,0,14.2,30.25,23.4,18.8,.09);
    box(clay[0],0,24.65,30.35,24.5,2.15,.44);
    for(let x=-12;x<=12;x+=3){box(bronze,x,12.4,30.45,.16,24.8,.24);box(brass,x,25.5,8,.1,.18,44);}
    for(let y=5.4;y<24;y+=4.6)box(bronze,0,y,30.5,24.1,.14,.27);
    const skyRoof=mesh(new T.BoxGeometry(24,.11,44),roofGlass,'Glazed_atrium_roof');skyRoof.position.set(0,26.0,8);skyRoof.rotation.x=-.025;
    for(let z=-14;z<=30;z+=3.7)box(bronze,0,26+(z-8)*.025,z,24.2,.17,.13);
    for(let x=-10;x<=10;x+=5)box(brass,x,26,8,.1,.1,44,detail);
    const brand=label('陶 里 汇',17,2.2,'#a36249','#f5e9d1',95,'Taoli_Galleria_brand');brand.position.set(0,24.65,30.59);
    const brandSub=label('TAOLI  GALLERIA',11,.55,'#302b27','#e9d4af',45,'Entrance_lettering');brandSub.position.set(0,4.5,30.73);
    // Ground-floor entrance, glass side screens and two sliding doors.
    for(const sign of [-1,1]){box(glass,sign*7.7,2.2,30.35,8.1,4.2,.08);box(bronze,sign*3.5,2.25,30.4,.14,4.4,.22);for(let j=0;j<3;j++)box(bronze,sign*(4.2+j*3.4),2.2,30.4,.08,4.2,.17);}
    for(const sign of [-1,1]){const group=new T.Group();group.name=sign<0?'Automatic_door_left':'Automatic_door_right';architecture.add(group);const pane=mesh(new T.BoxGeometry(3.22,3.7,.08),glass,'Sliding_glass',group);pane.position.set(sign*1.66,1.94,30.67);for(const x of [sign*.06,sign*3.27]){const post=mesh(new T.BoxGeometry(.07,3.85,.11),bronze,'Door_frame',group);post.position.set(x,1.94,30.69);}const handle=mesh(new T.BoxGeometry(.04,.7,.07),brass,'Door_pull',group);handle.position.set(sign*.25,1.6,30.8);doors.push({group,sign});}
    box(bronze,0,3.94,30.68,6.8,.2,.3);
    // Thin entry canopy, bronze fascia, structural ribs and recessed light strips.
    box(bronze,0,5.55,32.5,33,.28,10.3);box(roofGlass,0,5.73,32.5,31.8,.09,9.4);box(brass,0,5.42,37.62,33,.16,.08);
    for(let x=-15;x<=15;x+=3){box(bronze,x,5.31,32.4,.14,.3,10);box(glow,x,5.14,33,.07,.025,7.4,lighting);}for(const x of [-14.8,14.8])box(bronze,x,2.7,35.7,.19,5.4,.19);
    // Two sky bridges cross the real atrium void; glass balustrades preserve views.
    for(const y of [5.4,14.6]){box(pale,0,y-.12,-3,24,.3,4);box(floor,0,y+.05,-3,24,.07,3.8);rail(-11.9,-1,11.9,-1,y);rail(-11.9,-5,11.9,-5,y);box(glow,0,y-.3,-1.3,22,.025,.12,lighting);}
    // Escalator inclined undercarriage, paired moving treads and handrails.
    for(const sign of [-1,1]){const g=new T.Group();g.name='Escalator_'+sign;architecture.add(g);const centerX=sign*3.3,slope=Math.atan2(5.4,12),length=Math.hypot(5.4,12);
      box(bronze,centerX,2.94,10,2.7,.45,length,architecture);const base=batches.get(boxGeo.uuid+'|'+bronze.uuid+'|'+architecture.uuid).items;base[base.length-1].compose(new T.Vector3(centerX,2.94,10),new T.Quaternion().setFromEuler(new T.Euler(slope,0,0)),new T.Vector3(2.7,.44,length));
      for(const dx of [-1.32,1.32]){const railMesh=mesh(new T.BoxGeometry(.10,.15,length),bronze,'Escalator_handrail',detail);railMesh.position.set(centerX+dx,3.8,10);railMesh.rotation.x=slope;const panel=mesh(new T.BoxGeometry(.055,.92,length),glass,'Escalator_balustrade',detail);panel.position.set(centerX+dx,3.29,10);panel.rotation.x=slope;}
      const steps=new T.InstancedMesh(boxGeo,bronze,36);steps.name='Moving_escalator_steps';g.add(steps);stepGroups.push({mesh:steps,x:centerX,sign});
    }
    const shops=[['青屿咖啡',-32,25.32,10],['纸间书店',-19,25.32,10],['织物研究所',20,29.32,11],['木与日常',33,29.32,10]];shops.forEach(([n,x,z,w],i)=>shopFront(x,z,w,n,i));
    // Upper-level restaurant signage.
    for(const [x,z,y,n] of [[-23,13.3,18.5,'TERRA  KITCHEN'],[23,22.3,18.5,'THE  TERRACE'],[21,8.3,27.6,'ROOF  &  GARDEN']]){const s=label(n,10,.6,'#492f25','#ead4af',46,'Restaurant '+n);s.position.set(x,y,z);}
    // Perimeter drains, standing seams, downpipes and service doors.
    for(const x of [-40.4,40.4]){box(bronze,x,5,-31,.09,10,.09,detail);for(let y=1;y<10;y+=1.8)box(brass,x,y,-31,.14,.04,.17,detail);}
    box(bronze,27,1.5,-38.35,3,3,.16,detail);box(brass,27,1.5,-38.46,.04,.8,.05,detail);for(let i=0;i<14;i++)box(bronze,-22+i*.8,2.3,-38.33,.5,2.7,.12,detail);
    for(const z of [-40,32,49]){box(grout,0,.014,z,101,.028,.25,detail);for(let x=-50;x<50;x+=.65)box(bronze,x,.032,z,.28,.02,.12,detail);}
    for(let x=-54;x<=54;x+=3)box(grout,x,.012,0,.018,.012,110,detail);for(let z=-54;z<=54;z+=3)box(grout,0,.013,z,110,.012,.018,detail);
    // Low bollards and tactile guidance stay clear of the automatic-door approach.
    for(let x=-11;x<=11;x+=2.2){if(Math.abs(x)>4){cylinder(bronze,x,.42,40,.09,.84,detail);cylinder(brass,x,.8,40,.1,.045,detail);}}
    box(pale,0,.028,44,1.1,.045,20,detail);for(let x=-.4;x<=.4;x+=.2)box(brass,x,.055,44,.045,.014,20,detail);
    for(const x of [-17,17]){box(stone,x,.9,41,1.25,1.8,.55,detail);const s=label('TAOLI  /  入口 →',2.6,.7,'#302b27','#ead4af',53,'Plaza_wayfinding');s.position.set(x,1.4,41.31);}
    const directory=label('陶里汇  /  DIRECTORY\n',3,4.3,'#e5dccc','#342c26',45,'Directory');directory.position.set(-43,2.3,29);const dir2=label('1F 咖啡 · 生活   2F 时装\n',2.7,.6,'#e5dccc','#554635',45,'Directory_line');dir2.position.set(-43,2.1,29.02);
    const screen=label('TAOLI  /  NEW SEASON',5,2.6,'#4e5f4b','#e8e1cd',52,'Changing_digital_display');screen.position.set(8,8,29.95);flags.push({display:screen,slide:-1});
  }
  function tree(x,z,y=0,size=1){cylinder(stone,x,y+.16,z,1.7*size,.32);cylinder(soil,x,y+.33,z,1.5*size,.045);cylinder(bark,x,y+2.1*size,z,.13*size,3.8*size);for(let i=0;i<3;i++)primitive(cylinderGeo,bark,[x+(i-1)*.35*size,y+(3.0+i*.25)*size,z],[.06*size,1.7*size,.06*size],[.3+i*.3,0,(i-1)*.45],landscape);for(let j=0;j<7;j++){const a=j*2.4,r=j===0?0:1.25*size;leafParts.push({p:[x+Math.cos(a)*r,y+(4.5+random()*.9)*size,z+Math.sin(a)*r],s:[1.35*size,1.3*size,1.35*size],phase:random()*6,mi:j%3});}}
  function bench(x,z,ry=0){for(let i=0;i<6;i++)box(wood,x,0.48,z+(i-2.5)*.115,3,.085,.09,landscape,ry);for(const s of [-1,1])box(bronze,x+s*1.1,.22,z,.09,.44,.6,landscape);}
  function cafe(x,z){cylinder(bronze,x,.5,z,.055,.95,detail);cylinder(pale,x,1,z,.63,.06,detail);for(let j=0;j<3;j++){const a=j*2.094,px=x+Math.cos(a)*1.05,pz=z+Math.sin(a)*1.05;box(seat,px,.48,pz,.48,.08,.48,detail);box(wood,px,.75,pz+.24,.48,.6,.07,detail);for(const k of [-1,1])box(bronze,px+k*.17,.23,pz,.035,.46,.34,detail);}cylinder(bronze,x,1.7,z,.035,3.4,detail);const umbrella=mesh(new T.ConeGeometry(1.65,.38,8,1,true),seat,'Cafe_parasol',detail);umbrella.position.set(x,3.2,z);}
  if(!coarse&&includeLandscape){
    for(const x of [-49,49])for(const z of [-43,-21,1,23,44])tree(x,z,0,.9+random()*.12);
    tree(-29,42,0,.9);tree(30,43,0,1);
    for(const x of [-43,43]){bench(x,41);bench(x,-43);box(stone,x,.3,6,3,.6,13,landscape);box(soil,x,.62,6,2.6,.04,12.5,landscape);for(let j=0;j<17;j++)ball(leafM[j%3],x+(random()-.5)*1.7,.9,random()*11+.5,.55,landscape,.7);}
    for(const [x,z] of [[-35,31],[-28,32],[-35,37]])cafe(x,z);
    // Quiet reflecting basin with low fountains, leaving the middle approach open.
    box(stone,25,.22,42,12,.44,4.3,landscape);box(water,25,.47,42,11.4,.045,3.7,landscape);
    for(let i=0;i<5;i++){const p=mesh(new T.CylinderGeometry(.035,.055,1,7),jetMat,'Water_jet',landscape);p.position.set(21+i*2,.95,42);fountain.push({mesh:p,index:i});}
    for(const x of [-20,36]){cylinder(bronze,x,.52,35,.29,1.04,landscape);cylinder(pale,x,1.06,35,.31,.055,landscape);}
    for(let i=0;i<5;i++){const ring=mesh(new T.TorusGeometry(.45,.04,6,12,Math.PI),bronze,'Bicycle_rack',landscape);ring.position.set(40+i*1.1,.45,-43);}
    for(const x of [-46,46])for(const z of [-34,16,45]){cylinder(bronze,x,2.7,z,.055,5.4,landscape);box(bronze,x,5.38,z,1,.08,.55,landscape);box(glow,x,5.32,z,.7,.03,.3,lighting);}
    for(const [x,z] of [[-42,31],[42,31]]){cylinder(bronze,x,4,z,.05,8,landscape);const g=own(new T.PlaneGeometry(1.4,3,8,10)),m=mat('Banner '+x,0xa45c44,.95,0,{side:T.DoubleSide});const banner=mesh(g,m,'Wind_banner',landscape);banner.position.set(x+.72,5.8,z);flags.push({banner,base:g.attributes.position.array.slice(),phase:random()*4});}
    const skin=mat('Visitor skin',0xcba58c,.92),hair=mat('Visitor hair',0x39342e,.94),pants=mat('Visitor trousers',0x3c4547,.94),coats=[mat('Visitor cream coat',0xd5c7b2,.94),mat('Visitor sage coat',0x76816a,.94),mat('Visitor rust coat',0xa16a54,.94),mat('Visitor navy coat',0x465664,.94)];
    for(let i=0;i<28;i++){const phase=random()*100;residents.push({phase,travel:phase,speed:.65+random()*.5,route:routes[i%routes.length],coat:coats[i%4],skin,hair,pants,height:.92+random()*.14,carry:i%4===0});}
  }
  function flush(){for(const{g,m,parent,items}of batches.values()){if(!items.length)continue;const o=new T.InstancedMesh(g,m,items.length);o.name=m.name+' instances';items.forEach((a,i)=>o.setMatrixAt(i,a));o.castShadow=m!==glass&&m!==roofGlass&&m!==glow&&m!==shopGlow&&m!==grout&&m!==brass;o.receiveShadow=m!==grout&&m!==brass;o.computeBoundingSphere();parent.add(o);}batches.clear();}
  flush();
  const leafMeshes=leafM.map(m=>{const n=leafParts.filter(p=>p.mi===leafM.indexOf(m)).length;if(!n)return null;const o=new T.InstancedMesh(sphereGeo,m,n);o.name='Swaying_tree_canopies';o.instanceMatrix.setUsage(T.DynamicDrawUsage);o.castShadow=true;o.receiveShadow=true;landscape.add(o);return o;});
  const personBatches=new Map();for(const r of residents)for(const [key,m,g,n] of [['body',r.coat,boxGeo,1],['head',r.skin,sphereGeo,1],['hair',r.hair,sphereGeo,1],['legs',r.pants,boxGeo,2],['arms',r.coat,boxGeo,2],['bag',wood,boxGeo,r.carry?1:0]]){if(!n)continue;const id=key+m.uuid;if(!personBatches.has(id))personBatches.set(id,{m,g,count:0,indices:[],key});const b=personBatches.get(id);r[key]={batch:b,start:b.count};b.count+=n;}
  for(const b of personBatches.values()){b.mesh=new T.InstancedMesh(b.g,b.m,b.count);b.mesh.name='Animated_visitors_'+b.key;b.mesh.castShadow=true;b.mesh.instanceMatrix.setUsage(T.DynamicDrawUsage);people.add(b.mesh);}
  function personMatrix(entry,index,position,scale,rot=0){dummy.position.set(...position);dummy.scale.set(...scale);dummy.rotation.set(rot,entry.rotation||0,0);dummy.updateMatrix();entry.batch.mesh.setMatrixAt(entry.start+index,dummy.matrix);}
  function routePoint(route,distance){let total=0;const lengths=route.map((a,i)=>{const b=route[(i+1)%route.length];const d=Math.hypot(b[0]-a[0],b[1]-a[1]);total+=d;return d;});let p=distance%total;for(let i=0;i<route.length;i++){if(p<=lengths[i]){const a=route[i],b=route[(i+1)%route.length],u=p/lengths[i];return{x:a[0]+(b[0]-a[0])*u,z:a[1]+(b[1]-a[1])*u,angle:Math.atan2(b[0]-a[0],b[1]-a[1])};}p-=lengths[i];}return{x:0,z:36,angle:0};}
  function setTimeOfDay(value){const next=typeof value==='number'?value:({afternoon:0,sunset:.55,night:1}[value]??0);currentNight=T.MathUtils.clamp(next,0,1);applyLights();}
  function applyLights(){for(const m of litMaterials){const isSign=m.map&&m.emissiveMap;m.emissiveIntensity=lightsEnabled?(isSign ? .09+currentNight*.7 : .35+currentNight*2.4):0;}for(const light of localLights)light.intensity=lightsEnabled?8+currentNight*120:0;lighting.visible=lightsEnabled;}
  function setQuality(value){if(!['high','medium','low'].includes(value))throw new Error('quality 应为 high、medium 或 low');activeQuality=value;glass.transmission=value==='high'?.72:0;roofGlass.transmission=value==='high'?.42:0;glass.needsUpdate=true;roofGlass.needsUpdate=true;detail.visible=value!=='low';return activeQuality;}
  function update(dt=0,context={}){if(disposed)return;const previousTime=simTime;if(!context.paused)simTime=Number.isFinite(context.time)?context.time:simTime+Math.max(0,Math.min(dt,.25));const elapsed=Math.max(0,Math.min(.25,simTime-previousTime));if(Number.isFinite(context.nightFactor))currentNight=T.MathUtils.clamp(context.nightFactor,0,1);lightsEnabled=context.lights!==false;applyLights();people.visible=context.people!==false;const t=simTime,wind=context.wind===false?0:1;let nearDoor=false;
    const leafIndices=[0,0,0];for(const l of leafParts){const m=leafMeshes[l.mi],i=leafIndices[l.mi]++;dummy.position.set(l.p[0]+Math.sin(t*.85+l.phase)*.12*wind,l.p[1],l.p[2]+Math.cos(t*.7+l.phase)*.07*wind);dummy.rotation.set(0,Math.sin(t*.6+l.phase)*.03*wind,.025*Math.sin(t*.9+l.phase)*wind);dummy.scale.set(...l.s);dummy.updateMatrix();m.setMatrixAt(i,dummy.matrix);}for(const m of leafMeshes)if(m){m.instanceMatrix.needsUpdate=true;m.computeBoundingSphere();}
    if(people.visible){residents.forEach((r,i)=>{const pause=Math.sin((t+r.phase)*.11)>.88;if(!pause)r.travel+=elapsed*r.speed;const p=routePoint(r.route,r.travel),h=r.height,gait=pause?0:Math.sin(t*5.3+r.phase)*.38;if(Math.abs(p.x)<5&&Math.abs(p.z-30.5)<4.5)nearDoor=true;const sx=Math.cos(p.angle),sz=-Math.sin(p.angle);for(const key of ['body','head','hair','legs','arms','bag'])if(r[key])r[key].rotation=p.angle;personMatrix(r.body,0,[p.x,1.05*h,p.z],[.42*h,.62*h,.24*h]);personMatrix(r.head,0,[p.x,1.57*h,p.z],[.14*h,.18*h,.14*h]);personMatrix(r.hair,0,[p.x,1.69*h,p.z],[.145*h,.10*h,.145*h]);for(let k=0;k<2;k++){const sign=k?1:-1;personMatrix(r.legs,k,[p.x+sx*.115*sign,.40*h,p.z+sz*.115*sign],[.14*h,.74*h,.17*h],sign*gait);personMatrix(r.arms,k,[p.x+sx*.29*sign,1.04*h,p.z+sz*.29*sign],[.12*h,.58*h,.13*h],-sign*gait*.7);}if(r.bag)personMatrix(r.bag,0,[p.x+sx*.38,.7*h,p.z+sz*.38],[.23,.3,.14]);});for(const b of personBatches.values()){b.mesh.instanceMatrix.needsUpdate=true;b.mesh.computeBoundingSphere();}}
    for(const d of doors)d.group.position.x=T.MathUtils.damp(d.group.position.x,d.sign*(nearDoor?2.85:0),5,elapsed);
    for(const e of stepGroups){for(let i=0;i<36;i++){let u=(i/36+t*.045*e.sign)%1;if(u<0)u+=1;dummy.position.set(e.x,.22+u*5.4,16-u*12);dummy.rotation.set(0,0,0);dummy.scale.set(2.28,.18,.43);dummy.updateMatrix();e.mesh.setMatrixAt(i,dummy.matrix);}e.mesh.instanceMatrix.needsUpdate=true;e.mesh.computeBoundingSphere();}
    fountain.forEach(({mesh,index})=>{mesh.visible=context.water!==false;const h=.6+.2*Math.sin(t*1.6+index*.7);mesh.scale.y=h;mesh.position.y=.49+h/2;});water.roughness=.15+Math.sin(t*.4)*.025;
    flags.forEach(f=>{if(f.banner){const a=f.banner.geometry.attributes.position;for(let i=0;i<a.count;i++){const x=f.base[i*3];a.array[i*3+2]=f.base[i*3+2]+Math.sin(x*2.3+t*2.1+f.phase)*.12*(x+.7)/1.4*wind;}a.needsUpdate=true;f.banner.geometry.computeVertexNormals();}if(f.display){f.display.material.emissiveIntensity=lightsEnabled?.15+currentNight*.8+.04*Math.sin(t*.35):0;const slide=Math.floor(t/12)%3;if(slide!==f.slide){f.slide=slide;const c=f.display.material.map.image,ctx=c.getContext('2d');ctx.fillStyle=['#4e5f4b','#9a6245','#4a575f'][slide];ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#eee0c9';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='52px "Microsoft YaHei",sans-serif';ctx.fillText(['TAOLI / NEW SEASON','露台晚餐 · TERRACE','城市生活 · EVERYDAY'][slide],c.width/2,c.height/2,940);f.display.material.map.needsUpdate=true;}}});
    detail.visible=activeQuality!=='low'&&(!context.cameraDistance||context.cameraDistance<(activeQuality==='high'?340:210));
  }
  model.scale.setScalar(footprint/112);
  const metadata={id:'taoli-galleria',name:'陶里汇 · 商城综合体',version:'1.0.0',footprint:[footprint,footprint],units:'metres',upAxis:'Y',origin:'parcel-ground-centre',displayHeight:31.175*footprint/112,floors:6,nominalParcel:112,containsRoads:false,proceduralAnimations:true};model.userData.landmark=metadata;
  function getBounds(){model.updateMatrixWorld(true);return new T.Box3().setFromObject(model);}
  function dispose(){if(disposed)return;disposed=true;model.removeFromParent();model.traverse(o=>{if(o.isInstancedMesh)o.dispose();});for(const g of ownedG)g.dispose();for(const m of ownedM)m.dispose();for(const t of ownedTex)t.dispose();}
  setQuality(quality);update(0,{time:0});
  return{model,metadata,update,setQuality,setTimeOfDay,getBounds,dispose,materials,parts:{architecture,landscape,detail,people,lighting},get time(){return simTime;},get quality(){return activeQuality;}};
}
