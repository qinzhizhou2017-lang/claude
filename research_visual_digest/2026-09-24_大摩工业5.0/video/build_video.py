#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大摩 Industry 5.0 · 2 分钟竖屏视频：生成舞台 HTML（逐帧可寻址）、字幕 SRT、分镜脚本。
数字全部沿用 6 页精华版（已核对），出处写在 stage.html 的 <!--src--> 注释里。"""
import base64, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
QR = os.path.join(HERE, "..", "..", "..", ".claude", "skills", "yanbao-visual-digest-v3",
                  "素材", "THE_PORT_微信二维码_纯码.png")

GOLD = "#B07818"; GOLD_D = "#8E5A0C"; GOLD_L = "#C99A45"; INK = "#141D2A"; INK2 = "#37424F"
MUTED = "#69737F"; G1 = "#C9CFD6"; G2 = "#AEB7C2"; G3 = "#7D8894"; HAIR = "#D3D8DE"
BULL = "#0D6E55"; BEAR = "#B93A30"

DURATION = 120.0
# (id, 开始秒, 结束秒, 页眉标签)——原始（无配音）时间轴；配音版由 timeline.json 覆盖
ORIG_SCENES = [("s0", 0, 8, "开场"), ("s1", 8, 22, "节奏"), ("s2", 22, 35, "节奏"),
          ("s3", 35, 52, "改工厂"), ("s4", 52, 65, "改工厂"), ("s5", 65, 81, "卡脖子"),
          ("s6", 81, 97, "利润池与出海"), ("s7", 97, 112, "落到股票"), ("s8", 112, 120, "结尾")]
# 口播／字幕（开始秒, 结束秒, 文本）——一条字幕 ≤36 字，两行内
ORIG_CUES = [
    (0.3, 4.2, "大摩测算：中国工业 5.0，十年要多花 12 万亿美元。"),
    (4.2, 7.8, "但近九成的钱，要到 2030 年以后才花。"),
    (8.2, 13.5, "分年看，2026 到 27 年只多出 2 万亿元，"),
    (13.5, 17.8, "2034 到 35 年是 33 万亿元。"),
    (17.8, 21.8, "原因是过剩产能还没消化，起步会慢。"),
    (22.2, 27.5, "三条投资腿，只有工业往上：占 GDP 从 17.4% 升到 19.6%，"),
    (27.5, 30.5, "而基建和地产都在降。"),
    (30.5, 34.8, "对 GDP 的拉动是 J 曲线：头两年是零，后面才显现。"),
    (35.2, 40.0, "钱花在哪？6 万亿美元建新的产能，5.5 万亿用来改造工厂。"),
    (40.0, 45.8, "改造工厂有两个放大器：软件占设备投资的比重，从 7% 升到 17%；"),
    (45.8, 51.8, "有工业 5.0，机器人的年增速是 30%；没有，只有 15%。"),
    (52.2, 57.0, "回报已被验证：卓越级智能工厂的次品率降了一半。"),
    (57.0, 64.8, "但这样的工厂只有 230 多家，不到基础级的百分之一。"),
    (65.2, 68.5, "第二条线是卡脖子。"),
    (68.5, 75.0, "锂电、光伏设备国产化率已达 97%，半导体设备只有 13.5，目标 30。"),
    (75.0, 80.8, "国产化率越低的环节，抬升空间越大。"),
    (81.2, 84.5, "第三条线是利润和出海。"),
    (84.5, 89.5, "大摩预计，工业利润率从 5% 修复到 8% 左右。"),
    (89.5, 96.8, "关税改变的是组装地，不是产能：对美出口只有约四成容易被替代。"),
    (97.2, 103.0, "落到股票，大摩列了 45 只，37 只增持，上行空间中位数 46%。"),
    (103.0, 111.8, "比如改工厂的绿的谐波、卡脖子的兆易创新、出海的阳光电源。"),
    (112.2, 116.5, "一句话：不要只盯总量，要盯利润池往哪搬。"),
    (116.5, 119.8, "以上整理自大摩研报，不构成投资建议。"),
]


# 配音版：tts/synth_voiceover.py plan 按语音重排的时间轴；分镜内的动画按时长比例伸缩
_TL = os.path.join(HERE, "timeline.json")
if os.path.exists(_TL):
    _tl = json.load(open(_TL, encoding="utf-8"))
    SCENES = [tuple(x) for x in _tl["scenes"]]
    CUES = [tuple(x) for x in _tl["cues"]]
else:
    SCENES, CUES = list(ORIG_SCENES), list(ORIG_CUES)
SCALE = {n[0]: (n[2] - n[1]) / (o[2] - o[1]) for n, o in zip(SCENES, ORIG_SCENES)}

def f(x):
    return f"{x:.1f}"


def a(fx, t, d=0.6, extra=""):
    """动画属性：fx=fade|up|gx|gy|draw|num|pop；t=相对场景开始的秒数。"""
    return f'class="a" data-fx="{fx}" data-t="{t}" data-d="{d}" {extra}'


# ---------- S1 · 资本开支分段柱 ----------
def svg_capex():
    labels = ["20–21", "22–23", "24–25", "26–27E", "28–29E", "30–31E", "32–33E", "34–35E"]
    base = [35, 42, 48, 50, 52, 53, 53, 53]
    inc = [0, 0, 0, 2, 7, 15, 23, 33]
    W, H, y0, k = 920, 700, 620, 6.0
    slot = W / 8; bw = 72
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<!--src: MS p21 图（每两年合计，万亿元人民币）：基线 35/42/48/50/52/53/53/53，增量 +2/+7/+15/+23/+33-->']
    for i, (lb, b, n) in enumerate(zip(labels, base, inc)):
        x = i * slot + (slot - bw) / 2
        hb = b * k; yb = y0 - hb
        t = 0.3 + 0.12 * i
        o.append(f'<rect {a("gy", t, 0.6)} x="{f(x)}" y="{f(yb)}" width="{bw}" height="{f(hb)}" fill="{G2 if i < 3 else G1}"/>')
        o.append(f'<text {a("fade", t + 0.4, 0.4)} x="{f(x+bw/2)}" y="{y0-18}" class="in" text-anchor="middle">{b}</text>')
        if n:
            ti = 3.0 + 0.5 * (i - 3)
            hn = n * k; top = yb - hn
            o.append(f'<rect {a("gy", ti, 0.5)} x="{f(x)}" y="{f(top)}" width="{bw}" height="{f(hn)}" fill="{GOLD}"/>')
            o.append(f'<text {a("up", ti + 0.3, 0.4)} x="{f(x+bw/2)}" y="{f(top-12)}" class="inc" text-anchor="middle">+{n}</text>')
        o.append(f'<text x="{f(x+bw/2)}" y="{y0+44}" class="ax" text-anchor="middle">{lb}</text>')
    o.append(f'<line x1="0" y1="{y0}" x2="{W}" y2="{y0}" stroke="{INK2}" stroke-width="2"/>')
    xa = 3 * slot + (slot - bw) / 2; xb = 7 * slot + (slot + bw) / 2; yt = 40
    o.append(f'<g {a("fade", 5.8, 0.6)}><path d="M{f(xa)} {yt+12} V{yt} H{f(xb)} V{yt+12}" fill="none" stroke="{G3}" stroke-width="2"/>'
             f'<text x="{f((xa+xb)/2)}" y="{yt-12}" class="br" text-anchor="middle">工业 5.0 增量 ≈ 80 万亿元 ≈ 12 万亿美元</text></g>')
    o.append('<!--src: MS p21 图注 Cumulative ~Rmb80trn；标题 US$12tn-->')
    o.append('</svg>')
    return "\n".join(o)


# ---------- S2 · 潜在 GDP 拉动 ----------
def svg_jcurve():
    data = [("2026–27E", 0.0), ("2028–30E", 0.3), ("2031–35E", 0.5)]
    W, H, y0, k = 920, 300, 240, 380
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<!--src: MS p36 右图 Overall Growth 0.0% / 0.3% / 0.5%-->']
    for i, (lb, v) in enumerate(data):
        cx = 160 + i * 300; bw = 130
        h = max(v * k, 4)
        t = 8.6 + 0.5 * i
        o.append(f'<rect {a("gy", t, 0.6)} x="{f(cx-bw/2)}" y="{f(y0-h)}" width="{bw}" height="{f(h)}" fill="{INK2 if v else G2}"/>')
        o.append(f'<text {a("up", t + 0.4, 0.4)} x="{cx}" y="{f(y0-h-16)}" class="val" text-anchor="middle">{v:.1f}</text>')
        o.append(f'<text x="{cx}" y="{y0+44}" class="ax" text-anchor="middle">{lb}</text>')
    o.append(f'<line x1="0" y1="{y0}" x2="{W}" y2="{y0}" stroke="{INK2}" stroke-width="2"/>')
    o.append('</svg>')
    return "\n".join(o)


# ---------- S3 · 12 万亿美元拆账 ----------
def svg_alloc():
    segs = [("AI 基建", 0.2, "#5B6674"), ("能源", 0.3, G3), ("机器人", 1.5, GOLD),
            ("智能装备", 3.0, GOLD_L), ("软件", 1.0, GOLD_D), ("新产能", 6.0, G1)]
    W, H, yb, bh = 920, 250, 64, 96
    k = W / 12.0
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<!--src: MS p22 瀑布图 0.2/0.3/1.5/3.0/1.0/6.0，合计 12，US$tn（原报告小标题误写 bn）-->']
    x = 0.0; pos = {}
    for i, (name, v, col) in enumerate(segs):
        w = v * k
        o.append(f'<rect {a("gx", 0.3 + 0.3 * i, 0.45)} x="{f(x)}" y="{yb}" width="{f(w)}" height="{bh}" fill="{col}"/>')
        pos[name] = (x, w); x += w
    vals = dict((s[0], s[1]) for s in segs)
    for i, name in enumerate(["机器人", "智能装备", "软件"]):
        x0, w = pos[name]
        o.append(f'<text {a("fade", 1.2 + 0.3 * i, 0.4)} x="{f(x0+w/2)}" y="{yb-16}" class="lab" text-anchor="middle">{name} {vals[name]:.1f}</text>')
    x0, w = pos["新产能"]
    o.append(f'<text {a("fade", 2.1, 0.4)} x="{f(x0+w/2)}" y="{yb+bh/2+13}" class="labb" text-anchor="middle">新产能 6.0</text>')
    ib = pos["能源"][0] + pos["能源"][1]
    fa = pos["机器人"][0]; fb = pos["软件"][0] + pos["软件"][1]
    yl = yb + bh + 18
    o.append(f'<g {a("fade", 2.4, 0.5)}><path d="M1 {yl-10} V{yl} H{f(ib-1)} V{yl-10}" fill="none" stroke="{G3}" stroke-width="2"/>'
             f'<text x="0" y="{yl+38}" class="grp">基建 0.5</text></g>')
    o.append(f'<g {a("fade", 2.6, 0.5)}><path d="M{f(fa+1)} {yl-10} V{yl} H{f(fb-1)} V{yl-10}" fill="none" stroke="{GOLD}" stroke-width="2"/>'
             f'<text x="{f((fa+fb)/2)}" y="{yl+42}" class="grpg" text-anchor="middle">改工厂 5.5</text></g>')
    o.append('</svg>')
    return "\n".join(o)


# ---------- S5 · 国产化率哑铃 ----------
def svg_local():
    rows = [("半导体设备", 13.5, 30, 30, "30%", "13.5%"),
            ("高端液压", 35, 50, 60, "50–60%", "35%"),
            ("工业自动化", 40, 60, 70, "60–70%", "40%"),
            ("RV 减速器", 40, 60, 60, "60%", "40%"),
            ("工业机器人", 55, 70, 80, "70–80%", "55%"),
            ("谐波减速器", 55, 70, 80, "70–80%", "55%"),
            ("工程机械", 90, 90, 95, "90–95%", "90%"),
            ("锂电设备", 97, 99.5, 99.5, "≈100%", "97%"),
            ("光伏设备", 97, 99.5, 99.5, "≈100%", "97%")]
    W, rh, top = 920, 86, 6
    x0, x1 = 330, 820
    k = (x1 - x0) / 100
    H = top + rh * len(rows) + 44
    X = lambda v: x0 + v * k
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<!--src: MS p41 表 Localization rate 2025 → 2030e；WFE 行据 MS p15 图 2024 → 2027–29e 13.5% → 30%-->']
    yax = top + rh * len(rows)
    o.append(f'<line x1="{f(X(50))}" y1="{top}" x2="{f(X(50))}" y2="{yax}" stroke="{HAIR}" stroke-width="2" stroke-dasharray="4 8"/>')
    for tk in (0, 50, 100):
        o.append(f'<text x="{f(X(tk))}" y="{yax+36}" class="ax" text-anchor="middle">{tk}%</text>')
    for i, (lb, cur, lo, hi, tt, ct) in enumerate(rows):
        yc = top + i * rh + rh / 2
        t = 0.4 + 0.25 * i
        o.append(f'<g {a("fade", t, 0.35)}><text x="250" y="{f(yc+12)}" class="rl" text-anchor="end">{lb}</text>'
                 f'<circle cx="{f(X(cur))}" cy="{f(yc)}" r="11" fill="#fff" stroke="{G3}" stroke-width="4"/>'
                 f'<text x="{f(X(cur)-22)}" y="{f(yc+10)}" class="v0" text-anchor="end">{ct}</text></g>')
        if X(lo) - X(cur) > 1:
            o.append(f'<rect {a("gx", t + 0.2, 0.5)} x="{f(X(cur)+11)}" y="{f(yc-2)}" width="{f(X(lo)-X(cur)-11)}" height="4" fill="{G2}"/>')
        if hi > lo:
            o.append(f'<rect {a("gx", t + 0.55, 0.35)} x="{f(X(lo))}" y="{f(yc-11)}" width="{f(X(hi)-X(lo))}" height="22" fill="{GOLD}"/>')
        else:
            o.append(f'<circle {a("pop", t + 0.55, 0.35)} cx="{f(X(lo))}" cy="{f(yc)}" r="12" fill="{GOLD}"/>')
        o.append(f'<text {a("fade", t + 0.75, 0.35)} x="{f(X(hi)+22)}" y="{f(yc+11)}" class="v1">{tt}</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------- S6 · 利润率 U 型周期（示意） ----------
def svg_ucurve():
    W, H = 920, 530
    xa, xb, yt, yb = 40, 900, 40, 470
    s1, s2 = 250, 560
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<!--src: MS p34 示意图（定性）：0-1 最高利润 → 国产化＋内卷最低 → 出海长期修复后企稳-->']
    for sx in (s1, s2):
        o.append(f'<line x1="{sx}" y1="{yt}" x2="{sx}" y2="{yb}" stroke="{HAIR}" stroke-width="2" stroke-dasharray="5 8"/>')
    o.append(f'<line x1="{xa}" y1="{yt-10}" x2="{xa}" y2="{yb}" stroke="{INK2}" stroke-width="2"/>')
    o.append(f'<line x1="{xa}" y1="{yb}" x2="{xb}" y2="{yb}" stroke="{INK2}" stroke-width="2"/>')
    o.append(f'<text x="{xa+12}" y="{yt-10}" class="ax">利润率</text>')
    o.append(f'<path {a("draw", 0.4, 1.4)} d="M70 100 C190 100, 300 390, 420 415" fill="none" stroke="{INK2}" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<path {a("draw", 1.8, 1.4)} d="M420 415 C510 440, 560 255, 650 190 C720 145, 800 190, 880 195" fill="none" stroke="{GOLD}" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<circle {a("pop", 0.3, 0.3)} cx="70" cy="100" r="13" fill="{INK}"/>')
    o.append(f'<text {a("fade", 0.6, 0.4)} x="98" y="82" class="ann">利润最高</text>')
    o.append(f'<circle {a("pop", 1.7, 0.3)} cx="420" cy="415" r="13" fill="{INK}"/>')
    o.append(f'<text {a("fade", 1.9, 0.4)} x="420" y="458" class="ann" text-anchor="middle">内卷：利润最低</text>')
    o.append(f'<circle {a("pop", 3.1, 0.3)} cx="880" cy="195" r="13" fill="{GOLD}"/>')
    o.append(f'<text {a("fade", 3.2, 0.4)} x="880" y="140" class="ann" text-anchor="end">出海后修复、企稳</text>')
    for cx, tx in (((xa + s1) / 2, "0-1 窗口"), ((s1 + s2) / 2, "国产化＋内卷"), ((s2 + xb) / 2, "出海")):
        o.append(f'<text x="{f(cx)}" y="{yb+46}" class="zl" text-anchor="middle">{tx}</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------- S6 · 对美出口可替代性 ----------
def svg_subst():
    segs = [(40, "易替代 40%", "≈1,700 亿美元", G1, "labd"), (32, "中度 32%", "≈1,400 亿美元", G3, "labw"),
            (28, "难替代 28%", "≈1,250 亿美元", INK2, "labw")]
    W, H, bh = 920, 130, 76
    k = W / 100
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<!--src: MS p39 右图注 ~170BUSD or 40% / ~140BUSD or 32% / ~125BUSD or 28% of US imports from China-->']
    x = 0.0
    for i, (v, t1, t2, col, cls) in enumerate(segs):
        w = v * k
        t = 8.6 + 0.4 * i
        o.append(f'<rect {a("gx", t, 0.45)} x="{f(x)}" y="0" width="{f(w-4)}" height="{bh}" fill="{col}"/>')
        o.append(f'<text {a("fade", t + 0.3, 0.35)} x="{f(x+18)}" y="{bh/2+12}" class="{cls}">{t1}</text>')
        o.append(f'<text {a("fade", t + 0.4, 0.35)} x="{f(x+4)}" y="{bh+42}" class="ax">{t2}</text>')
        x += w
    o.append('</svg>')
    return "\n".join(o)


def qr_b64():
    with open(QR, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def srt_time(s):
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


if __name__ == "__main__":
    tpl = open(os.path.join(HERE, "stage_template.html"), encoding="utf-8").read()
    parts = {"SVG_CAPEX": svg_capex, "SVG_JCURVE": svg_jcurve, "SVG_ALLOC": svg_alloc,
             "SVG_LOCAL": svg_local, "SVG_UCURVE": svg_ucurve, "SVG_SUBST": svg_subst, "QR_B64": qr_b64,
             "SCENES_JSON": lambda: json.dumps([list(x) + [round(SCALE[x[0]], 4)] for x in SCENES], ensure_ascii=False),
             "CUES_JSON": lambda: json.dumps(CUES, ensure_ascii=False),
             "DURATION": lambda: str(DURATION)}
    html = tpl
    for key, fn in parts.items():
        html = html.replace("{{" + key + "}}", fn())
    # 同一标签上的两个 class 属性合并（浏览器只认第一个，第二个会被丢掉）
    html, n = re.subn(r'<(\w+) class="a" (data-fx="[^"]*" data-t="[^"]*" data-d="[^"]*" )([^>]*?) class="([^"]+)"',
                      r'<\1 class="a \4" \2\3', html)
    assert not re.search(r'<[^>]*class="[^"]*"[^>]*class="', html), "仍有重复 class"
    print("合并 class", n, "处")
    assert "{{" not in html, "未替换的占位符"
    open(os.path.join(HERE, "stage.html"), "w", encoding="utf-8").write(html)
    # 字幕
    with open(os.path.join(HERE, "..", "大摩-工业5.0-2分钟视频_字幕.srt"), "w", encoding="utf-8") as fh:
        for i, (s, e, t) in enumerate(CUES, 1):
            fh.write(f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{t}\n\n")
    chars = sum(len(t.replace(" ", "")) for _, _, t in CUES)
    print("stage.html ok；字幕", len(CUES), "条，口播", chars, "字，约", round(chars / DURATION, 1), "字/秒")
