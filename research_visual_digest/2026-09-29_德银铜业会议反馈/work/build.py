# 生成 德银-铜业CEO会议-4页精华版.html
# 图表坐标由本脚本计算（云端没有 svg_chart.py），数字出处写在每处 <!--src--> 注释里。
import base64, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "德银-铜业CEO会议-4页精华版.html"
QR = pathlib.Path("/home/user/claude/.claude/skills/yanbao-visual-digest-v3/素材/THE_PORT_微信二维码_纯码.png")
qr_b64 = base64.b64encode(QR.read_bytes()).decode()

C_GOLD = "#A06A12"
C_INK = "#141D2A"
C_SOFT = "#37424F"
C_MUTED = "#69737F"
C_HAIR = "#D3D8DE"
C_G1 = "#4A5563"   # 深灰
C_G2 = "#98A1AC"   # 中灰
C_G3 = "#C9CED5"   # 浅灰
MONO = "ui-monospace,'SF Mono',Menlo,'DejaVu Sans Mono',monospace"
SANS = "'PingFang SC','Noto Sans CJK SC',sans-serif"


# ---------- 图 1：全球可见库存按归属拆分（DB p7 图7，目测） ----------
def chart_ags():
    rows = [  # 未占用, 中国占用, 美国占用, 行业占用  —— 读数见 work/png/p007_fig7.png 像素量测
        ("25 年前", 87.4, 11.4, 0.0, 1.2),
        ("5 年前", 56.6, 41.8, 0.0, 1.6),
        ("今天", 28.6, 42.8, 27.0, 1.6),
    ]
    W, x0, x1 = 703, 78, 703
    bw = x1 - x0
    bh, gap, top = 44, 18, 4
    out = [f'<svg viewBox="0 0 {W} {top + 3 * bh + 2 * gap + 4}" width="{W}" role="img" aria-label="全球可见库存按归属拆分">']
    for i, (lab, un, cn, us, ind) in enumerate(rows):
        y = top + i * (bh + gap)
        out.append(f'<text x="0" y="{y + bh / 2 + 6}" font-family="{SANS}" font-size="17" font-weight="700" fill="{C_INK}">{lab}</text>')
        x = x0
        segs = [(un, C_GOLD, "未被占用", "#FFFFFF"), (cn, C_G2, "中国占用", "#FFFFFF"),
                (us, C_G1, "美国占用", "#FFFFFF"), (ind, C_G3, "", C_INK)]
        for v, col, name, tc in segs:
            if v <= 0:
                continue
            w = bw * v / 100
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{bh}" fill="{col}"/>')
            if name and w > 60:
                txt = f"{name} {round(v)}%" if w > 150 else f"{round(v)}%"
                out.append(f'<text x="{x + 10:.1f}" y="{y + bh / 2 + 5.5}" font-family="{SANS}" font-size="15.5" font-weight="700" fill="{tc}">{txt}</text>')
            x += w
    out.append("</svg>")
    return "\n".join(out)


# ---------- 图 2：19 家矿企 2026 指引 vs 2025 实产（DB p38 图50，差值为本文测算） ----------
TRACK = [  # 中文名, 2025 实产 kt, 2026 当前指引 kt, 中资
    ("第一量子", 396, 405, False), ("安托法加斯塔", 654, 640, False), ("伦丁矿业", 331, 313, False),
    ("自由港", 1535, 1406, False), ("泰克资源", 454, 493, False), ("必和必拓", 2014, 1839, False),
    ("嘉能可", 852, 840, False), ("力拓", 883, 835, False), ("英美资源", 695, 730, False),
    ("淡水河谷", 382, 370, False), ("南方铜业", 956, 917, False), ("智利国家铜业", 1332, 1344, False),
    ("KGHM", 710, 740, False), ("艾芬豪", 386, 310, False), ("South32", 71, 70, False),
    ("五矿资源", 507, 511, True), ("Hudbay", 118, 124, False), ("洛阳钼业", 741, 790, True),
    ("紫金矿业", 1085, 1200, True),
]


