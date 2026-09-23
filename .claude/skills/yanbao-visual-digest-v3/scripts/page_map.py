#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
page_map.py —— 研报页面地图（v3 · 开工第一步）

回答一个问题：**这份 PDF 的正文到底有几页？**
9.01 事故的算术根源就在这：51 页的报告正文只有 8 页，3 页成品 ≈ 全译。
不跑这一步，就不知道自己在做几页的活。

用法：
    python3 page_map.py 报告.pdf                 # 打印页面地图 + 页数档位建议
    python3 page_map.py 报告.pdf --json map.json # 同时存 JSON
    python3 page_map.py 报告.pdf --text body.txt # 只抽正文文本（供写作与回查用）
    python3 page_map.py 报告.pdf --render 1-8    # 把这些页渲染成 PNG（无文本层时必用）
    python3 page_map.py 报告.pdf --render all --outdir pages/

依赖：pypdf（必需）、pypdfium2（仅 --render 需要）
本机（Mac/Win）均无 poppler，渲染一律走 pypdfium2。
"""
from __future__ import annotations
import argparse, json, os, re, sys

# —— 披露区强关键词：只在每页“页首 400 字”内匹配 ——
# 坑：投行会把 "See Appendix A-1 for analyst certification" 印在**每页页脚**，
# 按整页命中判会把全篇正文误判成披露区（实测 Nomura 8/8 页全中）。
DISCLOSURE_KW = [
    "disclosure section", "disclosure appendix", "important disclosures",
    "analyst certification", "analyst's certification", "required disclosures",
    "regulatory disclosures", "legal entity disclosures", "important information",
    "companies mentioned", "valuation methodology and risks", "disclaimer",
    "coverage universe investment banking clients", "stock rating category",
    "distribution of ratings", "global research conflict management",
    "免责声明", "分析师声明", "评级说明", "法律声明", "风险提示", "特别声明",
]
# 披露区“首页页首有章节标题”＝硬证据，直接信、不卡百分比
DISCLOSURE_TITLE = re.compile(
    r"^(disclosure\s+(section|appendix)|important\s+disclosures|analyst\s+certification|"
    r"appendix\s+a|disclaimer|免责声明|分析师声明)", re.I)
EXHIBIT_RE = re.compile(r"\b(exhibit|figure|fig\.|chart|table)\s*\d+|图表\s*\d+|表\s*\d+", re.I)

CHART_CHARS = 700      # 文本量低于此且带图表编号 → 判为“图表页”
NOTEXT_CHARS = 60      # 低于此视为无文本层
PROSE_CHARS = 1200     # 超过此字数的页认定为真正文，图册区到此为止
GALLERY_MIN_RUN = 8    # 尾部连续图表页 ≥ 这个数才算“附录图册”
GALLERY_MIN_SHARE = 0.30      # 且要占全篇 30% 以上，否则那些图表页是正文的一部分
DISCLOSURE_SOFT_CAP = 0.60   # 纯靠关键词密度推出来的披露区，最多占全篇 60%


def page_text(reader, i: int) -> str:
    try:
        return reader.pages[i].extract_text() or ""
    except Exception:
        return ""


# 跑头（running header）：每页都印的机构名/页码，不是这一页的标题，跳过
RUNNING_HEAD = re.compile(
    r"^(morgan stanley|goldman sachs|j\.?p\.? morgan|citi(group)?|ubs|nomura|barclays|hsbc|"
    r"deutsche bank|bernstein|jefferies|macquarie|global\s+insight|exhibit\s*\d+\s*:?$|"
    r"[\d\s/.\-]+|page\s*\d+)$", re.I)


def head_lines(txt: str, k: int = 6) -> list[str]:
    out = []
    for line in txt.splitlines():
        s = line.strip()
        if len(s) < 4 or s.isdigit() or RUNNING_HEAD.match(s):
            continue
        out.append(s)
        if len(out) >= k:
            break
    return out


def first_heading(txt: str) -> str:
    h = head_lines(txt, 1)
    return h[0][:58] if h else ""


def digit_ratio(txt: str) -> float:
    if not txt:
        return 0.0
    d = sum(c.isdigit() for c in txt)
    return d / max(len(txt), 1)


def classify(pages: list[dict]) -> dict:
    n = len(pages)
    # 1) 披露区，两档信任（8.14 实测教训）：
    #    ①硬证据——文档后 60% 里第一页“页首就是披露章节标题”，直接信、不卡百分比
    #      （Nomura 正文仅 2 页、披露占 6 页＝75% 是真的，卡百分比会判错）
    #    ②软证据——只有尾部连续关键词命中，套 60% 上限，宁可不跳也不误吞正文
    disc_start = None
    for i in range(int(n * 0.4), n):
        if any(DISCLOSURE_TITLE.search(h) for h in pages[i]["head_lines"]):
            disc_start = i + 1
            break
    if disc_start is None:
        tail = n
        while tail > 0 and pages[tail - 1]["disclosure_head"]:
            tail -= 1
        if tail < n:
            cand = tail + 1
            if (n - cand + 1) / n <= DISCLOSURE_SOFT_CAP:
                disc_start = cand
    body_end = (disc_start - 1) if disc_start else n

    # 2) 附录图册：投行的图册永远挂在尾部（摘要在前、图册在后），所以从 body_end 往前走。
    #    容忍中间夹 1 页非图表（章节隔页），遇到 chars > PROSE_CHARS 的真正文页就停。
    #    只有“长且占比大”的尾部图表段才算图册；短报告里的 Exhibit 页是正文的一部分，不许剔除。
    gallery = None
    i = body_end - 1          # 0-based
    slack = 1
    while i >= 0:
        p = pages[i]
        if p["kind"] in ("chart", "notext") and p["chars"] <= PROSE_CHARS:
            i -= 1
            continue
        if slack > 0 and p["chars"] <= PROSE_CHARS:
            slack -= 1
            i -= 1
            continue
        break
    run_start = i + 2          # 1-based，图册候选起始页
    run_len = body_end - run_start + 1
    if run_len >= GALLERY_MIN_RUN and run_len / n >= GALLERY_MIN_SHARE and run_start > 2:
        gallery = run_start
        body_end = gallery - 1

    notext = sum(1 for p in pages if p["kind"] == "notext")
    return {
        "total": n,
        "body": (1, body_end),
        "gallery": (gallery, (disc_start - 1) if disc_start else n) if gallery else None,
        "disclosure": (disc_start, n) if disc_start else None,
        "notext_pages": notext,
        "scanned": notext / n > 0.6,
    }


def budget(body_pages: int) -> str:
    if body_pages <= 10:
        return "2 页"
    if body_pages <= 30:
        return "3 页"
    return "4 页"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--text", dest="text_out", help="把正文页文本写到这个文件")
    ap.add_argument("--render", help="all 或 1-8 或 3,5,7：渲染成 PNG")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()

    try:
        from pypdf import PdfReader
    except ImportError:
        print("需要 pypdf：pip install pypdf", file=sys.stderr)
        return 2

    reader = PdfReader(a.pdf)
    pages = []
    for i in range(len(reader.pages)):
        t = page_text(reader, i)
        head = t[:400].lower()
        kind = "prose"
        if len(t.strip()) < NOTEXT_CHARS:
            kind = "notext"
        elif len(t) < CHART_CHARS and (EXHIBIT_RE.search(t) or digit_ratio(t) > 0.18):
            kind = "chart"
        pages.append({
            "page": i + 1,
            "chars": len(t),
            "heading": first_heading(t),
            "head_lines": head_lines(t),
            "exhibits": len(EXHIBIT_RE.findall(t)),
            "digit_ratio": round(digit_ratio(t), 3),
            "disclosure_head": any(k in head for k in DISCLOSURE_KW),
            "kind": kind,
            "_text": t,
        })

    m = classify(pages)
    for p in pages:
        pg = p["page"]
        if m["disclosure"] and pg >= m["disclosure"][0]:
            p["zone"] = "披露"
        elif m["gallery"] and m["gallery"][0] <= pg <= m["gallery"][1]:
            p["zone"] = "图册"
        else:
            p["zone"] = "正文"

    body_n = m["body"][1] - m["body"][0] + 1
    name = os.path.basename(a.pdf)
    print(f"\n═══ 页面地图 · {name} ═══")
    print(f"{'页':>4} {'区':<4} {'字数':>6} {'图表':>4} {'首标题行'}")
    for p in pages:
        print(f"{p['page']:>4} {p['zone']:<4} {p['chars']:>6} {p['exhibits']:>4} "
              f"{p['heading'] if p['kind'] != 'notext' else '（无文本层）'}")

    print(f"\n正文 P{m['body'][0]}–P{m['body'][1]}（{body_n} 页）", end="")
    if m["gallery"]:
        print(f" ｜ 图册 P{m['gallery'][0]}–P{m['gallery'][1]}", end="")
    if m["disclosure"]:
        print(f" ｜ 披露 P{m['disclosure'][0]}–P{m['disclosure'][1]}", end="")
    print(f" ｜ 总页 {m['total']} ｜ 无文本层 {m['notext_pages']} 页")

    print(f"\n【页数档位】正文 {body_n} 页 → 建议做 {budget(body_n)}"
          f"（≤10→2 / 11–30→3 / >30→4；候选洞见 <6 条再降一档）")
    print(f"【来源条拟印】正文 {body_n} 页（原报告 {m['total']} 页"
          + (f"，P{m['gallery'][0]}–P{m['gallery'][1]} 为图册未纳入" if m["gallery"] else "") + "）")
    if body_n <= 10:
        print("⚠ 正文很短：如果用户指定了 3 页及以上，先回问——"
              "「这篇正文只有 %d 页，X 页预算接近全译，改 2 页还是只做图表/关键结论？」" % body_n)
    if m["scanned"]:
        print("⚠ 这份多半是**扫描件（无文本层）**：文本抽取与关键词跳披露全部失效。"
              "必须 --render all 转图按页读；grep 类回查失效，改走隔离交叉验证。")
    print("⚠ 分区是启发式建议，动笔前扫一眼那几页确认边界（尤其图册/披露的第一页）。\n")

    if a.text_out:
        with open(a.text_out, "w", encoding="utf-8") as f:
            for p in pages:
                if p["zone"] == "正文":
                    f.write(f"\n\n===== P{p['page']} =====\n{p['_text']}")
        print(f"正文文本 → {a.text_out}")

    if a.json_out:
        for p in pages:
            p.pop("_text", None)
            p.pop("head_lines", None)
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"file": a.pdf, "map": m, "pages": pages}, f, ensure_ascii=False, indent=2)
        print(f"JSON → {a.json_out}")

    if a.render:
        try:
            import pypdfium2 as pdfium
        except ImportError:
            print("渲染需要 pypdfium2：pip install pypdfium2", file=sys.stderr)
            return 2
        if a.render == "all":
            want = list(range(1, len(pages) + 1))
        else:
            want = []
            for part in a.render.split(","):
                if "-" in part:
                    s, e = part.split("-")
                    want += list(range(int(s), int(e) + 1))
                else:
                    want.append(int(part))
        os.makedirs(a.outdir, exist_ok=True)
        doc = pdfium.PdfDocument(a.pdf)
        for pg in want:
            out = os.path.join(a.outdir, f"p{pg:03d}.png")
            doc[pg - 1].render(scale=a.dpi / 72).to_pil().save(out)
            print(f"  渲染 P{pg} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
