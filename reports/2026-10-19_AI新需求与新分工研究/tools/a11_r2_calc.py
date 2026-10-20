# A11 R2：核验算术与三项市场规模估算（本文测算）
import numpy as np
rng = np.random.default_rng(20261020)
N = 200_000
def U(lo, hi): return rng.uniform(lo, hi, N)
def LU(lo, hi): return np.exp(rng.uniform(np.log(lo), np.log(hi), N))  # 对数均匀
def q(x): return np.percentile(x, [10, 50, 90])
def fmt(x, d=1): return " / ".join(f"{v:,.{d}f}" for v in q(x))

print("=== 0. 核验算术 ===")
print(f"Anthropic run-rate 2025底→2026-05: 9→47 = {47/9:.2f} 倍；2026-05→07: 47→65 = {65/47:.2f} 倍")
print(f"Anthropic 2025 确认收入 4.59 / 年末 run-rate 9 = {4.59/9:.2f}；2024→2025: 0.386→4.59 = {4.59/0.386:.1f} 倍")
print(f"Anthropic 2026Q2 初步收入 >11.5×4 = {11.5*4:.0f}（对照 5 月 run-rate 47）；Q1 4.73×4 = {4.73*4:.1f}")
print(f"OpenAI：2026 初 20 亿/月×12 = {2*12} 十亿；Bloomberg 9 月底约 50 vs Axios '接近 70'：差 {70/50-1:.0%}")
print(f"Gartner GenAI 2025：设备 398+服务器 181 = {398+181} / 644 = {(398+181)/644:.1%}（正文称 80%）")
print(f"Gartner AI 2026（9 月版）：基础设施 1,480 / 2,670 = {1480/2670:.1%}；隐含 2025 基数 2,670/1.495 = {2670/1.495:,.0f}（2025-09 版为 1,500）")
print(f"Gartner 2026（5 月版）AI 服务 585.5 / AI 软件 453.2 = {585.5/453.2:.2f}")
print(f"中标：7539/1520 = {7539/1520:.2f} 倍(+{7539/1520-1:.0%})；295.2/64.67 = {295.2/64.67:.2f} 倍(+{295.2/64.67-1:.0%})；2025 披露均值 {295.2e4/5779:.0f} 万元 vs 中位数 86 万元；2024 均值 {64.67e4/1107:.0f} 万元")
print(f"Mercor 2025 总收入 ≈ 614/1.7 = {614/1.7:.0f} 百万美元；H1 2026 净收入(30–40%) = {614*0.3:.0f}–{614*0.4:.0f}；2B run-rate 净额 = {2000*0.3:.0f}–{2000*0.4:.0f}")
print(f"Cursor：40 亿×75% = {4*0.75:.1f}（摘要另写 26 亿，自相矛盾）")
print(f"备案+登记 1112+731 = {1112+731}（不得合称“1843 款 AI 产品”）；2025-12→2026-08 备案月均新增 {(1112-748)/8:.1f} 款")

