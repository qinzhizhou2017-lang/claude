import sys, pathlib
from playwright.sync_api import sync_playwright
html = pathlib.Path(sys.argv[1]).resolve(); out=sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    pg = b.new_page(viewport={'width':820,'height':1200}, device_scale_factor=1.4)
    pg.goto(f'file://{html}?v=2'); pg.wait_for_timeout(400)
    pages = pg.query_selector_all('.page')
    idx = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv)>3 else range(1,len(pages)+1)
    for i in idx:
        pg.evaluate(f"document.querySelectorAll('.page')[{i-1}].style.overflow='visible'")
        pages[i-1].screenshot(path=f'{out}_p{i}.png')
    b.close()
