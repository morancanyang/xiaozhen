import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page(viewport={'width':1700,'height':1100});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 for coarse in [True,False]:
  page.goto((ROOT/'棕屿里.html').as_uri()+('?coarse=1' if coarse else ''),wait_until='networkidle');page.wait_for_function('window.mixedApp?.ready',timeout=60000);page.wait_for_timeout(800)
  page.screenshot(path=str(OUT/('coarse.png' if coarse else 'overview.png')))
 for view in ['facade','entrance','roof']:
  page.locator(f'[data-view={view}]').click();page.wait_for_timeout(650);page.screenshot(path=str(OUT/(view+'.png')))
 snapshot=page.evaluate('mixedApp.exportScene()');(OUT/'scene.json').write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 print(json.dumps({'errors':errors,'bounds':page.evaluate('({min:mixedApp.model.getBounds().min.toArray(),max:mixedApp.model.getBounds().max.toArray()})'),'objects':len(snapshot['objects'])}));b.close()
