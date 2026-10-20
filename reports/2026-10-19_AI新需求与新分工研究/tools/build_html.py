#!/usr/bin/env python3
"""把终稿 Markdown 转成带目录导航、表格可折叠、字号可调的 HTML 页面（无第三方依赖）。
用法：python3 -I tools/build_html.py
输出：AI新需求与新分工研究报告.html（按 Artifact 页面约定，不含 doctype／html／head／body 外壳）
"""
import html, os, re

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{B}/AI新需求与新分工研究报告.md"
OUT = f"{B}/AI新需求与新分工研究报告.html"
lines = open(SRC, encoding="utf-8").read().split("\n")


def join_sep(a, b):
    return " " if a and b and a[-1].isascii() and a[-1].isalnum() and b[0].isascii() and b[0].isalnum() else ""


def is_block_start(l):
    return bool(re.match(r"#{1,6} |\||```|- |\d+\. ", l))


# ---------- 块解析 ----------
blocks, i = [], 0
while i < len(lines):
    l = lines[i]
    if not l.strip():
        i += 1; continue
    m = re.match(r"(#{1,6}) (.*)", l)
    if m:
        blocks.append(("h", len(m.group(1)), m.group(2).strip())); i += 1; continue
    if l.startswith("```"):
        j, buf = i + 1, []
        while j < len(lines) and not lines[j].startswith("```"):
            buf.append(lines[j]); j += 1
        blocks.append(("code", "\n".join(buf).strip("\n"))); i = j + 1; continue
    if l.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append(lines[i]); i += 1
        blocks.append(("table", rows)); continue
    if re.match(r"- |\d+\. ", l):
        ordered = bool(re.match(r"\d+\. ", l))
        start = int(re.match(r"(\d+)", l).group(1)) if ordered else 1
        items = []
        while i < len(lines) and lines[i].strip():
            x = lines[i]
            mm = re.match(r"(?:- |\d+\. )(.*)", x)
            if mm:
                items.append(mm.group(1))
            elif x[:1].isspace() and items:
                items[-1] += join_sep(items[-1], x.strip()) + x.strip()
            else:
                break
            i += 1
        blocks.append(("ol" if ordered else "ul", items, start)); continue
    buf = l.strip(); i += 1
    while i < len(lines) and lines[i].strip() and not is_block_start(lines[i]):
        buf += join_sep(buf, lines[i].strip()) + lines[i].strip(); i += 1
    blocks.append(("p", buf))


def cells(row):
    r = row.strip()
    r = r[1:] if r.startswith("|") else r
    r = r[:-1] if r.endswith("|") else r
    return [c.strip() for c in r.split("|")]


def is_sep(row):
    return bool(re.match(r"^\|[\s\-:|]+\|?\s*$", row))


# 附录 B 的数据卡编号（用于正文中的数据卡链接）
APPB_IDS = set()
for b in blocks:
    if b[0] == "table" and cells(b[1][0])[:2] == ["数据卡", "指标"]:
        APPB_IDS = {cells(r)[0] for r in b[1][2:] if not is_sep(r)}


# ---------- 行内格式 ----------
def shorten(u):
    t = re.sub(r"^https?://(www\.)?", "", u)
    return t if len(t) <= 46 else t[:44] + "…"