def chart_track():
    rows = sorted(((n, b - a, cn) for n, a, b, cn in TRACK), key=lambda r: -r[1])
    lo, hi = -232, 122
    W, xl, xr = 703, 168, 652
    sc = (xr - xl) / (hi - lo)
    zx = xl + (-lo) * sc
    rh, bh, top = 17.6, 11, 5
    n = len(rows)
    H = top + n * rh + 36
    out = [f'<svg viewBox="0 0 {W} {H:.0f}" width="{W}" role="img" aria-label="19 家矿企 2026 年指引较 2025 年实产的增减">']
    for i, (name, d, cn) in enumerate(rows):
        yc = top + i * rh + rh / 2
        fw = "800" if cn else "500"
        out.append(f'<text x="112" y="{yc + 4.5:.1f}" text-anchor="end" font-family="{SANS}" font-size="14" font-weight="{fw}" fill="{C_INK if cn else C_SOFT}">{name}</text>')
        w = abs(d) * sc
        col = C_G1 if d < 0 else C_G2
        x = zx - w if d < 0 else zx
        out.append(f'<rect x="{x:.1f}" y="{yc - bh / 2:.1f}" width="{max(w, 1.5):.1f}" height="{bh}" fill="{col}"/>')
        lab = f"+{d}" if d > 0 else f"−{abs(d)}"
        if d < 0:
            out.append(f'<text x="{x - 5:.1f}" y="{yc + 4.3:.1f}" text-anchor="end" font-family="{MONO}" font-size="13" font-weight="700" fill="{C_SOFT}">{lab}</text>')
        else:
            out.append(f'<text x="{x + w + 5:.1f}" y="{yc + 4.3:.1f}" font-family="{MONO}" font-size="13" font-weight="700" fill="{C_SOFT}">{lab}</text>')
    # 零线
    out.append(f'<line x1="{zx:.1f}" y1="{top - 2}" x2="{zx:.1f}" y2="{top + n * rh + 2:.1f}" stroke="{C_INK}" stroke-width="1"/>')
    # 合计
    tot = 13877 - 14101  # 用原表合计行；分项加总为 −225，差 1 为原表四舍五入
    yT = top + n * rh + 14
    out.append(f'<line x1="0" y1="{yT - 6:.1f}" x2="{W}" y2="{yT - 6:.1f}" stroke="{C_HAIR}" stroke-width="1"/>')
    w = abs(tot) * sc
    out.append(f'<text x="112" y="{yT + 15:.1f}" text-anchor="end" font-family="{SANS}" font-size="14.5" font-weight="800" fill="{C_INK}">19 家合计</text>')
    out.append(f'<rect x="{zx - w:.1f}" y="{yT + 3:.1f}" width="{w:.1f}" height="14" fill="{C_GOLD}"/>')
    out.append(f'<text x="{zx + 8:.1f}" y="{yT + 14.5:.1f}" font-family="{MONO}" font-size="14" font-weight="800" fill="{C_GOLD}">−{abs(tot)} 千吨 · −2%</text>')
    out.append("</svg>")
    return "\n".join(out), tot


# ---------- 图 3：价格刻度（DB p10 表、p31 表、p38 图46） ----------
def chart_ladder():
    W = 703
    lo, hi = 9000, 15500
    xl, xr = 26, 677
    sc = (xr - xl) / (hi - lo)
    X = lambda v: xl + (v - lo) * sc
    y = 76
    pts = [  # 值, 上/下, 数字标注, 说明, 强调
        (9947, "up", "9,947", "2025 年均价", False),
        (12000, "dn", "&gt;12,000", "新建矿激励价", False),
        (12500, "up", "12,500", "德银 2027E", True),
        (13194, "dn", "13,194", "德银 2026E", False),
        (14728, "up", "14,728", "LME 现货 · 9/27", False),
    ]
    out = [f'<svg viewBox="0 0 {W} 148" width="{W}" role="img" aria-label="铜价刻度：现货、德银假设与激励价">']
    out.append(f'<line x1="{xl}" y1="{y}" x2="{xr}" y2="{y}" stroke="{C_INK}" stroke-width="1.2"/>')
    for v in range(9000, 15001, 1000):
        out.append(f'<line x1="{X(v):.1f}" y1="{y - 4}" x2="{X(v):.1f}" y2="{y + 4}" stroke="{C_MUTED}" stroke-width="1"/>')
    # 回调区间：12,500 → 14,728
    a, b = X(12500), X(14728)
    out.append(f'<rect x="{a:.1f}" y="{y - 7}" width="{b - a:.1f}" height="14" fill="{C_G3}" opacity=".55"/>')
    for v, pos, num, desc, em in pts:
        x = X(v)
        col = C_GOLD if em else C_INK
        r = 7 if em else 5.5
        out.append(f'<circle cx="{x:.1f}" cy="{y}" r="{r}" fill="{col if em else "#FFFFFF"}" stroke="{col}" stroke-width="2"/>')
        if pos == "up":
            out.append(f'<text x="{x:.1f}" y="{y - 40}" text-anchor="middle" font-family="{MONO}" font-size="{22 if em else 19}" font-weight="800" fill="{col}">{num}</text>')
            out.append(f'<text x="{x:.1f}" y="{y - 18}" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{C_SOFT}">{desc}</text>')
        else:
            out.append(f'<text x="{x:.1f}" y="{y + 34}" text-anchor="middle" font-family="{MONO}" font-size="19" font-weight="800" fill="{col}">{num}</text>')
            out.append(f'<text x="{x:.1f}" y="{y + 55}" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{C_SOFT}">{desc}</text>')
    # 区间标注
    mid = (a + b) / 2
    out.append(f'<text x="{mid:.1f}" y="{y - 22}" text-anchor="middle" font-family="{MONO}" font-size="14" font-weight="700" fill="{C_MUTED}">← −15% →</text>')
    out.append("</svg>")
    return "\n".join(out)


