# THE PORT · 摩根士丹利 2026.08.24 研报可视化精华（三篇合辑）

用 `yanbao-visual-digest` 技能，把三份 Morgan Stanley 研报各自提炼成 4 页 A4 的可视化精华版，
并合并为一份 12 页 PDF。二维码只出现在合辑最后一页（第 12 页）。

## 交付物

| 文件 | 说明 |
| --- | --- |
| `THE_PORT_MorganStanley_20260824_12p.pdf` | **12 页合辑**（3 篇 × 4 页），二维码仅在第 12 页 |
| `png/01_CrossAsset_BuybacksNotHikes_p1–p4.png` | 第 1 篇 4 页，220 dpi（1818×2573） |
| `png/02_USEquity_WhatAreCompaniesSaying_p1–p4.png` | 第 2 篇 4 页 |
| `png/03_Alphabet_TPU_p1–p4.png` | 第 3 篇 4 页 |
| `0X_..._4p.pdf` | 每篇单独的 4 页 PDF |

## 三篇的主线

1. **Cross-Asset Spotlight: Buybacks, Not Hikes**（Serena Tang 等）——30 年美债回到 2007 年高位、
   对冲基金净空 −32%，而按 2Q27 基准情景的「回报／风险」排序，前四名全是政府债券。
2. **What Are Companies Saying?**（Michael Wilson 等）——「上调指引」提及率创 2010 年来新高，
   但市场已经换了把尺子：只有 EPS 超预期不够，要看到 FCF 指引同步上调。
3. **Alphabet: $200bn of 1P TPU Revenue**（Brian Nowak）——三年近 2,000 亿美元的 TPU 外销，
   只换来 EPS 上修 1%／2%；真正的重估催化剂是 Gemini 4。

## 复现

```bash
bash ../../.claude/skills/yanbao-visual-digest/scripts/setup.sh   # 依赖与思源 CJK 字体
python3 build1.py && python3 build2.py && python3 build3.py       # 生成 HTML
bash ../../.claude/skills/yanbao-visual-digest/scripts/render.sh d1_crossasset.html d1.pdf
```

`build*.py` 生成 HTML（含手搓 SVG 图表），`styles.css` 是从技能模板抽出的设计系统 + 本系列新增组件
（`.quo` 引用卡、`.scen` 情景表、`.rank` 带零线排序条、`.navband` 系列导航条）。

## 核对

所有数字、评级、目标价、预测均逐条比对原研报（Exhibit 编号标注在每张图下方）。第二轮交叉复核
把关键表格渲染成图片逐格核对（Exhibit 1 的列映射、Exhibit 5 的机架口径、Exhibit 11 的档位、
Alphabet Risk Reward 页的共识均值），改正了以下各处：

| 位置 | 原写法 | 更正 |
| --- | --- | --- |
| 第 3 篇 P2 | v8/v9「单价」170 万／190 万美元 | 该数字是 Alphabet 的**机架采购成本**（Exhibit 5 注为 MS Est. Rack Cost），按 30% 毛利率加价后才是收入 |
| 第 2 篇 P2–P3 | 行业热力图用 0–100 数值柱 | 原报告只显示低／中／高三档色阶，改为同构的三档热力图，档位逐格比对原图 |
| 第 1 篇 P1 | 标题「最好的回报风险比也在这里」 | UST 10Y 的回报/风险为 1.30，排第 4；改为「回报风险比前四全是国债」 |
| 第 1 篇 P1 | 「长端的解药不是加息」 | 原报告未作此表述，改为「指向的是财政部的工具箱」 |
| 第 1 篇 P1 | US currency policy 译作「货币政策」 | 应为**汇率政策** |
| 第 1 篇 P1 | 黄金标签「单周最强」 | 改用报告原话「波动 +2.3 个标准差」 |
| 第 1 篇 P4 | 「通胀重新失控是真正对手」 | 原报告未说明熊市情景成因，改为就情景本身陈述 |
| 第 2 篇 P1–P2 | 「连续第 6 季改善」 | EPS 序列在 1Q25、4Q25 有回落，改为「2021 年三季度以来最高」 |
| 第 2 篇 P2 | 「2024 年三季度 1% 的谷底」 | 三、四季度均为 1% |
| 第 3 篇 P4 | 溢价约 20% 直接陈述 | 原报告三处口径不一（正文 ~20%、Exhibit 7 为 19%、Risk Reward 页 ~35%），改为注明出处并列出 Exhibit 7 数值 |
| 第 3 篇 P4 | 上行空间 +16% | 注明取自 Risk Reward 页对 $344.82 的标注；正文作「约 15%」，Exhibit 6 列为 14% |
| 第 1 篇 P3 | 黄金单周流入高于商品合计 | 加注：能源同期净流出 1.4 亿，且分类不完全穷尽 |

原报告本身存在若干内部不一致（黄金现价 Exhibit 1 为 4,603、Exhibit 5 图示为 4,645；GOOGL 上行
空间 14%／15%／16% 三种口径），本精华版统一采用其中一处并标明来源，不做调和。

二维码沿用原始微信二维码，未做任何变形；已用 pyzbar 在 150 dpi 与 300 dpi 各解码验证，
并确认 1–11 页不含二维码。市场数据截至 2026 年 8 月 21 日。本可视化仅供信息参考，不构成投资建议。
