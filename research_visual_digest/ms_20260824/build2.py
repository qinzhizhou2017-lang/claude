#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE PORT — 研报可视化精华版 · 第 2 篇
Morgan Stanley US Equity Strategy, "What Are Companies Saying?" (2026-08-24)"""

MAST = ('<div class="mast">\n'
        '    <div class="brand"><div class="dot"></div><div><div class="bname">THE&nbsp;PORT</div>'
        '<div class="bsub">全 球 投 行 研 报 精 选</div></div></div>\n'
        '    <div class="mright">{r}</div>\n  </div>')

COVER_R = ('<b>机构研究 · 可视化精华</b><br>来源：Morgan Stanley 美股策略 · 2026.08.24<br>'
           'Michael Wilson（首席美股策略师）、Nicholas Lentini 等')
INNER_R = '<b>美股策略</b> · What Are Companies Saying?<br>Morgan Stanley · 2026.08.24'


def foot(label, pg):
    return ('<div class="foot">\n'
            '    <span><b>THE PORT</b> · 全球投行研报精选</span>\n'
            f'    <span>{label}</span>\n'
            f'    <span class="pg">第 2 篇 &nbsp;·&nbsp; {pg} / 04</span>\n'
            '  </div>')


# ------------------------------------------------------------------ 柱状图生成器
def colchart(data, vid, w=680, h=250, unit=None, hi=-1, pad_l=46, pad_r=14,
             lab_every=3, note_hi=True):
    """data: [(label, value_pct), ...]  —— 带零线的柱状图，正绿负红"""
    vals = [v for _, v in data]
    vmax, vmin = max(vals + [0]), min(vals + [0])
    top, bot = 26, 40
    plot_h = h - top - bot
    span = (vmax - vmin) or 1
    y0 = top + plot_h * vmax / span                      # 零线
    scale = plot_h / span
    n = len(data)
    slot = (w - pad_l - pad_r) / n
    bw = min(slot * 0.62, 26)
    s = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{vid}">']
    # 网格线
    step = 5 if span <= 32 else 10
    g = []
    t = int(vmin // step) * step
    while t <= vmax:
        y = y0 - t * scale
        if top - 2 <= y <= h - bot + 2:
            g.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}"/>')
            s.append(f'<text class="axlab" x="{pad_l - 8}" y="{y + 4:.1f}" text-anchor="end" '
                     f'fill="#8A909A">{t}{unit or ""}</text>')
        t += step
    s.insert(1, '<g stroke="#ECE7DD" stroke-width="1">' + "".join(g) + '</g>')
    s.append(f'<line x1="{pad_l}" y1="{y0:.1f}" x2="{w - pad_r}" y2="{y0:.1f}" '
             f'stroke="#B4B0A6" stroke-width="1.5"/>')
    for i, (lab, v) in enumerate(data):
        cx = pad_l + slot * (i + 0.5)
        bh = abs(v) * scale
        y = y0 - bh if v >= 0 else y0
        last = (i == n - 1)
        if v >= 0:
            col = "#12705C" if (last and note_hi) else "#2E3A5C"
        else:
            col = "#C0271C"
        op = "" if (last or v < 0 or not note_hi) else ' opacity="0.82"'
        s.append(f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" '
                 f'height="{max(bh, 1.2):.1f}" rx="2" fill="{col}"{op}/>')
        if last or i == hi:
            ly = y - 7 if v >= 0 else y + bh + 15
            s.append(f'<text class="ptlab" x="{cx:.1f}" y="{ly:.1f}" text-anchor="middle" '
                     f'fill="{col}">{"+" if v > 0 else ""}{v}%</text>')
        if (i % lab_every == 0 and i < n - 2) or last:
            s.append(f'<text class="axlab" x="{cx:.1f}" y="{h - 14:.1f}" text-anchor="middle" '
                     f'fill="#8A909A" font-size="10">{lab}</text>')
    s.append('</svg>')
    return "\n        ".join(s)


EPS = [("3Q21", 16), ("4Q21", 8), ("1Q22", 1), ("2Q22", -2), ("3Q22", 2), ("4Q22", -5),
       ("1Q23", -8), ("2Q23", -8), ("3Q23", -10), ("4Q23", -11), ("1Q24", -5), ("2Q24", -1),
       ("3Q24", 0), ("4Q24", 3), ("1Q25", 2), ("2Q25", 5), ("3Q25", 7), ("4Q25", 4),
       ("1Q26", 10), ("2Q26e", 14)]

CAPEX = [("1Q23", 15), ("2Q23", 11), ("3Q23", 4), ("4Q23", 4), ("1Q24", 4), ("2Q24", 2),
         ("3Q24", 1), ("4Q24", 1), ("1Q25", 4), ("2Q25", 6), ("3Q25", 10), ("4Q25", 8),
         ("1Q26", 7), ("2Q26e", 10)]

# Exhibit 11 行业热力图：报告以三档色阶呈现（低 / 中 / 高位），下列档位逐格比对原图确认
SECTORS = ["通信<br>服务", "可选<br>消费", "必需<br>消费", "能源", "金融", "医疗<br>保健",
           "工业", "材料", "房地<br>产", "科技", "公用<br>事业"]
#            通信 可选 必需 能源 金融 医疗 工业 材料 房地产 科技 公用
HEAT = [("上调指引", ["hi","hi","hi","hi","hi","hi","hi","na","hi","hi","na"], "hi"),
        ("AI",       ["hi","hi","hi","hi","hi","hi","hi","hi","hi","md","hi"], "hi"),
        ("利润率压力",["lo","md","md","hi","hi","lo","md","hi","na","md","na"], "md"),
        ("更高利率",  ["lo","lo","lo","lo","lo","lo","lo","lo","lo","lo","na"], "lo")]


def heat_map():
    out = ['<div class="hh"><span></span>' + "".join(f'<span>{x}</span>' for x in SECTORS)
           + '<span></span><span style="color:var(--ink);">整体</span></div>']
    for name, cells, overall in HEAT:
        mark = ' mark' if name == "AI" else ''
        row = "".join(f'<div class="c {c}{mark if (c == "md" and name == "AI") else ""}"></div>'
                      for c in cells)
        out.append(f'<div class="hr"><div class="rl">{name}</div>{row}'
                   f'<div></div><div class="c {overall}"></div></div>')
    return "\n          ".join(out)


PAGES = []

# ============================================================ P1 封面
PAGES.append(f'''<section class="page">
  {MAST.format(r=COVER_R)}

  <div class="main">
    <div>
      <div class="cv-eyerow">
        <span class="eyebrow">美股策略 · 2Q 财报电话会文本挖掘</span>
        <span class="cv-tickers">样本：市值 <b>10 亿美元以上</b>美国上市公司</span>
      </div>
      <div class="rule-gold"></div>
      <h1 class="headline">上调指引创下新高，<br>市场却已<span class="box">不为 EPS 买单</span></h1>
      <p class="subhead">摩根士丹利用 AlphaSense 扫描了整个 2Q 财报季的电话会文本。"上调指引"的提及率升到约 <b>25% 的电话会</b>——2010 年有记录以来最高；标普 500 盈利修正广度 <b>+24%</b>，罗素 3000 中位数公司 EPS 同比 <b>+14%</b>。但首席美股策略师 Michael Wilson 团队补了一句关键的话：这一轮存在<b>全市场的质量转向</b>，只是 EPS 超预期已经不够，股票需要看到<b>自由现金流指引与 EPS 同步上调</b>。</p>
    </div>

    <div class="judg">
      <div class="lab"><span>核心</span><span>判断</span></div>
      <div class="body"><div>基本面确实很强——罗素 3000 中位数营收 <b>+8%</b>、EPS <b>+14%</b>、资本开支 <b>+10%</b>，衰退与周期见顶的语言依然稀少。但宏观辩论的焦点已经<b>不在就业和消费</b>，而在通胀与美联储的反应函数：经济团队认为疲软的非农可以让美联储 <span class="big">2026 全年按兵不动</span>，而标普 500 正承受<b>长端收益率上行</b>的压力。</div></div>
    </div>

    <div class="cv-metrics">
      <div class="mcard">
        <div class="tag">2010 年来最高</div>
        <div class="top">"上调指引"提及率</div>
        <div class="fig">~25<span class="u">%</span></div>
        <div class="cap">占全部电话会比例；行业热力图上<b>整体处于历史顶部区间</b></div>
      </div>
      <div class="mcard">
        <div class="tag">2021 年来最高</div>
        <div class="top">罗素 3000 中位数 EPS</div>
        <div class="fig g">+14<span class="u">%</span></div>
        <div class="cap">2Q26 同比（预估）；从 1Q26 的 <b>+10%</b> 继续加速</div>
      </div>
      <div class="mcard">
        <div class="top">标普 500 盈利修正广度</div>
        <div class="fig g">+24<span class="u">%</span></div>
        <div class="cap">2Q 财报季后<b>稳居正区间</b>，与指引上调互相印证</div>
      </div>
    </div>

    <div class="cv-two">
      <div class="wide">
        <div class="ic navy">AI</div>
        <div><div class="t">话题重心：从"花多少"转向"什么时候回本"</div>
        <div class="d">AI 建设没有降速的迹象，但"ROI"与"变现"的提及率<b>环比双双上升</b>——管理层被追问投资回收期的次数越来越多。</div></div>
      </div>
      <div class="wide">
        <div class="ic gold">kW</div>
        <div><div class="t">真正的瓶颈已经变成电力</div>
        <div class="d">数据中心与能源提及率持续攀升。贝克休斯引述 S&amp;P Global：数据中心用电到 2030 年<b>年均增长 18%</b>，约 <span class="bg">1,850 太瓦时</span>。</div></div>
      </div>
    </div>

    <div class="toc">
      <div class="ti"><div class="tn">01</div><div class="tt2">指引在涨，尺子在换</div><div class="td">中位数公司的盈利从 −11% 拉回 +14%，市场却开始盯自由现金流</div></div>
      <div class="ti"><div class="tn">02</div><div class="tt2">AI：从 Capex 到 ROI</div><div class="td">企业原话里的资本开支规模、回本周期与电力约束</div></div>
      <div class="ti"><div class="tn">03</div><div class="tt2">K 型消费与后市</div><div class="td">高端与低端的裂口，以及会强化／挑战这套逻辑的变量</div></div>
    </div>
  </div>

  {foot("封面 · Cover", "01")}
</section>''')

# ============================================================ P2 预期差
PAGES.append(f'''<section class="page">
  {MAST.format(r=INNER_R)}

  <div class="main">
    <div>
      <div class="sectlabel"><span class="no">01</span><span class="tt">最大预期差：指引在涨，市场却换了把尺子</span><span class="en">The Quality Shift</span></div>
      <div class="callout">
        <div class="q">"上调指引"创下 2010 年以来新高，订单与需求语言同步改善——说明这轮上调是<b>需求驱动而非成本驱动</b>。但摩根士丹利提醒：<b>光是 EPS 超预期已经不够了</b>，股票需要看到自由现金流指引与 EPS 一起上调。</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-t">中位数公司的盈利，已经从 <span class="accent">−11%</span> 拉回到 +14%</div>
      <div class="panel-sub">罗素 3000 中位数股票 EPS 同比增速。这条线衡量的不是巨头，而是"中间那家公司"——它在 2023 年四季度探底 −11%，此后一路回升，2Q26 预估达到 <b>+14%</b>，是 2021 年三季度以来最高。</div>
        {colchart(EPS, "罗素 3000 中位数股票 EPS 同比增速", w=680, h=252, unit="%")}
      <div class="src">来源：AlphaSense、Haver Analytics、Morgan Stanley Research。2026 年二季度为预估值（2026/2Qe）。</div>
    </div>

    <div class="split">
      <div class="panel" style="padding:15px 17px;">
        <div class="panel-t" style="font-size:13.5px;">资本开支回到 <span class="accent">两位数</span>，但峰值可能不远</div>
        <div class="panel-sub" style="margin-top:7px;">标普 500 中位数股票资本开支同比增速。从 2024 年三、四季度 1% 的谷底回到 <b>10%</b>；不过摩根士丹利指出，资本开支修正广度与"资本开支／销售额"因子都暗示，<b>增速的峰值可能就在不远处</b>。</div>
        {colchart(CAPEX, "标普 500 中位数股票资本开支同比增速", w=560, h=214, unit="%", lab_every=4, pad_l=40)}
        <div class="src">来源：Compustat、FactSet、Haver Analytics、Morgan Stanley Research。</div>
      </div>

      <div class="panel" style="padding:15px 17px;">
        <div class="panel-t" style="font-size:13.5px;">上调指引：<span class="accent">没有一个行业落在后面</span></div>
        <div class="panel-sub" style="margin-top:7px;">摩根士丹利把每类提及率放回它自己的历史区间，分成低／中／高位三档。"上调指引"这一行里，<b>有数据的 9 个板块全部落在高位档</b>；AI 也几乎全线高位，唯一的例外是<b>科技板块本身</b>（金框）——它一直在谈 AI，反而不算突出。</div>
        <div class="heat">
          {heat_map()}
        </div>
        <div class="heatkey">
          <span><i style="background:#1B2440;"></i>高位（历史前 33%）</span>
          <span><i style="background:#8FA0C8;"></i>中档</span>
          <span><i style="background:#DDE1EC;"></i>低位</span>
          <span><i style="background:#E6E2D8;"></i>样本不足</span>
        </div>
        <div class="src">来源：AlphaSense、Morgan Stanley Research（Exhibit 11 行业热力图），档位逐格比对原图。</div>
      </div>
    </div>

    <div class="callout green">
      <div class="q"><b>投资含义</b>&nbsp;不是所有上调都同等值钱。摩根士丹利判断市场正在发生"质量转向"——在 AI 内部，他们看到 <b>AI 采用者（Adopters）</b>的信号比纯粹的 <b>AI 使能者（Enablers）</b>更正面，轮动仍在继续。</div>
    </div>
  </div>

  {foot("最大预期差 · The Quality Shift", "02")}
</section>''')

# ============================================================ P3 AI / 资本开支 / 电力
PAGES.append(f'''<section class="page">
  {MAST.format(r=INNER_R)}

  <div class="main">
    <div>
      <div class="sectlabel"><span class="no">02</span><span class="tt">AI：从"花多少"到"什么时候回本"</span><span class="en">Capex → ROI → Power</span></div>
      <div class="kpirow">
        <div class="kpi"><div class="k">AI 提及率处于高位档</div><div class="v">10<span class="u"> / 11</span></div><div class="s">唯一的例外是<br><b>科技板块本身</b></div></div>
        <div class="kpi"><div class="k">上调指引处于高位档</div><div class="v g">9<span class="u"> / 9</span></div><div class="s">有数据的板块<br><b>全部在高位</b></div></div>
        <div class="kpi"><div class="k">利润率压力处于高位档</div><div class="v" style="color:var(--red)">3<span class="u"> / 9</span></div><div class="s">能源、金融、材料<br>整体<b>仅为中档</b></div></div>
        <div class="kpi"><div class="k">"更高利率"处于高位档</div><div class="v">0<span class="u"> / 10</span></div><div class="s">企业几乎不谈利率——<br>而<b>市场只盯着长端</b></div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-t">企业自己怎么说：<span class="accent">数字比形容词更有说服力</span></div>
      <div class="panel-sub">摘自 2026 年 7–8 月的财报电话会原文（经翻译整理，口径与原始引述一致）。</div>
      <div class="quos" style="margin-top:11px;">
        <div class="quo gold">
          <div class="qw"><span class="qc">Amazon</span><span class="qk">电商 / 云</span><span class="qd">2026.07.30</span></div>
          <div class="qb">"我们现在认为 2026 年现金资本开支约为 <b>2,200 亿美元</b>，高于此前约 2,000 亿的估计，主要是<span class="r">内存成本上升</span>推高了这个数字。但即便是这个金额，我们<b>仍然无法满足 2026 年的全部需求</b>，我相信 2027 年同样如此。事实上，我们手上已有的 2028 年需求令人震惊。"</div>
        </div>
        <div class="quo gold">
          <div class="qw"><span class="qc">Alphabet</span><span class="qk">互联网 / 云</span><span class="qd">2026.07.22</span></div>
          <div class="qb">"我们把 2026 年全年资本开支指引区间更新为 <b>1,950 亿至 2,050 亿美元</b>，此前为 1,800 亿至 1,900 亿。上调主要来自<b>产能交付的提速</b>，以满足不断增长的需求。我们继续预计 2027 年资本开支将显著增加。"</div>
        </div>
        <div class="quo green">
          <div class="qw"><span class="qc">Amazon</span><span class="qk">关于回本周期</span><span class="qd">ROI</span></div>
          <div class="qb">"服务器与网络设备平均<b>不到 3 年就能收回投资</b>，而这些服务器的使用寿命至少 5 到 6 年，我们大部分 AI 产能签的都是<b>至少 5 年期</b>的合约……我们在云计算的第一个时代做过同样的事，只是当时需求积累得更慢。<span class="g">AI 的利润率与回报，正在追踪核心云在同一发展阶段的轨迹，实际上还略微领先。</span>"</div>
        </div>
        <div class="quo">
          <div class="qw"><span class="qc">FIS</span><span class="qk">金融科技</span><span class="qd">2026.08.04</span></div>
          <div class="qb">"我们已有 <b>10 款 AI 产品</b>在市场上、<b>200 家客户</b>已上线、超过 <b>500 个</b>机会在管线中。工程侧吞吐提升 <span class="g">1.5–2 倍</span>、缺陷减少 30%；服务侧人工工单下降 <span class="g">70%</span>、分诊时间下降近 75%；员工侧超过 4 万名 AI Copilot 活跃用户、累计 1,600 万次辅助操作。"</div>
        </div>
        <div class="quo">
          <div class="qw"><span class="qc">Nasdaq</span><span class="qk">交易所与数据</span><span class="qd">2026.07.23</span></div>
          <div class="qb">"客户非常渴望用上我们提供的自动化，因为对他们而言这是<b>直接的投资回报</b>——能让内部效率更高……我们在 AI 能力的变现上<b>还处在非常早期的阶段</b>，但客户<span class="g">从免费转向付费订阅</span>的势头让我们很受鼓舞。"</div>
        </div>
        <div class="quo red">
          <div class="qw"><span class="qc">Baker Hughes</span><span class="qk">能源科技</span><span class="qd">2026.07.27</span></div>
          <div class="qb">"AI 与其他算力密集型负载的快速增长，正在带来电力需求的<b>阶跃式变化</b>，可靠、可扩展电力的获取<span class="r">正日益成为首要约束</span>……S&amp;P Global 预计数据中心用电需求到 2030 年将<b>年均增长 18%</b>，达到约 <b>1,850 太瓦时</b>——相当于印度到本十年末的全年用电量。"</div>
        </div>
      </div>
    </div>

    <div class="capband" style="padding:14px 18px;">
      <div class="h">2026 年资本开支指引：<span class="g">一场没有刹车的军备竞赛</span></div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:11px;">
        <div style="padding-right:14px;border-right:1px solid rgba(255,255,255,.13);"><div style="font-size:9.2px;color:#AEB4C6;font-weight:700;letter-spacing:.06em;">AMAZON</div><div style="font-family:var(--f-display);font-weight:600;font-size:23px;margin-top:6px;">$2,200<span style="font-size:11px;color:#AEB4C6;"> 亿</span></div><div style="font-size:8.6px;color:#C7CCDA;margin-top:4px;line-height:1.45;">较此前 2,000 亿上调</div></div>
        <div style="padding:0 14px;border-right:1px solid rgba(255,255,255,.13);"><div style="font-size:9.2px;color:#AEB4C6;font-weight:700;letter-spacing:.06em;">ALPHABET</div><div style="font-family:var(--f-display);font-weight:600;font-size:19px;margin-top:8px;white-space:nowrap;">$1,950–2,050<span style="font-size:10px;color:#AEB4C6;"> 亿</span></div><div style="font-size:8.6px;color:#C7CCDA;margin-top:4px;line-height:1.45;">较此前 1,800–1,900 亿上调</div></div>
        <div style="padding:0 14px;border-right:1px solid rgba(255,255,255,.13);"><div style="font-size:9.2px;color:#AEB4C6;font-weight:700;letter-spacing:.06em;">TESLA</div><div style="font-family:var(--f-display);font-weight:600;font-size:23px;margin-top:6px;">&gt; $250<span style="font-size:11px;color:#AEB4C6;"> 亿</span></div><div style="font-size:8.6px;color:#C7CCDA;margin-top:4px;line-height:1.45;">环比翻倍，未来 2–3 年继续增长</div></div>
        <div style="padding-left:14px;"><div style="font-size:9.2px;color:#AEB4C6;font-weight:700;letter-spacing:.06em;">INTEL</div><div style="font-family:var(--f-display);font-weight:600;font-size:23px;margin-top:6px;">&gt; $200<span style="font-size:11px;color:#AEB4C6;"> 亿</span></div><div style="font-size:8.6px;color:#C7CCDA;margin-top:4px;line-height:1.45;">2027 年将显著高于 2026</div></div>
      </div>
      <div class="capnote">应用材料（AMAT）称云服务商资本开支增速已"高于上季度提到的 30% 以上"，并预计 2027 年仍是强劲的一年；SK 海力士表示将继续扩产以应对强劲需求。来源：各公司财报电话会、Morgan Stanley Research。</div>
    </div>
  </div>

  {foot("AI 的重心转移 · Capex → ROI", "03")}
</section>''')

# ============================================================ P4 消费 + 后市
PAGES.append(f'''<section class="page">
  {MAST.format(r=INNER_R)}

  <div class="main">
    <div>
      <div class="sectlabel"><span class="no">03</span><span class="tt">K 型消费，与接下来该盯什么</span><span class="en">What Matters Next</span></div>
      <div class="callout navy">
        <div class="q">消费者健康度的语言"整体中性、环比没有实质恶化"——但把公司拆开看，<b>同一个月的美国消费者，被描述成了两种完全不同的人</b>。</div>
      </div>
    </div>

    <div class="split" style="grid-template-columns:1fr 1fr;">
      <div class="panel" style="padding:15px 17px;">
        <div class="panel-t" style="font-size:13.5px;">K 的上半支：<span style="color:var(--green)">在走强的那一侧</span></div>
        <div class="quos" style="margin-top:10px;">
          <div class="quo green">
            <div class="qw"><span class="qc">American Express</span><span class="qd">2026.07.24</span></div>
            <div class="qb">餐饮支出（最大的差旅娱乐品类）<span class="g">+10%</span>、航空 <span class="g">+10%</span>、全球 Amex 旅行预订 <span class="g">+22%</span>。"美国消费者支出增长 <b>11%</b>，是<b>剔除疫情影响后 2018 年一季度以来的最高水平</b>。千禧一代与 Z 世代仍是我们增长最快的客群。"</div>
          </div>
          <div class="quo green">
            <div class="qw"><span class="qc">Cardlytics</span><span class="qd">2026.08.05</span></div>
            <div class="qb">"总体上我们看到美国消费者支出在<b>走强</b>，尤其是相对本季度 5 月的小幅低谷……加油与多品类零售出现回升，可选消费在<b>部分细分人群中上升</b>。"</div>
          </div>
        </div>
      </div>

      <div class="panel" style="padding:15px 17px;">
        <div class="panel-t" style="font-size:13.5px;">K 的下半支：<span style="color:var(--red)">低端只认价值</span></div>
        <div class="quos" style="margin-top:10px;">
          <div class="quo red">
            <div class="qw"><span class="qc">Advantage Solutions</span><span class="qd">2026.08.05</span></div>
            <div class="qb">"我们上季度讨论的<b>K 型经济</b>主题仍在延续。中低收入家庭高度聚焦价值，购买越来越围绕促销和价格点来计划……<span class="r">价值导向的行为正在向各收入层扩散</span>。"</div>
          </div>
          <div class="quo red">
            <div class="qw"><span class="qc">Reynolds Consumer</span><span class="qd">2026.07.29</span></div>
            <div class="qb">"消费者背景与我们四月的描述基本一致，但<b>出现了一些新增的紧张迹象</b>。就业依然相对健康，但更高的借贷成本、<span class="r">上升的信用卡逾期率</span>以及家庭预算中实实在在的取舍，让消费者承受真实的支出压力。"</div>
          </div>
          <div class="quo red">
            <div class="qw"><span class="qc">Coca-Cola</span><span class="qd">2026.07.28</span></div>
            <div class="qb">"消费者仍在参与这个品类，但<b>低收入人群持续承压</b>，我们看到这真正关乎价值，而不只是价格。"</div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel" style="padding:14px 18px;">
      <div class="panel-t" style="font-size:13.5px;">2Q 财报季的基本面刻度</div>
      <div class="fcast" style="margin-top:10px;">
        <div class="fc"><div class="fk">中位数营收</div><div class="fv">+8<span class="u">%</span></div><div class="fs">罗素 3000</div></div>
        <div class="fc"><div class="fk">中位数 EPS</div><div class="fv">+14<span class="u">%</span></div><div class="fs">罗素 3000</div></div>
        <div class="fc"><div class="fk">中位数资本开支</div><div class="fv">+10<span class="u">%</span></div><div class="fs">罗素 3000</div></div>
        <div class="fc"><div class="fk">盈利修正广度</div><div class="fv">+24<span class="u">%</span></div><div class="fs">标普 500</div></div>
        <div class="fc"><div class="fk">上调指引提及率</div><div class="fv">~25<span class="u">%</span></div><div class="fs">2010 年来最高</div></div>
      </div>
    </div>

    <div class="watch">
      <div class="wbox up">
        <div class="wh">◤ 会强化这套逻辑</div>
        <ul>
          <li><b>订单簿与需求语言环比改善</b>——指引上调是需求驱动，而非成本转嫁</li>
          <li>衰退与"周期见顶"的语言依然稀少，<b>几乎没有公司预警近期下行</b></li>
          <li>劳动力语言中性：招聘与裁员提及大致互相抵消；小企业招聘意愿保持稳定</li>
          <li>AI 采用者的信号比纯粹的使能者更正面，<b>轮动仍在 AI 内部继续</b></li>
        </ul>
      </div>
      <div class="wbox dn">
        <div class="wh">◤ 会挑战这套逻辑</div>
        <ul>
          <li>成本与投入价格提及率偏高，<b>多家公司提示持续价格压力的风险</b></li>
          <li>利润率压力在能源、金融、<b>材料</b>三个板块已进入历史高位档</li>
          <li>油价波动仍是隐忧，<b>若原油持续走高，影响会显著放大</b></li>
          <li>资本开支修正广度与 Capex/Sales 因子暗示<b>增速峰值可能不远</b></li>
          <li>小企业提价意愿（NFIB）较三个月前<b>继续走高</b>，通胀黏性未消</li>
        </ul>
      </div>
    </div>

    <div class="track-chips">
      <span class="tl">重点跟踪</span>
      <span class="tchip">FCF 指引与 EPS 是否同步</span>
      <span class="tchip">"AI 与 ROI""变现"提及率</span>
      <span class="tchip">数据中心电力</span>
      <span class="tchip">长端收益率</span>
      <span class="tchip">非农与美联储路径</span>
      <span class="tchip">NFIB 提价意愿</span>
    </div>

    <div>
      <div class="navband">
        <div class="nh">本期精选：摩根士丹利 2026.08.24 三篇 <span class="nb">The Port Series</span></div>
        <div class="ng">
          <div class="ni"><div class="nn">01</div><div class="nt">Buybacks, Not Hikes</div><div class="nd">跨资产聚焦：被抛售的长端，回报风险比却排在前列</div></div>
          <div class="ni on"><div class="nn">02</div><div class="nt">What Are Companies Saying?</div><div class="nd">美股策略：上调指引创新高，市场却不再为 EPS 买单</div></div>
          <div class="ni"><div class="nn">03</div><div class="nt">Alphabet · TPU</div><div class="nd">近 2,000 亿美元的 TPU 外销，EPS 却只上修 1%–2%</div></div>
        </div>
      </div>
      <div class="disc">本文基于 Morgan Stanley 于 2026-08-24 发布的《US Equity Strategy: What Are Companies Saying?》（Michael Wilson、Nicholas Lentini、Andrew Pauker、Michelle Weaver、Diane Ding）整理，所有数字、提及率与公司引述均以原报告为准，公司原话经翻译整理。本可视化由 THE PORT 编辑制作，仅供信息参考与交流，不构成任何投资建议或要约；投资有风险，决策须谨慎。</div>
    </div>
  </div>

  {foot("结论与后市 · What Matters Next", "04")}
</section>''')

HTML = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<title>摩根士丹利 美股策略 · What Are Companies Saying? · 研报精华</title>\n'
        '<link rel="stylesheet" href="styles.css">\n</head>\n<body>\n\n'
        + "\n\n".join(PAGES) + "\n\n</body>\n</html>\n")

open("d2_companies.html", "w", encoding="utf-8").write(HTML)
print("d2_companies.html", len(HTML), "bytes")