ags_svg = chart_ags()
track_svg, track_tot = chart_track()
ladder_svg = chart_ladder()
assert track_tot == -224, track_tot

# 追踪表差值写成 src 注释（测算型）
track_src = "; ".join(f"{n} {b}−{a}={b - a}" for n, a, b, _ in TRACK)

CSS = r"""
:root{
  --paper:#E9EAEC; --surface:#FFFFFF; --ink:#141D2A; --ink-soft:#37424F; --muted:#69737F;
  --hair:#D3D8DE; --hair-soft:#E6E9ED; --gold:#A06A12; --gold-soft:#F4EAD6;
  --bull:#0D6E55; --bear:#B93A30; --g1:#4A5563; --g2:#98A1AC; --g3:#C9CED5;
  --mono:ui-monospace,"SF Mono",Menlo,"DejaVu Sans Mono",monospace;
  --sans:"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC",system-ui,sans-serif;
  --serif:"Songti SC","STSong","Noto Serif CJK SC",Georgia,serif;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:19.5px;line-height:1.5;-webkit-font-smoothing:antialiased}
.m{font-family:var(--mono);font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}

/* ---------- 工程件：固定页容器（沿用母本） ---------- */
.page{width:210mm;height:296.6mm;background:var(--surface);position:relative;padding:7mm 12mm 8mm;overflow:hidden;margin:0 auto 16px;box-shadow:0 6px 26px -10px rgba(20,32,46,.35)}
.page:last-child{margin-bottom:0}
.pg-head{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:12px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--hair);padding-bottom:5px;margin-bottom:10px}
.pg-head .r{margin-left:auto;color:var(--ink-soft);font-weight:700}
.pg-foot{position:absolute;left:12mm;right:12mm;bottom:5mm;display:flex;align-items:center;font-family:var(--mono);font-size:11.5px;color:var(--muted);letter-spacing:.06em;border-top:1px solid var(--hair-soft);padding-top:5px}
.pg-foot .r{margin-left:auto;font-weight:700;color:var(--ink-soft)}

/* ---------- 标题层 ---------- */
.eyebrow{font-family:var(--mono);font-size:13.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:700}
h1{font-weight:800;letter-spacing:-.015em;font-size:52px;line-height:1.12;margin:12px 0 0}
.en{font-family:var(--mono);font-size:15px;color:var(--muted);margin-top:8px;letter-spacing:.01em}
.sec-eye{font-family:var(--mono);font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:10px;margin-bottom:6px}
.sec-eye .no{color:var(--gold);font-weight:800}
.sec-eye::after{content:"";flex:1;height:1px;background:var(--hair)}
h2.sec{font-size:34px;line-height:1.16;font-weight:800;letter-spacing:-.015em;margin:0 0 8px}
h3{font-size:22px;font-weight:800;margin:0 0 6px;letter-spacing:-.01em;line-height:1.3}
p{margin:0 0 8px}
strong,b{font-weight:700;color:var(--ink)}
.lead{max-width:34em;color:var(--ink-soft)}
.lab{font-family:var(--mono);font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:700;margin-bottom:5px}
.cap{font-family:var(--mono);font-size:13px;color:var(--muted);line-height:1.5;margin:6px 0 0}
.cap b{color:var(--ink-soft)}
.calc{font-size:.82em;color:var(--muted);font-weight:500;white-space:nowrap}

/* ---------- P1 ---------- */
.thesis{font-family:var(--serif);font-size:23px;line-height:1.62;margin:20px 0 0;color:var(--ink);max-width:31em}
.thesis .tag{font-family:var(--mono);font-size:12.5px;letter-spacing:.14em;color:var(--muted);font-weight:700;margin-right:10px;vertical-align:2px}
.meta{margin-top:16px;padding-top:9px;border-top:1px solid var(--hair);font-family:var(--mono);font-size:12.5px;color:var(--muted);line-height:1.7}
.meta b{color:var(--ink-soft);font-weight:700}
.nums{display:grid;grid-template-columns:1.12fr .88fr .88fr 1.12fr;column-gap:16px;margin-top:26px}
.nums .it{border-top:1.5px solid var(--ink);padding-top:11px}
.nums .v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-weight:800;font-size:38px;line-height:1;letter-spacing:-.02em;white-space:nowrap}
.nums .u{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--muted);margin-top:6px;letter-spacing:.04em}
.nums .v.gd{color:var(--gold)}
.nums .l{font-size:15.5px;line-height:1.45;color:var(--ink-soft);margin-top:6px}
.box{border:1px solid var(--hair);border-radius:8px;padding:14px 18px 12px}
.gap2{display:grid;grid-template-columns:1fr 1fr;column-gap:26px}
.gap2 .side p{font-size:18px;line-height:1.5;margin:0;color:var(--ink-soft)}
.gap2 .side + .side{border-left:1px solid var(--hair-soft);padding-left:26px}
.box .foot{margin-top:11px;padding-top:9px;border-top:1px solid var(--hair-soft);font-size:17px;color:var(--ink-soft);line-height:1.5}
.menu{margin-top:0;border-top:1px solid var(--hair)}
.mi{display:grid;grid-template-columns:48px 1fr auto;align-items:baseline;column-gap:14px;padding:7px 0;border-bottom:1px solid var(--hair-soft)}
.mi .n{font-family:var(--mono);font-size:20px;font-weight:800;color:var(--ink-soft)}
.mi .t{font-size:20px;font-weight:700}
.mi .t em{font-style:normal;font-weight:400;color:var(--ink-soft);font-size:17px;margin-left:10px}
.mi .p{font-family:var(--mono);font-size:13px;color:var(--muted)}
.quote{font-family:var(--serif);font-size:24px;line-height:1.5;margin:0;color:var(--ink)}
.quote .by{display:block;font-family:var(--mono);font-size:12.5px;color:var(--muted);margin-top:6px;letter-spacing:.03em}

/* ---------- 列表 ---------- */
.dl{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.dl li{font-size:17.5px;line-height:1.48;color:var(--ink-soft);padding-left:16px;position:relative}
.dl li::before{content:"";position:absolute;left:0;top:11px;width:6px;height:1.5px;background:var(--ink-soft)}
.dl li b{color:var(--ink)}
.cols{display:grid;grid-template-columns:1fr 1fr;column-gap:26px}
.rule{border-top:1px solid var(--hair);padding-top:12px}

/* ---------- 表格：三条线 ---------- */
table{border-collapse:collapse;width:100%;font-size:16px;line-height:1.3}
thead th{font-family:var(--mono);font-size:12px;letter-spacing:.05em;color:var(--muted);text-align:right;padding:5px 7px;border-bottom:1px solid var(--ink);font-weight:700;white-space:nowrap}
thead th:first-child,tbody td:first-child{text-align:left}
tbody td{padding:4px 7px;text-align:right;border-bottom:1px solid var(--hair-soft);white-space:nowrap;font-family:var(--mono);font-variant-numeric:tabular-nums}
tbody tr:last-child td{border-bottom:0}
td.nm{font-family:var(--sans);font-weight:700}
td.nm i{font-style:normal;font-weight:400;color:var(--muted);font-family:var(--mono);font-size:12.5px;margin-left:6px}
td.tx{font-family:var(--sans);text-align:left;white-space:normal;color:var(--ink-soft);font-size:16px;line-height:1.4}
td.rt{font-family:var(--sans);text-align:center}
.up{color:var(--bull);font-weight:700} .dn{color:var(--bear);font-weight:700}
th.grp{border-bottom:1px solid var(--hair);text-align:center}

/* ---------- 算术卡 ---------- */
.arith .row{display:grid;grid-template-columns:1fr auto;column-gap:12px;align-items:baseline;padding:5px 0;border-bottom:1px solid var(--hair-soft);font-size:17px;color:var(--ink-soft)}
.arith .row .k{font-family:var(--mono);font-weight:800;color:var(--ink);font-size:18px;white-space:nowrap}
.arith .row.sum{border-bottom:0;padding-top:8px}
.arith .row.sum span:first-child{font-weight:700;color:var(--ink)}
.arith .row.sum .k{font-size:26px}
.arith .sub2{font-size:15.5px;color:var(--ink-soft);line-height:1.45;margin-top:4px}

/* ---------- 尾部：免责 + THE PORT 角标（走正常流） ---------- */
.tailrow{display:flex;align-items:flex-end;gap:20px;border-top:1px solid var(--hair);padding-top:9px}
.tailrow .disc{flex:1;font-size:13.5px;color:var(--muted);line-height:1.5;margin:0}
.tailrow .disc b{color:var(--ink-soft)}
.portmark{display:flex;align-items:flex-end;gap:11px;flex:0 0 auto}
.portmark .pm-t{text-align:right;font-family:var(--mono);line-height:1.5}
.portmark .pm-t .a{font-family:var(--sans);font-size:15px;font-weight:800;color:var(--ink);letter-spacing:.04em}
.portmark .pm-t .b{font-size:12px;color:var(--muted)}
.portmark .pm-q{width:84px;height:84px;display:block}

/* 局部收紧：只压间距，不动字号 */
.page.tight p{margin-bottom:6px}
.page.tight .dl{gap:4px}
.page.tight tbody td{padding:3px 7px}
.page.tight .box{padding:12px 16px 10px}
.page.tighter .mi{padding:9px 0}
.page.tighter thead th{padding:4px 7px}
.page.tightest tbody td{padding:2px 7px}

@media print{
  body{background:#fff}
  .page{margin:0;box-shadow:none;break-after:page;page-break-after:always}
  .page:last-child{break-after:auto;page-break-after:auto}
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .rv{opacity:1}
}
@page{size:A4;margin:0}
"""

