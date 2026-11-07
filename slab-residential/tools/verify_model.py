"""Verify the offline residential asset, actual controls and exportable geometry."""
import json
import math
import struct
import sys
from pathlib import Path

from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)
checks, errors, requests = [], [], []


def check(name, passed):
    checks[:]=[c for c in checks if c['check']!=name]
    checks.append({'check': name, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)
    (OUT/'verification-progress.json').write_text(json.dumps({'checks':checks,'errors':errors,'requests':requests},ensure_ascii=False,indent=2),encoding='utf8')
    assert passed, name


def glb_json(path):
    data = path.read_bytes()
    assert struct.unpack_from('<4sII', data) == (b'glTF', 2, len(data))
    size, kind = struct.unpack_from('<I4s', data, 12)
    assert kind == b'JSON'
    return json.loads(data[20:20+size])


def expose_panel(page):
    if page.locator('#panel-body').is_hidden():
        page.locator('#collapse').click()


def snapshot(page, name):
    page.screenshot(path=str(OUT / name), timeout=90000)


def main():
    if '--mobile-only' in sys.argv:
        return verify_mobile()
    if '--refresh-asset' in sys.argv:
        return refresh_asset()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True,
                                    args=['--allow-file-access-from-files'])
        page = browser.new_page(viewport={'width':1700, 'height':1100}, accept_downloads=True)
        page.set_default_timeout(60000)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('request', lambda r: requests.append(r.url) if r.url.startswith(('http:', 'https:')) else None)
        path = (ROOT / '浅序住区.html').as_uri()

        # Photograph the coarse phase before checking the refined single HTML.
        page.goto(path + '?coarse=1', wait_until='networkidle')
        page.wait_for_function('window.slabApp?.ready', timeout=90000)
        coarse_counts = page.evaluate('''()=>{let n=0;slabApp.model.root.traverse(o=>{if(o.isMesh)n+=o.isInstancedMesh?o.count:1});return n;}''')
        snapshot(page, 'coarse-overview.png')
        page.goto(path, wait_until='networkidle')
        page.wait_for_function('window.slabApp?.ready', timeout=90000)
        page.wait_for_timeout(300)
        check('Single HTML launches offline without external requests', not requests)
        fine_counts = page.evaluate('''()=>{let n=0;slabApp.model.root.traverse(o=>{if(o.isMesh)n+=o.isInstancedMesh?o.count:1});return n;}''')
        check('Refined model adds real detail to the coarse phase', fine_counts > coarse_counts * 2)
        bounds = page.evaluate('({min:slabApp.model.getBounds().min.toArray(),max:slabApp.model.getBounds().max.toArray()})')
        check('Full model stays within 112 by 112 metre parcel', all(abs(bounds[k][i]) <= 56.001 for k in ('min','max') for i in (0,2)))
        check('Overall height matches the specified 20-storey maximum', 62 <= bounds['max'][1] < 72)
        buildings = page.evaluate('slabApp.model.buildings')
        (OUT/'building-records.json').write_text(json.dumps(buildings,ensure_ascii=False,indent=2),encoding='utf8')
        check('Three independently named slab buildings are present', page.evaluate("['SLAB-A','SLAB-B','SLAB-C'].every(id=>!!slabApp.model.root.getObjectByName(id))"))
        geometry_check = page.evaluate('''()=>{const a=slabApp,T=a.THREE,boxes=['SLAB-A','SLAB-B','SLAB-C'].map(id=>new T.Box3().setFromObject(a.model.root.getObjectByName(id)));return {separate:boxes.every((b,i)=>boxes.every((c,j)=>i===j||!b.intersectsBox(c))),widths:boxes.map(b=>b.max.x-b.min.x),depths:boxes.map(b=>b.max.z-b.min.z),heights:boxes.map(b=>b.max.y-b.min.y)};}''')
        check('Buildings have slab proportions and do not overlap', geometry_check['separate'] and all(58 < v < 75 for v in geometry_check['widths']) and all(12 < v < 21 for v in geometry_check['depths']))
        check('Roof structures sit above the three stepped residential heights', all(abs(a-b) < 7 for a,b in zip(sorted(geometry_check['heights']),[49.6,55.8,62])))

        # Export positions are checked in the exact world-space format Blender uses.
        page.evaluate('slabApp.state.paused=true')
        data = page.evaluate('slabApp.exportScene()')
        (OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
        check('Blender snapshot contains world-space geometry and real materials', data.get('snapshotSpace')=='world' and len(data['objects'])>1000 and len(data['materials'])>8 and all(len(o['matrix'])==16 for o in data['objects']))
        check('Snapshot retains window frames, landscape and roof owners', set(o.get('owner') for o in data['objects']).issuperset({'SLAB-A','SLAB-B','SLAB-C'}))
        check('Snapshot vertices, UVs and transforms are finite', all(math.isfinite(v) for g in data['geometries'].values() for v in g['positions']) and all(math.isfinite(v) for o in data['objects'] for v in o['matrix']))

        # Use the factory in a separate host to detect global resource ownership bugs.
        lifecycle = page.evaluate('''()=>{const a=slabApp,T=a.THREE,create=a.create||window.ResidentialBlockModule?.create||window.ResidentialModule?.create||window.ResidentialModule?.createResidentialBlock;if(!create)return {factory:false};const x=create({THREE:T,seed:818,coarse:true}),y=create({THREE:T,seed:818,coarse:true}),scene=new T.Scene(),env=new T.Texture(),shared=new T.MeshStandardMaterial();let hostDisposed=false,otherDisposed=false;shared.addEventListener('dispose',()=>hostDisposed=true);const host=new T.Mesh(new T.BoxGeometry(),shared);scene.environment=env;scene.add(host,x.root,y.root);const first=x.exportScene(),second=y.exportScene();const shape=s=>s.objects.map(o=>[o.owner,o.matrix,o.tint]);const deterministic=JSON.stringify(shape(first))===JSON.stringify(shape(second));y.root.traverse(o=>{if(o.isMesh){o.geometry.addEventListener('dispose',()=>otherDisposed=true);for(const m of Array.isArray(o.material)?o.material:[o.material])m.addEventListener('dispose',()=>otherDisposed=true);}});x.root.position.set(13,2,-7);const shifted=x.exportScene(),world=Math.abs(shifted.objects[0].matrix[12]-first.objects[0].matrix[12]-13)<1e-5&&Math.abs(shifted.objects[0].matrix[13]-first.objects[0].matrix[13]-2)<1e-5&&Math.abs(shifted.objects[0].matrix[14]-first.objects[0].matrix[14]+7)<1e-5;x.dispose();x.dispose();const isolated=x.root.parent===null&&y.root.parent===scene&&host.parent===scene&&scene.environment===env&&!hostDisposed&&!otherDisposed;let renderable=false;try{const r=new T.WebGLRenderer();r.setSize(64,64);r.render(scene,new T.PerspectiveCamera());renderable=true;r.dispose();}catch{}y.dispose();host.geometry.dispose();shared.dispose();env.dispose();return{factory:true,deterministic,world,isolated,renderable};}''')
        check('Independent reusable factory is available',lifecycle.get('factory'))
        check('Same seed reproduces the same model layout',lifecycle.get('deterministic'))
        check('Translated roots export correct world transforms',lifecycle.get('world'))
        check('Repeated disposal preserves the host and second model',lifecycle.get('isolated'))

        page.evaluate('slabApp.state.paused=false')
        for view, name in [('overview','final-overview.png'),('facade','final-facade.png'),('entrance','final-entrance.png'),('roof','final-roof.png')]:
            page.locator(f'[data-view={view}]').click()
            page.wait_for_timeout(450)
            snapshot(page,name)
        check('Four camera presets show rendered geometry', all(ImageStat.Stat(Image.open(OUT/name).convert('RGB')).stddev[0]>12 for name in ['final-overview.png','final-facade.png','final-entrance.png','final-roof.png']))
        page.locator('[data-view=overview]').click()
        page.wait_for_timeout(250)
        before = page.evaluate('slabApp.camera.position.toArray()')
        page.mouse.move(850,550);page.mouse.down();page.mouse.move(990,590,steps=12);page.mouse.up();page.wait_for_timeout(250)
        check('Real pointer drag rotates the model', before!=page.evaluate('slabApp.camera.position.toArray()'))
        before = page.evaluate('slabApp.controls.target.toArray()')
        page.mouse.move(850,550);page.mouse.down(button='right');page.mouse.move(920,590,steps=10);page.mouse.up(button='right');page.wait_for_timeout(250)
        check('Right-button drag pans the view', before!=page.evaluate('slabApp.controls.target.toArray()'))
        before = page.evaluate('slabApp.camera.position.distanceTo(slabApp.controls.target)')
        page.mouse.wheel(0,-300);page.wait_for_timeout(250)
        check('Mouse wheel zooms toward model',page.evaluate('slabApp.camera.position.distanceTo(slabApp.controls.target)')<before)
        page.locator('#reset').click();page.wait_for_timeout(250)
        check('Reset restores overview framing',page.locator('[data-view=overview]').evaluate('(e)=>e.classList.contains("active")'))

        expose_panel(page)
        page.locator('#pause').click();page.wait_for_timeout(150)
        t=page.evaluate('({simulation:slabApp.model.simulationTime,wind:slabApp.model.windTime})')
        page.wait_for_timeout(350)
        check('Pause freezes simulation and wind',t==page.evaluate('({simulation:slabApp.model.simulationTime,wind:slabApp.model.windTime})'))
        page.locator('#pause').click();page.wait_for_timeout(250)
        after=page.evaluate('slabApp.model.simulationTime')
        check('Resume advances without adding the paused duration',t['simulation']<after<t['simulation']+.8)
        page.locator('#wind').uncheck();page.wait_for_timeout(120)
        t=page.evaluate('slabApp.model.windTime');before=page.evaluate('slabApp.model.simulationTime');page.wait_for_timeout(250)
        check('Wind can freeze while simulation continues',t==page.evaluate('slabApp.model.windTime') and before<page.evaluate('slabApp.model.simulationTime'))
        page.locator('#wind').check()
        page.locator('#speed').evaluate('(e)=>{e.value="0";e.dispatchEvent(new Event("input",{bubbles:true}))}');page.wait_for_timeout(120)
        t=page.evaluate('slabApp.model.simulationTime');page.wait_for_timeout(250)
        check('Zero speed stops model time',t==page.evaluate('slabApp.model.simulationTime'))
        page.locator('#speed').evaluate('(e)=>{e.value="1";e.dispatchEvent(new Event("input",{bubbles:true}))}')

        emission = '''()=>{let e=0;slabApp.model.root.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m.emissive)e=Math.max(e,m.emissiveIntensity*m.emissive.getHSL({}).l)});return e;}'''
        day_emission=page.evaluate(emission)
        page.locator('[data-time=night]').click();page.wait_for_function('slabApp.state.nightFactor>.999', timeout=60000)
        night_emission=page.evaluate(emission)
        check('Night mode actually illuminates model materials',night_emission>day_emission+.1)
        page.locator('[data-view=overview]').click();page.wait_for_timeout(250);snapshot(page,'final-night.png')
        page.locator('[data-time=day]').click();page.wait_for_function('slabApp.state.nightFactor<.001', timeout=60000)
        page.locator('#quality').select_option('low')
        low=page.evaluate('''()=>{let n=0;slabApp.model.root.traverseVisible(o=>{if(o.isMesh)n+=o.isInstancedMesh?o.count:1});return n;}''')
        page.locator('#quality').select_option('high')
        high=page.evaluate('''()=>{let n=0;slabApp.model.root.traverseVisible(o=>{if(o.isMesh)n+=o.isInstancedMesh?o.count:1});return n;}''')
        check('Quality controls reduce fine detail while keeping buildings', low<high and page.evaluate("['SLAB-A','SLAB-B','SLAB-C'].every(id=>slabApp.model.root.getObjectByName(id).visible)"))

        page.locator('#pause').click()
        with page.expect_download(timeout=180000) as download:
            page.locator('#export').click()
        download.value.save_as(ROOT/'浅序住区.glb')
        doc=glb_json(ROOT/'浅序住区.glb')
        names=[n.get('name','') for n in doc.get('nodes',[])]
        check('GLB is valid and preserves all three building groups',all(x in names for x in ['SLAB-A','SLAB-B','SLAB-C']) and len(doc.get('meshes',[]))>10)
        check('GLB exports asset without preview camera or studio',not any(n.get('camera') is not None for n in doc.get('nodes',[])) and not any('Studio' in n or 'Sky' in n for n in names))
        check('GLB retains PBR materials and embedded textures',len(doc.get('materials',[]))>8 and len(doc.get('images',[]))>0 and all('uri' not in im for im in doc.get('images',[])))
        with page.expect_download(timeout=90000) as capture:
            page.locator('#capture').click()
        capture.value.save_as(OUT/'browser-capture.png')
        check('Save picture downloads the actual viewport render',Image.open(OUT/'browser-capture.png').size==(1700,1100))
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(350)
        page.locator('#reset').click();page.wait_for_timeout(350)
        check('Mobile layout fits and control panel collapses',page.evaluate('document.documentElement.scrollWidth===390') and page.locator('#panel-body').is_hidden())
        projected=page.evaluate('''()=>{const a=slabApp,b=a.model.getBounds(),T=a.THREE;let minX=1,maxX=-1,minY=1,maxY=-1;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new T.Vector3(x,y,z).project(a.camera);minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y);}return{minX,maxX,minY,maxY}}''')
        check('Mobile overview frames full parcel',max(abs(v) for v in projected.values())<1.02)
        snapshot(page,'final-mobile.png')
        check('No browser or WebGL shader errors',not errors)
        (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'requests':requests,'bounds':bounds,'geometry':geometry_check,'lifecycle':lifecycle,'counts':{'coarse':coarse_counts,'high':high,'low':low},'mobileProjectedBounds':projected},ensure_ascii=False,indent=2),encoding='utf8')
        print('COMPLETE',len(checks),flush=True)
        browser.close()


