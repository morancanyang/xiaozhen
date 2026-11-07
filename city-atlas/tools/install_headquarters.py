"""Install the refined headquarters using the established city adapter contract."""
from pathlib import Path
import shutil,json
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';S=ROOT.parent/'henglian-headquarters'
for src,dst in [('model.js','headquarters-model.js'),('ecology.js','headquarters-ecology.js'),('stairs.js','headquarters-stairs.js')]:
 s=(S/'src'/src).read_text(encoding='utf8').replace("'./ecology.js'","'./headquarters-ecology.js'").replace("'./stairs.js'","'./headquarters-stairs.js'");(D/dst).write_text(s,encoding='utf8')
shutil.copyfile(S/'headquarters-manifest.json',D/'headquarters-manifest.json')
s=(D/'courtyard-site.js').read_text(encoding='utf8')
for a,b in [('createResidentialCourtyard','createCorporateHeadquarters'),('courtyard-model','headquarters-model'),('COURTYARD_SITE','HEADQUARTERS_SITE'),('installCourtyard','installHeadquarters'),('BLK-14','BLK-3'),('x:252,z:-70','x:-112,z:70'),('CHENGXU','HENGLIAN'),('澄序住区','衡联总部'),('Chengxu','Henglian'),('residential-courtyard','corporate-headquarters'),('现代住宅 · 蓝灰窗格与庭院','企业总部 · 银灰幕墙与空中连廊')]:s=s.replace(a,b)
s=s.replace("if(city.groups.has('HENGLIAN-A'))", "if(city.groups.has('HENGLIAN-MAIN'))")
s=s.replace("for(const b of model.manifest.buildings){", "for(const b of [...model.manifest.buildings,{id:'bridge',name:'空中连廊',x:1.5,z:3,w:21,d:6,height:4.4,floors:1}]){")
s=s.replace("const id='HENGLIAN-'+b.id,g=model.buildings.get(b.id)", "const id='HENGLIAN-'+b.id.toUpperCase(),g=model.groups.get(b.id)")
s=s.replace('width:22,depth:20','width:b.w,depth:b.d').replace('groundY:site.groundY,blockId','groundY:site.groundY+(b.id===\'bridge\'?36.8:0),blockId')
s=s.replace("onlyId.replace('HENGLIAN-','')", "onlyId.replace('HENGLIAN-','').toLowerCase()")
(D/'headquarters-site.js').write_text(s,encoding='utf8')
p=D/'city.js';s=p.read_text(encoding='utf8').replace("'BLK-9','BLK-14']);","'BLK-9','BLK-14','BLK-3']);").replace("side*bx===-112&&[-70,210]", "side*bx===-112&&[-70,70,210]");p.write_text(s,encoding='utf8')
p=D/'main.js';s=p.read_text(encoding='utf8')
s="import {installHeadquarters} from './headquarters-site.js';\nlet headquartersIntegration;\nconst headquartersActivities={people:true,birds:true,mechanical:true,bridge:true};\n"+s
s=s.replace('courtyardIntegration=installCourtyard(city);','courtyardIntegration=installCourtyard(city);headquartersIntegration=installHeadquarters(city);')
s=s.replace('let skylineEnv=null,',"headquartersIntegration.model.root.traverse(o=>{if(o.material?.metalness>.25)skylineReflective.add(o.material);});\nlet skylineEnv=null,")
s=s.replace("'chengxu-residential-courtyard'].includes", "'chengxu-residential-courtyard','henglian-corporate-headquarters'].includes")
s=s.replace('const setCourtyardQuality=',"const setHeadquartersQuality=headquartersIntegration.model.setQuality;\nheadquartersIntegration.model.setQuality=value=>{setHeadquartersQuality(value);replacements.forEach((saved,id)=>{if(id.startsWith('HENGLIAN-'))saved.original.forEach(o=>o.visible=false);});};\nconst setCourtyardQuality=")
s=s.replace('courtyardIntegration.model.setTimeOfDay(p.night*t);','courtyardIntegration.model.setTimeOfDay(p.night*t);headquartersIntegration.model.setTimeOfDay(p.night*t);')
s=s.replace('state.quality=e.target.value;', "state.quality=e.target.value;headquartersIntegration.model.setQuality({cinema:'high',balanced:'medium',fast:'low'}[state.quality]);")
s=s.replace('courtyardIntegration.model.update(dt);', 'courtyardIntegration.model.update(dt);headquartersIntegration.model.setDynamicsEnabled(!state.paused);headquartersIntegration.model.setActivity({wind:state.wind,people:state.traffic&&headquartersActivities.people,birds:headquartersActivities.birds,bridge:headquartersActivities.bridge,mechanical:headquartersActivities.mechanical});headquartersIntegration.model.update(dt);')
s=s.replace('if(modules.length)data.modules=modules;',"if(!onlyId||onlyId.startsWith('HENGLIAN-')){const m=headquartersIntegration.model;modules.push({id:m.manifest.id,blockId:headquartersIntegration.site.blockId,position:m.root.position.toArray(),source:'./headquarters-model.js',snapshotSpace:'world',snapshot:m.exportScene(onlyId)});}\n  if(modules.length)data.modules=modules;")
s=s.replace('window.cityApp={','window.cityApp={headquarters:headquartersIntegration.model,headquartersSite:headquartersIntegration.site,headquartersActivities,')
s=s.replace('const courtyardQuality=courtyardIntegration.model.quality,quality=', 'const headquartersQuality=headquartersIntegration.model.quality,courtyardQuality=courtyardIntegration.model.quality,quality=')
s=s.replace("courtyardIntegration.model.setQuality('high');slabIntegration", "headquartersIntegration.model.setQuality('high');courtyardIntegration.model.setQuality('high');slabIntegration")
s=s.replace('finally{courtyardIntegration.model.setQuality(courtyardQuality);','finally{headquartersIntegration.model.setQuality(headquartersQuality);courtyardIntegration.model.setQuality(courtyardQuality);')
# Preserve the site's existing framing and mobile behavior.
shortcut=s[s.index("$('#courtyard-view').onclick="):s.index("for(const key of Object.keys(courtyardActivities))")]
shortcut=shortcut.replace('courtyard','headquarters').replace('Courtyard','Headquarters')
s+='\n'+shortcut+"\nfor(const key of Object.keys(headquartersActivities))$('#headquarters-'+key).onchange=e=>headquartersActivities[key]=e.target.checked;\n"
p.write_text(s,encoding='utf8')
p=D/'index.html';s=p.read_text(encoding='utf8');controls='<button id="headquarters-view" class="hospital-jump">衡联总部 · BLK-3 ↗</button><details class="park-controls"><summary>总部生活动态</summary>'
for id,label in [('people','总部员工'),('bridge','连廊通行'),('birds','庭院飞鸟'),('mechanical','电梯与风机')]:controls+=f'<label class="skyline-flight-toggle"><span>{label}</span><input id="headquarters-{id}" type="checkbox" checked role="switch"></label>'
controls+='</details>';s=s.replace('<button id="courtyard-view"',controls+'<button id="courtyard-view"');p.write_text(s,encoding='utf8')
p=ROOT/'package.json';d=json.loads(p.read_text(encoding='utf8'));d['scripts']['check']+=' && node --check dist/headquarters-model.js && node --check dist/headquarters-ecology.js && node --check dist/headquarters-stairs.js && node --check dist/headquarters-site.js';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
