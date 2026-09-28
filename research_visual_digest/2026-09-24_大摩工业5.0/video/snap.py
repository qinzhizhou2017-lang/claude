import sys, pathlib
from playwright.sync_api import sync_playwright
html = pathlib.Path(__file__).with_name('stage.html').resolve()
times = [float(x) for x in sys.argv[1].split(',')]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    pg = b.new_page(viewport={'width':1080,'height':1920})
    pg.goto(f'file://{html}'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
    for t in times:
        pg.evaluate(f'renderAt({t})')
        pg.screenshot(path=f'snap_{t:05.1f}.png', type='png')
    b.close()
