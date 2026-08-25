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

- 所有数字、评级、目标价、预测均逐条比对原研报（含 Exhibit 编号，标注在每张图下方）。
- 二维码沿用原始微信二维码，未做任何变形；已用 pyzbar 在 150 dpi 与 300 dpi 各解码验证，
  并确认 1–11 页不含二维码。
- 市场数据截至 2026 年 8 月 21 日。本可视化仅供信息参考，不构成投资建议。