def inline(s, link_cards=True):
    s = html.escape(s, quote=False)
    codes = []

    def keep(m):
        codes.append(m.group(1)); return f"\x00{len(codes) - 1}\x00"
    s = re.sub(r"`([^`]+)`", keep, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    kinds = {"事实": "fact", "推断": "infer", "预测": "forecast"}
    s = re.sub(r"【((事实|推断|预测)[^】]{0,60})】",
               lambda m: f'<span class="tag tag-{kinds[m.group(2)]}">{m.group(1)}</span>', s)

    def cites(m):
        ids = re.findall(r"R\d{3}", m.group(1))
        return ('<span class="cites">[' + "; ".join(
            f'<a class="cite" href="#{r}">{r}</a>' for r in ids) + "]</span>")
    s = re.sub(r"\[(R\d{3}(?:; R\d{3})*)\]", cites, s)
    if link_cards:
        s = re.sub(r"(?<![\w-])(A\d\d-D\d{3})(?![\w-])",
                   lambda m: f'<a class="card" href="#{m.group(1)}">{m.group(1)}</a>' if m.group(1) in APPB_IDS else m.group(1), s)

    def url(m):
        raw = html.unescape(m.group(1))
        return (f'<a class="url" href="{html.escape(raw)}" target="_blank" rel="noopener" '
                f'title="{html.escape(raw)}">{html.escape(shorten(raw))}</a>')
    s = re.sub(r"(https?://[^\s<>）)】，。；、\"]+)", url, s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)
    return s


def plain(s):
    return re.sub(r"\*\*|`", "", s)


# ---------- 标题编号 ----------
CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7}


def h2_id(text, n):
    if text.startswith("执行摘要"):
        return "summary"
    m = re.match(r"第([一二三四五六七])章", text)
    if m:
        return f"ch{CN[m.group(1)]}"
    m = re.match(r"附录 ([A-E])", text)
    if m:
        return f"app{m.group(1)}"
    return f"s{n}"


def split_eyebrow(text):
    m = re.match(r"(第[一二三四五六七八九十]+章|附录 [A-E])[\s　]+(.*)", text)
    return (m.group(1), m.group(2)) if m else ("", text)


# ---------- 表格 ----------
def render_table(rows, caption, kind, n_open=10):
    head = cells(rows[0])
    body = [cells(r) for r in rows[1:] if not is_sep(r)]
    labels = [html.escape(plain(h)) for h in head]
    big = kind in ("refs", "cards")
    out = []
    for r in body:
        rid = r[0] if big else ""
        tds = []
        for k, c in enumerate(r):
            lab = labels[k] if k < len(labels) else ""
            cls = ' class="u"' if "http" in c else ""
            tds.append(f'<td data-label="{lab}"{cls}>{inline(c, link_cards=not (kind == "cards" and k == 0))}</td>')
        idattr = f' id="{html.escape(rid)}"' if rid else ""
        out.append(f"<tr{idattr}>" + "".join(tds) + "</tr>")
    ths = "".join(f"<th>{inline(h)}</th>" for h in head)
    wide = " wide" if len(head) >= 6 else ""
    is_open = (not big) and len(body) <= n_open
    cls = "exhibit big" if big else "exhibit"
    return (f'<details class="{cls}"{" open" if is_open else ""}>'
            f'<summary><span class="cap">{caption}</span><span class="rows">{len(body)} 行</span></summary>'
            f'<div class="tw"><table class="t{wide}"><thead><tr>{ths}</tr></thead><tbody>{"".join(out)}</tbody></table></div></details>')


# ---------- 主体渲染 ----------
hero = {"title": "", "sub": "", "meta": [], "guide": ""}
toc, html_parts = [], []
cur_h2, h3n, h2n = None, 0, 0
pending_caption = None
k = 0
# 标题页：第一个 h1 到第一个正文 h2（“目录”除外）之间的块
assert blocks[0][0] == "h" and blocks[0][1] == 1
hero["title"] = blocks[0][2]
k = 1
while k < len(blocks) and not (blocks[k][0] == "h" and blocks[k][1] == 2):
    b = blocks[k]
    if b[0] == "p" and re.fullmatch(r"\*\*[^*]+\*\*", b[1]):
        hero["sub"] = inline(b[1][2:-2])
    elif b[0] == "table":
        hero["meta"] = [cells(r) for r in b[1][2:] if not is_sep(r)]
    elif b[0] == "p":
        hero["guide"] += f"<p>{inline(b[1])}</p>"
    k += 1
