#!/usr/bin/env python3
"""检查各 Agent 来源台账与数据卡：可解析性、字段完整性、URL 重复、类型分布。"""
import json, glob, os, collections, sys
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
need_s = ["id","title","org","type","pub_date","url","access","key_content"]
allurls = collections.defaultdict(list)
for f in sorted(glob.glob(f"{base}/sources/*.jsonl")):
    rows, bad = [], 0
    for i, l in enumerate(open(f, encoding='utf-8')):
        if not l.strip(): continue
        try: rows.append(json.loads(l))
        except Exception: bad += 1
    types = collections.Counter(r.get("type","?") for r in rows)
    acc = collections.Counter(r.get("access","?") for r in rows)
    miss = sum(1 for r in rows if any(not r.get(k) for k in need_s))
    for r in rows: allurls[r.get("url","").rstrip('/')].append(r.get("id"))
    print(os.path.basename(f), "条数", len(rows), "坏行", bad, "缺字段", miss, dict(types), dict(acc))
dups = {u: ids for u, ids in allurls.items() if len(ids) > 1}
print("跨台账重复 URL 数：", len(dups))
for f in sorted(glob.glob(f"{base}/data/*.jsonl")):
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip())
    print(os.path.basename(f), "数据卡", n)
