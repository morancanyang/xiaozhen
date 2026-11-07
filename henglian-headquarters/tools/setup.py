from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'chengxu-courtyard'
for d in ['src','outputs','tools']:(ROOT/d).mkdir(exist_ok=True)
for name in ['build.cjs','package.json','src/app.js','src/shell.html','src/style.css','tools/inspect_model.py','tools/blender_import.py','tools/render_blender.py','tools/blender_mcp.py','tools/run_blender_mcp.py','tools/show_scene.py']:
 s=(BASE/name).read_text(encoding='utf8')
 for a,b in [('澄序住区','衡联总部'),('CHENGXU COURTYARD','HENGLIAN CAMPUS'),('CHENGXU_COURTYARD','HENGLIAN_CAMPUS'),('chengxu-residential-courtyard','henglian-corporate-headquarters'),('createResidentialCourtyard','createCorporateHeadquarters'),('ResidentialCourtyardModule','CorporateHeadquartersModule'),('courtyardApp','headquartersApp'),('courtyard-scene','headquarters-scene'),('courtyard-manifest','headquarters-manifest'),('courtyard_camera_','headquarters_camera_'),('CHENGXU_','HENGLIAN_'),('blender_start_courtyard_render','blender_start_headquarters_render'),('blender_courtyard_status','blender_headquarters_status'),('blender_open_courtyard_scene','blender_open_headquarters_scene'),('chengxu_courtyard_blender','henglian_headquarters_blender'),('COURTYARD_BLENDER_EXE','HEADQUARTERS_BLENDER_EXE')]:s=s.replace(a,b)
 (ROOT/name).write_text(s,encoding='utf8')
s=(BASE/'src/model.js').read_text(encoding='utf8');header=s[:s.index(' // One square parcel')]
header=header.replace('createResidentialCourtyard','createCorporateHeadquarters').replace('澄序住区','衡联总部').replace('chengxu-residential-courtyard','henglian-corporate-headquarters').replace('max:[56,78,56]','max:[56,100,56]').replace("['playground','儿童与休憩花园']","['playground','商务休憩花园']")
header=header.replace("peopleCount:22,birdCount:5","peopleCount:22,birdCount:5").replace('walkwayCenterline:41','walkwayCenterline:41,bridgeFloor:36.8,bridgeTop:41.2')
header=header.replace("mat('beige-panel',0xc9c5b7)","mat('beige-panel',0xbac5cc)").replace("['glass',0x527e91],['glass-blue',0x628a9a],['glass-shadow',0x375867]","['glass',0x427d9b],['glass-blue',0x6797ad],['glass-shadow',0x2a536e]")
tail=s[s.index(' for(const b of batches.values())'):]
tail=tail.replace("format:'chengxu-residential-courtyard-v1'","format:'henglian-corporate-headquarters-v1'")
start=tail.index('  for(const a of people)');end=tail.index('  if(activity.mechanical)',start)
tail=tail[:start]+'''  for(const a of people){let x,z,yaw,y=.23;
   if(a.i<8){const d=(time*.75+a.i*5.5)%76;x=d<38?-17+d:59-d;z=3+(a.i%2?.8:-.8);y=37.07;yaw=d<38?Math.PI/2:-Math.PI/2}
   else if(a.i<14){const d=(time*.7+a.i*13)%160;x=d<80?-40+d:120-d;z=39+(a.i%2?.6:-.6);yaw=d<80?Math.PI/2:-Math.PI/2}
   else if(a.i<20){[x,z,yaw]=squareRoute(time*.72+a.i*39,41)}
   else {x=a.i===20?-23:24;const d=(time*.55+a.i*3)%12;const front=a.i===20?9:16;z=front+1+(d<6?d:12-d);yaw=d<6?0:Math.PI}
   a.g.position.set(x,y,z);a.g.rotation.y=yaw;a.g.visible=activity.people&&(a.i>=8||activity.bridge)&&(level!=='low'||a.i<4||a.i>17);a.limbs.forEach((l,j)=>l.rotation.x=Math.sin(time*4+a.i+(j===0||j===3?0:Math.PI))*(j%2?.25:.35))
  }
  for(const d of doors){const near=activity.people&&people.some(a=>a.i>=8&&a.g.visible&&Math.hypot(a.g.position.x-d.x,a.g.position.z-d.z)<4);const wanted=d.base+d.side*(near?.72:0);d.object.position.x+=(wanted-d.object.position.x)*Math.min(1,dt*4)}
  if(activity.mechanical)elevators.forEach((lift,i)=>{const b=manifest.buildings[i],height=b.roofY-5;lift.position.y=2+(.5+.5*Math.sin(time*.12+i*2))*height});
'''+tail[end:]
tail=tail.replace("swing.rotation.x=Math.sin(time*1.2)*.1;",'').replace("enabled=true,disposed=false","enabled=true,disposed=false")
header=header.replace('mechanical:true};','mechanical:true,bridge:true};').replace('people=[],birds=[]','people=[],birds=[],elevators=[]')
tail=tail.replace('return{root,groups,buildings,manifest,','return{root,groups,buildings,main:buildings.get(\'main\'),annex:buildings.get(\'annex\'),bridge:groups.get(\'bridge\'),manifest,')
(ROOT/'outputs/model-header.txt').write_text(header,encoding='utf8');(ROOT/'outputs/model-tail.txt').write_text(tail,encoding='utf8')
print('Prepared offline viewer and Blender bridge')
