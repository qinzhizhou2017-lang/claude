#!/usr/bin/env python3
"""合成最终报告：正文（第 0–7 章）＋附录 B–E，统一把 [A0X-S00n] 重编号为 [R00n]，生成附录 A 参考文献。
用法：python3 -I tools/assemble.py
输出：AI新需求与新分工研究报告.md
"""
import json, glob, os, re, datetime
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DR = f"{B}/drafts"

# ---------- 附录 B：关键数据证据表 ----------
KEY_CARDS = """
A01-D001 A01-D032 A01-D003 A01-D004 A01-D006 A01-D007 A01-D011 A11-D044 A01-D013 A01-D017 A01-D019 A01-D020 A01-D022 A01-D023
A11-D013 A11-D014 A11-D016 A11-D021 A11-D018 A04-D010 A04-D014 A11-D023 A04-D006 A04-D007 A11-D035 A11-D040 A11-D041 A11-D042
A04-D018 A04-D020 A04-D021 A05-D002 A05-D007 A05-D010 A05-D021 A11-D052 A10-D016 A04-D033 A11-D046 A10-D009 A10-D010 A11-D047
A02-D001 A02-D002 A02-D004 A11-D043 A02-D008 A02-D009 A02-D010 A02-D012 A02-D013 A02-D014 A02-D015 A02-D017 A08-D002 A08-D005
A08-D008 A07-D005 A07-D020 A07-D021 A07-D019 A07-D026
A11-D001 A11-D002 A11-D004 A11-D006 A11-D008 A03-D006 A03-D007 A03-D010 A03-D011 A03-D012 A03-D013 A03-D017 A03-D023 A03-D024
A03-D025 A11-D038 A11-D054 A11-D055 A03-D038 A03-D039
A10-D025 A10-D026 A10-D027 A10-D028 A10-D029 A10-D030 A10-D031 A10-D034 A10-D035 A10-D036 A10-D041 A11-D056
A08-D018 A08-D021 A08-D024 A08-D026 A08-D029
A01-D024 A01-D025 A01-D026 A01-D027 A01-D028 A01-D029 A01-D030
A02-D026 A02-D027 A02-D029 A02-D032 A02-D033 A11-D050 A11-D057
A05-D028 A05-D031 A05-D033 A05-D035 A05-D036 A05-D037
A06-D001 A06-D002 A06-D011 A06-D016 A06-D018 A06-D019 A06-D021 A06-D025
A07-D003 A07-D032 A07-D033 A07-D038 A07-D040 A07-D041 A07-D042
A09-D001 A09-D006 A09-D011 A09-D013 A09-D017 A09-D020 A09-D023 A09-D024 A09-D027 A09-D029
A04-D036 A04-D037 A04-D039 A04-D041 A04-D042 A04-D043 A04-D044 A04-D045 A04-D046
""".split()

cards = {}
for f in glob.glob(f"{B}/data/*.jsonl"):
    for l in open(f, encoding="utf-8"):
        if l.strip():
            r = json.loads(l); cards[r["id"]] = r

def cell(s, n=None):
    s = str(s if s is not None else "").replace("|", "／").replace("\n", " ").strip()
    if n and len(s) > n:
        s = s[:n] + "…"
    return s or "—"

rows = ["| 数据卡 | 指标 | 数值 | 单位 | 地区 | 统计期间 | 发布日期 | 来源 | 方法与口径限制 | 口径 | 交叉验证 | 性质 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|"]
missing = []
for cid in KEY_CARDS:
    r = cards.get(cid)
    if not r:
        missing.append(cid); continue
    srcs = "".join(f"[{s}]" for s in (r.get("source_ids") or []))
    rows.append("| " + " | ".join([cid, cell(r.get("metric")), cell(r.get("value"), 220), cell(r.get("unit")), cell(r.get("region")),
                                   cell(r.get("period")), cell(r.get("pub_date")), cell(srcs), cell(r.get("method_limits"), 160),
                                   cell(r.get("market_type")), cell(r.get("cross_check"), 120), cell(r.get("nature"))]) + " |")
