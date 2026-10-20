#!/usr/bin/env python3
"""主协调复核：重算报告正文中引用的关键“本文测算”数字。
参数取自对应深度研究稿与来源台账；输出写入附录 C。
运行：python3 -I tools/verify_calcs.py
"""
from math import log, sqrt, erf, prod

def Phi(x):
    return 0.5 * (1 + erf(x / sqrt(2)))

def line(title):
    print("\n【" + title + "】")

line("C1 Palantir 2025 年毛利率（5.1、表 4-1）")
rev, cogs = 44.75, 7.89                     # 亿美元 [A03-S009]
print(f"毛利率 = (44.75 - 7.89) / 44.75 = {(rev-cogs)/rev:.1%}")

line("C2 FDE 全口径年成本与客户最低年合同额（5.1）")
base = 173816                               # 美元，Bloomberry 中位数 [A03-S017]
lo, hi = base*1.15*1.20, base*1.50*1.35     # 总薪酬倍数 × 雇主附加成本
print(f"每名 FDE 年成本 = {lo:,.0f} – {hi:,.0f} 美元")
for share in (1.0, 0.5, 0.25):
    for cap in (0.30, 0.15):
        print(f"  分摊 {share} 人年、FDE 成本占 ACV ≤{cap:.0%}：最低 ACV {lo*share/cap/1e4:,.0f} – {hi*share/cap/1e4:,.0f} 万美元")

line("C3 Infosys 非 AI 收入增速对上年 AI 占比 p 的敏感性（5.2）")
for p in (0.03, 0.05, 0.06, 0.07):
    g = 1.024 * (1 - 0.082) / (1 - p) - 1    # 总增速 2.4%，当期 AI 占比 8.2% [A10-S072]
    print(f"  p={p:.0%}: 非 AI 收入同比 {g:+.1%}")
line("C4 Upwork 非 AI 交易额增速对上年 AI 占比 q 的敏感性（5.2）")
for q in (0.10, 0.20):
    g = (0.96 - q * 1.22) / (1 - q) - 1      # 总 GSV -4%，AI 相关 +22% [A10-S052]
    print(f"  q={q:.0%}: 非 AI 交易额同比 {g:+.1%}")

line("C5 2025 年大模型中标项目的对数正态拆分（5.2）")
med, mean, total = 86.0, 511.0, 295.2       # 万元、万元、亿元 [A10-S041]
mu, s2 = log(med), 2 * log(mean / med)
s = sqrt(s2)
for cut in (100, 300):
    n_share = Phi((log(cut) - mu) / s)
    a_share = Phi((log(cut) - mu - s2) / s)
    print(f"  ≤{cut} 万元：项目数占比 {n_share:.1%}，金额占比 {a_share:.1%}，约 {a_share*total:.1f} 亿元（σ={s:.2f}）")

line("C6 三人交付团队单位经济的简化复核（5.2；参数见 A10-D041，运营起始月份与其他费用为主协调假设）")
def team(builds, price, conv, fee, staff, coll=0.90, token=0.08, start_month=6.5, other=0.0):
    ops_clients = builds * conv
    y1_ops = ops_clients * fee * (12 - start_month)
    y1_rev = (builds * price + y1_ops) * coll * (1 - token)
    y1 = y1_rev - 3 * staff * 12 - other
    y2_ops = ops_clients * fee * 12 + ops_clients * fee * (12 - start_month)   # 第二年零流失
    y2_rev = (builds * price + y2_ops) * coll * (1 - token)
    y2 = y2_rev - 3 * staff * 12 - other
    return y1, y2, y1_ops / (builds * price + y1_ops), y2_ops / (builds * price + y2_ops)
for name, args in [("保守", (6, 6, 0.2, 0.5, 2.0)), ("基准", (8, 12, 0.4, 1.0, 2.5)), ("乐观", (10, 20, 0.6, 1.5, 3.0))]:
    y1, y2, s1, s2_ = team(*args)
    print(f"  {name}：第一年 {y1:+.0f} 万元，第二年 {y2:+.0f} 万元；运营收入占比 {s1:.0%} → {s2_:.0%}")