HTML = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>德银铜业 CEO 会议 · 精华版</title>
<style>{CSS}</style></head>
<body>

<!-- ============ PAGE 1 · 主线 ============ -->
<div class="page" id="p1">
  <div class="pg-head"><span>德意志银行 · 全球铜业 CEO 会议纪要 · 提炼</span><span class="r">01 / 04 · 主线</span></div>

  <div class="eyebrow">Deutsche Bank · Global Copper · 2026-09-28</div>
  <h1>铜价的顶看华盛顿，底看工地</h1>
  <div class="en">DB Copper Conference: Feedback &amp; Key Themes</div>

  <p class="thesis"><span class="tag">本文判断</span>眼下近 1.5 万美元的铜价，是<b>库存被锁住</b>的价格——美国 2025 年以来囤下约 160 万吨，非美只剩 2.5 天用量；1.2 万美元以上，是<b>新矿建得出来</b>的价格——缺的是熟练工人、审批和一路上涨的造价。前者取决于美国关税，可以逆转；后者不能。关税撤销能触发回调，逆转不了这轮周期。<!--src: DB p5,p12 正文；激励价 DB p8 正文,p38 图46--></p>

  <div class="meta"><b>来源</b> 德意志银行 Liam Fitzpatrick 等 · Industry Update · 2026-09-28 · 9 家公司高管 + 2 位专家<br><b>范围</b> 正文 38 页（原报告 41 页，P39–P41 为披露未纳入）· 价格截至 9/24、9/27</div>

  <div class="nums">
    <div class="it"><div class="v">14,728</div><div class="u">美元/吨 · LME 现货</div><div class="l">9 月 27 日收盘；12 个月 +45.2%，年内 +18.3%</div><!--src: DB p10 表--></div>
    <div class="it"><div class="v">160</div><div class="u">万吨 · 美国囤积</div><div class="l">2025 年初以来累积，约 70 万吨在交易所，非美买不到</div><!--src: DB p5,p12 正文--></div>
    <div class="it"><div class="v gd">2.5</div><div class="u">天 · 非美库存</div><div class="l">非美约 30 万吨，只相当于 2.5 天消费；中国面临断货风险</div><!--src: DB p5,p12 正文--></div>
    <div class="it"><div class="v">&gt;12,000</div><div class="u">美元/吨 · 激励价</div><div class="l">新建矿所需铜价；长期一致预期 18 个月内上调约 20–25%</div><!--src: DB p8 正文, p38 图46--></div>
  </div>

  <div style="height:46px"></div>
  <div class="box">
    <div class="lab">预期差 · 会场内外的温差</div>
    <div class="gap2">
      <div class="side"><h3>场外：投资者</h3><p>提问集中在铜价下行风险——对近期强势能否持续，明显存疑。<!--src: DB p1 正文--></p></div>
      <div class="side"><h3>场内：管理层与专家组</h3><p>短期风险偏上行，“任何回调都有激进买盘”；没人报告需求走弱。<!--src: DB p1,p4,p6 正文--></p></div>
    </div>
    <div class="foot">德银自己的盈利模型站在中间：铜价 2026E 13,194、2027E 12,500 美元/吨，2027E 比现货低约 15%<span class="calc">（本文测算）</span>——见第 4 页。<!--src: DB p31 表；测算 = 12,500/14,728−1 = −15.1%，现货据 DB p10 表--></div>
  </div>

  <div style="height:22px"></div>
  <div class="menu">
    <div class="mi"><span class="n">01</span><span class="t">库存<em>看得见的在涨，买得到的只剩三成</em></span><span class="p">P.2</span></div>
    <div class="mi"><span class="n">02</span><span class="t">供给<em>矿不是挖不出来，是建不出来</em></span><span class="p">P.3</span></div>
    <div class="mi"><span class="n">03</span><span class="t">价格<em>德银模型里的 2027：贴着激励价</em></span><span class="p">P.4</span></div>
  </div>

  <div class="pg-foot"><span>数据口径：德银会议纪要 + 德银估算；“本文测算 / 本文判断”为编者推算</span><span class="r">01 / 04</span></div>
