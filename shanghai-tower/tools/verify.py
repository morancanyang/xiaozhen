import json,struct,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def read_glb(path):
    blob=path.read_bytes();assert blob[:4]==b'glTF';length=struct.unpack_from('<I',blob,12)[0];return json.loads(blob[20:20+length])
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1600,'height':1000},device_scale_factor=1);page=context.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('request',lambda r:requests.append(r.url))
    context.set_offline(True);page.goto((ROOT/'上海中心.html').as_uri(),wait_until='load');page.wait_for_function('window.towerApp?.ready');page.wait_for_timeout(1200)
    check('single HTML opens fully offline',page.evaluate('towerApp.ready') and all(url.startswith('file:') for url in requests))
    bounds=page.evaluate('({min:towerApp.tower.getBounds().min.toArray(),max:towerApp.tower.getBounds().max.toArray()})')
    check('112 m square parcel clearance',bounds['min'][0]>=-52.1 and bounds['max'][0]<=52.1 and bounds['min'][2]>=-52.1 and bounds['max'][2]<=52.1)
    check('96 m display and 632 m reference',95.9<bounds['max'][1]<96.1 and page.evaluate('towerApp.tower.metadata.nominalHeight===632'))
    check('no roadway or parking in model',page.evaluate("!towerApp.tower.model.getObjectByName('Road') && !towerApp.tower.materials.asphalt"))
    check('two separate curtain walls',page.evaluate("!!towerApp.tower.model.getObjectByName('Inner_Curtain_Wall') && !!towerApp.tower.model.getObjectByName('Twisting_Double_Skin')"))
    pos=page.evaluate('towerApp.camera.position.toArray()');page.mouse.move(850,430);page.mouse.down();page.mouse.move(970,470,steps=10);page.mouse.up();page.wait_for_timeout(300);check('drag rotation',pos!=page.evaluate('towerApp.camera.position.toArray()'))
    distance=page.evaluate('towerApp.camera.position.distanceTo(towerApp.controls.target)');page.mouse.wheel(0,-250);page.wait_for_timeout(300);check('wheel zoom',distance>page.evaluate('towerApp.camera.position.distanceTo(towerApp.controls.target)'))
    pos=page.evaluate('towerApp.controls.target.toArray()');page.mouse.down(button='right');page.mouse.move(1050,510,steps=8);page.mouse.up(button='right');page.wait_for_timeout(250);check('right-button pan',pos!=page.evaluate('towerApp.controls.target.toArray()'))
    for name in ['hero','facade','entry','crown','overview']:
        page.locator('[data-view='+name+']').click();page.wait_for_timeout(1700);check(name+' camera preset',page.locator('[data-view='+name+']').evaluate("el=>el.classList.contains('active')"));page.screenshot(path=str(ROOT/f'outputs/final-{name}.png'))
    page.locator('#pause').click();before=page.evaluate('towerApp.metrics.time');page.wait_for_timeout(400);check('pause freezes simulation',before==page.evaluate('towerApp.metrics.time'));page.locator('#pause').click()
    before=page.evaluate('towerApp.tower.parts.residents.children[0].position.toArray()');page.wait_for_timeout(400);check('residents move after resume',before!=page.evaluate('towerApp.tower.parts.residents.children[0].position.toArray()'))
    page.locator('#lights').uncheck();page.wait_for_timeout(100);check('window lights toggle',not page.evaluate('towerApp.tower.parts.windows.visible'));page.locator('#lights').check()
    page.locator('#people').uncheck();page.wait_for_timeout(100);check('residents toggle',not page.evaluate('towerApp.tower.parts.residents.visible'));page.locator('#people').check()
    page.locator('#orbit').click();check('automatic orbit',page.evaluate('towerApp.state.orbit'));page.mouse.move(840,480);page.mouse.down();page.mouse.move(860,485);page.mouse.up();check('manual action stops orbit',not page.evaluate('towerApp.state.orbit'))
    page.locator('[data-time=day]').click();page.wait_for_timeout(1800);check('day-night light transition',page.evaluate("towerApp.scene.children.find(o=>o.isHemisphereLight).intensity>1.7"));page.locator('[data-time=blue]').click()
    page.locator('#quality').select_option('low');page.wait_for_timeout(250);check('low quality changes detail',not page.evaluate('towerApp.tower.parts.detail.visible'));page.locator('#quality').select_option('high')
    with page.expect_download(timeout=60000) as result:page.locator('#export-glb').click()
    result.value.save_as(ROOT/'上海中心.glb');glb=read_glb(ROOT/'上海中心.glb');names=[node.get('name','') for node in glb['nodes']];check('GLB contains building only',not glb.get('cameras') and 'Photography_Environment' not in names and 'Inner_Curtain_Wall' in names)
    page.locator('#help').click();page.locator('#resolution').select_option('3840');page.locator('#close-guide').click()
    with page.expect_download(timeout=60000) as result:page.locator('#save-png').click()
    result.value.save_as(ROOT/'outputs/browser-4k.png');from PIL import Image
    check('native 4K browser PNG',Image.open(ROOT/'outputs/browser-4k.png').size==(3840,2160))
    page.set_viewport_size({'width':390,'height':844});page.locator('#reset').click();page.wait_for_timeout(1800);page.locator('#collapse').click();page.screenshot(path=str(ROOT/'outputs/final-mobile.png'));check('mobile layout fits viewport',page.evaluate('document.documentElement.scrollWidth===390'))
    metrics=page.evaluate('towerApp.metrics')
    context.set_offline(False)
    page.goto('http://127.0.0.1:5299/接入演示.html',wait_until='networkidle');page.wait_for_function('window.integrationDemo?.result',timeout=30000);result=page.evaluate('integrationDemo.result');check('same-origin factory uses host THREE',result['sameTHREE']);check('asset has no cameras or lights',not result['modelHasCamera'] and not result['modelHasLight']);check('asset mode has no renderer',page.evaluate("integrationDemo.frame.contentDocument.querySelectorAll('canvas').length===0"));check('host sets placement elevation',result['hostGroundY']==.34);page.screenshot(path=str(ROOT/'outputs/integration-demo.png'))
    page.evaluate('integrationDemo.landmark.dispose()');check('dispose removes model from host',page.evaluate('integrationDemo.landmark.model.parent===null'))
    check('no script or WebGL errors',not errors)
    report={'checks':checks,'errors':errors,'bounds':bounds,'metrics':metrics,'browser':browser.version,'offline_requests':requests[:3]};(ROOT/'outputs/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True));context.close();browser.close()
