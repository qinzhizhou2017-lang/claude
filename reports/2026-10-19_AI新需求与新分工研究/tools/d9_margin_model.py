#!/usr/bin/env python3
"""D9 推理成本工程毛利节省估算（A09，R2，2026-10-20）。
所有参数为本文假设，取值依据见 agents/R2/D9_AI单位经济工程.md 第 5 节。
价格基准：旗舰档输入 4、输出 20 美元/百万 token，缓存读为输入价 5% [A01-S035]；
缓存写入溢价 1.25 倍 [A09-S041][A09-S042]；批处理/低谷 5 折 [A01-S039][A01-S044]。
"""
from itertools import product

SC = ["保守", "基准", "乐观"]
P = {
    # 起始毛利与推理占营业成本比例
    "GM0":   [0.60, 0.45, 0.25],   # Bessemer 流星 60% / ICONIQ 均值 45% / 超新星 25%
    "k_inf": [0.40, 0.51, 0.70],   # 推理占营业成本；0.51 来自 S-4/A [A09-S017]
    # 负载结构：输入:输出 token 比
    "r_io":  [3, 10, 30],          # 对话型 / 一般 Agent / 编程 Agent（假设）
    # 缓存命中率：平台默认 h0 → 工程优化后 h1
    "h0":    [0.40, 0.30, 0.20],
    "h1":    [0.55, 0.70, 0.85],
    # 路由：可降档请求占比 f、降档后单价比 p、升级重跑率 e
    "f":     [0.20, 0.40, 0.60],
    "p":     [0.50, 0.25, 0.05],   # Sonnet 级 0.5 / 开源旗舰约 0.2–0.33 / Haiku 级 0.025
    "e":     [0.15, 0.10, 0.05],
    "g_route_default": [0.50, 0.30, 0.10],  # 平台默认路由已拿走的路由节省份额（2027 年）
    # 批处理/低谷可转移负载占比
    "b":     [0.05, 0.15, 0.30],
    # 上下文压缩：未命中缓存输入 token 的削减比例
    "x":     [0.05, 0.15, 0.30],
}
PIN, POUT, CACHE_READ, NET_HIT_SAVING = 4.0, 20.0, 0.05, 0.90  # 净节省 = 0.95 - 写入溢价 0.25 / 约 5 次复用

def run(i):
    v = {k: P[k][i] for k in P}
    c = (1 - v["GM0"]) * v["k_inf"]                       # 推理成本 / 收入
    phi = v["r_io"] * PIN / (v["r_io"] * PIN + POUT)       # 输入成本占推理成本份额
    s_cache_def = phi * v["h0"] * NET_HIT_SAVING           # 平台默认缓存（不需工程）
    s_cache_inc = phi * (v["h1"] - v["h0"]) * NET_HIT_SAVING
    s_route_all = v["f"] * (1 - v["p"] - v["e"])
    s_route_def = s_route_all * v["g_route_default"]
    s_route_inc = s_route_all - s_route_def
    s_batch = v["b"] * 0.5
    s_comp = phi * (1 - v["h1"]) * v["x"]
    comb = lambda xs: 1 - __import__("math").prod(1 - s for s in xs)
    S_def = comb([s_cache_def, s_route_def])
    S_all = comb([s_cache_def + s_cache_inc, s_route_all, s_batch, s_comp])
    S_inc = 1 - (1 - S_all) / (1 - S_def)                  # 相对“已用默认功能”基线的增量
    return dict(c=c, phi=phi, S_def=S_def, S_all=S_all, S_inc=S_inc,
                dGM_all=c * S_all, dGM_inc=c * (1 - S_def) * S_inc,
                parts=dict(cache_inc=s_cache_inc, route_inc=s_route_inc, batch=s_batch, comp=s_comp))

print("情景 | 推理/收入 c | 输入成本份额 | 默认功能节省 | 全部可得节省 | 工程增量节省 | 毛利提升(全部,pp) | 毛利提升(增量,pp)")
res = {}
for i, s in enumerate(SC):
    r = run(i); res[s] = r
    print(f"{s} | {r['c']:.1%} | {r['phi']:.0%} | {r['S_def']:.1%} | {r['S_all']:.1%} | {r['S_inc']:.1%} | {r['dGM_all']*100:.1f} | {r['dGM_inc']*100:.1f}")
    print("    分项(占推理成本):", {k: f"{x:.1%}" for k, x in r["parts"].items()})