</div>

<!-- ============ PAGE 2 · 库存 ============ -->
<div class="page" id="p2">
  <div class="pg-head"><span>01 库存 · Inventories</span><span class="r">02 / 04 · 库存</span></div>

  <div class="sec-eye"><span class="no">01</span><span>Visible vs. Available</span></div>
  <h2 class="sec">库存在涨，能买到的铜只剩不到三成</h2>
  <p class="lead">德银大宗商品同事 Daniel Ghali 的判断：可见库存在上升，可自由买卖的金属却前所未有地稀缺——美国关税驱动的搬库和囤货，掩盖了实物市场的收紧，越来越多库存实际上不对市场开放。<!--src: DB p7 正文--></p>

  <div style="height:12px"></div>
  <div class="lab">全球可见库存（AGS）按归属拆分 · 占比</div>
  {ags_svg}
  <!--src: DB p7 图7/目测：未被占用 87%→57%→29%；中国占用 11%→42%→43%；美国占用 今天 27%；行业占用约 1–2%-->
  <p class="cap">这张图想说：25 年前近九成库存“有人要就能买到”，今天不到三成；新增的锁库方是美国（约 27%），中国占用的比例 5 年来没降。图上读数，行业占用约 1–2% 未标注。</p>

  <div style="height:30px"></div>
  <p class="quote">“职业生涯里第一次，中国真有可能断货。”<span class="by">——会议金句（P4，原文未署名）</span><!--src: DB p4 正文--></p>
  <div style="height:18px"></div>
  <div class="cols rule">
    <div>
      <h3>美国吸走的，非美补不回来</h3>
      <ul class="dl">
        <li>美国 2025 年以来累积约 <b>160 万吨</b>；专家组预计关税不确定期间，流入会持续到年底。<!--src: DB p12 正文--></li>
        <li>非美库存约 <b>30 万吨 = 2.5 天</b>消费。LME 与上期所现货升水、洋山铜溢价走高，都指向稀缺。<!--src: DB p6,p12 正文--></li>
        <li>专家组：短期风险偏上行；若美国继续吸货，铜价还有上行空间。<!--src: DB p12 正文--></li>
      </ul>
    </div>
    <div>
      <h3>需求：三类买家不太看价格</h3>
      <ul class="dl">
        <li><b>电网投资、美国政策性囤货、AI 基础设施</b>被点名为对铜价较不敏感的需求。<!--src: DB p8,p12 正文--></li>
        <li>AI / 数据中心用铜：2026 年约 <b>60 万吨</b>，2030 年可能到约 <b>150 万吨</b>。<!--src: DB p13 正文--></li>
        <li>铝替代在加速：2026 年全球约 <b>40 万吨</b>，约八成在中国；2027 年起铝供给增加会带来更多替代，但不足以实质放松铜市。<!--src: DB p13 正文--></li>
      </ul>
    </div>
  </div>

  <div style="height:30px"></div>
  <div class="box">
    <div class="lab">下行风险只有一个开关：美国政策</div>
    <p style="font-size:18px;color:var(--ink-soft);margin:0">德银基准情形是美国<b>维持关税威胁</b>，并可能对精铜进口征税；45X 税收抵免等工具也能扶持本土产量。若美国进口骤停，非美市场每月要多吸收约 <b>15 万吨</b>；放出美国库存会明显放松供给——但专家组不预期“洪水”。另一项风险是宏观全面避险。多数管理层也承认关税与搬库抬高了价格，但同时认为供需基本面给了很强的支撑。<!--src: DB p5,p6,p13 正文--></p>
  </div>

  <div class="pg-foot"><span>库存数据：德银、Wood Mackenzie、彭博；AGS 拆分为图上读数</span><span class="r">02 / 04</span></div>
