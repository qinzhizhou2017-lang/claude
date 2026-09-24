#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大摩 Industry 5.0 · 4 页精华版生成器。SVG 坐标全部由函数计算，不手算。"""
import base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "大摩-工业5.0-4页精华版.html")
QR = os.path.join(HERE, "..", "..", "..", ".claude", "skills", "yanbao-visual-digest-v3",
                  "素材", "THE_PORT_微信二维码_纯码.png")

GOLD = "#B07818"; GOLD_D = "#8E5A0C"; INK = "#141D2A"; INK2 = "#37424F"; MUTED = "#69737F"
G1 = "#C9CFD6"; G2 = "#AEB7C2"; G3 = "#7D8894"; HAIR = "#D3D8DE"; BULL = "#0D6E55"; BEAR = "#B93A30"


def f(x):
    return f"{x:.1f}"


# ---------- P1 · 工业资本开支分段柱 ----------
def svg_capex():
    labels = ["2020–21", "2022–23", "2024–25", "2026–27E", "2028–29E", "2030–31E", "2032–33E", "2034–35E"]
    base = [35, 42, 48, 50, 52, 53, 53, 53]
    inc = [0, 0, 0, 2, 7, 15, 23, 33]
    W, H, y0, k = 700, 222, 182, 1.6
    slot = W / len(labels); bw = 52
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" role="img" aria-label="工业资本开支分段柱">']
    o.append('<!--src: MS p21 图（柱内数值为图上标注，单位万亿元人民币，每两年合计）-->')
    for i, (lb, b, n) in enumerate(zip(labels, base, inc)):
        x = i * slot + (slot - bw) / 2
        hb = b * k; yb = y0 - hb
        col = G2 if i < 3 else G1
        o.append(f'<rect x="{f(x)}" y="{f(yb)}" width="{bw}" height="{f(hb)}" fill="{col}"/>')
        o.append(f'<text x="{f(x+bw/2)}" y="{f(y0-10)}" class="in" text-anchor="middle">{b}</text>')
        top = yb
        if n:
            hn = n * k; top = yb - hn
            o.append(f'<rect x="{f(x)}" y="{f(top)}" width="{bw}" height="{f(hn)}" fill="{GOLD}"/>')
            o.append(f'<text x="{f(x+bw/2)}" y="{f(top-7)}" class="inc" text-anchor="middle">+{n}</text>')
        o.append(f'<text x="{f(x+bw/2)}" y="{y0+22}" class="ax" text-anchor="middle">{lb}</text>')
    o.append(f'<line x1="0" y1="{y0}" x2="{W}" y2="{y0}" stroke="{INK2}" stroke-width="1"/>')
    # 预测区括号
    xa = 3 * slot + (slot - bw) / 2; xb = 7 * slot + (slot + bw) / 2
    yt = 20
    o.append(f'<path d="M{f(xa)} {yt+8} V{yt} H{f(xb)} V{yt+8}" fill="none" stroke="{G3}" stroke-width="1"/>')
    o.append(f'<text x="{f((xa+xb)/2)}" y="{yt-6}" class="br" text-anchor="middle">'
             f'工业 5.0 增量合计 ≈ 80 万亿元 ≈ 12 万亿美元</text>')
    o.append('<!--src: MS p21 图注 Cumulative ~Rmb80trn；US$12tn 据 p21 标题-->')
    # 历史区标注
    o.append('</svg>')
    return "\n".join(o)


# ---------- P1 · 潜在 GDP 拉动（J 曲线） ----------
def svg_jcurve():
    data = [("26–27E", 0.0), ("28–30E", 0.3), ("31–35E", 0.5)]
    W, H, y0, k = 210, 116, 86, 110
    slot = W / 3; bw = 34
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" role="img" aria-label="GDP 拉动">',
         '<!--src: MS p36 右图 Overall Growth 标注 0.0% / 0.3% / 0.5%-->']
    for i, (lb, v) in enumerate(data):
        x = i * slot + (slot - bw) / 2
        h = max(v * k, 1.5)
        o.append(f'<rect x="{f(x)}" y="{f(y0-h)}" width="{bw}" height="{f(h)}" fill="{INK2 if v else G2}"/>')
        o.append(f'<text x="{f(x+bw/2)}" y="{f(y0-h-7)}" class="val" text-anchor="middle">{v:.1f}</text>')
        o.append(f'<text x="{f(x+bw/2)}" y="{y0+20}" class="ax" text-anchor="middle">{lb}</text>')
    o.append(f'<line x1="0" y1="{y0}" x2="{W}" y2="{y0}" stroke="{INK2}" stroke-width="1"/>')
    o.append('</svg>')
    return "\n".join(o)


