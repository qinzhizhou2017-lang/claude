#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE PORT — 研报可视化精华版 · 第 3 篇
Morgan Stanley, Alphabet Inc.: "$200bn of 1P TPU Revenue on the Way and 3 Catalysts Ahead" (2026-08-24)"""

MAST = ('<div class="mast">\n'
        '    <div class="brand"><div class="dot"></div><div><div class="bname">THE&nbsp;PORT</div>'
        '<div class="bsub">全 球 投 行 研 报 精 选</div></div></div>\n'
        '    <div class="mright">{r}</div>\n  </div>')

COVER_R = ('<b>机构研究 · 可视化精华</b><br>来源：Morgan Stanley 互联网研究 · 2026.08.24<br>'
           '分析师 Brian Nowak, CFA（增持 Overweight）')
INNER_R = '<b>Alphabet Inc.</b> · GOOGL.O · 增持 Overweight<br>Morgan Stanley · 2026.08.24'


def foot(label, pg):
    return ('<div class="foot">\n'
            '    <span><b>THE PORT</b> · 全球投行研报精选</span>\n'
            f'    <span>{label}</span>\n'
            f'    <span class="pg">第 3 篇 &nbsp;·&nbsp; {pg} / 04</span>\n'
            '  </div>')


# ------------------------------------------------------- 图 A：TPU 收入 原预测 vs 新预测
def tpu_chart():
    data = [("2026", 5, 7, None), ("2027", 62, 84, "+35%"), ("2028", 79, 108, "+37%")]
    W, H = 660, 258
    L, R, TOP, BOT = 52, 16, 30, 40
    vmax = 120.0
    ph = H - TOP - BOT
    y0 = TOP + ph
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="GOOGL 第一方 TPU 收入：原预测 vs 新预测">']
    g = []
    for t in range(0, 121, 30):
        y = y0 - ph * t / vmax
        g.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W - R}" y2="{y:.1f}"/>')
        s.append(f'<text class="axlab" x="{L - 9}" y="{y + 4:.1f}" text-anchor="end" fill="#8A909A">${t}</text>')
    s.insert(1, '<g stroke="#ECE7DD" stroke-width="1">' + "".join(g) + '</g>')
    s.append(f'<line x1="{L}" y1="{y0}" x2="{W - R}" y2="{y0}" stroke="#B4B0A6" stroke-width="1.5"/>')
    slot = (W - L - R) / 3
    bw = 62
    for i, (lab, prior, cur, delta) in enumerate(data):
        cx = L + slot * (i + 0.5)
        for j, (v, col, nm) in enumerate([(prior, "#B4B0A6", "prior"), (cur, "#1B2440", "cur")]):
            x = cx - bw - 5 + j * (bw + 10)
            h = ph * v / vmax
            s.append(f'<rect x="{x:.1f}" y="{y0 - h:.1f}" width="{bw}" height="{h:.1f}" rx="3" '
                     f'fill="{col}"/>')
            s.append(f'<text class="ptlab" x="{x + bw / 2:.1f}" y="{y0 - h - 8:.1f}" '
                     f'text-anchor="middle" fill="{"#8A909A" if nm == "prior" else "#1B2440"}">${v}</text>')
        if delta:
            s.append(f'<text x="{cx + bw / 2 + 5:.1f}" y="{y0 - ph * cur / vmax - 26:.1f}" '
                     f'text-anchor="middle" font-family="Inter" font-size="12.5" font-weight="800" '
                     f'fill="#12705C">{delta}</text>')
        s.append(f'<text class="axlab" x="{cx:.1f}" y="{H - 13}" text-anchor="middle" '
                 f'fill="#4C535D" font-size="12" font-weight="700">{lab}</text>')
    s.append('<g font-size="10.5" font-weight="700" font-family="Inter">'
             '<rect x="52" y="10" width="13" height="9" rx="2" fill="#B4B0A6"/>'
             '<text x="70" y="18" fill="#4C535D">原预测 Prior</text>'
             '<rect x="176" y="10" width="13" height="9" rx="2" fill="#1B2440"/>'
             '<text x="194" y="18" fill="#4C535D">新预测 Current（十亿美元）</text></g>')
    s.append('</svg>')
    return "\n        ".join(s)


# ------------------------------------------------------- 图 B：云 EBIT 与占公司 EBIT 比重
def cloud_chart():
    data = [("2023", 1865, 2), ("2024", 6112, 5), ("2025", 13565, 11),
            ("2026", 36406, 21), ("2027", 86467, 38), ("2028", 136590, 48)]
    W, H = 660, 262
    L, R, TOP, BOT = 56, 46, 30, 40
    vmax, pmax = 145000.0, 55.0
    ph = H - TOP - BOT
    y0 = TOP + ph
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Google Cloud EBIT 及其占 Alphabet EBIT 的比重">']
    g = []
    for t in range(0, 145001, 35000):
        y = y0 - ph * t / vmax
        g.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W - R}" y2="{y:.1f}"/>')
        s.append(f'<text class="axlab" x="{L - 9}" y="{y + 4:.1f}" text-anchor="end" '
                 f'fill="#8A909A">{t // 1000}</text>')
    s.insert(1, '<g stroke="#ECE7DD" stroke-width="1">' + "".join(g) + '</g>')
    for t in (0, 20, 40):
        y = y0 - ph * t / pmax
        s.append(f'<text class="axlab" x="{W - R + 9}" y="{y + 4:.1f}" text-anchor="start" '
                 f'fill="#C0271C">{t}%</text>')
    s.append(f'<line x1="{L}" y1="{y0}" x2="{W - R}" y2="{y0}" stroke="#B4B0A6" stroke-width="1.5"/>')
    slot = (W - L - R) / len(data)
    bw = 48
    pts = []
    for i, (lab, ebit, pct) in enumerate(data):
        cx = L + slot * (i + 0.5)
        h = ph * ebit / vmax
        last = (i == len(data) - 1)
        fill = "#12705C" if last else "#1B2440"
        op = "" if last else ' opacity="0.86"'
        s.append(f'<rect x="{cx - bw / 2:.1f}" y="{y0 - h:.1f}" width="{bw}" height="{max(h, 1.5):.1f}" '
                 f'rx="3" fill="{fill}"{op}/>')
        s.append(f'<text class="axlab" x="{cx:.1f}" y="{H - 13}" text-anchor="middle" fill="#4C535D" '
                 f'font-size="11.5" font-weight="700">{lab}</text>')
        pts.append((cx, y0 - ph * pct / pmax, pct))
    s.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts) +
             '" fill="none" stroke="#C0271C" stroke-width="2.6" stroke-linejoin="round"/>')
    for i, (x, y, pct) in enumerate(pts):
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5 if i == len(pts) - 1 else 4}" fill="#C0271C"/>')
        s.append(f'<text class="ptlab" x="{x:.1f}" y="{y - 9:.1f}" text-anchor="middle" '
                 f'fill="#C0271C" font-size="11.5">{pct}%</text>')
    s.append('<g font-size="10.5" font-weight="700" font-family="Inter">'
             '<rect x="56" y="10" width="13" height="9" rx="2" fill="#1B2440"/>'
             '<text x="74" y="18" fill="#4C535D">Google Cloud EBIT（十亿美元，左轴）</text>'
             '<rect x="330" y="12" width="13" height="4" rx="2" fill="#C0271C"/>'
             '<text x="348" y="18" fill="#4C535D">占 Alphabet 总 EBIT 比重（右轴）</text></g>')
    s.append('</svg>')
    return "\n        ".join(s)


PAGES = []

# ============================================================ P1 封面
PAGES.append(f'''<section class="page">
  {MAST.format(r=COVER_R)}

  <div class="main">
    <div>
      <div class="cv-eyerow">
        <span class="eyebrow">Alphabet · TPU 外销与三大催化剂</span>
        <span class="cv-tickers"><b>GOOGL.O</b>&nbsp;纳斯达克&nbsp;&nbsp;/&nbsp;&nbsp;市值 <b>4.27 万亿美元</b></span>
      </div>
      <div class="rule-gold"></div>
      <h1 class="headline">近 <span class="hl">2,000 亿美元</span>的芯片外销，<br>换来的 EPS 上修只有 <span class="box">1%–2%</span></h1>
      <p class="subhead">摩根士丹利把 Alphabet 第一方 TPU 外销的定价假设从 <b>200 亿美元/GW 上调到 270 亿美元/GW</b>，毛利率从 20% 提到 30%。2027／2028 年 TPU 相关的 Google Cloud 收入因此升到 <b>843 亿／1,083 亿美元</b>，比原预测高 35%／37%——加上 2026 年的 70 亿，三年合计接近 <b>2,000 亿美元</b>。但公司层面的收入只上修 2%／3%，<b>EPS 只上修 1%／2%</b>，目标价维持 400 美元不变。</p>
    </div>

    <div class="judg">
      <div class="lab"><span>核心</span><span>判断</span></div>
      <div class="body"><div>收入故事和估值故事，<b>不是同一个故事</b>。分析师 Brian Nowak 说得很直接：TPU 销售推动的是<b>盈利预测的上修</b>，但真正能让股票重估的，是 <b>Gemini 4</b>——让 Google 回到或接近前沿，把股价带回 2025 年 11 月 Gemini 3 发布后的水平。维持<b>增持</b>，目标价 <span class="big">$400</span>，较 8 月 21 日收盘价 <b>+16%</b>。</div></div>
    </div>

    <div class="cv-metrics">
      <div class="mcard">
        <div class="tag">原为 $20bn</div>
        <div class="top">TPU 每 GW 售价假设</div>
        <div class="fig">$27<span class="u">bn</span></div>
        <div class="cap">毛利率同步从 20% 上调到 <b>30%</b>；对应约 100 万颗 TPU 换 350 亿美元的市场传闻</div>
      </div>
      <div class="mcard">
        <div class="tag">2023 年仅 2%</div>
        <div class="top">2028 年云占公司 EBIT</div>
        <div class="fig g">48<span class="u">%</span></div>
        <div class="cap">Google Cloud EBIT 从 19 亿美元升至 <b>1,366 亿美元</b>，五年五个台阶</div>
      </div>
      <div class="mcard">
        <div class="top">TPU 每 GW 相对英伟达</div>
        <div class="fig" style="color:var(--red)">−18<span class="u">%</span></div>
        <div class="cap">TPU 每 GW 收入 265 亿美元，对比 Vera Rubin 机架成本 <b>324 亿美元</b></div>
      </div>
    </div>

    <div class="cv-two">
      <div class="wide">
        <div class="ic navy">G4</div>
        <div><div class="t">催化剂一：Gemini 4（2026 年底／2027 年初）</div>
        <div class="d">摩根士丹利认为这是<b>最重要的重估催化剂</b>——让 Google 回到或接近模型前沿，是三条催化剂里权重最高的一条。</div></div>
      </div>
      <div class="wide">
        <div class="ic gold">$</div>
        <div><div class="t">但自由现金流会先变成负数</div>
        <div class="d">资本开支 2027 年 <b>3,750 亿美元</b>、2028 年 4,000 亿（本次未调整），自由现金流 2027 年为 <b>−692 亿美元</b>。</div></div>
      </div>
    </div>

    <div class="toc">
      <div class="ti"><div class="tn">01</div><div class="tt2">TPU 的账怎么算</div><div class="td">一笔外部合同重写了模型：$20bn/GW → $27bn/GW</div></div>
      <div class="ti"><div class="tn">02</div><div class="tt2">云成为利润主引擎</div><div class="td">五年从 2% 到 48%，以及被 TPU 摊薄的利润率</div></div>
      <div class="ti"><div class="tn">03</div><div class="tt2">估值与三大催化剂</div><div class="td">为什么 EPS 上修了，目标价却一动不动</div></div>
    </div>
  </div>

  {foot("封面 · Cover", "01")}
</section>''')

# ============================================================ P2 TPU 的账
PAGES.append(f'''<section class="page">
  {MAST.format(r=INNER_R)}

  <div class="main">
    <div>
      <div class="sectlabel"><span class="no">01</span><span class="tt">一笔外部合同，重写了整个模型</span><span class="en">Repricing The TPU</span></div>
      <div class="callout">
        <div class="q">市场传闻 Alphabet 承诺供应约 <b>100 万颗 TPU</b>（摩根士丹利估算约 1.3 GW）换取约 <b>350 亿美元</b>——折合约 <b>270 亿美元/GW</b>。叠加与 Marvell 扩大的定制芯片协议，摩根士丹利把此前 200 亿/GW、20% 毛利率的假设，一次性上调到 <b>270 亿/GW、30% 毛利率</b>。</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-t">同一门生意，<span class="accent">换个价格假设，2028 年多出 290 亿美元</span></div>
      <div class="panel-sub">Alphabet 第一方 TPU 销售收入预测。定价与毛利率的两处调整，让 2027／2028 年的预测分别抬高 <b>35%／37%</b>——三年合计接近 2,000 亿美元，这正是报告标题里的那个数字。</div>
        {tpu_chart()}
      <div class="src">来源：公司数据、Morgan Stanley Research（Exhibit 1）。单位：十亿美元。2026 年为 2H26 的 0.3 GW 出货。</div>
    </div>

    <div class="split">
      <div class="panel" style="padding:15px 17px;">
        <div class="panel-t" style="font-size:13.5px;">2027 年的账，<span class="accent">拆到机架这一层</span></div>
        <div class="panel-sub" style="margin-top:8px;">摩根士丹利把 2027 年的 843 亿美元拆成两代产品：v8 出货 <b>31,154 台</b>机架、v9 出货 <b>6,114 台</b>。机架成本（摩根士丹利估算 Alphabet 的采购价）v8 为 <b>170 万美元/台</b>、v9 为 190 万美元（较 v8 高 10%）；两代都按 <b>30% 的毛利率</b>加价，得到 693 亿 + 150 亿美元的收入。功耗上 v8 每机架 83 千瓦（每颗芯片 1.3 千瓦），v9 每机架 96 千瓦（1.5 千瓦）。</div>
        <div class="mini" style="margin-top:11px;">
          <div class="mi"><div class="k">2H26 出货</div><div class="v">0.3<span class="u"> GW</span></div><div class="s">起步阶段<br>收入 <b>$70 亿</b></div></div>
          <div class="mi"><div class="k">2027 出货</div><div class="v">3.2<span class="u"> GW</span></div><div class="s">v8 2.6 + v9 0.6<br>收入 <b>$843 亿</b></div></div>
          <div class="mi"><div class="k">2028 出货</div><div class="v g">4.2<span class="u"> GW</span></div><div class="s">继续放量<br>收入 <b>$1,083 亿</b></div></div>
        </div>
        <div class="src">来源：Morgan Stanley Research（Exhibit 5 / Exhibit 8）。</div>
      </div>

      <div class="panel" style="padding:15px 17px;">
        <div class="panel-t" style="font-size:13.5px;">定价空间从哪来：<span class="accent">比英伟达便宜 18%</span></div>
        <div class="panel-sub" style="margin-top:8px;margin-bottom:11px;">每 GW 的价格对比（百万美元）。即便把售价从 200 亿抬到 270 亿美元/GW，TPU 相对英伟达 Vera Rubin 的机架成本仍有<b>接近两成的折让</b>——这既解释了客户为什么买，也说明这个价格假设并不激进。</div>
        <div class="bars">
          <div class="bar"><div class="nm"><b>Vera Rubin</b>英伟达机架成本</div><div class="track"><div class="fill" style="width:100%"></div></div><div class="val">32,446</div></div>
          <div class="bar hl"><div class="nm"><b>TPU 1P</b>每 GW 收入</div><div class="track"><div class="fill" style="width:81.7%"></div></div><div class="val">26,512</div></div>
        </div>
        <div style="margin-top:13px;padding:11px 13px;background:var(--greensoft);border-radius:8px;">
          <div style="font-size:10.2px;color:var(--ink);line-height:1.55;font-weight:500;">摩根士丹利同时指出，Alphabet 与 <b>Marvell</b> 扩大的定制芯片协议，本身就<b>支持 TPU 的售价／ASP 高于此前假设</b>——这是两条互相印证的证据，而不是一次孤立的上调。</div>
        </div>
        <div class="src">来源：Morgan Stanley Research（Exhibit 5）。</div>
      </div>
    </div>

    <div class="callout green">
      <div class="q"><b>投资含义</b>&nbsp;这次上调的性质是<b>定价假设的重估，不是需求假设的上修</b>——出货量（GW）没有变，变的是每 GW 值多少钱、以及 Alphabet 能从中留下多少毛利。看懂这一点，才能理解为什么收入大幅上修、EPS 却几乎没动。</div>
    </div>
  </div>

  {foot("TPU 的账怎么算 · Repricing The TPU", "02")}
</section>''')

# ============================================================ P3 云成为利润主引擎
PAGES.append(f'''<section class="page">
  {MAST.format(r=INNER_R)}

  <div class="main">
    <div>
      <div class="sectlabel"><span class="no">02</span><span class="tt">云计算，正在变成 Alphabet 的利润主引擎</span><span class="en">Cloud Becomes The Engine</span></div>
      <div class="kpirow">
        <div class="kpi"><div class="k">2027 云收入</div><div class="v">$236<span class="u">bn</span></div><div class="s">原预测 $223bn<br>上修 <b>+6%</b></div></div>
        <div class="kpi"><div class="k">2027 云收入增速</div><div class="v g">+118<span class="u">%</span></div><div class="s">原预测 <b>+106%</b><br>上修全部来自 TPU</div></div>
        <div class="kpi"><div class="k">2027 云 EBIT 增速</div><div class="v g">+137<span class="u">%</span></div><div class="s">原预测 <b>+105%</b><br>EBIT $865 亿</div></div>
        <div class="kpi"><div class="k">2028 云利润率</div><div class="v">40<span class="u">%</span></div><div class="s">报告口径，从 41% <b>下调</b><br>被 TPU 摊薄</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-t">五年五个台阶：云的 EBIT 占比从 <span class="accent">2% 到 48%</span></div>
      <div class="panel-sub">Google Cloud 的 EBIT 与它在 Alphabet 总 EBIT 中的比重。2028 年，<b>公司将近一半的经营利润来自云</b>——而 2023 年这个比例只有 2%。对一家至今仍被当作广告公司定价的企业来说，这是结构性的变化。</div>
        {cloud_chart()}
      <div class="src">来源：公司数据、Morgan Stanley Research（Exhibit 3）。左轴为 Google Cloud EBIT（十亿美元），右轴为占 Alphabet 总 EBIT 的比重。</div>
    </div>

    <div class="split" style="grid-template-columns:1fr 1.02fr;">
      <div class="vecs">
        <div class="vec">
          <div class="vi">01</div>
          <div><div class="vt">核心云的赚钱能力没有变</div>
          <div class="vd">剔除 TPU 与 SPCX 算力协议后，核心云的<b>增量利润率维持在约 50%</b>（2026 年 57%、2027 年 51%、2028 年 48%）。真正被稀释的是报告口径，不是底层生意。</div></div>
        </div>
        <div class="vec">
          <div class="vi">02</div>
          <div><div class="vt">TPU 是低毛利、高体量的生意</div>
          <div class="vd">按 30% 的 EBIT 利润率计，TPU 在 2027／2028 年贡献 253 亿／325 亿美元 EBIT，但把云的报告口径利润率从 <b>38%／41% 拉低到 37%／40%</b>。</div></div>
        </div>
        <div class="vec">
          <div class="vi">03</div>
          <div><div class="vt">核心云收入反而被下调了</div>
          <div class="vd">剔除 TPU 后的云收入，2027 年从 1,600 亿下调到 <b>1,510 亿</b>、2028 年从 2,410 亿下调到 2,350 亿。<b>这次上修的增量，全部来自 TPU</b>。</div></div>
        </div>
      </div>

      <div class="capband" style="padding:15px 18px;">
        <div class="h">利润在涨，<span class="g">现金流先往下走</span></div>
        <div class="capstat"><div class="l">资本开支 2027E<br><span style="font-size:8.4px;color:#8FA0C8;">本次未调整</span></div><div class="r">$3,750<span class="u"> 亿</span></div></div>
        <div class="capstat"><div class="l">资本开支 2028E<br><span style="font-size:8.4px;color:#8FA0C8;">本次未调整</span></div><div class="r">$4,000<span class="u"> 亿</span></div></div>
        <div class="capstat"><div class="l">自由现金流 2027E<br><span style="font-size:8.4px;color:#8FA0C8;">每股 −$5.52</span></div><div class="r" style="color:#F0C4BE;">−$692<span class="u"> 亿</span></div></div>
        <div class="capstat"><div class="l">自由现金流 2028E<br><span style="font-size:8.4px;color:#8FA0C8;">刚刚回正</span></div><div class="r">+$2.9<span class="u"> 亿</span></div></div>
        <div class="capnote">另一处需要留意的调整：为了对齐剔除 TPU 后的增量利润率，摩根士丹利把"其他营业成本"在 2027／2028 年<b>上调了 4%／6%</b>——这抵消了大部分收入上修，也是 EPS 只动 1%／2% 的直接原因。来源：Morgan Stanley Research（Exhibit 9）。</div>
      </div>
    </div>
  </div>

  {foot("云成为利润主引擎 · Cloud Becomes The Engine", "03")}
</section>''')

# ============================================================ P4 估值 + 催化剂 + 二维码
PAGES.append(f'''<section class="page">
  {MAST.format(r=INNER_R)}

  <div class="main">
    <div>
      <div class="sectlabel"><span class="no">03</span><span class="tt">为什么 EPS 上修了，目标价却一动不动</span><span class="en">What Matters Next</span></div>
      <div class="callout navy">
        <div class="q">400 美元的目标价，等于给 2027／2028 年平均 EPS <b>约 24 倍</b>——报告正文称这在增长调整后较同业溢价约 <b>20%</b>，而 Alphabet 目前只溢价约 5%。<b>要走到目标价，市场必须先愿意给它一个更高的倍数</b>，这件事 TPU 做不到，只有模型能做到。</div>
      </div>
    </div>

    <div class="val2">
      <div class="valcard">
        <div class="vh"><div class="nm">摩根士丹利 目标价</div><div class="tk">增持 OVERWEIGHT</div></div>
        <div class="prices">
          <div class="nowcol"><div class="nowlab">8/21 收盘</div><div class="nowval">$344.82</div></div>
          <div class="arr">→</div>
          <div class="ptcol"><div class="pt">$400</div><div class="up">+16%</div></div>
        </div>
        <div class="meta">≈24× 的 2027／2028 平均 EPS（$16.84）　·　牛市 <b>$460</b>（+33%）／熊市 <b>$225</b>（−35%）</div>
      </div>
      <div class="valcard">
        <div class="vh"><div class="nm">市场共识</div><div class="tk">90% 增持 / 10% 中性 / 0% 减持</div></div>
        <div class="prices">
          <div class="nowcol"><div class="nowlab">目标价区间</div><div class="nowval">$240–515</div></div>
          <div class="arr">→</div>
          <div class="ptcol"><div class="pt" style="color:var(--navy)">$421</div><div class="up" style="background:#E7EAF1;color:var(--navy)">均值</div></div>
        </div>
        <div class="meta">2026 年预测 EPS：摩根士丹利 <b>$20.29</b> vs 共识 $20.60　·　机构持股中主动型占 <b>56.5%</b></div>
      </div>
    </div>

    <div class="panel" style="padding:14px 18px;">
      <div class="panel-t" style="font-size:13.5px;">期权市场怎么定价这三档情景</div>
      <div class="fcast" style="margin-top:10px;">
        <div class="fc"><div class="fk">涨过 $460（牛市）</div><div class="fv">16.9<span class="u">%</span></div><div class="fs">12 个月隐含概率</div></div>
        <div class="fc"><div class="fk">涨过 $400（目标价）</div><div class="fv">30.9<span class="u">%</span></div><div class="fs">12 个月隐含概率</div></div>
        <div class="fc"><div class="fk">跌破 $225（熊市）</div><div class="fv">11.3<span class="u">%</span></div><div class="fs">12 个月隐含概率</div></div>
        <div class="fc"><div class="fk">2027E EPS</div><div class="fv">$15.19</div><div class="fs">上修 +0.8%</div></div>
        <div class="fc"><div class="fk">2028E EPS</div><div class="fv">$18.49</div><div class="fs">上修 +1.8%</div></div>
      </div>
      <div class="src">概率由 2026 年 8 月 21 日的期权隐含波动率估算，为风险中性概率。同业 2028 年市盈率中位数 18 倍（AAPL 29×、MSFT 18×、META 16×、AMZN 17×、NFLX 18×）；Exhibit 7 口径下，$400 目标价对应 PEG 1.5 倍、较同业中位数溢价 19%（现价为 1.3 倍、溢价 3%）。上行空间 +16% 取自 Risk Reward 页对 $344.82 的标注；报告正文表述为"约 15%"，Exhibit 6 列为 14%。来源：Refinitiv、Morgan Stanley Research（Exhibit 6 / 7 / Risk Reward）。</div>
    </div>

    <div class="watch">
      <div class="wbox up">
        <div class="wh">◤ 三大催化剂与上行风险</div>
        <ul>
          <li><b>Gemini 4</b>（2026 年底／2027 年初）——报告认为这是最重要的重估催化剂</li>
          <li><b>Gemini Flash</b> 等高效低成本模型：企业 AI 预算日趋审慎，性价比是关键</li>
          <li>GenAI 产品<b>全面规模化铺开</b>，支撑搜索与 YouTube 更持久的增长</li>
          <li>新产品贡献超预期、<b>更大规模回购</b>、人均支出低于预期</li>
        </ul>
      </div>
      <div class="wbox dn">
        <div class="wh">◤ 需要警惕的地方</div>
        <ul>
          <li>全球广告增速进一步放缓、利润率承压；<b>费用纪律若不到位</b>，利润率扩张会落空</li>
          <li>新 AI 产品<b>变现率偏低、算力密集</b>，可能带来超预期的利润率压力</li>
          <li>对<b>中小企业与旅游行业敞口较高</b>，一旦衰退，广告收入首当其冲</li>
          <li>盯紧资产负债表上<b>新披露的存货</b>——TPU 销售兑现时的堆积或消化信号</li>
        </ul>
      </div>
    </div>

    <div>
      <div class="qrcard">
        <div class="qrinner">
          <div class="qrbox"><img src="qr.png" alt="THE PORT 微信二维码"></div>
          <div class="qrtxt">
            <div class="qbrand"><div class="qdot"></div><div class="qn">THE&nbsp;PORT</div></div>
            <div class="qh">读懂全球投行的<span class="r">核心观点</span></div>
            <div class="qs">扫码添加，每日获取高盛、摩根士丹利、摩根大通等一线机构研报的精华解读与可视化速览。本期为摩根士丹利 2026.08.24 三篇合辑。</div>
            <div class="qcta">微信扫一扫 · 或长按识别二维码</div>
          </div>
        </div>
      </div>
      <div class="disc">本文基于 Morgan Stanley 于 2026-08-24 发布的《Alphabet Inc.: $200bn of 1P TPU Revenue on the Way and 3 Catalysts Ahead》（分析师 Brian Nowak, CFA）整理，所有数字、评级、目标价与预测均以原报告为准，股价与市值数据截至 2026 年 8 月 21 日。本可视化由 THE PORT 编辑制作，仅供信息参考与交流，不构成任何投资建议或要约；投资有风险，决策须谨慎。</div>
    </div>
  </div>

  {foot("估值与催化剂 · What Matters Next", "04")}
</section>''')

HTML = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<title>摩根士丹利 Alphabet · TPU 外销与三大催化剂 · 研报精华</title>\n'
        '<link rel="stylesheet" href="styles.css">\n</head>\n<body>\n\n'
        + "\n\n".join(PAGES) + "\n\n</body>\n</html>\n")

open("d3_alphabet.html", "w", encoding="utf-8").write(HTML)
print("d3_alphabet.html", len(HTML), "bytes")
