# 三份投行研报 · 可视化精华（2026.08.19–08.20）

摩根士丹利与摩根大通各 3 页、巴克莱 4 页，合计 10 页 A4 PDF。使用 `.claude/skills/yanbao-visual-digest` 技能的设计系统
（暖纸底 + 藏青 / 信号红 / 深绿 + 思源宋黑 + Inter / Fraunces）。

## 成品

| 文件 | 研报 | 页数 |
| --- | --- | --- |
| `pdf/摩根士丹利_亚洲EM股票策略2026秋季更新_研报精华_ThePort.pdf` | Morgan Stanley, *Asia EM Equity Strategy 2026 Fall Update*（2026-08-20） | 3 |
| `pdf/摩根大通_FlowsLiquidity_谁在为AI买单_研报精华_ThePort.pdf` | J.P. Morgan, *Flows & Liquidity: Are large enterprises spending $1.5tr on AI already?*（2026-08-20） | 3 |
| `pdf/巴克莱_SpaceX信用首次覆盖_研报精华_ThePort.pdf` | Barclays, *SpaceX (SPCX): No Free Launch; Initiate at OW*（2026-08-19） | 4 |
| `pdf/全球投行研报精华_三份合集_10页_ThePort.pdf` | 以上三份合并 | 10 |

## 每份的主线

- **摩根士丹利**：跌的是杠杆，不是盈利。七月回调源于去杠杆与仓位出清，EM 与日本盈利预期同时上修到牛市情景；
  维持「资本开支 > 消费」，但设出罕见宽的牛熊区间（TOPIX +18% / −37%）。
- **摩根大通**：别问 AI 赚不赚钱，先看谁在付钱。用大企业成本表反推需求——未来 12 个月约 1.7 万亿美元的
  企业 AI 支出，对上 AI 生态 1.6 万亿的收入运行率与 7.5 万亿的累计资本开支。
- **巴克莱**：杠杆不是问题，现金流才是。SPCX 每年烧 750 亿美元自由现金流，但外部融资需求要到 3Q27 才出现，
  是一个六个月跑道最干净的战术性多头。第 3 页单独展开「三台引擎与飞轮」——太空压低入轨成本、连接把覆盖变现、
  AI 叠成新的算力层，以及 2029 年轨道算力上天把发射次数推高三倍的连锁反应；第 4 页收在交易、评级与风险。

## 重新渲染

```bash
cd src
bash ../../../.claude/skills/yanbao-visual-digest/scripts/render.sh r1_ms.html ../pdf/r1.pdf
```

`style.css` 为共用设计系统（模板 CSS + 表格 / 堆叠柱 / 牛熊区间 / 时间轴 / 引擎卡 / 评级带等组件）。
`measure.py <file.html>` 用无头 Chromium 量出每页 `.main` 的可用高度与实际占用（slack 为负即溢出），
排版增删内容时先跑它，比反复肉眼比对快得多。
`qr.png` 为公众号二维码，已用 pyzbar 在 150dpi 与 300dpi 验证可扫。

## 免责

所有数字、评级、目标价与预测均以各家原报告为准；本可视化仅供信息参考与交流，不构成任何投资建议。