# ---------- P2 · 12 万亿美元拆账条 ----------
def svg_alloc():
    segs = [("AI 基建", 0.2, "#5B6674"), ("能源", 0.3, G3), ("机器人", 1.5, GOLD),
            ("智能装备", 3.0, "#C99A45"), ("软件", 1.0, "#9C6A1C"), ("新产能", 6.0, G1)]
    W, H, yb, bh = 700, 104, 30, 32
    k = W / 12.0
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" role="img" aria-label="12 万亿美元拆账">',
         '<!--src: MS p22 瀑布图 0.2/0.3/1.5/3.0/1.0/6.0，合计 12，单位 US$tn-->']
    x = 0.0; pos = {}
    for name, v, col in segs:
        w = v * k
        o.append(f'<rect x="{f(x)}" y="{yb}" width="{f(w)}" height="{bh}" fill="{col}"/>')
        pos[name] = (x, w)
        x += w
    # 顶部标签（窄段不在顶上标）
    for name in ["机器人", "智能装备", "软件"]:
        x0, w = pos[name]
        v = dict((s[0], s[1]) for s in segs)[name]
        o.append(f'<text x="{f(x0+w/2)}" y="{yb-9}" class="lab" text-anchor="middle">{name} {v:.1f}</text>')
    x0, w = pos["新产能"]
    o.append(f'<text x="{f(x0+w/2)}" y="{yb+bh/2+6}" class="labd" text-anchor="middle">新产能 6.0</text>')
    # 底部分组括号
    def bracket(xa, xb, text, anchor="middle", tx=None):
        yl = yb + bh + 12
        s = [f'<path d="M{f(xa+1)} {yl-6} V{yl} H{f(xb-1)} V{yl-6}" fill="none" stroke="{G3}" stroke-width="1"/>']
        tx = (xa + xb) / 2 if tx is None else tx
        s.append(f'<text x="{f(tx)}" y="{yl+20}" class="grp" text-anchor="{anchor}">{text}</text>')
        return "".join(s)
    ia = 0; ib = pos["能源"][0] + pos["能源"][1]
    fa = pos["机器人"][0]; fb = pos["软件"][0] + pos["软件"][1]
    na = pos["新产能"][0]
    o.append(bracket(ia, ib, "基建 0.5", "start", 0))
    o.append(bracket(fa, fb, "工厂升级 5.5"))
    o.append('</svg>')
    return "\n".join(o)