</div>

<!-- ============ PAGE 3 · 供给 ============ -->
<div class="page" id="p3">
  <div class="pg-head"><span>02 供给 · Supply</span><span class="r">03 / 04 · 供给</span></div>

  <div class="sec-eye"><span class="no">02</span><span>Above ground, not below</span></div>
  <h2 class="sec">矿不是挖不出来，是建不出来</h2>
  <p class="lead">会议金句：“增加供给最大的约束，根本上在地面以上，而不在地下。”审批之外，<b>熟练劳动力短缺</b>正成最大瓶颈；造价也在涨：Vicuña 一期 71 亿美元，德银不意外超 80 亿；Bagdad 35 亿涨到约 46 亿。<!--src: DB p4,p8 正文；Vicuña DB p17,p34 正文；Bagdad DB p19 正文--></p>

  <div style="height:8px"></div>
  <div class="lab">19 家主要矿企：2026 年产量指引较 2025 年实产的增减 · 千吨</div>
  {track_svg}
  <!--src: DB p38 图50 表；差值为本文测算：{track_src}；合计用原表合计行 13,877−14,101=−224（分项加总 −225，差 1 为四舍五入）-->
  <p class="cap">这张图想说：合计少 22.4 万吨<span class="calc">（本文测算）</span>，年初指引 14,196 千吨已下调至 13,877；10 家减产，减量集中在必和必拓、自由港、艾芬豪，增量最大的是<b>紫金矿业、洛阳钼业</b>（加粗为中资）。<!--src: DB p38 图50--></p>

  <div style="height:25px"></div>
  <div class="cols rule">
    <div>
      <h3>今年在减，明年也难补</h3>
      <ul class="dl">
        <li>2025 年全球矿产增长不到 1%，2026 年可能负增长。<!--src: DB p7 正文--></li>
        <li>2027 年行业指引 <b>+5–6%</b>，与会者看到下行风险；专家组扣掉干扰后约 <b>2–3%</b>。<!--src: DB p7 正文；p12 专家纪要写作 ~2–2.5--></li>
        <li>现货 TC 创纪录负值，Aurubis 预计明年长协加工费承压；中国精铜受原料约束将走平，空头逻辑少了一块。<!--src: DB p7,p8,p25 正文--></li>
      </ul>
    </div>
    <div class="box arith">
      <div class="lab">2027 年最大的三个近端增量</div>
      <div class="row"><span>Cobre Panamá 复产</span><span class="k">+167</span></div><!--src: DB p16 表；测算 = 205−38-->
      <div class="row"><span>Grasberg 爬坡</span><span class="k">≈ +179</span></div><!--src: DB p21 表；测算 = (1,226−832)×0.4536 = 178.7-->
      <div class="row"><span>自由港美国堆浸</span><span class="k">≈ +45</span></div><!--src: DB p19 正文；测算 = 100×0.4536 = 45.4-->
      <div class="row sum"><span>合计 · 千吨</span><span class="k">≈ 391</span></div><!--src: 测算 = 167+179+45 = 391-->
      <div class="sub2">只够每年所需新增 90 万吨的 <b>43%</b><span class="calc">（本文测算）</span>；新项目多在 2028 年后。<!--src: DB p4 正文；测算 = 391/900 = 43.4%--></div>
    </div>
  </div>
  <p class="cap">口径：Cobre 为德银模型（假设复产）38→205 千吨；Grasberg 为自由港印尼 832→1,226 百万磅，堆浸约 2→3 亿磅，按 0.4536 千吨/百万磅折算。之后：Spence、Kennecott（2028）、Centinela（2029）、Alemão、Vicuña（2030）、Escondida（CY31–32）。<!--src: DB p16,p21 表, p19, p22, p32, p17 图16, p30 正文--></p>

  <div class="pg-foot"><span>P38 追踪表：必和必拓 / South32 按 6 月财年，自由港为销量指引，第一量子不含 Cobre 库存矿</span><span class="r">03 / 04</span></div>
