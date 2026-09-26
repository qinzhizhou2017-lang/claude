import sys, pathlib
from playwright.sync_api import sync_playwright
html = pathlib.Path(sys.argv[1]).resolve()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    pg = b.new_page(viewport={'width':1000,'height':1400})
    pg.goto(f'file://{html}?v=1'); pg.wait_for_timeout(400)
    res = pg.evaluate('''() => [...document.querySelectorAll('.page')].map((p,i)=>{
      const foot=p.querySelector('.pg-foot').getBoundingClientRect();
      const kids=[...p.children].filter(c=>getComputedStyle(c).position!=='absolute');
      const last=kids[kids.length-1].getBoundingClientRect();
      // 最大纵向空隙（相邻在流子元素之间）
      let gaps=[];for(let j=1;j<kids.length;j++){const a=kids[j-1].getBoundingClientRect(),c=kids[j].getBoundingClientRect();gaps.push(Math.round(c.top-a.bottom))}
      return {page:i+1, room:Math.round(foot.top-last.bottom), lastCls:kids[kids.length-1].className, gaps};
    })''')
    for r in res: print(r)
    b.close()