# ---------- P2 · GenAI 落地场景横条 ----------
def svg_genai():
    rows = [("知识管理", 57, 0), ("流程改进", 38, 0), ("质量改进", 30, 0),
            ("预测性维护", 20, 1), ("机器人", 10, 1), ("CNC／自适应控制", 8, 1)]
    W, rh, lx, bx, k = 330, 27, 128, 136, 2.95
    H = rh * len(rows) + 6
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" role="img" aria-label="GenAI 落地场景">',
         '<!--src: MS p24 右图 Area of GenAI Implementation（MLC 2026-04-01 调查）57/38/30/20/10/8-->']
    for i, (lb, v, hi) in enumerate(rows):
        y = i * rh + 4
        o.append(f'<text x="{lx}" y="{y+15}" class="rl" text-anchor="end">{lb}</text>')
        o.append(f'<rect x="{bx}" y="{y+3}" width="{f(v*k)}" height="15" fill="{INK2 if hi else G1}"/>')
        o.append(f'<text x="{f(bx+v*k+6)}" y="{y+15}" class="val2">{v}%</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------- P3 · 国产化率哑铃 ----------
def svg_local():
    # (标签, 当前, 目标低, 目标高, 目标文字, 当前文字, 星标)
    rows = [("半导体设备 WFE", 13.5, 30, 30, "30%", "13.5%", "¹"),
            ("高端液压", 35, 50, 60, "50–60%", "35%", ""),
            ("工业自动化", 40, 60, 70, "60–70%", "40%", ""),
            ("RV 减速器", 40, 60, 60, "60%", "40%", ""),
            ("工业机器人", 55, 70, 80, "70–80%", "55%", "²"),
            ("谐波减速器", 55, 70, 80, "70–80%", "55%", ""),
            ("工程机械", 90, 90, 95, "90–95%", "90%", ""),
            ("锂电设备", 97, 99.5, 99.5, "≈100%", "97%", ""),
            ("光伏设备", 97, 99.5, 99.5, "≈100%", "97%", "")]
    W, rh, top = 700, 31, 8
    x0, x1 = 176, 628
    k = (x1 - x0) / 100
    H = top + rh * len(rows) + 30
    X = lambda v: x0 + v * k
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" role="img" aria-label="国产化率哑铃图">',
         '<!--src: MS p41 表 Localization rate 2025 / 2030e；WFE 行据 MS p15 图 2024→2027–29e 13.5%→30%-->']
    # 50% 极淡辅助线 + 轴
    yax = top + rh * len(rows) + 2
    o.append(f'<line x1="{f(X(50))}" y1="{top}" x2="{f(X(50))}" y2="{yax}" stroke="{HAIR}" stroke-width="1" stroke-dasharray="2 4"/>')
    for t in (0, 50, 100):
        o.append(f'<text x="{f(X(t))}" y="{yax+18}" class="ax" text-anchor="middle">{t}%</text>')
    for i, (lb, cur, lo, hi, tt, ct, star) in enumerate(rows):
        yc = top + i * rh + rh / 2
        o.append(f'<text x="{x0-14}" y="{f(yc+5)}" class="rl" text-anchor="end">{lb}<tspan class="sup" dy="-6">{star}</tspan></text>')
        o.append(f'<line x1="{f(X(cur))}" y1="{f(yc)}" x2="{f(X(lo))}" y2="{f(yc)}" stroke="{G2}" stroke-width="2"/>')
        if hi > lo:
            o.append(f'<rect x="{f(X(lo))}" y="{f(yc-5)}" width="{f(X(hi)-X(lo))}" height="10" fill="{GOLD}"/>')
        else:
            o.append(f'<circle cx="{f(X(lo))}" cy="{f(yc)}" r="6" fill="{GOLD}"/>')
        o.append(f'<circle cx="{f(X(cur))}" cy="{f(yc)}" r="5.5" fill="#fff" stroke="{G3}" stroke-width="2"/>')
        o.append(f'<text x="{f(X(cur)-11)}" y="{f(yc+5)}" class="v0" text-anchor="end">{ct}</text>')
        o.append(f'<text x="{f(X(hi)+11)}" y="{f(yc+5)}" class="v1">{tt}</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------- P3 · 对美出口可替代性 100% 条 ----------
def svg_subst():
    segs = [(40, "易替代 40%", "≈1,700 亿美元", G1, "labd"),
            (32, "中度 32%", "≈1,400 亿美元", G3, "labw"),
            (28, "难替代 28%", "≈1,250 亿美元", INK2, "labw")]
    W, H, bh = 640, 58, 30
    k = W / 100
    o = [f'<svg class="sv" viewBox="0 0 {W} {H}" role="img" aria-label="对美出口可替代性">',
         '<!--src: MS p39 右图注 ~170BUSD or 40% / ~140BUSD or 32% / ~125BUSD or 28% of US imports-->']
    x = 0.0
    for v, t1, t2, col, cls in segs:
        w = v * k
        o.append(f'<rect x="{f(x)}" y="0" width="{f(w-2)}" height="{bh}" fill="{col}"/>')
        o.append(f'<text x="{f(x+10)}" y="{bh/2+6}" class="{cls}">{t1}</text>')
        o.append(f'<text x="{f(x+2)}" y="{bh+21}" class="ax">{t2}</text>')
        x += w
    o.append('</svg>')
    return "\n".join(o)


def qr_b64():
    with open(QR, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


TEMPLATE = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
html = (TEMPLATE
        .replace("{{SVG_CAPEX}}", svg_capex())
        .replace("{{SVG_JCURVE}}", svg_jcurve())
        .replace("{{SVG_ALLOC}}", svg_alloc())
        .replace("{{SVG_GENAI}}", svg_genai())
        .replace("{{SVG_LOCAL}}", svg_local())
        .replace("{{SVG_SUBST}}", svg_subst())
        .replace("{{QR_B64}}", qr_b64()))
assert "{{" not in html, "未替换的占位符"
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(html)
print("写出", os.path.normpath(OUT), len(html), "bytes")
