import json,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1700,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(e.stack));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle');page.wait_for_function('window.cityApp?.ready');page.wait_for_timeout(1000);page.locator('#mall-view').click()
    for i in range(4):
        page.wait_for_timeout(1500);print(json.dumps({'errors':list(dict.fromkeys(errors)),'state':page.evaluate('({selected:cityApp.state.selected?.id,target:cityApp.controls().target.toArray(),pos:cityApp.camera().position.toArray(),metrics:cityApp.metrics()})')},ensure_ascii=True),flush=True)
    page.screenshot(path=str(ROOT/'outputs/mall-integration/inspection.png'));browser.close()
server.shutdown()
