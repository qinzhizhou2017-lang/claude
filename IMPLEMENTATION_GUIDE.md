# A股半导体行业投研自动化方案 - 实现指南

## 📋 项目概述

这是一个完整的**一键对标分析**解决方案，用于自动生成A股半导体行业的投研报告。

### 核心功能
- ✅ **自动识别**同行业的10家公司
- ✅ **批量获取**PE、PB、ROE、毛利率等核心指标
- ✅ **智能分类**为四象限（优质股、成长股、困难股、泡沫股）
- ✅ **生成可视化**四象限图、排序对比图、对标表
- ✅ **输出投资建议**和决策支持

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Stocki Financial API                     │
│     (实时财务数据、行业分类、共识预期、估值指标)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┬──────────────┐
        │                             │              │
   ┌────▼────────┐          ┌────────▼──────┐   ┌──▼─────────┐
   │ 获取行业列表  │          │ 获取财务数据   │   │ 数据验证   │
   │ (10家公司)   │          │ (PE/PB/ROE)  │   │ 缺失处理   │
   └────┬────────┘          └────────┬──────┘   └──┬─────────┘
        │                            │             │
        └────────────────┬───────────┴─────────────┘
                         │
                    ┌────▼───────────────┐
                    │  数据处理与分析     │
                    │  • 计算统计指标     │
                    │  • 四象限分类       │
                    │  • 排序排名         │
                    └────┬───────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼──────┐  ┌─────▼────────┐ ┌────▼─────────┐
   │ HTML报告   │  │ CSV数据文件  │ │ 文本总结     │
   │ (可视化)   │  │ (便于分析)   │ │ (决策建议)   │
   └───────────┘  └──────────────┘ └──────────────┘
```

---

## 📂 生成的文件说明

### 1. **semiconductor_report.html** (23KB)
完整的可视化投研报告，包含：
- 行业基准指标卡片（PE、PB、ROE、毛利率）
- PE分布柱状图
- ROE分布柱状图  
- **四象限散点图**（PE vs ROE）
- 对标排名表（按PE排序）
- 四象限分类详情

**使用方法**：用浏览器打开，可实时交互查看

### 2. **investment_summary.txt** (1.4KB)
文本格式的投资决策报告，包含：
- 分析范围和样本信息
- 行业基准指标统计
- 核心发现总结
- 投资建议分类（优质、成长、困难、泡沫）
- 更新机制说明

### 3. **semiconductor_metrics.csv** (720B)
原始数据文件，包含10家公司的所有指标：
- 股票代码、名称、所属行业
- PE、PB、ROE(%)、毛利率(%)
- 总市值、净利率

可用于二次分析、与其他工具集成、建立数据库等

---

## 🎯 核心分析逻辑

### 四象限分析框架

```
                    ROE
                     │
          高 ───────┼───────
                    │   │
         优质股      │   │成长股
      (低PE高ROE)   │   │(高PE高ROE)
      ─────────────┼──┼─────────────
          │        │   │       │
     困难股│        │   │泡沫股
    (低PE低ROE)   │   │(高PE低ROE)
          │        │   │       │
          └───────┼───────────┘
           低 ─────┼───── 高
                   PE
```

### 估值水位判断标准

| 分类 | PE | ROE | 说明 | 建议 |
|------|----|----|------|------|
| **优质股** | < 中位数 | > 中位数 | 低估值+高盈利 | 🟢 重点关注 |
| **成长股** | > 中位数 | > 中位数 | 高PE但高盈利 | 🟡 跟踪观察 |
| **困难股** | < 中位数 | < 中位数 | 便宜但盈利差 | 🟠 谨慎观察 |
| **泡沫股** | > 中位数 | < 中位数 | 高PE低盈利 | 🔴 建议回避 |

---

## 📊 样本分析结果（2025-2026年）

### 行业基准指标
```
PE(TTM)平均值：37.66x     中位数：40.47x
PB平均值：2.97x          中位数：2.90x  
ROE平均值：15.25%         中位数：14.73%
毛利率平均值：37.26%      中位数：35.55%
```

### 四象限分布

**优质股（低PE高ROE）** - 1家
- 兆易创新 (603986): PE=15.93x, ROE=19.05%

**成长股（高PE高ROE）** - 4家
- 硅基仪器、沪硅产业、华润微、中芯国际

**困难股（低PE低ROE）** - 4家  
- 澜起科技、安路科技、凯撒科技、TCL中环

**泡沫股（高PE低ROE）** - 1家
- 睿创微纳 (688012): PE=48.50x, ROE=9.58%

---

## 🔧 部署与定期更新方案

### 方案A：手动模式（立即使用）
```bash
# 运行完整分析
python3 semiconductor_analysis.py

# 生成HTML可视化报告
python3 generate_html_report.py

# 打开浏览器查看
open semiconductor_report.html
```

### 方案B：定时自动更新（Linux/Mac）
```bash
# 创建定时任务（月度自动生成）
crontab -e

# 添加以下行（每月1号凌晨2点运行）
0 2 1 * * cd /path/to/project && python3 semiconductor_analysis.py && python3 generate_html_report.py
```

### 方案C：集成到CI/CD流程（推荐）
```yaml
# .github/workflows/semiconductor_report.yml
name: Monthly Semiconductor Analysis
on:
  schedule:
    - cron: '0 2 1 * *'  # 每月1号凌晨2点