# 跳过 markdown 自带的“目录”节，由生成的章节索引代替
if blocks[k][0] == "h" and blocks[k][2] == "目录":
    k += 1
    while k < len(blocks) and blocks[k][0] in ("ul", "ol", "p"):
        k += 1
    html_parts.append("<!--CHAPTER_INDEX-->")

while k < len(blocks):
    b = blocks[k]
    nxt = blocks[k + 1] if k + 1 < len(blocks) else None
    if b[0] == "h":
        lvl, text = b[1], b[2]
        if lvl == 1:
            html_parts.append(f'<div class="part" id="appendix"><span>{inline(text)}</span></div>')
            toc.append((1, "appendix", text, ""))
        elif lvl == 2:
            h2n += 1; h3n = 0
            cur_h2 = h2_id(text, h2n)
            eb, rest = split_eyebrow(text)
            ebh = f'<span class="eyebrow">{html.escape(eb)}</span>' if eb else ""
            html_parts.append(f'<h2 id="{cur_h2}" data-short="{html.escape(plain(text))}">{ebh}{inline(rest)}</h2>')
            toc.append((2, cur_h2, rest, eb))
        else:
            h3n += 1
            hid = f"{cur_h2}-{h3n}"
            html_parts.append(f'<h3 id="{hid}" data-ch="{cur_h2}">{inline(text)}</h3>')
            toc.append((3, hid, text, ""))
    elif b[0] == "p":
        if nxt and nxt[0] == "table" and re.fullmatch(r"\*\*表[^*]+\*\*", b[1]):
            pending_caption = inline(b[1][2:-2])
        else:
            html_parts.append(f"<p>{inline(b[1])}</p>")
    elif b[0] == "table":
        head = cells(b[1][0])
        kind = "normal"
        if head[:2] == ["编号", "来源"]:
            kind = "refs"; cap = "参考文献表"
        elif head[:2] == ["数据卡", "指标"]:
            kind = "cards"; cap = "关键数据证据表"
        else:
            cap = pending_caption or html.escape(" · ".join(plain(h) for h in head[:4]) + (" …" if len(head) > 4 else ""))
        html_parts.append(render_table(b[1], cap, kind))
        pending_caption = None
    elif b[0] in ("ul", "ol"):
        tag = b[0]
        st = f' start="{b[2]}"' if tag == "ol" and b[2] != 1 else ""
        html_parts.append(f"<{tag}{st}>" + "".join(f"<li>{inline(x)}</li>" for x in b[1]) + f"</{tag}>")
    elif b[0] == "code":
        html_parts.append(f"<pre><code>{html.escape(b[1])}</code></pre>")
    k += 1

# 章节索引
chap = [t for t in toc if t[0] == 2 and not t[1].startswith("app")]
apps = [t for t in toc if t[0] == 2 and t[1].startswith("app")]
idx = ('<nav class="chapters" aria-label="章节索引"><ol>' + "".join(
    f'<li><a href="#{cid}"><span class="n">{html.escape(eb or "摘要")}</span><span class="t">{inline(t)}</span></a></li>'
    for _, cid, t, eb in chap) + "</ol>"
    + '<p class="apps"><span>附录</span>' + "".join(
    f'<a href="#{cid}">{html.escape(eb.replace("附录 ", ""))}　{inline(t)}</a>' for _, cid, t, eb in apps) + "</p></nav>")
body_html = "\n".join(html_parts).replace("<!--CHAPTER_INDEX-->", idx)

# 侧栏目录
tl, open_li = [], False
for lvl, tid, text, eb in toc:
    if lvl == 1:
        if open_li:
            tl.append("</ol></li>"); open_li = False
        tl.append(f'<li class="tp"><a href="#{tid}">{inline(text)}</a></li>')
    elif lvl == 2:
        if open_li:
            tl.append("</ol></li>")
        lab = f'<span class="n">{html.escape(eb)}</span>' if eb else ""
        tl.append(f'<li class="t2"><a href="#{tid}">{lab}{inline(text)}</a><ol>')
        open_li = True
    else:
        tl.append(f'<li class="t3"><a href="#{tid}">{inline(text)}</a></li>')
