from pathlib import Path
import json,struct
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    ctx=p.chromium.launch_persistent_context(str(ROOT/'outputs/qa-browser-profile'),channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'],accept_downloads=True)
    ctx.set_offline(True);page=ctx.new_page();page.goto((ROOT/'澄序住区.html').as_uri(),wait_until='networkidle');page.wait_for_function('window.courtyardApp?.ready',polling=100,timeout=120000)
    for id in 'ABCD':
        page.evaluate('(id)=>courtyardApp.view(id)',id)
        with page.expect_download(timeout=120000) as dl:page.click('#export-part')
        target=ROOT/'outputs'/('chengxu-'+id+'.glb');dl.value.save_as(target);data=target.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);names=[n.get('name') for n in doc['nodes']]
        assert id in names and all(other not in names for other in 'ABCD' if other!=id)
        print(id,target.stat().st_size,flush=True)
    ctx.close()