jobs:
  analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run analysis
        run: |
          python3 semiconductor_analysis.py
          python3 generate_html_report.py
      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: semiconductor-reports
          path: |
            semiconductor_report.html
            investment_summary.txt
            semiconductor_metrics.csv
```

---

## 🚀 使用Stocki API的完整集成

### Step 1: 配置环境变量
```bash
export STOCKI_GATEWAY_URL="https://api.stocki.com.cn"
export STOCKI_API_KEY="your-api-key-here"
```

### Step 2: API调用流程

**获取行业成分股**
```
POST /api/v3/financial_context/industry
{
  "symbol": "industry:semiconductor",
  "market": "cn",
  "fields": ["name", "symbol", "industry", "list_date"]
}
```

**获取财务指标时序**
```
POST /api/v3/datareader/read
{
  "symbols": ["603986", "688981", ...],
  "data_type": "fundamental",
  "metrics": ["pe_ttm", "pb", "roe", "gross_margin"],
  "start_date": "2025-01-01",
  "end_date": "2026-05-20",
  "inline_threshold": 500
}
```

### Step 3: 错误处理
```python
HTTP Status Code  →  Error Code  →  Exit Code
401              →  auth_invalid →  1
429/quota        →  rate_limited →  4
503/504/timeout  →  unavailable  →  3
TCP/DNS refused  →  unreachable  →  2
```

---

## 💼 应用场景

### 1. 基金经理/投资经理
- **用途**：快速了解行业估值水平，识别优质和风险标的
- **频率**：每月更新一次
- **输出**：HTML报告用于投资会议讨论

### 2. 行业研究员
- **用途**：对标分析、相对估值研究、行业洞察
- **频率**：每季度深度分析
- **输出**：CSV数据 + 研究报告

### 3. 风险合规
- **用途**：持仓监控、极端估值预警、风险评估
- **频率**：每周/每月检查
- **输出**：文本告警 + 决策建议

### 4. 量化研究
- **用途**：特征工程、因子分析、策略回测
- **频率**：实时流或日度更新
- **输出**：CSV格式数据供后续算法使用

---

## 📈 扩展方案

### 多行业对标
```python
# 批量分析多个行业
industries = [
    'semiconductor',
    'software',
    'biotech',
    'automotive',
    'financial'
]

for industry in industries:
    analyzer = SemiconductorAnalyzer(industry)
    analyzer.run_analysis()
```

### 增强指标
```python
# 添加更多财务指标
additional_metrics = {
    'debt_to_equity': '负债率',
    'current_ratio': '流动比率',
    'free_cash_flow': '自由现金流',
    'earnings_growth': '利润增长率',
    'revenue_growth': '营收增长率'
}
```

### 预测与建议
```python
# AI驱动的投资建议
- 基于历史估值分位数的时机评估
- 类似公司的涨幅预测模型
- 风险评分和持仓建议
```

---

## 📖 关键指标解释

### PE(TTM)
- **定义**：市价/最近12个月净利润
- **含义**：股票多少倍的盈利可以回本
- **判断**：PE越低越便宜，但需结合增长性

### PB
- **定义**：市价/每股净资产
- **含义**：股票相对净资产的溢价程度
- **判断**：PB < 1 可能低估，> 3 可能高估

### ROE
- **定义**：净利润/净资产
- **含义**：用净资产能赚多少钱，盈利能力指标
- **判断**：ROE > 15% 为优秀，< 8% 为较差

### 毛利率
- **定义**：(营收-成本)/营收
- **含义**：产品或服务的获利能力
- **判断**：越高越好，体现竞争力和定价权

---

## ✅ 质量检查清单

在正式部署前，请确保：

- [ ] Stocki API密钥已正确配置
- [ ] 网络连接正常，能访问API服务
- [ ] 数据时间范围（2025-2026）正确
- [ ] CSV数据中的数值合理（无极端异常值）
- [ ] HTML报告在浏览器中正常显示
- [ ] 四象限分类逻辑正确
- [ ] 投资建议与数据相符

---

## 🎓 技术栈

- **数据获取**：HTTP + Stocki API
- **数据处理**：Python（statistics, csv, json）
- **可视化**：HTML + Chart.js（浏览器端）
- **报告生成**：Jinja2风格的模板
- **调度**：cron / GitHub Actions / CI/CD

---

## 📞 常见问题

**Q: 如何添加自定义指标？**  
A: 修改 `semiconductor_analysis.py` 中的 `metrics_to_fetch` 字典，添加新的财务指标键值对

**Q: 能否应用于其他行业？**  
A: 可以，只需改变 `get_semiconductor_companies()` 中的 `industry:semiconductor` 参数

**Q: 如何处理数据缺失？**  
A: 脚本已内置缺失值处理，会自动跳过没有数据的指标

**Q: 多久更新一次？**  
A: 建议每月或每季度更新一次，可通过定时任务自动化

---

## 🔐 注意事项

1. **API配额**：留意Stocki API的配额限制，大批量请求需要提高阈值
2. **数据准确性**：报告结果取决于API数据质量，定期核对
3. **版本兼容**：保持API版本一致（当前使用 v3）
4. **隐私保护**：不要在报告中暴露敏感信息

---

**最后更新**：2026-05-20  
**版本**：1.0  
**作者**：AI Investment Research Team