print("  注：A10 原稿为保守 -53/-47、基准 -10/+22、乐观 +94/+188 万元；简化模型方向一致，绝对值对运营起始月份、其他费用与流失率敏感。")

line("C7 中国生成式 AI 备案与登记代理年收入（5.7）")
def filing(nf, nr, pen, pf, pr):
    return nf * pen * pf + nr * pen * pr      # 万元
print(f"  保守：{filing(546, 444, 0.3, 5, 1):,.0f} 万元")
print(f"  基准：{filing((546+732)/2, (444+603)/2, 0.5, 10, 2.5):,.0f} 万元")
print(f"  乐观：{filing(732, 603, 0.7, 20, 5):,.0f} 万元")

line("C8 按件交付的单件成本与毛利（5.8，表 5-5；参数为 A07 假设）")
def unit(P, ai, t, r, w, e, L, a=0.95):
    review = t * (1 + r) / 60 * w
    C = (ai + review + e * L) / a
    return C, review / a, e * L / a, 1 - C / P
for name, args in [("标准函件", (60, 0.855, 6, 0.2, 90, 0.01, 500)),
                   ("人身损害索赔材料包", (1500, 12.35, 90, 0.3, 150, 0.01, 10000)),
                   ("对账差异条目", (10, 0.1425, 2, 0.15, 80, 0.005, 200))]:
    C, rv, lb, gm = unit(*args)
    print(f"  {name}：单件成本 {C:.1f} 元（复核 {rv:.1f}、责任准备 {lb:.1f}），毛利率 {gm:.0%}")

line("C9 客服解决率与人员结构（5.3，表 5-3；α 为假设）")
per_agent = 28e6 * 0.81 / 853 / 12          # Klarna 口径 [A08-S068]
base_agents = 1e6 / per_agent
print(f"  每名等效坐席每月处理 {per_agent:,.0f} 次；每月 100 万次接触需 {base_agents:.0f} 名坐席")
for r, k in ((0.5, 1.3), (0.7, 1.6), (0.85, 2.0)):
    seats = 1e6 * (1 - r) * k / per_agent
    ai_eq = 1e6 * r / per_agent
    print(f"  解决率 {r:.0%}，k={k}：兜底坐席 {seats:.0f}（{seats/base_agents:.0%}），运营层 {ai_eq*0.03:.0f}–{ai_eq*0.08:.0f}")

line("C10 其他比例")
print(f"  埃森哲 FY2025 生成式 AI 收入占比 = 27 / 697 = {27/697:.1%} [A05-S003]")
print(f"  埃森哲先进 AI 平均项目新签额 = 115 亿 / 11,000 = {115e8/11000/1e4:,.0f} 万美元 [A05-S005]")
print(f"  Prisma AIRS 占 Palo Alto 下一代安全 ARR = 1.0–1.2 / 91 = {1.0/91:.1%}–{1.2/91:.1%} [A12-S047][A12-S048]")
print(f"  AI 应用层安全并购已披露对价合计 = 7.00 + 1.336 + 1.80 = {7.00+1.336+1.80:.2f} 亿美元（Prompt Security 只计现金）")
print(f"  Appen 2024 年收入较 2021 年峰值 = 2.343 / 4.47 - 1 = {2.343/4.47-1:.0%} [A12-S038][A02-S077]")
print(f"  Anthropic 2025 年确认收入 / 年末年化 = 45.9 / 90 = {45.9/90:.0%} [A11-S073][A04-S039]")
print(f"  中国 FDE 年包（月薪 3–8 万元 × 15 薪）= {3*15} – {8*15} 万元；普通驻场（1–2 万 × 12–13 薪）= 12 – 26 万元")