</div>

<!-- ============ PAGE 4 · 价格 ============ -->
<div class="page" id="p4">
  <div class="pg-head"><span>03 价格 · Price</span><span class="r">04 / 04 · 价格</span></div>

  <div class="sec-eye"><span class="no">03</span><span>Where DB's price deck sits</span></div>
  <h2 class="sec">德银的 2027：1.25 万美元，贴着激励价</h2>
  <p class="lead">会上的“紧”是真的，但德银给公司估值用的铜价并不追现货。它把回调的终点放在新矿激励价上方，而不是 2025 年不到 1 万美元的均价<span class="calc">（本文判断）</span>。<!--src: DB p31 表, p38 图46--></p>

  {ladder_svg}
  <!--src: 14,728 DB p10 表；13,194 / 12,500 / 9,947 DB p31 表（力拓模型 Copper $/t：FY26E / FY27E / FY25）；>12,000 DB p38 图46；−15% 测算 = 12,500/14,728−1-->
  <p class="cap">这张图想说：2027E 假设比现货低约 15%、只比激励价高约 4%<span class="calc">（均为本文测算）</span>；第 3 页的供给缺口，是回调有底的理由<span class="calc">（本文判断）</span>。美元/吨；德银日历年铜价假设 2026E / 2027E 为 5.98 / 5.67 美元/磅。<!--src: DB p16,p21,p31 表；测算 = 12,500/12,000−1 = 4.2%--></p>

  <div style="height:46px"></div>
  <div class="lab">德银评级 · 13 家：6 买入 · 6 持有 · 1 卖出</div>
  <table>
    <thead>
      <tr><th>公司</th><th>评级</th><th>目标价</th><th>现价</th><th>空间</th><th>2027E PE<br>德银铜价</th><th>2027E PE<br>现货铜价</th></tr>
    </thead>
    <tbody>
      <tr><td class="nm">自由港<i>USD</i></td><td class="rt">买入</td><td>70</td><td>72</td><td class="dn">▼3%</td><td>18.0</td><td>12.1</td></tr>
      <tr><td class="nm">第一量子<i>CAD</i></td><td class="rt">买入</td><td>50</td><td>45</td><td class="up">▲11%</td><td>21.0</td><td>12.0</td></tr>
      <tr><td class="nm">泰克资源<i>USD</i></td><td class="rt">买入</td><td>68</td><td>67</td><td class="up">▲2%</td><td>19.0</td><td>11.8</td></tr>
      <tr><td class="nm">英美资源<i>GBP</i></td><td class="rt">买入</td><td>4,500</td><td>3,980</td><td class="up">▲13%</td><td>19.9</td><td>15.7</td></tr>
      <tr><td class="nm">嘉能可<i>GBP</i></td><td class="rt">买入</td><td>630</td><td>549</td><td class="up">▲15%</td><td>14.9</td><td>10.0</td></tr>
      <tr><td class="nm">中国宏桥<i>HKD</i></td><td class="rt">买入</td><td>33</td><td>21</td><td class="up">▲59%</td><td>4.7</td><td>4.7</td></tr>
      <tr><td class="nm">伦丁矿业<i>CAD</i></td><td class="rt">持有</td><td>36</td><td>35</td><td class="up">▲4%</td><td>17.6</td><td>12.9</td></tr>
      <tr><td class="nm">Boliden<i>SEK</i></td><td class="rt">持有</td><td>620</td><td>518</td><td class="up">▲20%</td><td>9.2</td><td>7.1</td></tr>
      <tr><td class="nm">必和必拓<i>GBP</i></td><td class="rt">持有</td><td>2,700</td><td>3,190</td><td class="dn">▼15%</td><td>18.8</td><td>17.8</td></tr>
      <tr><td class="nm">力拓<i>GBP</i></td><td class="rt">持有</td><td>7,400</td><td>7,070</td><td class="up">▲5%</td><td>11.9</td><td>12.7</td></tr>
      <tr><td class="nm">淡水河谷<i>USD</i></td><td class="rt">持有</td><td>18</td><td>14</td><td class="up">▲33%</td><td>7.4</td><td>7.7</td></tr>
      <tr><td class="nm">挪威海德鲁<i>NOK</i></td><td class="rt">持有</td><td>102</td><td>83</td><td class="up">▲23%</td><td>10.6</td><td>10.0</td></tr>
      <tr><td class="nm">安托法加斯塔<i>GBP</i></td><td class="rt">卖出</td><td>3,400</td><td>3,718</td><td class="dn">▼9%</td><td>30.3</td><td>22.1</td></tr>
    </tbody>
  </table>
  <!--src: DB p9 图10（德银估算）/ 图11（现货价）；价格截至 2026-09-24；6+6+1=13-->
  <p class="cap">价格截至 9/24。两列 PE 差越大，估值对铜价越敏感<span class="calc">（本文判断）</span>；自由港目标价低于现价，德银仍维持买入。<!--src: DB p2 正文, p9 图10/11--></p>

  <div style="height:14px"></div>
  <div class="tailrow">
    <p class="disc"><b>免责声明：</b>第三方研报（Deutsche Bank《DB Copper Conference: Feedback &amp; Key Themes》，2026-09-28）中文提炼，观点、评级与预测归属德意志银行；“本文测算 / 本文判断”为编者推算。<b>不构成投资建议。</b></p>
    <div class="portmark">
      <div class="pm-t"><div class="a">全球投行研报精选</div><div class="b">微信扫码 · 每日研报精华</div></div>
      <img class="pm-q" alt="THE PORT 微信二维码" src="data:image/png;base64,{qr_b64}">
    </div>
  </div>

  <div class="pg-foot"><span>END · 德银全球铜业 CEO 会议 · 中文提炼</span><span class="r">04 / 04</span></div>
</div>

</body></html>
"""

OUT.write_text(HTML, encoding="utf-8")
print("wrote", OUT, len(HTML))