print("\n=== D1 FDE/AI 部署类岗位劳动力成本（2026，本文测算）===")
base = 173_816                       # Bloomberry 基本工资中位数 [A11-S005]
c = U(1.15, 1.50)                    # 总薪酬/基本工资（假设）
l = U(1.20, 1.35)                    # 雇主附加成本（假设）
loaded = base * c * l
print("美国人均雇主成本(美元) P10/P50/P90:", fmt(loaded, 0))
v = U(0.10, 0.25)                    # 空缺率=空缺/在岗（假设）
# A 窄口径：FDE 头衔在线职位（全球 1,000–1,400；普查 1,333，2026-09-12）
open_glob = U(1000, 1400)
us_share = U(0.55, 0.80)             # 假设
hc_us_A = open_glob * us_share / v
W_us_A = hc_us_A * loaded / 1e9
print("A 美国 FDE 头衔在岗人数:", fmt(hc_us_A, 0), "；雇主成本(十亿美元):", fmt(W_us_A, 2))
# B R1 口径：Indeed 5,330 条 × 去重
hc_us_B = 5330 * U(0.40, 0.70) / v
W_us_B = hc_us_B * loaded / 1e9
print("B 美国（Indeed 5,330×去重）在岗:", fmt(hc_us_B, 0), "；成本:", fmt(W_us_B, 2))
# C 宽口径：含同类客户侧工程岗 18,000–25,000 条（全球）
open_broad = U(18000, 25000)
hc_us_C = open_broad * U(0.45, 0.70) / v
loaded_C = loaded * U(0.75, 1.0)     # 宽口径薪酬低于 FDE（假设）
W_us_C = hc_us_C * loaded_C / 1e9
print("C 美国宽口径在岗:", fmt(hc_us_C, 0), "；成本:", fmt(W_us_C, 1))
# 全球（不含中国）：窄口径
hc_gl_A = open_glob / v
W_gl_A = (hc_us_A * loaded + (hc_gl_A - hc_us_A) * loaded * U(0.45, 0.75)) / 1e9
print("全球(窄)在岗:", fmt(hc_gl_A, 0), "；成本:", fmt(W_gl_A, 2))
hc_gl_C = open_broad / v
W_gl_C = (hc_us_C * loaded_C + (hc_gl_C - hc_us_C) * loaded_C * U(0.45, 0.75)) / 1e9
print("全球(宽)在岗:", fmt(hc_gl_C, 0), "；成本:", fmt(W_gl_C, 1))
# 中国：窄口径（大厂/模型厂商 FDE），人数为纯假设
hc_cn = LU(1000, 5000)
pay_cn = U(3.5, 8.0) * U(14, 16) * U(1.30, 1.45)   # 万元/年：月薪×薪月×五险一金等
W_cn = hc_cn * pay_cn / 1e4                        # 亿元
print("中国窄口径人均成本(万元):", fmt(pay_cn, 0), "；总成本(亿元):", fmt(W_cn, 0))
# 中国：由公开中标额反推实施人力（交叉校验，仅公开招投标渠道）
tot_cn = 295.2 + 1760 * U(0.4, 0.86) / 100        # 亿元，未披露项目按 40–86 万元补
svc_cn = tot_cn * U(0.40, 0.70) * U(0.50, 0.80)   # 非硬件占比 × 服务占比
lab_cn = svc_cn * U(0.50, 0.70)                   # 人力成本占服务收入
fte_cn = lab_cn * 1e4 / U(20, 40)                 # 人均 20–40 万元/年
print("中国公开中标→实施服务(亿元):", fmt(svc_cn, 0), "；隐含实施人力(人年):", fmt(fte_cn, 0))
# 敏感性：各参数高/低比
print(f"敏感性(高/低)：空缺率 {0.25/0.10:.2f}；美国份额 {0.80/0.55:.2f}；在线职位 {1400/1000:.2f}；c {1.5/1.15:.2f}；l {1.35/1.2:.2f}")

