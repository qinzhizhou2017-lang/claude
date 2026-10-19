#!/usr/bin/env python3
"""把正文中的 [A0X-S00n] 引用统一重编号为 [R001]…，按首次出现顺序；同一 URL 合并为同一编号。
用法：python3 build_refs.py <输入正文.md> <输出正文.md> <输出参考文献.md>
未在台账中找到的编号会被列出（必须为 0 才能交付）。
"""
import json, glob, os, re, sys
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = {}
for f in glob.glob(f"{base}/sources/*.jsonl"):
    for l in open(f, encoding='utf-8'):
        if l.strip():
            r = json.loads(l); src[r["id"].strip()] = r
def norm(u): return re.sub(r'[#?].*$', '', (u or '').strip().rstrip('/').lower().replace('http://','https://').replace('://www.','://'))
inp, outp, refp = sys.argv[1:4]
text = open(inp, encoding='utf-8').read()
pat = re.compile(r'A\d{2}-S\d{3}')
order, url2r, id2r, missing = [], {}, {}, set()
for m in pat.finditer(text):
    sid = m.group(0)
    if sid in id2r: continue
    if sid not in src: missing.add(sid); continue
    u = norm(src[sid].get("url"))
    if u and u in url2r: id2r[sid] = url2r[u]; order[int(url2r[u][1:])-1][1].append(sid); continue
    rid = f"R{len(order)+1:03d}"; id2r[sid] = rid; order.append((rid, [sid]))
    if u: url2r[u] = rid
new = pat.sub(lambda m: id2r.get(m.group(0), m.group(0)), text)
# 合并同一方括号内的重复编号，如 [R001; R001]
def dedup(m):
    items = [x.strip() for x in re.split(r'[;；,，]', m.group(1))]
    seen = []
    for x in items:
        if x and x not in seen: seen.append(x)
    return '[' + '; '.join(seen) + ']'
new = re.sub(r'\[((?:R\d{3}|A\d{2}-S\d{3})(?:\s*[;；,，]\s*(?:R\d{3}|A\d{2}-S\d{3}))*)\]', dedup, new)
open(outp, 'w', encoding='utf-8').write(new)
lines = ["| 编号 | 来源 | 发布机构 | 类型 | 发布日期 | 数据期间 | 访问状态 | 链接 | 原台账编号 |", "|---|---|---|---|---|---|---|---|---|"]
for rid, sids in order:
    r = src[sids[0]]
    esc = lambda s: str(s or '').replace('|', '／').replace('\n', ' ')
    lines.append(f"| {rid} | {esc(r.get('title'))} | {esc(r.get('org'))} | {esc(r.get('type'))} | {esc(r.get('pub_date'))} | {esc(r.get('data_period'))} | {esc(r.get('access'))} | {esc(r.get('url'))} | {', '.join(sids)} |")
open(refp, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print("引用来源数", len(order), "原编号数", len(id2r), "缺失编号", sorted(missing))