appB = ("## 附录 B　关键数据证据表\n\n"
        f"下表从 12 名 Agent 建立的 {len(cards)} 张数据卡中选出支撑正文结论的 {len(rows)-2} 张，按正文章节顺序排列。"
        "“数值”与“方法与口径限制”两列过长时截断（以“…”标示），完整内容见 `data/*.jsonl`。"
        "“口径”列为市场规模类型（M1a 确认收入、M1b 合同口径、M1c 年化外推、M2 企业支出、M3 融资、M4 潜在市场、M5 预测）；"
        "“性质”列区分事实、推断与预测。标注“本文测算”的数值的计算过程见附录 C。\n\n" + "\n".join(rows) + "\n")
open(f"{DR}/appB.md", "w", encoding="utf-8").write(appB)

# ---------- 合成 ----------
order = ["ch0_执行摘要.md", "ch1_研究问题方法与证据边界.md", "ch2_技术成本与企业采用.md", "ch3_替代重构与新增需求.md",
         "ch4_分析尺度与候选机会地图.md", "ch5_重点方向深度研究.md", "ch6_机会比较情景分析与反方结论.md", "ch7_个人转型与小团队行动方案.md"]
body = "\n\n".join(open(f"{DR}/{f}", encoding="utf-8").read().strip() for f in order)
apps = "\n\n".join(open(f"{DR}/{f}", encoding="utf-8").read().strip() for f in ["appB.md", "appC.md", "appD.md", "appE.md"])

# 章节标题层级：章为一级标题 → 二级；节为二级 → 三级（在最终文件中由报告标题占据一级）
def demote(t):
    return re.sub(r"(?m)^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", t)
body = demote(body)
apps_d = apps  # 附录内已用二级、三级标题

text = body + "\n\n# 附录\n\n<!--APPENDIX_A-->\n\n" + apps_d

# 重编号
src = {}
for f in glob.glob(f"{B}/sources/*.jsonl"):
    for l in open(f, encoding="utf-8"):
        if l.strip():
            r = json.loads(l); src[r["id"].strip()] = r
def norm(u):
    return re.sub(r"[#?].*$", "", (u or "").strip().rstrip("/").lower().replace("http://", "https://").replace("://www.", "://"))
pat = re.compile(r"A\d{2}-S\d{3}")
order_ids, url2r, id2r, miss = [], {}, {}, set()
for m in pat.finditer(text):
    sid = m.group(0)
    if sid in id2r: continue
    if sid not in src: miss.add(sid); continue
    u = norm(src[sid].get("url"))
    if u and u in url2r:
        id2r[sid] = url2r[u]; order_ids[int(url2r[u][1:]) - 1][1].append(sid); continue
    rid = f"R{len(order_ids)+1:03d}"; id2r[sid] = rid; order_ids.append((rid, [sid]))
    if u: url2r[u] = rid
text = pat.sub(lambda m: id2r.get(m.group(0), m.group(0)), text)
def dedup(m):
    items, seen = [x.strip() for x in re.split(r"[;；,，]", m.group(1))], []
    for x in items:
        if x and x not in seen: seen.append(x)
    return "[" + "; ".join(seen) + "]"
text = re.sub(r"\[((?:R\d{3})(?:\s*[;；,，]\s*R\d{3})*)\]", dedup, text)
text = re.sub(r"\]\[(R\d{3})", r"; \1", text)  # [R001][R002] → [R001; R002]
text = re.sub(r"\[((?:R\d{3})(?:;\s*R\d{3})*)\]", dedup, text)

typ = {"E1": 0, "E2": 0, "E3": 0, "E4": 0, "E5": 0}
lines = []
for rid, sids in order_ids:
    r = src[sids[0]]
    t = (r.get("type") or "").strip()[:2]
    if t in typ: typ[t] += 1
    e = lambda s: cell(s)
    lines.append(f"| {rid} | {e(r.get('title'))} | {e(r.get('org'))} | {e(r.get('type'))} | {e(r.get('pub_date'))} | {e(r.get('data_period'))} | {e(r.get('access'))} | {e(r.get('url'))} | {', '.join(sids)} |")
