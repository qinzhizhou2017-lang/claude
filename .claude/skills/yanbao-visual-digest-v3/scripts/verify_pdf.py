#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_pdf.py —— 成品 PDF 机器验收：页数 + 留白漏风审计 + 残留词

为什么要机器量留白：**漏风肉眼扫 PNG 抓不住**。2026-08-12 加上这一档之后，
回归测把此前"已交付"的作品全照出来了（有 8/10 页漏风的、10/13 页漏风的）。

判定（正文带内最大纵向空隙）：≥14mm = 漏风必修 ｜ 10–14mm = 偏松 ｜ <10mm = OK
封面默认豁免（hero 呼吸区 35–45mm 是设计，不是漏风）。

用法：
    python3 verify_pdf.py 成品.pdf --pages 3
    python3 verify_pdf.py 成品.pdf --pages 3 --gap-fail          # 把漏风升为硬门禁
    python3 verify_pdf.py 成品.pdf --no-gap                       # 只查页数与残留词
    python3 verify_pdf.py 成品.pdf --cover 1,5,9                  # 多份合辑：指定哪些页是封面/分隔页

依赖：pypdf、pypdfium2、pillow、numpy
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

# 模板范例残留词。⚠ 这些词也可能是**这篇研报真正要讲的公司**（比如做锂业时提宁德时代），
# 所以默认只 WARN，人看一眼再定；确定是残留就删，`--forbid-fail` 可升为硬门禁。
DEFAULT_FORBID = ["宁德时代", "占位", "Lorem ipsum", "示例数据", "TODO", "XXX", "待填"]
A4_H_MM = 297.0


def gap_audit(pdf: str, cover_pages: set[int], top_mm: float, bot_mm: float,
              dpi: int = 100, ink_thresh: float = 0.004):
    import numpy as np
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf)
    rows = []
    for i in range(len(doc)):
        page = doc[i]
        img = page.render(scale=dpi / 72, grayscale=True).to_pil()
        arr = np.asarray(img)
        h, w = arr.shape
        mm_per_px = A4_H_MM / h
        ink = (arr < 200).mean(axis=1)              # 每一行的“有墨比例”
        lo = int(top_mm / mm_per_px)                # 去掉页眉带
        hi = h - int(bot_mm / mm_per_px)            # 去掉页脚带
        band = ink[lo:hi]
        blank = band < ink_thresh
        best = cur = 0
        best_at = cur_at = 0
        for j, b in enumerate(blank):
            if b:
                if cur == 0:
                    cur_at = j
                cur += 1
                if cur > best:
                    best, best_at = cur, cur_at
            else:
                cur = 0
        gap_mm = best * mm_per_px
        at_mm = (lo + best_at) * mm_per_px
        # 页面底部“room”：最后一行墨到页脚带上沿的距离
        inked = (~blank).nonzero()[0]
        room_mm = ((hi - lo) - (inked[-1] + 1)) * mm_per_px if len(inked) else (hi - lo) * mm_per_px
        rows.append({"page": i + 1, "gap_mm": gap_mm, "at_mm": at_mm,
                     "room_mm": room_mm, "cover": (i + 1) in cover_pages})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", type=int, help="期望页数（对不上直接 FAIL）")
    ap.add_argument("--cover", default="1", help="封面/分隔页页码（逗号分隔），这些页豁免留白判定")
    ap.add_argument("--top", type=float, default=16.0, help="页眉带高度 mm，默认 16")
    ap.add_argument("--bottom", type=float, default=13.0, help="页脚带高度 mm，默认 13")
    ap.add_argument("--gap-fail", action="store_true", help="把漏风从 WARN 升为 FAIL")
    ap.add_argument("--no-gap", action="store_true")
    ap.add_argument("--forbid", default=",".join(DEFAULT_FORBID))
    ap.add_argument("--forbid-fail", action="store_true", help="把残留词从 WARN 升为 FAIL")
    a = ap.parse_args()

    pdf = Path(a.pdf)
    if not pdf.exists():
        sys.exit(f"没有这个文件：{pdf}")
    fails, warns = [], []

    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    n = len(reader.pages)
    print(f"\n═══ 验收 · {pdf.name} ═══\n页数：{n}", end="")
    if a.pages:
        if n == a.pages:
            print(f" ✅ = 期望 {a.pages}")
        else:
            print(f" ❌ 期望 {a.pages}")
            fails.append(f"页数 {n} ≠ 期望 {a.pages}")
    else:
        print()

    # 残留词（模板范例数据没删干净是老毛病）
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    hits = [w for w in a.forbid.split(",") if w.strip() and w.strip().lower() in text.lower()]
    if hits:
        print(f"残留词：△ 命中 {hits}（可能是模板范例没删干净，也可能这篇本来就讲它——人看一眼）")
        (fails if a.forbid_fail else warns).append(f"疑似模板残留词 {hits}")
    else:
        print("残留词：✅ 无")

    if not a.no_gap:
        cover = {int(x) for x in a.cover.split(",") if x.strip().isdigit()}
        rows = gap_audit(str(pdf), cover, a.top, a.bottom)
        print(f"\n{'页':>3} {'最大空隙':>8} {'位置':>7} {'底部room':>9}  判定")
        for r in rows:
            if r["cover"]:
                verdict = "封面/分隔页（豁免）"
            elif r["gap_mm"] >= 14:
                verdict = "❌ 漏风必修"
                (fails if a.gap_fail else warns).append(
                    f"P{r['page']} 空隙 {r['gap_mm']:.0f}mm（距页顶 {r['at_mm']:.0f}mm）")
            elif r["gap_mm"] >= 10:
                verdict = "△ 偏松"
                warns.append(f"P{r['page']} 空隙 {r['gap_mm']:.0f}mm 偏松")
            else:
                verdict = "✅ OK"
            if not r["cover"] and r["room_mm"] >= 40:
                verdict += " ｜ 底部富余，去回填内容"
            print(f"{r['page']:>3} {r['gap_mm']:>7.1f}mm {r['at_mm']:>6.0f}mm "
                  f"{r['room_mm']:>8.1f}mm  {verdict}")

    print()
    if warns:
        print("WARN：")
        for w in warns:
            print("  -", w)
        print("  修法优先级：①回原报告捞真内容（首选）→ ②全局放大组件一档（只能吃 25–30mm/页）"
              "→ ③给留白找结构归属。**永远不降字号**。")
    if fails:
        print("FAIL：")
        for f in fails:
            print("  -", f)
        return 1
    print("✅ 机器验收通过（注意：机器只查得了版式与抄录，C 类『数字对、主语错』查不出来）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
