from pathlib import Path
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1500,'height':1000});page.goto((Path.cwd()/'霁衡中心.html').as_uri());page.wait_for_function('window.officeApp?.ready',polling=100,timeout=120000)
 page.click('#pause');page.wait_for_timeout(200);page.click('#pause');page.wait_for_timeout(200)
 print(page.evaluate('({zoom:officeApp.camera.zoom,state:officeApp.controls.state,enable:officeApp.controls.enableZoom,tag:document.elementFromPoint(750,650).tagName})'))
 page.evaluate("window.wheels=[];officeApp.renderer.domElement.addEventListener('wheel',e=>wheels.push({dy:e.deltaY,state:officeApp.controls.state}))")
 page.mouse.move(750,650);page.mouse.wheel(0,-280);page.wait_for_timeout(1000);print(page.evaluate('({zoom:officeApp.camera.zoom,state:officeApp.controls.state,wheels})'))
 page.mouse.move(770,450);page.mouse.down();page.mouse.move(895,490,steps=8);page.mouse.up();page.wait_for_timeout(200);page.mouse.down(button='right');page.mouse.move(950,550,steps=8);page.mouse.up(button='right');page.wait_for_timeout(200)
 print(page.evaluate('({zoom:officeApp.camera.zoom,state:officeApp.controls.state,tag:document.elementFromPoint(750,650).tagName})'))
 page.mouse.move(750,650);page.mouse.wheel(0,-280);page.wait_for_timeout(1000);print(page.evaluate('({zoom:officeApp.camera.zoom,state:officeApp.controls.state,wheels})'));b.close()
