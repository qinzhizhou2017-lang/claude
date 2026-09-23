#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coverage_report.py —— 出处注释覆盖报数（原型 · **只报数，不判定**）

聚合成品 HTML 里的 `<!--src: MS p24 表-->` 注释，回答"我到底用了原文的哪些页"。

⚠ 三条使用纪律（2026-09-02 复盘定的，别自作主张改）：
  1. **不设门禁、不判 FAIL。** 尤其"前三页引用占比"不做硬约束——实测五份成品从 14% 到 86%，
     与满意度无关：被接受的批次里有 86% 的，被打回的只有 48%。投行研报摘要在前、图册在后，
     前三页占比高是**输入性质**，不是失败信号。
  2. 真正的门禁是人回答的三道是非题：标题是不是英文直译？章节顺序是不是照原文？
     有没有一句原文没有的主线判断？——加一条页数算术。
  3. 样本只有 5 份，任何阈值先当参考看。**跑满 5 次、用户点头，再决定这脚本要不要进流程。**

用法：
    python3 coverage_report.py 成品.html --doc MS:1-8/51 --doc GS:1-9/9 --pages MS=2,GS=2
      --doc  前缀:正文起-正文止/总页数    （前缀＝注释里用的那个标识，如 MS / GS / STAR）
      --pages 前缀=成品页数              （用来对页数档位；不传就只报数）
"""
from __future__ import annotations
import argparse, re, sys
from collections import defaultdict
from pathlib import Path

SRC_RE = re.compile(r"<!--\s*src\s*[:：]\s*(.*?)-->", re.S | re.I)
PAGE_RE = re.compile(r"(?:p|P|页)\s*\.?\s*(\d{1,3})")
RANGE_RE = re.compile(r"(?:p|P)\s*\.?\s*(\d{1,3})\s*[-–~]\s*(?:p|P)?\s*(\d{1,3})")
LITERAL_RE = re.compile(r"直译")
CALC_RE = re.compile(r"测算|本文测算")
EYE_RE = re.compile(r"目测|图/目测")
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


def budget(body: int) -> int:
    return 2 if body <= 10 else (3 if body <= 30 else 4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--doc", action="append", default=[],
                    help="前缀:正文起-正文止/总页数，可重复，如 MS:1-8/51")
    ap.add_argument("--pages", default="", help="前缀=成品页数，逗号分隔，如 MS=2,GS=2")
    a = ap.parse_args()

    html = Path(a.html).read_text(encoding="utf-8", errors="ignore")
    docs = {}
    for d in a.doc:
        try:
            pre, rest = d.split(":", 1)
            span, total = rest.split("/")
            s, e = span.split("-")
            docs[pre.upper()] = {"body": (int(s), int(e)), "total": int(total)}
        except ValueError:
            sys.exit(f"--doc 写法不对：{d}（应为 MS:1-8/51）")
    made = {}
    for kv in [x for x in a.pages.split(",") if x.strip()]:
        k, v = kv.split("=")
        made[k.strip().upper()] = int(v)

    notes = SRC_RE.findall(html)
    refs = defaultdict(list)       # 前缀 → [页码…]（同一注释里多个页码各计一次）
    counts = defaultdict(int)      # 前缀 → 注释条数
    literal = calc = eye = 0
    unknown = 0
    for n in notes:
        txt = " ".join(n.split())
        literal += 1 if LITERAL_RE.search(txt) else 0
        calc += 1 if CALC_RE.search(txt) else 0
        eye += 1 if EYE_RE.search(txt) else 0
        head = re.split(r"[\s:：]", txt.strip(), maxsplit=1)[0].upper().strip(",；;")
        pre = head if head in docs else (list(docs)[0] if len(docs) == 1 else "?")
        if pre == "?":
            for k in docs:
                if txt.upper().startswith(k):
                    pre = k
                    break
        if pre == "?":
            unknown += 1
        counts[pre] += 1
        pages = []
        for m in RANGE_RE.finditer(txt):
            pages += list(range(int(m.group(1)), int(m.group(2)) + 1))
        rest = RANGE_RE.sub(" ", txt)
        pages += [int(x) for x in PAGE_RE.findall(rest)]
        refs[pre] += pages

    title = ""
    m = H1_RE.search(html)
    if m:
        title = TAG_RE.sub("", m.group(1)).strip()

    print(f"\n═══ 覆盖报数 · {Path(a.html).name} ═══")
    print(f"出处注释共 {len(notes)} 条｜其中标『直译』{literal}、『测算』{calc}、『目测』{eye}")
    if unknown:
        print(f"⚠ 有 {unknown} 条注释认不出是哪份报告（前缀对不上 --doc），只计入总数")
    if title:
        print(f"成品大标题：{title}")

    for pre, d in docs.items():
        bs, be = d["body"]
        body_pages = set(range(bs, be + 1))
        used = [p for p in refs.get(pre, []) if 1 <= p <= d["total"]]
        used_body = [p for p in used if p in body_pages]
        uniq = sorted(set(used))
        uniq_body = sorted(set(used_body))
        first3 = [p for p in used if p <= bs + 2]
        cov = len(uniq_body) / max(len(body_pages), 1)
        n_body = be - bs + 1
        print(f"\n[{pre}] 总页 {d['total']} · 正文 P{bs}–P{be}（{n_body} 页）"
              f" · 注释 {counts.get(pre,0)} 条 · 引用 {len(used)} 次")
        print(f"      被引用的正文页 {uniq_body or '—'}")
        print(f"      正文覆盖率 {cov*100:.0f}%（{len(uniq_body)}/{n_body}）"
              f" · 未被引用的正文页 {sorted(body_pages - set(uniq_body)) or '—'}")
        print(f"      正文外（图册/披露）引用 {len(used) - len(used_body)} 次"
              f" · 前三页占引用 {len(first3)/max(len(used),1)*100:.0f}%（**只报数，不判定**）")
        want = budget(n_body)
        if pre in made:
            flag = "✅ 匹配" if made[pre] == want else "⚠ 不匹配"
            print(f"      页数档位：正文 {n_body} 页 → 建议 {want} 页，实际做了 {made[pre]} 页 {flag}")
            if made[pre] > want:
                print(f"      INFO 正文仅 {n_body} 页而做了 {made[pre]} 页：装载比接近 1:1，"
                      f"读起来会像翻译——这是页预算问题，不是文笔问题")
        else:
            print(f"      页数档位：正文 {n_body} 页 → 建议 {want} 页（没传 --pages，未对照）")
        if not uniq:
            print("      INFO 这份一条出处都没聚合到：注释前缀是不是写成别的了？")

    if literal:
        print(f"\nINFO 有 {literal} 处注释自标『直译』——大标题若在其中，按三条铁律第 1 条不过。")
    print("\n人来回答这三道是非题（机器答不了）：")
    print("  ① 大标题是不是英文原标题的直译？")
    print("  ② 章节顺序是不是照原文？")
    print("  ③ 有没有一句原文没有的主线判断？")
    return 0


if __name__ == "__main__":
    sys.exit(main())
