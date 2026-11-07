"""Verify the installed BLK-6 parcel using the real city controls and exports."""
import json
import struct
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/garden-integration'
OUT.mkdir(parents=True,exist_ok=True)
checks=[]
errors=[]
network_problems=[]
PRIOR_MODULES=['hospital-campus','skyline-one','mall-complex','shanghai-tower','university-campus','dome-arena','amusement-park','linxu-residential','quiet-city-park','qinghe-sports-field','qianxu-slab-residential']

def check(name,value):
    checks.append({'check':name,'passed':bool(value)})
    (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors},indent=2),encoding='utf8')
    print(('PASS ' if value else 'FAIL ')+name,flush=True)
    if not value:raise AssertionError(name)

def glb_names(path):
    raw=path.read_bytes()
    assert raw[:4]==b'glTF'
    count=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+count])
    return [node.get('name','') for node in doc['nodes']]

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True)
    page.set_default_timeout(45000)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.on('requestfailed',lambda request:network_problems.append({'url':request.url,'failure':request.failure}))
    page.on('response',lambda response:network_problems.append({'url':response.url,'status':response.status}) if response.status>=400 else None)
    try:
        page.goto('http://127.0.0.1:5173',wait_until='networkidle')
        page.wait_for_function('window.cityApp?.ready',timeout=120000,polling=100)
    except Exception as exception:
        diagnostic={'error':repr(exception),'errors':errors,'network_problems':network_problems}
        try:
            diagnostic['page']=page.evaluate("({url:location.href,documentReady:document.readyState,appReady:!!window.cityApp?.ready,appKeys:window.cityApp?Object.keys(cityApp):[],loading:document.querySelector('#load-message')?.textContent??null,loadingPresent:!!document.querySelector('#loading'),canvasCount:document.querySelectorAll('canvas').length,contextLost:window.cityApp?.renderer?.getContext()?.isContextLost()??null})")
        except Exception as inspection_error:
            diagnostic['inspection_error']=repr(inspection_error)
        (OUT/'startup-diagnostic.json').write_text(json.dumps(diagnostic,indent=2,ensure_ascii=True),encoding='utf8')
        print(json.dumps(diagnostic,ensure_ascii=True),flush=True)
        try:page.screenshot(path=str(OUT/'startup-failed.png'),timeout=10000)
        except Exception:pass
        browser.close()
        raise

    check('BLK-6 is the western outer parcel at (-252,-70)',page.evaluate("cityApp.gardenSite.blockId==='BLK-6'&&cityApp.gardenSite.x===-252&&cityApp.gardenSite.z===-70&&cityApp.plan.blocks.find(b=>b.id==='BLK-6').moduleId==='nuanting-garden-housing'"))
    check('four original BLK-6 homes are removed',page.evaluate("['QR-021','QR-022','QR-023','QR-024'].every(id=>!cityApp.scene.getObjectByName(id))"))
    check('four garden houses retain floors and independent records',page.evaluate("['A','B','C','D'].every((id,i)=>{const b=cityApp.plan.buildings.find(b=>b.id==='NUANTING-'+id);return b?.blockId==='BLK-6'&&b.floors===[4,5,5,6][i]&&cityApp.scene.getObjectByName(b.id)})"))

    baseline=(OUT/'city-before-garden.js').read_text(encoding='utf8')
    before=page.evaluate('''async source=>{
      const T=await import('three'),url=URL.createObjectURL(new Blob([source],{type:'text/javascript'})),m=await import(url);
      URL.revokeObjectURL(url);const scene=new T.Scene(),prior=m.buildCity(scene).plan.buildings.filter(b=>b.blockId!=='BLK-6');
      const actual=cityApp.plan.buildings.filter(b=>!b.moduleId),life=m.createLife(scene);
      return {same:prior.length===actual.length&&prior.every(b=>actual.some(a=>JSON.stringify(a)===JSON.stringify(b))),pedestrians:life.walkers.length,cars:life.cars.length};
    }''',baseline)
    check('all other original residences remain unchanged',before['same'])
    check('all prior landmarks including BLK-12 and the river remain',page.evaluate("ids=>ids.every(id=>cityApp.plan.buildings.some(b=>b.moduleId===id))&&cityApp.river.manifest.id==='qinglan-river'",PRIOR_MODULES))
    check('old BLK-6 site furniture is absent from city batches',page.evaluate("async()=>{const m=await import('/city.js'),b=m.exportCity().batches;return b.length>0&&b.every(bucket=>bucket.items.every(i=>i.blockId!=='BLK-6'))}"))

    bounds=page.evaluate('''async()=>{const T=await import('three'),box=new T.Box3();for(const child of cityApp.garden.root.children)if(child.name!=='Nuanting road connections')box.expandByObject(child);return {min:box.min.toArray(),max:box.max.toArray()}}''')
    check('112m parcel stays within BLK-6 and meets sidewalk grade',bounds['min'][0]>=-308.001 and bounds['max'][0]<=-195.999 and bounds['min'][2]>=-126.001 and bounds['max'][2]<=-13.999 and abs(bounds['min'][1]+.06)<.001)
    approaches=page.evaluate('''async()=>{
      const T=await import('three'),names=['Nuanting public entrance','Nuanting vehicle entrance','Nuanting service entrance'];cityApp.garden.root.updateWorldMatrix(true,true);
      const points=[];for(const name of names){const o=cityApp.garden.root.getObjectByName(name);if(!o?.isMesh)return false;const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++)points.push(new T.Vector3().fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld));}
      return points.every(v=>v.x>=-308.01&&v.x<=-195.99&&v.z>=-140.01&&v.z<=.01)&&Math.abs(Math.min(...points.map(v=>v.y))-.085)<.01&&Math.max(...points.map(v=>v.y))>=.339&&Math.abs(Math.min(...points.map(v=>v.z))+140)<.01&&Math.abs(Math.max(...points.map(v=>v.z)))<.01;
    }''')
    check('three entrance ramps reach the existing road surface',approaches)
    check('22 point lights use the parcel world transform',page.evaluate('''async()=>{const T=await import('three'),a=cityApp.gardenLights,f=cityApp.garden.manifest.lightFixtures;cityApp.garden.root.updateWorldMatrix(true,true);return a.length===22&&a.every((l,i)=>l.isPointLight&&l.getWorldPosition(new T.Vector3()).distanceTo(cityApp.garden.root.localToWorld(new T.Vector3(...f[i].position)))<.001)}'''))
    check('city retains one rendering canvas',page.locator('#viewport canvas').count()==1)
    metrics=page.evaluate('cityApp.metrics()')
    check('old BLK-6 walkers are removed and road traffic retained',metrics['pedestrians']==before['pedestrians']-7 and metrics['cars']==before['cars'])

    page.screenshot(path=str(OUT/'city-overview.png'))
    page.locator('#garden-view').click()
    page.wait_for_function('Math.abs(cityApp.controls().target.x+252)<.1&&Math.abs(cityApp.controls().target.z+70)<.1',timeout=90000)
    check('garden shortcut frames the complete BLK-6 parcel',page.evaluate("cityApp.garden.root.visible&&[...cityApp.garden.buildings.values()].every(g=>g.visible)&&Math.abs(cityApp.controls().target.x+252)<.1&&Math.abs(cityApp.controls().target.z+70)<.1"))
    page.screenshot(path=str(OUT/'garden-context.png'))
    selections=page.evaluate("()=>['A','B','C','D'].every(id=>{cityApp.select('NUANTING-'+id);return cityApp.state.selected.id==='NUANTING-'+id})")
    check('all four garden houses can be selected independently',selections)

    page.locator('#pause').click()
    time=page.evaluate('cityApp.garden.simulationTime')
    page.wait_for_timeout(250)
    check('global pause freezes garden animation',time==page.evaluate('cityApp.garden.simulationTime'))
    page.locator('#pause').click()
    page.wait_for_function('(t)=>cityApp.garden.simulationTime>t',arg=time)
    check('resume advances garden simulation',page.evaluate('cityApp.garden.simulationTime')>time)
    page.locator('#traffic').uncheck()
    page.wait_for_function("!cityApp.garden.root.getObjectByName('Resident 0').visible&&!cityApp.garden.root.getObjectByName('Moving car 0').visible")
    check('global traffic controls garden residents and vehicles',page.evaluate("!cityApp.garden.root.getObjectByName('Resident 0').visible&&!cityApp.garden.root.getObjectByName('Moving car 0').visible"))
    page.locator('#traffic').check()

    for selector in ['#garden-people','#garden-vehicles']:
        page.locator(selector).evaluate("e=>{const d=e.closest('details');if(d)d.open=true}")
    page.locator('#garden-people').uncheck()
    page.wait_for_function("!cityApp.garden.root.getObjectByName('Resident 0').visible&&cityApp.garden.root.getObjectByName('Moving car 0').visible")
    check('resident switch preserves vehicle activity',page.evaluate("!cityApp.garden.root.getObjectByName('Resident 0').visible&&cityApp.garden.root.getObjectByName('Moving car 0').visible"))
    page.locator('#garden-people').check()
    page.locator('#garden-vehicles').uncheck()
    page.wait_for_function("cityApp.garden.root.getObjectByName('Resident 0').visible&&!cityApp.garden.root.getObjectByName('Moving car 0').visible")
    check('vehicle switch preserves resident activity',page.evaluate("cityApp.garden.root.getObjectByName('Resident 0').visible&&!cityApp.garden.root.getObjectByName('Moving car 0').visible"))
    page.locator('#garden-vehicles').check()
    page.locator('#garden-people').evaluate("e=>{const d=e.closest('details');if(d)d.open=false}")

    page.locator('#wind').uncheck()
    page.wait_for_timeout(150)
    curtain=page.evaluate("(()=>{let c;cityApp.garden.root.traverse(o=>{if(!c&&o.name.startsWith('Curtain '))c=o});return {name:c.name,x:c.position.x,time:cityApp.garden.simulationTime}})()")
    page.wait_for_function('(t)=>cityApp.garden.simulationTime>t+.2',arg=curtain['time'])
    check('natural dynamics switch freezes curtain wind while time advances',page.evaluate('(c)=>cityApp.garden.root.getObjectByName(c.name).position.x===c.x',curtain))
    page.locator('#wind').check()
    page.locator('#quality').select_option('fast')
    check('city quality reduces garden grass detail',page.evaluate("cityApp.garden.quality==='low'&&cityApp.garden.root.getObjectByName('Individual grass blades').count===1000"))
    page.locator('#quality').select_option('balanced')
    page.locator('[data-time=night]').click()
    page.wait_for_function("(()=>{let lit=false;cityApp.garden.root.traverse(o=>{if(o.material?.name==='window-lit'&&o.material.emissiveIntensity>1.3)lit=true});return lit})()",timeout=90000)
    check('night activates garden windows and all 22 point lights',page.evaluate('cityApp.gardenLights.length===22&&cityApp.gardenLights.every(l=>l.intensity>0)'))
    page.screenshot(path=str(OUT/'garden-night.png'))
    page.locator('[data-time=morning]').click()
    page.wait_for_function('cityApp.gardenLights.every(l=>l.intensity===0)',timeout=90000)
    check('morning turns garden point lights off',page.evaluate('cityApp.gardenLights.every(l=>l.intensity===0)'))

    page.evaluate("cityApp.select('NUANTING-D')")
    page.locator('#focus-building').click()
    page.wait_for_function("cityApp.scene.getObjectByName('NUANTING-D').visible&&!cityApp.scene.getObjectByName('NUANTING-A').visible&&!cityApp.scene.getObjectByName('SKY-ONE').visible")
    check('single-house view isolates D from other city buildings',page.evaluate("['A','B','C'].every(id=>!cityApp.scene.getObjectByName('NUANTING-'+id).visible)&&cityApp.scene.getObjectByName('NUANTING-D').visible"))
    page.screenshot(path=str(OUT/'garden-D-isolated.png'))
    with page.expect_download(timeout=180000) as result:page.locator('#export-building').click()
    result.value.save_as(OUT/'NUANTING-D.glb')
    names=glb_names(OUT/'NUANTING-D.glb')
    check('single GLB contains D and excludes the other houses','NUANTING-D' in names and all(n not in names for n in ['NUANTING-A','NUANTING-B','NUANTING-C','SKY-ONE']))
    single=page.evaluate("(()=>{const m=cityApp.exportCity('NUANTING-D').modules.find(m=>m.id==='nuanting-garden-housing');return {owners:[...new Set(m.snapshot.objects.map(o=>o.owner))],objects:m.snapshot.objects.length,world:m.snapshotSpace}})()")
    check('single JSON filters ownership to NUANTING-D',single['owners']==['NUANTING-D'] and single['objects']>1000 and single['world']=='world')

    page.evaluate("cityApp.select('SKY-ONE')")
    page.locator('#focus-building').click()
    page.wait_for_function("!cityApp.scene.getObjectByName('NUANTING-D').visible&&cityApp.scene.getObjectByName('SKY-ONE').visible")
    exported=page.evaluate("(()=>{const all=cityApp.exportCity(),g=all.modules.find(m=>m.id==='nuanting-garden-housing');return {modules:all.modules.map(m=>m.id),block:g.blockId,world:g.snapshotSpace,objects:g.snapshot.objects.length,owners:[...new Set(g.snapshot.objects.map(o=>o.owner))],finite:g.snapshot.objects.every(o=>o.matrix.every(Number.isFinite)),hidden:[...cityApp.garden.buildings.values()].every(o=>!o.visible),quality:cityApp.garden.quality}})()")
    check('full JSON includes the complete garden while another building is isolated',exported['block']=='BLK-6' and exported['world']=='world' and exported['objects']>20000 and exported['finite'] and exported['hidden'] and exported['quality']=='medium' and all('NUANTING-'+i in exported['owners'] for i in ['A','B','C','D']) and all(i in exported['modules'] for i in PRIOR_MODULES))
    with page.expect_download(timeout=300000) as result:page.locator('#export').click()
    result.value.save_as(OUT/'town-with-garden.glb')
    names=glb_names(OUT/'town-with-garden.glb')
    check('full GLB preserves all garden houses and prior landmarks',all(n in names for n in ['NUANTING-A','NUANTING-B','NUANTING-C','NUANTING-D','QINGHE-SPORTS','LINXU-A','SKY-ONE','ARENA-DOME','RIVER-QINGLAN','SKYDAY-PARK','SENYIN-PARK','QIANXU-RESIDENTIAL']))
    page.locator('#home').click()
    page.locator('[data-view=free]').click()
    page.wait_for_function('cityApp.state.freeView')
    check('city free camera remains available',page.evaluate('cityApp.state.freeView'))
    page.keyboard.press('Escape')

    page.set_viewport_size({'width':420,'height':880})
    if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
    page.locator('#garden-view').click()
    page.wait_for_function('Math.abs(cityApp.controls().target.x+252)<.1&&Math.abs(cityApp.controls().target.z+70)<.1',timeout=90000)
    fitting=page.evaluate('''async()=>{const T=await import('three'),box=new T.Box3().setFromObject(cityApp.garden.root),c=cityApp.camera();c.updateMatrixWorld();return [box.min.x,box.max.x].every(x=>[box.min.y,box.max.y].every(y=>[box.min.z,box.max.z].every(z=>{const v=new T.Vector3(x,y,z).project(c);return Math.abs(v.x)<1&&Math.abs(v.y)<1})))}''')
    check('mobile shortcut fits the full parcel and closes settings',fitting and page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'))
    page.screenshot(path=str(OUT/'garden-mobile.png'))
    check('no JavaScript or WebGL errors',not errors)
    (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'bounds':bounds,'single':single,'snapshot':exported,'metrics':page.evaluate('cityApp.metrics()')},indent=2),encoding='utf8')
    print(json.dumps({'passed':len(checks)}),flush=True)
    browser.close()
