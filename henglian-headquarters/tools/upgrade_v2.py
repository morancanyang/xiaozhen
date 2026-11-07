"""One-time geometry revision; source remains in src/ after this transformation."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'src/model.js';s=p.read_text(encoding='utf8')
s="import {createEcology} from './ecology.js';\nimport {createStairs} from './stairs.js';\n"+s
s=s.replace('version:1,','version:2,')
anchor=' // Native metric site'
i=s.index(anchor)
helpers='''
 function custom(name,points,indices,material,owner){const g=G(new THREE.BufferGeometry());const origin=new THREE.Vector3(...origins.get(owner));const local=points.map(p=>new THREE.Vector3(...p).sub(origin));g.setAttribute('position',new THREE.Float32BufferAttribute(local.flatMap(p=>p.toArray()),3));g.setAttribute('uv',new THREE.Float32BufferAttribute(points.flatMap(p=>[p[0]*.5,p[2]*.5]),2));g.setIndex(indices);g.computeVertexNormals();const o=new THREE.Mesh(g,materials[material]);o.name=name;o.castShadow=o.receiveShadow=true;groups.get(owner).add(o);return o}
 function slabSlope(owner,xx,base,start,dir,run,rise,width){const a=new THREE.Vector3(xx,base,start),b=new THREE.Vector3(xx,base+rise,start+dir*run),mid=a.clone().add(b).multiplyScalar(.5);part('box','stone',mid.toArray(),[width,.16,Math.hypot(run,rise)],[-Math.atan2(rise,dir*run),0,0],owner,1)}
 function floorWithWell(m,x,y,z,w,h,d,owner,tier=0){const cx=x-3,cz=z-3,hx=2.78,hz=4.25,left=x-w/2,right=x+w/2,back=z-d/2,front=z+d/2;box(m,(left+cx-hx)/2,y,z,cx-hx-left,h,d,owner,tier);box(m,(right+cx+hx)/2,y,z,right-cx-hx,h,d,owner,tier);box(m,cx,y,(back+cz-hz)/2,hx*2,h,cz-hz-back,owner,tier);box(m,cx,y,(front+cz+hz)/2,hx*2,h,front-cz-hz,owner,tier)}
 const ecology=createEcology({THREE,G,geo,materials,mat,part,box,random,coarse,textures,groups,manifest});
 const stairs=createStairs({THREE,group,part,box,beam,coarse,manifest,groups,custom,slabSlope});
'''
s=s[:i]+helpers+s[i:]
s=s.replace("box('dark',x,base+.12,z,w-.22,.24,d-.22,f);box('trim',x,base+.03,z,w+.06,.07,d+.06,f);","floorWithWell('dark',x,base+.12,z,w-.22,.24,d-.22,f);floorWithWell('trim',x,base+.03,z,w+.06,.07,d+.06,f);")
s=s.replace("base=fl===0?.3:","base=fl===0?.65:").replace("fh=fl===0?4.5:4","fh=fl===0?4.15:4")
s=s.replace("box('stone',x-3,roofY/2,z-3,5,roofY,5,inside);", "for(const dx of [-2.9,2.9])box('stone',x-3+dx,roofY/2,z-3,.2,roofY,8.7,inside);box('stone',x-3,roofY/2,z-7.25,5.6,roofY,.2,inside);box('stone',x-3,roofY/2,z+1.25,5.6,roofY,.2,inside);stairs.internal(id,x,z,floors,roofY);")
s=s.replace("const y=fl===0?.32:","const y=fl===0?.69:")
s=s.replace("box('stone',x,.16,front+3.5,10,.32,7,en);", "stairs.entrance(id,x,z,front);")
s=s.replace("[side*.8,1.85,d/2+.12]","[side*.8,2.3,d/2+.12]")
s=s.replace("box('frame',x+side*1.62,1.85,front+.18,.08,3.4,.14,en)","box('frame',x+side*1.62,2.3,front+.18,.08,3.4,.14,en)")
s=s.replace("box('roof',x,roofY,z,w,.18,d,r);","floorWithWell('roof',x,roofY,z,w,.18,d,r);")
s=s.replace("z-3,6,3,6,r)","z-3,6,3,9,r)").replace("z-3,6.3,.2,6.3,r)","z-3,6.3,.2,9.3,r)")
a=s.index(' function tree(');b=s.index(' for(const x of [-52,52])',a);s=s[:a]+" const tree=ecology.tree;\n"+s[b:]
s=s.replace("part('leaf','leaf',[x,.6,34],[1.7,1,.95],0,'landscape',1)","ecology.shrub(x,34,1.4)")
a=s.index(' let grassMesh;');b=s.index(' for(const b of batches.values())',a)
s=s[:a]+" ecology.grass(specs);manifest.ecology=ecology.counts;\n"+s[b:]
s=s.replace("['leaf','leaf-light','grass-blade','curtain','curtain-warm']","['foliage-sun','foliage-shade','foliage-young','grass-blade','curtain','curtain-warm']")
s=s.replace("if(grassMesh)grassMesh.count=value==='high'?16000:value==='medium'?5000:1200", "for(const m of ecology.grassMeshes)m.count=m.userData[value==='high'?'highCount':value==='medium'?'mediumCount':'lowCount']")
s=s.replace("else {x=a.i===20?", "else {x=a.i===20?")
s=s.replace("yaw=d<6?0:Math.PI}\n   a.g.position", "yaw=d<6?0:Math.PI;const approach=z-front;y=approach<5.2?.69:approach<5.6?.69:approach<6?.54:approach<6.4?.39:.24}\n   a.g.position")
s=s.replace("uv:g.attributes.uv?Array.from(g.attributes.uv.array):null}","uv:g.attributes.uv?Array.from(g.attributes.uv.array):null,colors:g.attributes.color?Array.from(g.attributes.color.array):null}")
s=s.replace("roughness:m.roughness,metalness:m.metalness", "vertexColors:m.vertexColors,roughness:m.roughness,metalness:m.metalness")
p.write_text(s,encoding='utf8')
p=ROOT/'build.cjs';s=p.read_text(encoding='utf8');s+="\nfor(const f of ['ecology.js','stairs.js'])fs.copyFileSync(path.join(__dirname,'src',f),path.join(__dirname,f));\n";p.write_text(s,encoding='utf8')
p=ROOT/'package.json';data=json.loads(p.read_text(encoding='utf8'));data['type']='module';data['version']='2.0.0';p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
p=ROOT/'src/app.js';s=p.read_text(encoding='utf8');s=s.replace("if(model.buildings.has(name))", "if(name==='stairs'){isolate('main-stairs');return name;}\n if(model.buildings.has(name))")
s=s.replace("roof:{p:","trees:{p:[-45,4,47],q:[-52,3.7,42],orthographic:false},grass:{p:[-9,.65,30.8],q:[-10,.17,29.8],orthographic:false},steps:{p:[-13,3,22],q:[-23,.6,14.8],orthographic:false},stairs:{p:[-17,7,0],q:[-26,3,-9],orthographic:false},roof:{p:")
s=s.replace('sun.shadow.normalBias=.025','sun.shadow.normalBias=.012').replace('renderer.toneMappingExposure=.97','renderer.toneMappingExposure=.88')
s=s.replace("sun.shadow.mapSize.set(2048,2048)","sun.shadow.mapSize.set(3072,3072)")
p.write_text(s,encoding='utf8')
p=ROOT/'src/shell.html';s=p.read_text(encoding='utf8').replace('<button data-view="main">', '<button data-view="steps">台阶</button><button data-view="stairs">楼梯</button><button data-view="trees">树木</button><button data-view="grass">草坪</button><button data-view="main">');p.write_text(s,encoding='utf8')
