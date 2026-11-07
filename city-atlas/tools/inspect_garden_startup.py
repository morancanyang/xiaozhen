import json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']); page=b.new_page(viewport={'width':1700,'height':1100});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 r=page.goto('http://127.0.0.1:5173',wait_until='networkidle');page.wait_for_timeout(4000)
 print(json.dumps({'errors':errors,'status':r.status,'load':page.evaluate("({url:location.href,title:document.title,load:document.querySelector('#load-message')?.textContent,body:document.body.innerText.slice(0,200)})"),'ready':page.evaluate('!!window.cityApp?.ready')},ensure_ascii=True),flush=True)
 page.screenshot(path='outputs/garden-integration/startup.png');b.close()