print("\n=== D2 AI 实施服务市场（2025，本文测算）===")
us_spend = 37.0                       # Menlo 美国企业 GenAI 支出 2025（十亿美元）[A04-S001]
us_of_glob = U(0.45, 0.60)            # 美国占全球（假设）
glob_spend = us_spend / us_of_glob
self_share = U(0.50, 0.70)            # 自助型（编程/对话/席位）占比（假设）
k_self = U(0.05, 0.30)                # 自助型 服务/软件比（假设，SaaS 经验）
k_int = U(1.0, 3.0)                   # 集成型 服务/软件比（ERP 类比下限 1；IDC 生态乘数 5–9 仅作上界）
k = self_share * k_self + (1 - self_share) * k_int
S_top = glob_spend * k
print("全球企业 GenAI 支出(十亿美元):", fmt(glob_spend, 0), "；加权 k:", fmt(k, 2), "；服务市场(十亿美元):", fmt(S_top, 0))
S_top_us = us_spend * k
print("美国服务市场(十亿美元):", fmt(S_top_us, 0))
# 供给侧：埃森哲 + IBM 咨询 GenAI 收入 ÷ 份额
acn = 2.7                             # 埃森哲 FY2025 GenAI 收入 [A05-S003]
ibm = U(2.5, 5.0)                     # IBM 咨询 GenAI 年收入（由业务簿推算，假设）
share = U(0.10, 0.25)                 # 两家合计份额（假设）
S_sup = (acn + ibm) / share
print("供给侧(十亿美元):", fmt(S_sup, 0), f"；两法中位数之比 {np.median(S_top)/np.median(S_sup):.2f}")
lo_hi_top = q(S_top); lo_hi_sup = q(S_sup)
print(f"P10–P90 重叠区间: {max(lo_hi_top[0], lo_hi_sup[0]):.0f}–{min(lo_hi_top[2], lo_hi_sup[2]):.0f} 十亿美元")
# 若机械套用 IDC 生态乘数
print(f"机械套用 IDC 乘数 5.2–8.8 × 全球支出中位 {np.median(glob_spend):.0f} = {5.2*np.median(glob_spend):.0f}–{8.8*np.median(glob_spend):.0f} 十亿美元（不采用）")
print(f"Gartner 2026 AI 服务 585.5 十亿美元为 M5 宽口径，是本测算中位数的 {585.5/np.median(S_top):.0f} 倍（不可比）")
# 中国公开渠道
print("中国公开中标渠道实施服务(亿元):", fmt(svc_cn, 0))
print(f"86 万元中位项目 ÷ 人月成本 2–3 万元 = {86/3:.0f}–{86/2:.0f} 人月")
# 人力含量交叉：全球实施服务 × 人力占比 ÷ 人均成本
fte_glob = S_top * 1e9 * U(0.5, 0.7) / U(120_000, 250_000)
print("全球 GenAI 实施隐含人力(人年):", fmt(fte_glob, 0))

print("\n=== D5 专家数据市场（本文测算）===")
# 2024 年（M1a 近似：媒体/研究机构所称年度收入，总额口径）
scale24 = 0.87; surge24 = U(1.0, 1.2); turing24 = 0.30; mercor24 = U(0.05, 0.15); other24 = U(1.1, 1.4)
core24 = scale24 + surge24 + turing24 + mercor24
print("2024 核心四家(十亿美元):", fmt(core24, 2), "；含长尾:", fmt(core24 * other24, 2))
# 2026 年中 run-rate（M1c，总额口径）
mercor26 = 2.0; hshake26 = U(1.0, 1.1)
surge26 = U(1.2, 3.0); scale26 = U(0.5, 1.5); turing26 = U(0.3, 0.8)   # 后三项为假设
gross26 = (mercor26 + hshake26 + surge26 + scale26 + turing26) * other24
print("2026 年中 总额 run-rate(十亿美元):", fmt(gross26, 1))
take = U(0.30, 0.45)                  # 平台留存率（Mercor/Handshake 披露 30–40%，Surge 等假设更高）
net26 = gross26 * take
payout26 = gross26 - net26
print("净收入 run-rate:", fmt(net26, 1), "；付给专家的年化报酬:", fmt(payout26, 1))
hrs = U(800, 1800); wage = U(85, 122)
fte_exp = payout26 * 1e9 / (hrs * wage)
print("隐含“满负荷当量”专家人数(人):", fmt(fte_exp, 0))
# 买方侧校验（独立参数）：实验室收入 × 人类数据支出比例
labs = U(110, 160)                    # OpenAI+Anthropic+Google/Meta/xAI 等相关 run-rate（假设，十亿美元）
ratio = U(0.03, 0.07)                 # 人类数据支出/收入（假设）
buy = labs * ratio
print("买方侧(十亿美元):", fmt(buy, 1), f"；与供给侧总额中位数之比 {np.median(gross26)/np.median(buy):.2f}")
print(f"Mercor 集中度：约 90% 收入来自 AI 模型公司；Surge 约 12 家前沿实验室")
