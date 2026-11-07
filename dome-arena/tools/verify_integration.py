import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1280,'height':900});context.set_offline(True)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((ROOT/'穹光体育中心.html').as_uri());page.wait_for_function('window.arenaApp?.ready');page.wait_for_timeout(1000)
    result=page.evaluate('''async sources=>{
      const modelURL=URL.createObjectURL(new Blob([sources.model],{type:'text/javascript'}));
      const adapterURL=URL.createObjectURL(new Blob([sources.adapter.replace("'./arena-module.mjs'",JSON.stringify(modelURL))],{type:'text/javascript'}));
      const {mountArena}=await import(adapterURL),T=arenaApp.THREE,host=new T.Group();
      const block=mountArena({THREE:T,scene:host,center:{x:100,z:-100},groundY:2,blockSize:84,rotationY:Math.PI/2,fixtureLights:true});
      const entry=block.entryWorld(),entryOK=entry.distanceTo(new T.Vector3(142,2,-100))<.001;
      const spots=block.parcel.children.filter(o=>o.isSpotLight);block.setNight(1);
      const lightsOK=spots.length===4&&spots.every(o=>o.intensity>0&&!o.castShadow);
      block.parcel.updateWorldMatrix(true,true);const expected=block.arena.root.localToWorld(new T.Vector3(-49,37,-43)),actual=spots[0].getWorldPosition(new T.Vector3());
      const alignment=expected.distanceTo(actual)<.001;
      block.update(.1);const advances=block.arena.simulationTime===.1;block.setNight(0);const dayOK=spots.every(o=>o.intensity===0);
      block.dispose();block.dispose();const disposed=host.children.length===0&&block.arena.disposed;
      URL.revokeObjectURL(modelURL);URL.revokeObjectURL(adapterURL);
      return {moduleImport:true,entryOK,lightsOK,alignment,advances,dayOK,disposed};
    }''',{'model':(ROOT/'arena-module.mjs').read_text(encoding='utf8'),'adapter':(ROOT/'integration-example.mjs').read_text(encoding='utf8')})
    result['noBrowserErrors']=not errors
    (ROOT/'outputs/integration-verification.json').write_text(json.dumps({'checks':result,'errors':errors},indent=2),encoding='utf8')
    print(json.dumps(result,indent=2));browser.close()
    if not all(result.values()):raise SystemExit('Integration verification failed')
