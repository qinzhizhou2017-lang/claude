#!/usr/bin/env python3
"""抓取「Mark的AI产品经理知识库」全部公开页面并归档为 Markdown。

用途：knowledge/ai-pm/ 归档的原文补全工具。要求运行环境能访问 *.feishu.cn
（Claude Code 云端环境需在环境设置中放开网络策略；本地运行无此限制）。

依赖：
    pip install playwright
    # Claude Code 云端环境已预装 Chromium（PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers），
    # 本地运行则需：playwright install chromium

用法：
    python3 tools/crawl_feishu_kb.py            # 抓取全部种子及 Wiki 子页面
    python3 tools/crawl_feishu_kb.py --max 50   # 限制最多抓取页面数

输出：
    knowledge/ai-pm/raw/<序号>-<标题>.md   每页正文
    knowledge/ai-pm/raw/_index.md          抓取索引（标题、URL、发现的外链）
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "knowledge" / "ai-pm" / "raw"

SEEDS = [
    "https://www.feishu.cn/community/article?id=7444818740039909395",
    "https://www.feishu.cn/community/article?id=7577703602626497758",
    "https://qqs7y1hozd1.feishu.cn/wiki/DzlJw541diset0kFeYJcTlH3nRh",
    "https://qqs7y1hozd1.feishu.cn/wiki/QnPwwpKgKiGpFCkUrs7ciMIbnff",
]

# 只在该 Wiki 租户内做子页面遍历，避免爬出边界
WIKI_HOST = "qqs7y1hozd1.feishu.cn"
PAGE_DELAY_S = 2.0
RENDER_WAIT_S = 6.0

DOM_TO_MARKDOWN_JS = """
() => {
  const main = document.querySelector(
    '.wiki-content, .render-unit-wrapper, [data-page-id], article, .article-content, main'
  ) || document.body;
  const links = [];
  const walk = (node, depth) => {
    let out = '';
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) { out += child.textContent; continue; }
      if (child.nodeType !== Node.ELEMENT_NODE) continue;
      const tag = child.tagName.toLowerCase();
      const inner = () => walk(child, depth + 1);
      if (/^h[1-6]$/.test(tag)) {
        out += '\\n\\n' + '#'.repeat(+tag[1]) + ' ' + child.innerText.trim() + '\\n\\n';
      } else if (tag === 'li') {
        out += '\\n' + '  '.repeat(depth) + '- ' + inner().trim();
      } else if (tag === 'p' || tag === 'div' || tag === 'section') {
        out += inner() + (tag === 'p' ? '\\n\\n' : '\\n');
      } else if (tag === 'a') {
        const href = child.href || '';
        const text = child.innerText.trim();
        if (href) links.push({ text, href });
        out += text && href ? `[${text}](${href})` : text;
      } else if (tag === 'img') {
        out += `![${child.alt || 'image'}](${child.src || ''})`;
      } else if (tag === 'pre' || tag === 'code') {
        out += '\\n```\\n' + child.innerText + '\\n```\\n';
      } else if (tag === 'table') {
        out += '\\n' + child.innerText + '\\n';
      } else if (tag !== 'script' && tag !== 'style' && tag !== 'svg') {
        out += inner();
      }
    }
    return out;
  };
  const md = walk(main, 0).replace(/\\n{3,}/g, '\\n\\n').trim();
  return { title: document.title, markdown: md, links };
}
"""

COLLECT_WIKI_LINKS_JS = """
() => Array.from(document.querySelectorAll('a[href*="/wiki/"]'))
  .map(a => a.href).filter(Boolean)
"""


def slugify(title: str, index: int) -> str:
    clean = re.sub(r'[\\/:*?"<>|\s]+', "-", title).strip("-")[:60] or "untitled"
    return f"{index:02d}-{clean}.md"


async def scroll_sidebar(page):
    """滚动 Wiki 侧边栏，触发目录树懒加载。"""
    try:
        await page.evaluate(
            """async () => {
              const bars = document.querySelectorAll(
                '.wiki-tree, [class*="sidebar"], [class*="catalog"], [class*="tree"]');
              for (const el of bars) {
                for (let y = 0; y < el.scrollHeight; y += 300) {
                  el.scrollTop = y;
                  await new Promise(r => setTimeout(r, 150));
                }
              }
            }"""
        )
    except Exception:
        pass


async def crawl(max_pages: int) -> None:
    from playwright.async_api import async_playwright

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    queue = list(SEEDS)
    seen, results = set(), []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            locale="zh-CN",
        )
        while queue and len(results) < max_pages:
            url = queue.pop(0)
            key = url.split("#")[0].rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            print(f"[{len(results) + 1}] fetching {url}", flush=True)
            try:
                await page.goto(url, wait_until="networkidle", timeout=60_000)
            except Exception as exc:
                print(f"    ! failed: {exc}", file=sys.stderr)
                continue
            await asyncio.sleep(RENDER_WAIT_S)
            await scroll_sidebar(page)

            data = await page.evaluate(DOM_TO_MARKDOWN_JS)
            results.append({"url": url, **data})

            idx = len(results)
            out = OUT_DIR / slugify(data["title"], idx)
            out.write_text(
                f"# {data['title']}\n\n> 来源：{url}\n\n{data['markdown']}\n",
                encoding="utf-8",
            )
            print(f"    -> {out.relative_to(REPO_ROOT)} ({len(data['markdown'])} chars)")

            # 仅在目标 Wiki 租户内继续发现子页面
            if urlparse(url).hostname == WIKI_HOST:
                for href in await page.evaluate(COLLECT_WIKI_LINKS_JS):
                    href = urljoin(url, href)
                    if urlparse(href).hostname == WIKI_HOST:
                        k = href.split("#")[0].rstrip("/")
                        if k not in seen and href not in queue:
                            queue.append(href)
            await asyncio.sleep(PAGE_DELAY_S)
        await browser.close()

    index = OUT_DIR / "_index.md"
    lines = ["# 抓取索引\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. [{r['title']}]({r['url']}) — `{slugify(r['title'], i)}`")
        for link in r.get("links", [])[:50]:
            if link["href"].split("#")[0] != r["url"].split("#")[0]:
                lines.append(f"    - 外链：[{link['text'] or link['href']}]({link['href']})")
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\ndone: {len(results)} pages -> {OUT_DIR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=200, help="最多抓取页面数")
    args = parser.parse_args()
    asyncio.run(crawl(args.max))
