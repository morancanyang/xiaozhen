/** Seeded botanical geometry. No opaque canopy blobs in the refined model. */
export function createEcology(c){
 const {THREE,G,geo,materials,mat,part,box,random,coarse,textures,groups,manifest}=c;
 const counts={trees:0,branches:0,leaves:0,shrubs:0,grassTufts:0,grassBlades:0};
 const twig=G(new THREE.CylinderGeometry(.23,.5,1,9,3));geo.branch=twig;
 // A softly folded lanceolate leaf, with an actual midrib, curled tip and UVs.
 const lp=[],lu=[],li=[];
 for(let row=0;row<=5;row++){const t=row/5,w=.003+Math.pow(Math.max(0,Math.sin(Math.PI*t)),.8)*.497;for(const side of [-1,0,1]){lp.push(side*w,t,Math.sin(t*Math.PI)*.08+Math.abs(side)*.06+Math.pow(t,4)*.11);lu.push((side+1)/2,t)}}
 for(let r=0;r<5;r++)for(let k=0;k<2;k++){const a=r*3+k;li.push(a,a+1,a+3,a+1,a+4,a+3)}
 const leaf=G(new THREE.BufferGeometry());leaf.setAttribute('position',new THREE.Float32BufferAttribute(lp,3));leaf.setAttribute('uv',new THREE.Float32BufferAttribute(lu,2));leaf.setIndex(li);leaf.computeVertexNormals();geo.botanicalLeaf=leaf;
 function canvasTexture(kind){const n=512,canvas=document.createElement('canvas');canvas.width=canvas.height=n;const x=canvas.getContext('2d');
  x.fillStyle=kind==='bark'?'#6c6957':kind==='leaf'?'#b5c691':'#b7b7b0';x.fillRect(0,0,n,n);
  if(kind==='bark'){for(let i=0;i<460;i++){const px=random()*n,w=.3+random()*2;x.strokeStyle=i%3?'#282d234a':'#d0c3a058';x.lineWidth=w;x.beginPath();x.moveTo(px,0);for(let y=0;y<=n;y+=16)x.lineTo(px+Math.sin(y*.07+i)*2.5,y);x.stroke()}for(let i=0;i<1600;i++){x.fillStyle=i%2?'#acaa7930':'#2d352a40';x.fillRect(random()*n,random()*n,2+random()*6,1+random()*4)}}
  if(kind==='leaf'){const g=x.createLinearGradient(0,0,512,0);g.addColorStop(0,'#81966d');g.addColorStop(.5,'#c4d49c');g.addColorStop(1,'#829965');x.fillStyle=g;x.fillRect(0,0,n,n);x.strokeStyle='#d2d9a780';x.lineWidth=3;x.beginPath();x.moveTo(256,0);x.lineTo(256,512);x.stroke();x.lineWidth=1;for(let y=30;y<510;y+=30)for(const s of [-1,1]){x.beginPath();x.moveTo(256,y);x.quadraticCurveTo(256+s*100,y-30,256+s*250,y-65);x.stroke()}}
  if(kind==='stone'){const d=x.getImageData(0,0,n,n);for(let y=0;y<n;y++)for(let xx=0;xx<n;xx++){const i=(y*n+xx)*4,v=(random()-.5)*20+Math.sin(xx*.017+Math.sin(y*.025))*5;for(let k=0;k<3;k++)d.data[i+k]+=v}x.putImageData(d,0,0)}
  const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=8;textures.add(t);return t;
 }
 const barkMap=canvasTexture('bark');materials.bark.map=barkMap;materials.bark.bumpMap=barkMap;materials.bark.bumpScale=.035;materials.bark.color.setHex(0xb9b1a0);materials.bark.roughness=.94;
 const leafMap=canvasTexture('leaf');
 for(const [name,color] of [['foliage-sun',0x65823f],['foliage-shade',0x3c622b],['foliage-young',0x839952]])mat(name,color,{map:leafMap,roughness:.66,side:THREE.DoubleSide});
 for(const n of ['stone','paving']){materials[n].map=canvasTexture('stone');materials[n].color.setHex(n==='stone'?0xc4c1b2:0xd7d4c8);materials[n].bumpMap=materials[n].map;materials[n].bumpScale=.006;materials[n].roughness=.76}
 mat('stair-stone',0xc6c6bb,{map:materials.stone.map,roughness:.72});mat('stair-inlay',0x4f5a56,{roughness:.56,metalness:.55});
 const v=new THREE.Vector3(),end=new THREE.Vector3(),q=new THREE.Quaternion(),e=new THREE.Euler();
 function branch(a,b,diameter,owner='landscape',tier=0){v.fromArray(a);end.fromArray(b);const l=v.distanceTo(end),mid=v.clone().add(end).multiplyScalar(.5);q.setFromUnitVectors(new THREE.Vector3(0,1,0),end.sub(v).normalize());part('branch','bark',mid.toArray(),[diameter,l,diameter],e.setFromQuaternion(q).toArray().slice(0,3),owner,tier);counts.branches++}
 function leavesAt(p,n,radius,owner='landscape',tier=1){for(let j=0;j<n;j++){const a=random()*Math.PI*2,h=random()*2-1,r=Math.cbrt(random())*radius,s=Math.sqrt(1-h*h),pos=[p[0]+Math.cos(a)*s*r,p[1]+h*r*.7,p[2]+Math.sin(a)*s*r];const len=.14+random()*.11;part('botanicalLeaf',j%7===0?'foliage-young':j%3===0?'foliage-shade':'foliage-sun',pos,[len*.6,len,len],[random()*2.8-.6,random()*Math.PI*2,random()*2-1],owner,tier);counts.leaves++}}
 function tree(x,z,size=1){counts.trees++;if(coarse){part('cyl','bark',[x,2.5*size,z],[.32*size,5*size,.32*size]);part('leaf','leaf',[x,5*size,z],[4*size,4*size,4*size]);return}
  const height=(6.9+random()*.8)*size,top=[x+.17*size,height*.68,z-.1*size];branch([x,.08,z],top,.48*size);branch(top,[x+.22*size,height*.96,z-.05*size],.16*size);leavesAt([x+.22*size,height*.94,z-.05*size],180,.5*size);
  for(let b=0;b<7;b++){const a=b*2.399+random()*.3,start=[x+.04*b,height*(.29+b*.035),z],reach=(1.05+random()*.65)*size,tip=[x+Math.sin(a)*reach,height*(.54+random()*.25),z+Math.cos(a)*reach];branch(start,tip,(.14-b*.009)*size);
   for(let k=0;k<6;k++){const aa=a+k*1.31,rr=(.3+random()*.52)*size,tt=[tip[0]+Math.sin(aa)*rr,Math.min(height,tip[1]+(.35+random()*.5)*size),tip[2]+Math.cos(aa)*rr];branch(tip,tt,.028*size,'landscape',1);leavesAt(tt,62,.46*size,'landscape',k%3===0?2:1)}
  }
  // Root flare, shallow soil bowl and porous tree grate with four separate edging strips.
  for(let j=0;j<5;j++){const a=j*Math.PI*.4;branch([x,.38,z],[x+Math.sin(a)*.55,.09,z+Math.cos(a)*.55],.12,'landscape',1)}
  box('earth',x,.075,z,2,.08,2,'landscape',1);for(const dx of [-1.06,1.06])box('stone',x+dx,.14,z,.12,.16,2.24,'landscape',1);for(const dz of [-1.06,1.06])box('stone',x,.14,z+dz,2,.16,.12,'landscape',1);
 }
 function shrub(x,z,size=1){counts.shrubs++;if(coarse){part('leaf','leaf',[x,.6,z],[size,1,size]);return}for(let k=0;k<5;k++){const a=k*2.4,tip=[x+Math.sin(a)*size*.28,.55+random()*.35,z+Math.cos(a)*size*.25];branch([x,.09,z],tip,.018,'landscape',1);leavesAt(tip,65,.28*size,'landscape',1)}}
 // Six curved, tapered blades per tuft; vertex colors darken the root and warm the tips.
 const gp=[],gn=[],gu=[],gc=[],gi=[];
 for(let j=0;j<6;j++){const a=j*2.399,w=.0025+random()*.0035,h=.075+random()*.095,bend=.02+random()*.035;
  const offset=gp.length/3;
  for(let row=0;row<=3;row++){const t=row/3,ww=w*(1-t)+.00025;for(const side of [-1,1]){gp.push(Math.cos(a)*ww*side+Math.sin(a)*bend*t*t,h*t,Math.sin(a)*ww*side+Math.cos(a)*bend*t*t);gu.push((side+1)/2,t);const color=new THREE.Color().lerpColors(new THREE.Color(0x29441e),new THREE.Color(0x78924b),t);gc.push(color.r,color.g,color.b)}}
  for(let row=0;row<3;row++){const i=offset+row*2;gi.push(i,i+2,i+1,i+1,i+2,i+3)}
 }
 const tuft=G(new THREE.BufferGeometry());tuft.setAttribute('position',new THREE.Float32BufferAttribute(gp,3));tuft.setAttribute('uv',new THREE.Float32BufferAttribute(gu,2));tuft.setAttribute('color',new THREE.Float32BufferAttribute(gc,3));tuft.setIndex(gi);tuft.computeVertexNormals();geo.grassTuft=tuft;
 materials['grass-blade'].color.setHex(0xffffff);materials['grass-blade'].vertexColors=true;materials['grass-blade'].roughness=.9;
 // Turf substrate is mottled at two scales, with small directional strands in its bitmap.
 const turf=document.createElement('canvas');turf.width=turf.height=1024;const tx=turf.getContext('2d');tx.fillStyle='#405c2f';tx.fillRect(0,0,1024,1024);for(let i=0;i<160000;i++){const xx=random()*1024,yy=random()*1024;tx.strokeStyle=i%4===0?'#89975b60':i%3===0?'#172e1e60':'#56793e70';tx.lineWidth=.5;tx.beginPath();tx.moveTo(xx,yy);tx.lineTo(xx+random()*2-1,yy-1-random()*4);tx.stroke()}
 const turfMap=new THREE.CanvasTexture(turf);turfMap.colorSpace=THREE.SRGBColorSpace;turfMap.wrapS=turfMap.wrapT=THREE.RepeatWrapping;turfMap.repeat.set(5,4);turfMap.anisotropy=8;textures.add(turfMap);materials.grass.map=turfMap;materials.grass.bumpMap=turfMap;materials.grass.bumpScale=.009;
 const grassMeshes=[];
 function grass(specs){if(coarse)return;const total=132000,o=new THREE.InstancedMesh(tuft,materials['grass-blade'],total),m=new THREE.Matrix4(),p=new THREE.Vector3(),q=new THREE.Quaternion(),s=new THREE.Vector3();o.name='Curved botanical grass tufts';o.castShadow=true;o.receiveShadow=true;o.userData.highCount=total;o.userData.mediumCount=28000;o.userData.lowCount=3800;
  for(let i=0;i<total;i++){let x,z;do{x=-40+random()*80;z=-40+random()*75}while(specs.some(b=>Math.abs(x-b[1])<b[4]/2+.85&&Math.abs(z-b[2])<b[5]/2+1.1)||Math.abs(x)<7.6||Math.abs(x+23)<(z<17?8.2:4.3)&&z>8||Math.abs(x-24)<(z<24?8.2:4.3)&&z>15||z>7.5&&z<22.5||Math.abs(Math.abs(x)-12)<3.1&&z>23||Math.abs(Math.abs(x)-10)<1.1&&z>22||z>33.1&&z<34.9);p.set(x,.079,z);q.setFromAxisAngle(new THREE.Vector3(0,1,0),random()*Math.PI*2);const patch=.75+.35*Math.sin(x*1.7)*Math.cos(z*1.9),a=.72+random()*.7;s.set(a,patch*(.65+random()*.7),a);m.compose(p,q,s);o.setMatrixAt(i,m)}o.computeBoundingSphere();groups.get('landscape').add(o);grassMeshes.push(o);counts.grassTufts=total;counts.grassBlades=total*6;
 }
 return{tree,shrub,grass,grassMeshes,counts};
}