# 按节省分成的生意：上限与持续期
print("\n按节省分成：客户收入 R（美元）× 工程增量毛利提升 → 年节省；分成 α；增量逐年衰减 δ")
alpha = {"保守": 0.20, "基准": 0.25, "乐观": 0.30}
delta = {"保守": 0.60, "基准": 0.40, "乐观": 0.25}   # 平台吸收 + 客户内化 + 同能力降价
for R in [2e6, 10e6, 50e6]:
    row = []
    for s in SC:
        sav = R * res[s]["dGM_inc"]
        fee1 = alpha[s] * sav
        fee3 = sum(alpha[s] * sav * (1 - delta[s]) ** t for t in range(3))
        row.append(f"{s}: 年节省 {sav/1e3:,.0f}k，首年分成 {fee1/1e3:,.0f}k，三年累计 {fee3/1e3:,.0f}k")
    print(f"R={R/1e6:.0f}M | " + " ; ".join(row))

# 盈亏门槛：一名独立顾问要从单客户拿到 10 万美元/年分成，客户需要多大收入
print("\n单客户年分成 10 万美元所需客户收入：")
for s in SC:
    need = 1e5 / alpha[s] / res[s]["dGM_inc"]
    print(f"  {s}: 约 {need/1e6:.1f}M 美元年收入")

# 蒙特卡洛：各参数在 [保守, 乐观] 区间内独立均匀抽样（独立性为本文假设），给出分布而非角点
import random, statistics
random.seed(20261020)
def draw():
    v = {}
    for k, arr in P.items():
        lo, hi = min(arr), max(arr)
        v[k] = random.uniform(lo, hi) if k != "r_io" else random.choice([3, 5, 10, 20, 30])
    if v["h1"] < v["h0"]: v["h1"] = v["h0"]
    return v
def run_v(v):
    import math
    c = (1 - v["GM0"]) * v["k_inf"]
    phi = v["r_io"] * PIN / (v["r_io"] * PIN + POUT)
    sc_def = phi * v["h0"] * NET_HIT_SAVING
    sc_all = phi * v["h1"] * NET_HIT_SAVING
    sr_all = max(0.0, v["f"] * (1 - v["p"] - v["e"]))
    sr_def = sr_all * v["g_route_default"]
    S_def = 1 - (1 - sc_def) * (1 - sr_def)
    S_all = 1 - (1 - sc_all) * (1 - sr_all) * (1 - v["b"] * 0.5) * (1 - phi * (1 - v["h1"]) * v["x"])
    return c, S_def, S_all, c * (S_all - S_def)
N = 100000
out = [run_v(draw()) for _ in range(N)]
def pct(xs, q): xs = sorted(xs); return xs[int(q * (len(xs) - 1))]
for name, idx in [("推理/收入", 0), ("默认功能节省(占推理)", 1), ("全部可得节省(占推理)", 2), ("工程增量毛利提升(占收入)", 3)]:
    xs = [o[idx] for o in out]
    print(f"MC {name}: P10 {pct(xs,.1):.1%} | P50 {pct(xs,.5):.1%} | P90 {pct(xs,.9):.1%}")
inc = [o[3] for o in out]
for q in [.1, .5, .9]:
    d = pct(inc, q)
    print(f"MC 单客户年分成10万美元(α=25%)所需客户收入 @P{int(q*100)} 毛利提升 {d:.1%}: 约 {1e5/0.25/d/1e6:.1f}M 美元")
# 平台吸收敏感性：2028 年默认路由份额升到 0.6、默认缓存命中 h0 提高 0.2 时，增量缩水多少
def shift(v):
    v = dict(v); v["g_route_default"] = min(1, v["g_route_default"] + 0.4); v["h0"] = min(v["h1"], v["h0"] + 0.2); return v
random.seed(20261020)
pairs = []
for _ in range(N):
    v = draw(); a = run_v(v)[3]; b = run_v(shift(v))[3]; pairs.append((a, b))
ratio = statistics.median([b / a for a, b in pairs if a > 0])
print(f"MC 平台吸收情景（默认路由份额+0.4、默认缓存命中+0.2）后工程增量剩余中位比例: {ratio:.0%}")
