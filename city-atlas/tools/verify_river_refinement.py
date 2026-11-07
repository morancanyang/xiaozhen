"""Check the visible current, excavated river profile and shared city controls."""
import json, threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/river-refinement'
OUT.mkdir(parents=True, exist_ok=True)
checks, errors = [], []

def check(name, passed):
    checks.append({'check': name, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)
    assert passed, name

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True, args=['--enable-webgl','--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width':1700, 'height':1100})
        page.set_default_timeout(60000)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type=='error' else None)
        page.goto(f'http://127.0.0.1:{server.server_port}', wait_until='networkidle')
        page.wait_for_function('window.cityApp?.ready', timeout=60000)
        check('Water level is 3.2 m below datum', page.evaluate('cityApp.river.manifest.waterLevel===-3.2&&cityApp.plan.corridor.waterLevel===-3.2'))
        profile = page.evaluate('''()=>{const r=cityApp.river;let edgeError=0,deepest=0,overlap=0;for(let z=-300;z<=300;z+=2){edgeError=Math.max(edgeError,Math.abs(r.terrainHeight(-32,z)-.02),Math.abs(r.terrainHeight(32,z)-.02));deepest=Math.min(deepest,r.terrainHeight(r.center(z),z));for(let x=-32;x<=32;x+=.5)if(Math.abs(x-r.center(z))<r.halfWidth(z)-.05&&r.terrainHeight(x,z)>=r.manifest.waterLevel)overlap++;}const f=r.root.getObjectByName('River foundation');return{edgeError,deepest,overlap,foundationTop:f.position.y+f.scale.y/2,foundationBottom:f.position.y-f.scale.y/2};}''')
        check('Both bank crests meet the unchanged street edge', profile['edgeError']<1e-9)
        check('Continuous bed remains below water', profile['overlap']==0 and profile['deepest']<-5.9)
        check('Foundation stays under deepest bed and inside town base', profile['foundationTop']<profile['deepest'] and abs(profile['foundationBottom']+7.3)<1e-9)
        bounds = page.evaluate('''async()=>{const T=await import('three'),b=new T.Box3().setFromObject(cityApp.river.root);return{min:b.min.toArray(),max:b.max.toArray()}}''')
        check('River remains in original 64 x 600 m reservation', bounds['min'][0]>=-32.001 and bounds['max'][0]<=32.001 and bounds['min'][2]>=-300.001 and bounds['max'][2]<=300.001)
        check('All 16 blocks and existing landmark modules remain', page.evaluate("cityApp.plan.blocks.length===16&&['SENYIN-PARK','SHANGHAI-TOWER','UNIVERSITY-CAMPUS','ARENA-DOME'].every(id=>cityApp.scene.getObjectByName(id))&&!!cityApp.park&&!!cityApp.residential&&!!cityApp.mall&&!!cityApp.skyline&&!!cityApp.hospital"))
        check('City slabs still leave full river corridor excavated', page.evaluate("cityApp.exportCity('SHANGHAI-TOWER').batches.filter(b=>b.owner==='world'&&['base','soil','asphalt'].includes(b.material)).every(b=>b.items.every(i=>i.p[0]+i.s[0]/2<=-31.999||i.p[0]-i.s[0]/2>=31.999||i.p[2]+i.s[2]/2<=-299.999||i.p[2]-i.s[2]/2>=299.999))"))
        page.screenshot(path=str(OUT/'city-overview.png'))
        page.locator('#river-view').click()
        page.wait_for_function('Math.abs(cityApp.controls().target.y+2.2)<.01&&Math.abs(cityApp.controls().target.z-25)<.01', timeout=60000)
        check('Along-river camera targets new sunken water level', page.evaluate('Math.abs(cityApp.controls().target.y+2.2)<.01'))
        page.screenshot(path=str(OUT/'river-context.png'))
        hit = page.evaluate('''async()=>{const T=await import('three'),r=new T.Raycaster(new T.Vector3(0,3,25),new T.Vector3(0,-1,0));return r.intersectObjects(cityApp.scene.children,true).filter(h=>h.object.isMesh).slice(0,5).map(h=>({name:h.object.name,y:h.point.y}));}''')
        check('Top-down ray sees water before actual bed, without blocking slab', len(hit)>1 and hit[0]['name']=='Dynamic river surface' and abs(hit[0]['y']+3.2)<.01 and hit[1]['name']=='Continuous excavated riverbed')
        check('Real reflection and refraction depth buffers remain active', page.evaluate('cityApp.riverPass.metrics.updates>0&&cityApp.river.waterUniforms.uHasBuffers.value===1&&!!cityApp.river.waterUniforms.uDepth.value'))
        # Freeze city motion and compare two deterministic water times at one view.
        page.locator('#pause').click()
        t = page.evaluate('cityApp.river.waterTime')
        page.wait_for_timeout(300)
        check('Global pause freezes flowing surface', page.evaluate('cityApp.river.waterTime')==t)
        point = page.evaluate('''async()=>{const T=await import('three'),r=cityApp.river,p=new T.Vector3(r.center(45),r.manifest.waterLevel,45).project(cityApp.camera());return{x:(p.x*.5+.5)*innerWidth,y:(.5-p.y*.5)*innerHeight}}''')
        page.screenshot(path=str(OUT/'flow-t0.png'))
        page.evaluate('cityApp.river.setDynamicsEnabled(true);for(let i=0;i<12;i++)cityApp.river.update(.25)')
        page.wait_for_timeout(150)
        page.screenshot(path=str(OUT/'flow-t3.png'))
        a,b=Image.open(OUT/'flow-t0.png').convert('RGB'),Image.open(OUT/'flow-t3.png').convert('RGB')
        x,y=round(point['x']),round(point['y']);box=(x-55,y-65,x+55,y+65)
        ac,bc=a.crop(box),b.crop(box);ac.save(OUT/'water-t0.png');bc.save(OUT/'water-t3.png')
        delta=ImageChops.difference(ac,bc);motionMean=sum(ImageStat.Stat(delta).mean)/3
        changed=sum(max(v)>8 for v in delta.getdata())/(delta.width*delta.height)
        check('Rendered water visibly changes while camera and city stay still', motionMean>1.5 and changed>.12)
        check('Current advection is declared toward +Z at readable metre scale', page.evaluate("cityApp.river.manifest.flowDirection==='+Z'&&cityApp.river.manifest.surfaceFlowMetersPerSecond===3.6"))
        # Cover independent speed zero and wind independence using controlled updates.
        check('Flow slider allows 0 to 3 times', page.locator('#river-flow').get_attribute('max')=='3')
        check('Zero flow speed freezes water while fish simulation continues', page.evaluate('''()=>{const r=cityApp.river;r.setDynamicsEnabled(true);r.setFlowSpeed(0);const w=r.waterTime,t=r.simulationTime;r.update(.2);const ok=r.waterTime===w&&r.simulationTime>t;r.setFlowSpeed(1);return ok;}'''))
        check('Turning wind off still permits downstream current', page.evaluate('''()=>{const r=cityApp.river;r.setDynamicsEnabled(true);r.setWindEnabled(false);const w=r.waterTime,t=r.windTime;r.update(.2);const ok=r.waterTime>w&&r.windTime===t;r.setWindEnabled(true);return ok;}'''))
        fish = page.evaluate('''async()=>{const T=await import('three'),r=cityApp.river,m=r.root.getObjectByName('Schooling fish bodies'),matrix=new T.Matrix4();let ok=true;for(let j=0;j<20;j++){r.setDynamicsEnabled(true);r.update(.25);for(let i=0;i<m.count;i++){m.getMatrixAt(i,matrix);const p=new T.Vector3().setFromMatrixPosition(matrix);ok&&=p.y<r.manifest.waterLevel-.2&&p.y>r.terrainHeight(p.x,p.z)+.1;}}return ok;}''')
        check('Fish stay below lowered water and above bed over time',fish)
        page.locator('#pause').click()
        page.locator('#river-fish-view').click()
        page.wait_for_function('Math.abs(cityApp.controls().target.y+2.9)<.01&&Math.abs(cityApp.controls().target.z-39)<.01',timeout=60000)
        check('Fish camera follows lowered water', page.evaluate('cityApp.camera().position.y<6&&Math.abs(cityApp.controls().target.y+2.9)<.01'))
        page.screenshot(path=str(OUT/'river-close.png'))
        page.locator('#quality').select_option('fast')
        page.wait_for_function("cityApp.river.quality==='low'&&cityApp.riverPass.metrics.width===512",timeout=60000)
        page.screenshot(path=str(OUT/'river-fast.png'))
        check('Fast mode keeps actual animated water and depth pass', page.evaluate('cityApp.river.waterUniforms.uHasBuffers.value===1'))
        page.locator('#quality').select_option('balanced')
        page.locator('[data-time=night]').click()
        page.wait_for_function('cityApp.river.waterUniforms.uNight.value>.99',timeout=60000)
        check('Night water follows city lighting',page.evaluate('cityApp.river.waterUniforms.uNight.value>.99'))
        page.locator('#river-view').click()
        page.wait_for_function('Math.abs(cityApp.controls().target.z-25)<.01',timeout=60000)
        page.screenshot(path=str(OUT/'river-night.png'))
        page.locator('[data-time=morning]').click()
        page.wait_for_function('cityApp.river.waterUniforms.uNight.value<.01',timeout=60000)
        snapshot=page.evaluate('cityApp.river.exportScene()')
        check('Export contains lowered water vertices and world coordinates',snapshot['snapshotSpace']=='world' and snapshot['manifest']['waterLevel']==-3.2 and any(m['name']=='River water static PBR' for m in snapshot['materials'].values()))
        check('Forest lake level stays independent from main river',page.evaluate('cityApp.forest.getBounds().min.y> -3.2&&cityApp.forestSite.blockId===\'BLK-15\''))
        page.set_viewport_size({'width':420,'height':880})
        if page.locator('#panel-content').is_hidden():page.locator('#collapse').click()
        page.locator('#river-view').click()
        page.wait_for_function('Math.abs(cityApp.controls().target.y+2.2)<.01',timeout=60000)
        page.screenshot(path=str(OUT/'river-mobile.png'))
        check('Mobile river view closes panel without horizontal overflow',page.locator('#panel-content').is_hidden() and page.evaluate('document.documentElement.scrollWidth===420'))
        check('No runtime or WebGL shader errors',not errors)
        (OUT/'verification.json').write_text(json.dumps({'checks':checks,'profile':profile,'raycast':hit,'motionMean':motionMean,'changedFraction':changed,'errors':errors},ensure_ascii=False,indent=2),encoding='utf8')
        print('COMPLETE',len(checks),flush=True)
        browser.close()
finally:
    server.shutdown()