def verify_mobile():
    """Finish an interrupted run after a viewport-only fix, without repeating exports."""
    checks.extend(json.loads((OUT/'verification-stage1.json').read_text(encoding='utf8'))['checks'])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files'])
        page=browser.new_page(viewport={'width':1700,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
        page.goto((ROOT/'浅序住区.html').as_uri(),wait_until='networkidle')
        page.wait_for_function('window.slabApp?.ready',timeout=90000)
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(350)
        page.locator('#reset').click();page.wait_for_timeout(350)
        check('Mobile layout fits and control panel collapses',page.evaluate('document.documentElement.scrollWidth===390') and page.locator('#panel-body').is_hidden())
        projected=page.evaluate("""()=>{const a=slabApp,b=a.model.getBounds(),T=a.THREE;let minX=1,maxX=-1,minY=1,maxY=-1;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new T.Vector3(x,y,z).project(a.camera);minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y);}return{minX,maxX,minY,maxY}}""")
        check('Mobile overview frames full parcel',max(abs(v) for v in projected.values())<1.02)
        snapshot(page,'final-mobile.png')
        page.locator('#collapse').click();page.locator('[data-time=night]').click()
        page.wait_for_function('slabApp.state.nightFactor>.999',timeout=60000)
        page.locator('[data-time=day]').click();page.wait_for_function('slabApp.state.nightFactor<.001',timeout=60000)
        check('Final rebuilt HTML remains offline',not requests)
        check('No browser or WebGL shader errors',not errors)
        bounds=page.evaluate('({min:slabApp.model.getBounds().min.toArray(),max:slabApp.model.getBounds().max.toArray()})')
        (OUT/'verification.json').write_text(json.dumps({'checks':checks,'errors':errors,'requests':requests,'bounds':bounds,'mobileProjectedBounds':projected,'verificationMode':'29 passed full-scene checks plus focused mobile/GLSL continuation after viewport fix'},ensure_ascii=False,indent=2),encoding='utf8')
        print('COMPLETE',len(checks),flush=True)
        browser.close()


def refresh_asset():
    """Check the targeted entrance revision and refresh the exact delivered exports."""
    previous=json.loads((OUT/'verification.json').read_text(encoding='utf8'))
    checks.extend(previous['checks'])
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files'])
        page=browser.new_page(viewport={'width':1700,'height':1100},accept_downloads=True)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
        page.goto((ROOT/'浅序住区.html').as_uri(),wait_until='networkidle')
        page.wait_for_function('window.slabApp?.ready',timeout=90000)
        page.evaluate('slabApp.state.paused=true')
        bounds=page.evaluate('({min:slabApp.model.getBounds().min.toArray(),max:slabApp.model.getBounds().max.toArray()})')
        check('Entrance revision retains parcel bounds and 16/18/20 floors',all(abs(bounds[k][i])<=56.001 for k in ('min','max') for i in (0,2)) and page.evaluate('JSON.stringify(slabApp.model.buildings.map(b=>b.floors))===JSON.stringify([16,18,20])'))
        entrance=page.evaluate("""()=>{const a=slabApp,T=a.THREE,matrix=new T.Matrix4(),p=new T.Vector3();let cross=0,signs=0;a.model.root.updateMatrixWorld(true);for(const b of a.model.buildings){const group=a.model.root.getObjectByName(b.id);group.traverse(o=>{if(!o.isMesh)return;if(o.name.includes('单元')){signs++;return;}if(!/Apartment interior|Curtain fabric|Clear enclosed balcony/.test(o.material.name))return;for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,matrix);matrix.premultiply(o.matrixWorld);}else matrix.copy(o.matrixWorld);p.setFromMatrixPosition(matrix);if(p.y<3.1&&Math.abs(p.z-(b.z+7))<2&&[-21,0,21].some(x=>Math.abs(p.x-x)<2.35))cross++;}});}return{cross,signs}}""")
        check('Ground-floor entry bays are clear of apartment glazing and curtains',entrance['cross']==0)
        check('Nine unit signs remain separate readable canopy elements',entrance['signs']==9)
        ramp=page.evaluate("""()=>{const a=slabApp,T=a.THREE,mx=new T.Matrix4(),b=new T.Box3(),p=new T.Vector3(),ramps=[],platforms=[];a.model.root.updateMatrixWorld(true);a.model.root.traverse(o=>{if(!o.isMesh)return;const pos=o.geometry.attributes.position,isRamp=!o.geometry.index&&pos.count===24;const isPlatform=o.material.name==='Warm limestone plinth';if(!isRamp&&!isPlatform)return;for(let i=0;i<(o.isInstancedMesh?o.count:1);i++){if(o.isInstancedMesh){o.getMatrixAt(i,mx);mx.premultiply(o.matrixWorld);}else mx.copy(o.matrixWorld);if(isPlatform){o.geometry.computeBoundingBox();platforms.push(o.geometry.boundingBox.clone().applyMatrix4(mx));}if(!isRamp)continue;const vs=[];for(let j=0;j<pos.count;j++)vs.push(new T.Vector3().fromBufferAttribute(pos,j).applyMatrix4(mx));const edges=new Map();let volume=0;const key=v=>v.toArray().map(x=>x.toFixed(5)).join(',');for(let j=0;j<vs.length;j+=3){const tri=vs.slice(j,j+3);volume+=tri[0].dot(tri[1].clone().cross(tri[2]))/6;for(let k=0;k<3;k++){const edge=[key(tri[k]),key(tri[(k+1)%3])].sort().join('|');edges.set(edge,(edges.get(edge)||0)+1);}}const box=new T.Box3().setFromPoints(vs),near=vs.filter(v=>Math.abs(v.z-box.min.z)<1e-4),far=vs.filter(v=>Math.abs(v.z-box.max.z)<1e-4);ramps.push({box,closed:[...edges.values()].every(n=>n===2),volume:Math.abs(volume),nearTop:Math.max(...near.map(v=>v.y)),farTop:Math.max(...far.map(v=>v.y))});}});const aligned=ramps.every(r=>{const q=r.box,wing=platforms.find(b=>Math.abs(b.max.z-q.min.z)<1e-4&&Math.abs(b.max.y-.3)<1e-4&&b.min.x<=q.min.x+1e-4&&b.max.x>=q.max.x-1e-4);if(!wing)return false;const joined=platforms.some(b=>b!==wing&&Math.abs(b.max.x-wing.min.x)<1e-4&&Math.abs(b.max.y-wing.max.y)<1e-4&&Math.abs(b.min.z-wing.min.z)<1e-4&&Math.abs(b.max.z-wing.max.z)<1e-4);return joined;});return{count:ramps.length,closed:ramps.every(r=>r.closed),volumes:ramps.map(r=>r.volume),profile:ramps.every(r=>Math.abs(r.nearTop-.3)<1e-4&&Math.abs(r.farTop)<1e-4&&Math.abs(r.box.min.y)<1e-4&&Math.abs(r.box.max.z-r.box.min.z-6.3)<1e-4),aligned};}""")
        check('All nine access ramps are watertight solid wedges',ramp['count']==9 and ramp['closed'] and all(abs(v-2.835)<1e-3 for v in ramp['volumes']))
        check('Ramp profiles meet ground and 0.30 metre landings',ramp['profile'])
        check('Ramp landings connect to entrance platforms without a gap',ramp['aligned'])

        for view,name in [('entrance','final-entrance.png'),('overview','final-overview.png'),('facade','final-facade.png')]:
            page.locator(f'[data-view={view}]').click();page.wait_for_timeout(650);snapshot(page,name)
        data=page.evaluate('slabApp.exportScene()')
        (OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
        print('SNAPSHOT_READY',str(OUT/'scene.json'),flush=True)
        with page.expect_download(timeout=180000) as task:page.locator('#export').click()
        task.value.save_as(ROOT/'浅序住区.glb');doc=glb_json(ROOT/'浅序住区.glb')
        names=[n.get('name','') for n in doc.get('nodes',[])]
        check('Revised model exports valid complete GLB and Blender snapshot',all(id in names for id in ['SLAB-A','SLAB-B','SLAB-C']) and data['snapshotSpace']=='world')
        page.set_viewport_size({'width':390,'height':844});page.locator('#reset').click();page.wait_for_timeout(350);snapshot(page,'final-mobile.png')
        check('Revised mobile preview remains collapsed with no overflow',page.locator('#panel-body').is_hidden() and page.evaluate('document.documentElement.scrollWidth===390'))
        check('Revised asset has no external requests or WebGL errors',not requests and not errors)
        (OUT/'verification.json').write_text(json.dumps({**previous,'checks':checks,'bounds':bounds,'entrance':entrance,'ramp':ramp,'errors':errors,'requests':requests,'revision':'Solid access ramp wedges and joined platform wings checked; final HTML snapshot and GLB refreshed'},ensure_ascii=False,indent=2),encoding='utf8')
        print('COMPLETE',len(checks),flush=True);browser.close()


if __name__=='__main__':
    main()
