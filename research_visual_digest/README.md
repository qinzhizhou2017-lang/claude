# 宁德时代 CATL · 2Q26 研报精华（可视化精华版）

一份面向投资者与财经读者的 **4 页 A4 可视化精华 PDF**，基于 J.P. Morgan 亚太股票研究
《CATL: 2Q26 result in-line; all eyes on 2027 demand outlook》（2026-07-25，分析师 Rebecca Wen）
提炼、重新编辑与可视化而成。

## 交付物

- **`宁德时代CATL_2Q26研报精华_ThePort.pdf`** — 最终成品（4 页，A4，字体全部内嵌，二维码经解码验证可扫描）。

## 内容结构

| 页 | 主题 | 核心 |
|----|------|------|
| 01 | 封面 + 一句话判断 | 市场在卖毛利率，真正的护城河纹丝未动；核心结论卡片 |
| 02 | 最大预期差 | ASP 腰斩而单瓦时净利润四年一条水平线；1Q22 剧本重演；同业对比 |
| 03 | 增长引擎 | 销量/产能/现金流 KPI；全球份额攀升；资本回报与三大新增长极 |
| 04 | 结论与后市 | A/H 目标价、强化与挑战逻辑、重点跟踪 + 二维码 |

所有数字、评级、目标价与预测均以原研报为准。本可视化仅供信息参考与交流，不构成投资建议。

## 复现

`src/` 包含完整源文件（`report.html` + 字体 + 二维码）。用无头 Chromium 渲染即可：

```bash
chromium --headless=new --no-sandbox --disable-gpu \
  --no-pdf-header-footer --allow-file-access-from-files \
  --run-all-compositor-stages-before-draw --virtual-time-budget=8000 \
  --print-to-pdf=宁德时代CATL_2Q26研报精华_ThePort.pdf \
  "file://$PWD/src/report.html"
```

字体：Inter（OFL）、Fraunces（OFL）、Noto Serif / Sans CJK SC（系统安装，OFL）。