if open_li:
    tl.append("</ol></li>")
toc_html = "<ol>" + "".join(tl) + "</ol>"
toc_html = toc_html.replace("<ol></ol>", "")

meta_html = "".join(f"<div><dt>{inline(a)}</dt><dd>{inline(b)}</dd></div>" for a, b, *_ in hero["meta"])

CSS = open(f"{B}/tools/report_page.css", encoding="utf-8").read()
JS = open(f"{B}/tools/report_page.js", encoding="utf-8").read()

page = f"""<title>AI新需求与新分工研究报告</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&family=Noto+Serif+SC:wght@600;700&display=swap">
<style>
{CSS}
</style>
<header class="bar">
  <div class="bar-in">
    <button type="button" id="toc-btn" class="btn toc-btn" aria-controls="toc" aria-expanded="false">目录</button>
    <span id="where" class="where">AI 新需求与新分工研究报告</span>
    <div class="tools" role="group" aria-label="阅读设置">
      <button type="button" id="fs-down" class="btn" aria-label="缩小字号">A<small>−</small></button>
      <button type="button" id="fs-up" class="btn" aria-label="放大字号">A<small>+</small></button>
      <button type="button" id="tables" class="btn" aria-pressed="false">展开表格</button>
    </div>
  </div>
  <div class="progress" aria-hidden="true"><i id="prog"></i></div>
</header>
<div id="scrim" class="scrim" hidden></div>
<div class="layout">
  <nav id="toc" class="toc" aria-label="目录">
    <p class="toc-h">目录</p>
    {toc_html}
  </nav>
  <main id="main">
    <section class="hero">
      <p class="kicker">深度研究报告 · 证据截止 2026-10-20</p>
      <h1>{inline(hero["title"])}</h1>
      <p class="sub">{hero["sub"]}</p>
      <dl class="meta">{meta_html}</dl>
      <div class="guide">
        {hero["guide"]}
        <p class="legend">标签样式：<span class="tag tag-fact">事实｜高</span> <span class="tag tag-infer">推断｜中</span> <span class="tag tag-forecast">预测｜低</span>，竖线后是置信度。点按正文中的来源编号（如 <span class="cites">[<a class="cite" href="#R012">R012</a>]</span>）可查看来源；超过 10 行的表格默认收起，点按表头展开。</p>
      </div>
    </section>
    {body_html}
    <footer class="foot">
      <p>本页由报告的 Markdown 终稿自动转换生成（2026-10-20）。数字与来源以 Markdown 终稿及 <code>sources/</code>、<code>data/</code> 台账为准。</p>
    </footer>
  </main>
</div>
<div id="pop" class="pop" role="dialog" aria-modal="false" aria-labelledby="pop-title" hidden>
  <div class="pop-top"><span id="pop-id" class="pop-id"></span><span id="pop-lvl" class="pop-lvl"></span><button type="button" id="pop-x" class="btn pop-x" aria-label="关闭">关闭</button></div>
  <p id="pop-title" class="pop-title"></p>
  <p id="pop-org" class="pop-org"></p>
  <p id="pop-acc" class="pop-acc"></p>
  <div class="pop-act"><a id="pop-link" class="btn" target="_blank" rel="noopener">打开原始链接</a><button type="button" id="pop-go" class="btn">在参考文献表中查看</button></div>
</div>
<button type="button" id="back" class="back" hidden>返回刚才的位置</button>
<script>
{JS}
</script>
"""
open(OUT, "w", encoding="utf-8").write(page)
print(f"写出 {OUT}：{len(page.encode('utf-8')) / 1024:.0f} KB；目录条目 {len(toc)}；数据卡锚点 {len(APPB_IDS)}")
