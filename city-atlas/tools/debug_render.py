from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=b.new_page(viewport={'width':1400,'height':900})
    page.on('console',lambda msg: print(msg.type,msg.text[:2000]) if msg.type=='error' else None)
    page.goto('http://127.0.0.1:5173',wait_until='networkidle')
    page.wait_for_function('window.cityApp?.ready')
    page.evaluate('window.cityApp.composer.passes[2].enabled=false')
    page.wait_for_timeout(1000)
    page.screenshot(path=str(root/'outputs'/'debug-no-bloom.png'))
    page.evaluate('window.cityApp.composer.passes[3].enabled=false')
    page.wait_for_timeout(600)
    page.screenshot(path=str(root/'outputs'/'debug-no-output.png'))
    print(page.evaluate('({gpu:cityApp.renderer.getContext().getParameter(cityApp.renderer.getContext().RENDERER),ext:cityApp.renderer.extensions.has("EXT_color_buffer_float")})'))
    b.close()
