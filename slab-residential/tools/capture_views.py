"""Refresh final browser photographs after camera/UI transitions finish."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--allow-file-access-from-files'])
    page=browser.new_page(viewport={'width':1700,'height':1100})
    page.goto((ROOT/'浅序住区.html').as_uri(),wait_until='networkidle')
    page.wait_for_function('window.slabApp?.ready',timeout=90000)
    for view in ['entrance','overview','facade','roof']:
        page.locator(f'[data-view={view}]').click()
        page.wait_for_timeout(650)
        page.screenshot(path=str(OUT/f'final-{view}.png'),timeout=90000)
        print('CAPTURE',view,flush=True)
    page.locator('[data-time=night]').click()
    page.wait_for_function('slabApp.state.nightFactor>.999',timeout=60000)
    page.locator('[data-view=overview]').click();page.wait_for_timeout(650)
    page.screenshot(path=str(OUT/'final-night.png'),timeout=90000)
    page.locator('[data-time=day]').click()
    page.wait_for_function('slabApp.state.nightFactor<.001',timeout=60000)
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#reset').click();page.wait_for_timeout(650)
    page.screenshot(path=str(OUT/'final-mobile.png'),timeout=90000)
    print('CAPTURE night and mobile',flush=True)
    browser.close()