appA = ("## 附录 A　参考文献\n\n"
        f"正文与附录共引用 {len(order_ids)} 个不同来源（同一 URL 被多个 Agent 记录时合并为一个编号）。"
        f"按证据等级：E1 {typ['E1']} 个、E2 {typ['E2']} 个、E3 {typ['E3']} 个、E4 {typ['E4']} 个、E5 {typ['E5']} 个。"
        "“访问状态”如实标注：本研究环境无法打开原文，“检索摘要级”指内容来自检索工具对页面的摘要，“多检索式复核”指两个以上不同检索式结果一致，“未能确认”指未能在原始发布方确认。"
        "“原台账编号”对应 `sources/*.jsonl` 中的记录，可追溯到提出该来源的 Agent 与检索式。\n\n"
        "| 编号 | 来源 | 发布机构 | 等级 | 发布日期 | 数据期间 | 访问状态 | 链接 | 原台账编号 |\n|---|---|---|---|---|---|---|---|---|\n" + "\n".join(lines) + "\n")
text = text.replace("<!--APPENDIX_A-->", appA)

# 字数统计（正文 = 附录之前）
han = re.compile(r"[一-鿿㐀-䶿]")
cp = re.compile(r"[　-〿＀-￯—…“”‘’]")
body_part = text.split("\n# 附录\n")[0]
h = len(han.findall(body_part)); p = len(cp.findall(body_part))
ch0_end = body_part.find("\n## 第一章")
h_wo0 = len(han.findall(body_part[ch0_end:]))

today = "2026-10-20"
header = f"""# 知识工作的成本塌缩之后：2027–2031 年人工智能催生的可验证新需求、新分工与个人进入路径

**一项由 1 名主协调 Agent 与 12 名专业 Agent 分轮完成的深度研究**

| 项目 | 内容 |
|---|---|
| 研究执行期 | 2026 年 10 月 19 日至 10 月 20 日 |
| 证据检索截止日期 | {today} |
| 预测区间 | 2027 年 1 月至 2031 年 10 月（三年观察点 2029 年底，五年观察点 2031 年） |
| 正文篇幅 | 执行摘要与第一至七章共 {h:,} 个汉字（含中文标点 {h+p:,} 字）；其中第一至七章 {h_wo0:,} 个汉字。参考文献与附录不计入正文 |
| 证据规模 | 来源台账 {len(src):,} 条，正文与附录引用 {len(order_ids)} 个不同来源；数据卡 {len(cards)} 张 |
| 证据边界 | 研究环境只能使用网页检索、无法打开原文，全部来源为“检索摘要级”；详见第一章 1.5 节与附录 D |

**阅读说明。**方括号中的编号（如 [R012]）对应附录 A 参考文献。关键判断标注为【事实】【推断】【预测】并附置信度（高／中／低）；“本文测算”的数字见附录 C。机会类别：T1 新产业或新细分市场、T2 新商业模式、T3 新职业或新组织职能、T4 既有行业或职业升级、T5 短期过渡机会；新颖度：N0 改名、N1 既有需求显著扩张、N2 既有职能重构、N3 真正新需求；案例状态 C1 宣布或试点至 C5 持续续约，C-R 为撤回或缩减；市场口径 M1a/M1b/M1c/M2/M3/M4/M5 见第一章 1.4 节。

## 目录

- 执行摘要与核心结论
- 第一章　研究问题、方法与证据边界
- 第二章　技术、成本与企业采用的变化
- 第三章　知识工作的替代、重构与新增需求
- 第四章　分析尺度：从核实 FDE 开始，到候选机会地图
- 第五章　重点方向深度研究（D1–D10）
- 第六章　机会比较、情景分析与反方结论
- 第七章　个人转型与小团队行动方案
- 附录 A　参考文献；附录 B　关键数据证据表；附录 C　关键计算过程；附录 D　重要争议说明与证据缺口；附录 E　Agent 执行记录

"""
out = header + text
open(f"{B}/AI新需求与新分工研究报告.md", "w", encoding="utf-8").write(out)
print("缺失台账编号:", sorted(miss), "缺失数据卡:", missing)
print(f"引用来源 {len(order_ids)}；正文汉字 {h}（含标点 {h+p}）；第一至七章汉字 {h_wo0}；附录 B 行数 {len(rows)-2}")
