"""Verify the real BLK-9 integration, city controls, exports and native scene preservation."""
import json,struct,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/office-integration';OUT.mkdir(parents=True,exist_ok=True)
baseline=(OUT/'city-before-office.js').read_text(encoding='utf8') if (OUT/'city-before-office.js').exists() else subprocess.check_output(['git','show','96bf3030209d0bb3d7a1726a0a9cffb9c02f8ac2:dist/city.js'],cwd=ROOT).decode('utf8')
checks=[];errors=[]
def check(name,result):
    checks.append({'check':name,'passed':bool(result)});print(('PASS ' if result else 'FAIL ')+name,flush=True)
    (OUT/'logic-verification.json').write_text(json.dumps({'checks':checks,'errors':errors},indent=2),encoding='utf8')
    if not result:raise AssertionError(name)
def glb(path):
    data=path.read_bytes();assert data[:4]==b'glTF';n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);return [i.get('name','') for i in doc['nodes']]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
    page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True);page.set_default_timeout(180000)
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    # Verify UI/model/export integration with pixels suspended. Real city and
    # isolated tower renders are verified separately in the same output folder.
    source=(ROOT/'dist/main.js').read_text(encoding='utf8').replace("$('#viewport').appendChild(renderer.domElement);","$('#viewport').appendChild(renderer.domElement);renderer.render=()=>{};",1)
    page.route('**/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source))
    page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready',polling=100,timeout=360000)
    check('one city canvas',page.locator('canvas').count()==1)
    check('BLK-9 has the single correct landmark',page.evaluate("(()=>{const a=cityApp,b=a.plan.blocks.find(b=>b.id==='BLK-9'),r=a.plan.buildings.filter(b=>b.blockId==='BLK-9');return b.x===112&&b.z===-210&&b.moduleId==='jiheng-landmark-office'&&r.length===1&&r[0].id==='JIHENG-ONE'&&r[0].floors===46&&r[0].height===184})()"))
    check('four original houses and their furniture removed',page.evaluate("(()=>{const a=cityApp,ids=['QR-033','QR-034','QR-035','QR-036'];return ids.every(id=>!a.plan.buildings.some(b=>b.id===id))&&a.scene.getObjectByName('Qianren-City').children.every(o=>!ids.includes(o.name))})()"))
    preservation=page.evaluate('''async(source)=>{
      const T=await import('three'),module=await import(URL.createObjectURL(new Blob([source],{type:'text/javascript'}))),scene=new T.Scene(),old=module.buildCity(scene),life=module.createLife(scene);
      const wanted=old.plan.buildings.filter(b=>b.blockId!=='BLK-9'),current=cityApp.plan.buildings.filter(b=>b.id.startsWith('QR-'));
      const buildings=JSON.stringify(wanted)===JSON.stringify(current),nativeCars=life.cars.length;
      const oldWorld=[...old.buckets.values()].filter(b=>!['base','soil','asphalt'].includes(b.material)).map(b=>({...b,items:b.items.filter(i=>i.blockId!=='BLK-9')})).filter(b=>b.items.length&& !['QR-033','QR-034','QR-035','QR-036'].includes(b.owner));
      const nowModule=await import('./city.js');const now=nowModule.exportCity().batches.filter(b=>!['base','soil','asphalt'].includes(b.material));
      return{buildings,nativeCars,oldWalkers:life.walkers.length,furniture:JSON.stringify(oldWorld)===JSON.stringify(now)};
    }''',baseline)
    check('all other native buildings exactly preserved',preservation['buildings'])
    check('other native furniture exactly preserved',preservation['furniture'])
    check('native city traffic unchanged except seven replaced parcel walkers',page.evaluate('cityApp.metrics().cars')==preservation['nativeCars'] and page.evaluate('cityApp.metrics().pedestrians')==preservation['oldWalkers']-7)
    prior=['hospital-campus','skyline-one','mall-complex','shanghai-tower','university-campus','dome-arena','amusement-park','linxu-residential','zongyu-mixeduse','qinghe-sports-field','qianxu-slab-residential','nuanting-garden-housing']
    check('all twelve existing building modules and river preserved',page.evaluate('(ids)=>ids.every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))&&!!cityApp.river',prior))
    bounds=page.evaluate('''async()=>{const T=await import('three'),a=cityApp,b=new T.Box3().setFromObject(a.office.groups.get('site')),root=new T.Box3();for(const g of a.office.groups.values())root.union(new T.Box3().setFromObject(g));return{min:root.min.toArray(),max:root.max.toArray(),position:a.office.root.position.toArray(),children:a.office.root.children.map(g=>g.name)}}''')
    check('native square and height align to city ground',all(abs(v-e)<.015 for v,e in zip(bounds['min'],[56,-2.46,-266])) and all(abs(v-e)<.015 for v,e in zip(bounds['max'],[168,184.34,-154])))
    check('three graded street approaches have upward normals',page.evaluate('''()=>{const g=cityApp.office.root.getObjectByName('Jiheng road connections');return g.children.length===3&&g.children.every(o=>o.geometry.attributes.normal.getY(0)>0)&&g.children.every(o=>{const a=o.geometry.attributes.position.array;return [...a].filter((_,i)=>i%3===1).some(y=>Math.abs(y+cityApp.officeSite.groundY-.085)<1e-6)})}'''))
    check('city ground is cut below the basement ramp',page.evaluate('''async()=>{const {exportCity}=await import('./city.js');return exportCity().batches.filter(b=>b.owner==='world'&&['base','soil','asphalt'].includes(b.material)).every(b=>b.items.every(i=>{const [x,y,z]=i.p,[w,h,d]=i.s;return !(x-w/2<72.5&&x+w/2>67.5&&z-d/2<-192&&z+d/2>-225)}))}'''))
    check('sixteen real lights placed in the new parcel',page.evaluate('cityApp.officeLights.length===16&&cityApp.officeLights.every(l=>l.isPointLight&&l.parent.parent===cityApp.office.root)'))
    None
    page.locator('#office-view').click();page.wait_for_function('Math.abs(cityApp.controls().target.x-112)<.005&&Math.abs(cityApp.controls().target.z+210)<.005',polling=100,timeout=180000)
    check('landmark shortcut selects BLK-9 and fits its center',page.evaluate("cityApp.state.selected.id==='JIHENG-ONE'&&Math.abs(cityApp.controls().target.x-112)<.05&&Math.abs(cityApp.controls().target.z+210)<.05"))
    None
    check('building metadata displayed', '184' in page.locator('#building-detail').inner_text() and 'BLK-9' in page.locator('#building-id').inner_text())
    page.locator('#pause').click();t=page.evaluate('cityApp.office.simulationTime');page.wait_for_timeout(220);check('global pause freezes the tower',t==page.evaluate('cityApp.office.simulationTime'))
    page.locator('#pause').click();page.wait_for_function('(t)=>cityApp.office.simulationTime>t',arg=t,polling=100);check('global resume advances tower',page.evaluate('cityApp.office.simulationTime')>t)
    page.locator('#traffic').uncheck();page.wait_for_timeout(150);check('global traffic controls office people and cars',page.evaluate("!cityApp.office.root.getObjectByName('Office pedestrian 0').visible&&!cityApp.office.root.getObjectByName('Office car 0').visible"));page.locator('#traffic').check()
    page.locator('details').filter(has=page.locator('#office-people')).locator('summary').click()
    page.locator('#office-people').uncheck();page.wait_for_timeout(150);check('office people can be controlled independently',page.evaluate("!cityApp.office.root.getObjectByName('Office pedestrian 0').visible&&cityApp.office.root.getObjectByName('Office car 0').visible"));page.locator('#office-people').check()
    page.locator('#office-mechanical').uncheck();fan=page.evaluate("cityApp.office.root.getObjectByName('Cooling fan 0').rotation.y");page.wait_for_timeout(250);check('office machinery control freezes fan',fan==page.evaluate("cityApp.office.root.getObjectByName('Cooling fan 0').rotation.y"));page.locator('#office-mechanical').check()
    page.locator('#wind').uncheck();t=page.evaluate('cityApp.office.windTime');page.wait_for_timeout(200);check('global wind freezes tower foliage clock',t==page.evaluate('cityApp.office.windTime'));page.locator('#wind').check()
    page.locator('#quality').select_option('fast');check('global quality propagates to tower',page.evaluate("cityApp.office.quality==='low'&&cityApp.officeLights.every(l=>!l.visible)"));page.locator('#quality').select_option('balanced')
    page.locator('[data-time="night"]').click();page.wait_for_function("cityApp.office.materials['office-lit'].emissiveIntensity>1.3",polling=100);check('night lights and lit office windows follow city',page.evaluate("cityApp.officeLights.every(l=>l.intensity>0)&&cityApp.office.materials['office-lit'].emissiveIntensity>1"));None
    page.locator('[data-time="morning"]').click();page.wait_for_function('cityApp.officeLights.every(l=>l.intensity===0)',polling=100);check('day turns plaza lights off',page.evaluate('cityApp.officeLights.every(l=>l.intensity===0)'))
    page.locator('#focus-building').click();page.wait_for_function('Math.abs(cityApp.controls().target.x-112)<.005&&Math.abs(cityApp.controls().target.z+210)<.005',polling=100);check('single-building architecture view focuses on tower',page.evaluate("document.querySelector('[data-view=architecture]').classList.contains('active')"));None
    data=page.evaluate("(()=>{const a=cityApp,d=a.exportCity('JIHENG-ONE'),m=d.modules[0];return{count:d.modules.length,id:m.id,blockId:m.blockId,space:m.snapshotSpace,position:m.position,objects:m.snapshot.objects.length,owners:[...new Set(m.snapshot.objects.map(o=>o.owner))],quality:a.office.quality}})()")
    check('selected JSON includes complete world-space module',data['count']==1 and data['id']=='jiheng-landmark-office' and data['blockId']=='BLK-9' and data['space']=='world' and data['objects']>10000 and data['quality']=='medium')
    with page.expect_download(timeout=180000) as dl:page.locator('#export-building').click()
    selected=OUT/'JIHENG-ONE.glb';dl.value.save_as(selected);names=glb(selected);check('selected GLB contains only complete landmark',all(n in names for n in ['JIHENG-ONE','lower','middle','upper','podium','roof','site']) and 'NUANTING-A' not in names)
    page.evaluate("cityApp.select('NUANTING-A')");page.locator('#focus-building').click();page.wait_for_timeout(2100)
    check('full JSON includes tower while another building is isolated',page.evaluate("cityApp.exportCity().modules.find(m=>m.id==='jiheng-landmark-office').snapshot.objects.length>10000"))
    with page.expect_download(timeout=240000) as dl:page.locator('#export').click()
    whole=OUT/'town-with-office.glb';dl.value.save_as(whole);names=glb(whole);check('whole city GLB preserves old modules and tower',all(n in names for n in ['JIHENG-ONE','NUANTING-A','QIANXU-RESIDENTIAL','QINGHE-SPORTS','SHANGHAI-TOWER']))
    page.locator('#office-view').click();page.wait_for_timeout(2200);page.locator('[data-view="free"]').click();check('landmark works with existing free camera',page.evaluate('cityApp.state.freeView'));page.locator('#free-view-exit').click()
    page.set_viewport_size({'width':390,'height':844});page.wait_for_function('Math.abs(cityApp.camera().aspect-390/844)<.000001',polling=100);page.locator('#collapse').click() if page.locator('#panel-content').is_hidden() else None
    expected=page.evaluate('''async()=>{const T=await import('three'),a=cityApp,b=new T.Box3().setFromObject(a.office.root),sp=b.getBoundingSphere(new T.Sphere()),c=b.getCenter(new T.Vector3()),half=T.MathUtils.degToRad(a.camera().fov/2),angle=Math.min(half,Math.atan(Math.tan(half)*a.camera().aspect));return c.add(new T.Vector3(-160,130,180).normalize().multiplyScalar(sp.radius/Math.sin(angle)*1.12)).toArray()}''')
    page.locator('#office-view').click();page.wait_for_function('(p)=>{const c=cityApp.camera().position;return Math.hypot(c.x-p[0],c.y-p[1],c.z-p[2])<.05}',arg=expected,polling=100);check('mobile shortcut collapses control panel',page.locator('#panel-content').is_hidden());check('mobile has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth===390'))
    ndc=page.evaluate('''async()=>{const T=await import('three'),a=cityApp,b=new T.Box3();for(const g of a.office.groups.values())b.union(new T.Box3().setFromObject(g));a.camera().updateMatrixWorld();return [b.min.x,b.max.x].flatMap(x=>[b.min.y,b.max.y].flatMap(y=>[b.min.z,b.max.z].map(z=>new T.Vector3(x,y,z).project(a.camera()).toArray())))}''')
    check('complete parcel and tower fit mobile screen',all(abs(v[0])<1 and abs(v[1])<1 for v in ndc));None
    check('no JavaScript errors',not errors)
    (OUT/'logic-verification.json').write_text(json.dumps({'rendering_suspended':True,'checks':checks,'errors':errors,'bounds':bounds,'preservation':preservation,'selected_json':data,'metrics':page.evaluate('cityApp.metrics()')},indent=2),encoding='utf8');browser.close()
