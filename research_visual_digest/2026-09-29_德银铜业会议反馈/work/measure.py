# 量每页 room：最后一个非绝对定位子元素 bottom vs 页脚 top；并截每页 PNG
import sys, pathlib
from playwright.sync_api import sync_playwright

html = pathlib.Path(sys.argv[1]).resolve()
shot = len(sys.argv) > 2
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 900, "height": 1200}, device_scale_factor=1.6)
    pg.emulate_media(media="print")
    pg.goto(html.as_uri())
    pg.wait_for_timeout(400)
    res = pg.evaluate("""() => [...document.querySelectorAll('.page')].map(pg => {
      const foot = pg.querySelector('.pg-foot').getBoundingClientRect();
      let last = 0, lastEl = '';
      for (const c of pg.children) {
        const cs = getComputedStyle(c);
        if (cs.position === 'absolute' || c.classList.contains('pg-foot')) continue;
        const r = c.getBoundingClientRect();
        if (r.bottom > last) { last = r.bottom; lastEl = c.className || c.tagName; }
      }
      // 最大连续空白（子元素之间）
      const kids = [...pg.children].filter(c => getComputedStyle(c).position !== 'absolute' && !c.classList.contains('pg-foot'));
      let gaps = [];
      for (let i = 1; i < kids.length; i++) {
        const g = kids[i].getBoundingClientRect().top - kids[i-1].getBoundingClientRect().bottom;
        gaps.push([Math.round(g), kids[i-1].className || kids[i-1].tagName]);
      }
      gaps.push([Math.round(foot.top - last), 'tail→foot']);
      return {id: pg.id, room: Math.round(foot.top - last), lastEl, gaps: gaps.filter(g => g[0] >= 30)};
    })""")
    for r in res:
        print(r["id"], "room", r["room"], "px ≈", round(r["room"] / 3.78, 1), "mm | last:", r["lastEl"], "| gaps≥30px:", r["gaps"])
    if shot:
        out = html.parent / "work" / "shots"
        out.mkdir(exist_ok=True)
        for i, el in enumerate(pg.query_selector_all(".page")):
            el.screenshot(path=str(out / f"page{i + 1}.png"))
        print("shots →", out)
    b.close()
