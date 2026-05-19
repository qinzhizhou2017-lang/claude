# A股港股量化选股回测系统 - 项目总结

## 📌 项目概述

这是一个完整的**量化投资选股与回测分析系统**，用于在A股和港股市场中自动筛选满足特定量化条件的股票，并进行历史回测分析。

### 核心价值
✨ 自动化的选股流程
✨ 多因子量化策略
✨ 完整的回测分析
✨ 交互式可视化报告

---

## 📊 核心策略

### 三因子筛选模型

```
选股公式：
(PB分位 ≤ 30%) ∩ (RSI > 60) ∩ (EPS修正向上)
```

| 因子 | 指标 | 条件 | 含义 |
|------|------|------|------|
| **估值** | PB（市净率） | 历史30%分位以下 | 便宜的股票 |
| **动量** | RSI（相对强弱） | 过去6个月 > 60 | 市场强势 |
| **修正** | EPS共识预期 | 过去30天向上 | 基本面改善 |

### 投资组合构建
- **类型**：等权重组合
- **调仓**：每月末最后一个交易日
- **市场**：A股 + 港股

---

## 📁 项目文件清单

### 核心脚本

#### 1️⃣ `stock_quant_backtest.py` (主程序)
**功能**：完整的选股和回测流程
```python
main函数流程：
1. 获取股票列表 (A股+港股)
2. 按三因子筛选
3. 获取历史价格数据
4. 进行月度等权回测
5. 计算性能指标
6. 输出CSV结果
```

**输出文件**：
- `backtest_results.csv` - 月度净值数据
- `screened_stocks.csv` - 筛选出的股票

**API调用**：
```
5个API端点：
- /api/v3/market/stock_list          (获取股票列表)
- /api/v3/financial_context/read     (PB估值分位)
- /api/v3/datareader/read            (RSI技术指标)
- /api/v3/datareader/read            (EPS共识预期)
- /api/v3/datareader/read            (价格历史)
```

---

#### 2️⃣ `visualize_backtest.py` (可视化脚本)
**依赖**：pandas, numpy, matplotlib

**功能**：生成回测结果图表
```
输出内容：
1. 组合净值曲线图
2. 最大回撤曲线图
3. 月度收益率直方图
4. 性能指标汇总表
```

**输出文件**：
- `backtest_chart.png` - 4合1图表
- `backtest_summary.csv` - 指标汇总

**使用方式**：
```bash
pip install pandas numpy matplotlib
python3 visualize_backtest.py
```

---

#### 3️⃣ `generate_demo_results_simple.py` (演示数据生成)
**特点**：无外部依赖

**功能**：生成演示用的回测数据
```
模拟数据：
- 24个月的净值曲线
- 14只筛选股票
- 完整的性能指标
```

**使用方式**：
```bash
python3 generate_demo_results_simple.py
```

---

### 文档与报告

#### 📄 `backtest_report.html` (交互式报告)
**特点**：独立的HTML文件，无需任何依赖

**包含内容**：
```html
✓ 策略概述
✓ 性能指标卡片
✓ 交互式图表 (Chart.js)
✓ 筛选结果详情
✓ 详细数据表格
✓ 关键指标汇总
```

**使用方式**：
```bash
# 直接在浏览器打开
open backtest_report.html
firefox backtest_report.html
```

**文件大小**：~50KB (自包含，包含所有CSS和JavaScript)

---

#### 📖 `QUANT_BACKTEST_README.md`
**内容**：
- 项目概述
- 环境配置
- 使用方法
- 文件说明
- 故障排除
- 性能注意事项

**长度**：~1000行

---

#### 📖 `IMPLEMENTATION_GUIDE.md` (本指南)
**内容**：
- 完整的实现细节
- 选股策略详解
- API调用说明
- 回测方法论
- 自定义扩展
- 风险提示

**长度**：~1500行

---

#### 📖 `PROJECT_SUMMARY.md` (项目总结)
当前文件，提供快速参考。

---

### 生成的数据文件

#### `backtest_results.csv`
```csv
Date,Portfolio_Value
2024-05-31,1.000000
2024-06-28,1.013271
...
2026-04-30,1.261879
```
**用途**：月度净值数据，用于计算收益率和回撤

---

#### `screened_stocks.csv`
```csv
Symbol,Stock_Count
600519,14
600036,14
...
6078.HK,14
```
**用途**：筛选出的股票列表

---

#### `backtest_summary.csv`
```csv
指标,数值
总收益率(%),28.45
年化收益率(%),12.67
...
最大回撤(%),-18.93
```
**用途**：性能指标汇总

---

## 🚀 快速使用指南

### 场景1：完整流程（需要API）

```bash
# 第一步：设置API环境变量
export STOCKI_GATEWAY_URL="https://api.stocki.com.cn"
export STOCKI_API_KEY="your-api-key"

# 第二步：运行主程序（选股+回测）
python3 stock_quant_backtest.py

# 输出：
# - backtest_results.csv
# - screened_stocks.csv

# 第三步：生成图表
python3 visualize_backtest.py

# 输出：
# - backtest_chart.png
# - backtest_summary.csv
```

---

### 场景2：查看演示结果（无需API）

```bash
# 第一步：生成演示数据
python3 generate_demo_results_simple.py

# 输出：
# - backtest_results.csv (演示数据)
# - screened_stocks.csv (演示数据)
# - backtest_summary.csv (演示数据)

# 第二步：在浏览器打开报告
open backtest_report.html

# 第三步（可选）：生成PNG图表
python3 visualize_backtest.py
# 输出：
# - backtest_chart.png
```

---

### 场景3：只查看HTML报告

```bash
# backtest_report.html 已经包含示例数据
# 直接打开即可查看完整报告
open backtest_report.html

# 包含内容：
# - 实时计算的图表
# - 完整的数据表格
# - 性能指标
# - 策略说明
```

---

## 📈 演示结果

### 回测绩效

```
┌────────────────────────────┐
│      回测绩效总览          │
├────────────────────────────┤
│ 总收益率      : +26.19%    │
│ 年化收益率    : +12.67%    │
│ 年化波动率    : 14.82%     │
│ 夏普比率      : 0.72       │
│ 最大回撤      : -20.82%    │
│ 回测周期      : 24个月     │
│ 开始日期      : 2024-05-31 │
│ 结束日期      : 2026-04-30 │
└────────────────────────────┘
```

### 筛选结果

```
符合条件的股票：14只

A股 (9只):
✓ 600519 贵州茅台 - 低估+强势+EPS↑
✓ 600036 招商银行 - 低估+强势+EPS↑
✓ 601398 工商银行 - 低估+强势+EPS↑
✓ 600000 浦发银行 - 低估+强势+EPS↑
✓ 600016 民生银行 - 低估+强势+EPS↑
✓ 601988 中国银行 - 低估+强势+EPS↑
✓ 600031 三一重工 - 低估+强势+EPS↑
✓ 601857 中国石油 - 低估+强势+EPS↑
✓ 600585 海螺水泥 - 低估+强势+EPS↑

港股 (5只):
✓ 0700.HK 腾讯控股 - 低估+强势+EPS↑
✓ 0941.HK 中国移动 - 低估+强势+EPS↑
✓ 9988.HK 阿里巴巴 - 低估+强势+EPS↑
✓ 3690.HK 美团 - 低估+强势+EPS↑
✓ 6078.HK JD.com - 低估+强势+EPS↑
```

---

## 🔧 核心技术

### 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **数据源** | Stocki API | 机构级财务数据 |
| **后端处理** | Python 3.8+ | 数据处理和计算 |
| **数据处理** | Pandas/NumPy | 时间序列分析 |
| **可视化** | Matplotlib | 生成PNG图表 |
| **报告** | HTML5 + Chart.js | 交互式网页报告 |

### API集成

```
Stocki API (https://api.stocki.com.cn)
├── /api/v3/market/stock_list              → 股票列表
├── /api/v3/financial_context/read         → 估值分位
├── /api/v3/datareader/read                → 技术指标
│   ├── data_type: "indicator", metrics: ["rsi_14"]
│   └── data_type: "estimate", metrics: ["eps_consensus"]
└── /api/v3/datareader/read                → 价格历史
    └── data_type: "price", OHLCV数据
```

---

## 📊 数据流图

```
┌──────────────────┐
│  A股 & 港股池    │
│  (全量股票)      │
└────────┬─────────┘
         │
         ↓
┌──────────────────────┐
│  获取四类数据         │
├──────────────────────┤
│ 1. PB估值分位        │
│ 2. RSI技术指标       │
│ 3. EPS共识预期       │
│ 4. 历史价格数据      │
└────────┬─────────────┘
         │
         ↓
┌──────────────────────┐
│  三因子筛选           │
├──────────────────────┤
│ PB ≤ 30分位 ✓        │
│ RSI > 60 ✓           │
│ EPS向上修正 ✓        │
└────────┬─────────────┘
         │
         ↓
┌──────────────────────┐
│  筛选结果             │
│  N只目标股票         │
└────────┬─────────────┘
         │
         ↓
┌──────────────────────┐
│  等权组合回测         │
├──────────────────────┤
│ 权重：1/N            │
│ 调仓：月度末         │
│ 时间：过去2年        │
└────────┬─────────────┘
         │
         ↓
┌──────────────────────┐
│  性能指标计算         │
├──────────────────────┤
│ ✓ 总收益率           │
│ ✓ 年化收益率         │
│ ✓ 年化波动率         │
│ ✓ 夏普比率           │
│ ✓ 最大回撤           │
└────────┬─────────────┘
         │
         ↓
┌──────────────────────┐
│  输出报告             │
├──────────────────────┤
│ CSV表格数据          │
│ HTML交互式报告       │
│ PNG图表              │
└──────────────────────┘
```

---

## 💡 自定义建议

### 调整筛选条件

```python
# 更严格的估值条件
if pb_percentile > 20:  # 改为20%分位
    continue

# 更高的动量阈值
if rsi_latest <= 70:  # 改为70
    continue

# 更长的EPS观察窗口
get_eps_revisions(symbol, days=60)  # 改为60天
```

### 改变调仓频率

```python
# 季度调仓
backtest_strategy(screened, price_df, rebalance_freq="Q")

# 半年调仓
backtest_strategy(screened, price_df, rebalance_freq="2Q")
```

### 添加新因子

```python
# 例如：ROE > 某阈值
roe_data = get_roe_data(symbol)
if roe_data.get("roe") < 10:  # ROE < 10%
    continue
```

---

## ⚠️ 重要风险提示

### 局限性

❌ **不考虑交易成本**：实际成本会降低收益

❌ **完全流动性假设**：大额交易可能无法按计划成交

❌ **参数优化偏差**：条件可能存在过度优化

❌ **时间错配**：实际交易信息会有延迟

### 使用建议

⚠️ 本框架仅供学习和研究使用

⚠️ 不构成任何投资建议

⚠️ 实盘交易前需专业咨询

⚠️ 使用者自行承担投资风险

---

## 📞 获取帮助

### 常见问题

**Q: 脚本运行很慢**
A: 这是正常的，因为需要：
   - 获取所有股票列表
   - 为每只股票获取4类数据
   - 建议使用演示数据先测试

**Q: 没有股票通过筛选**
A: 可能原因：
   - 市场当前没有同时满足三个条件的股票
   - 条件过于严格
   - 建议调整条件或查看API数据

**Q: 能否修改策略参数**
A: 完全可以，见 `IMPLEMENTATION_GUIDE.md` 中的"自定义与扩展"部分

---

## 📚 更多资源

### 文档
- `QUANT_BACKTEST_README.md` - 使用手册
- `IMPLEMENTATION_GUIDE.md` - 实现指南
- `backtest_report.html` - 可视化报告

### 外部参考
- [Stocki API文档](https://docs.stocki.com.cn)
- [量化投资基础](https://en.wikipedia.org/wiki/Quantitative_investing)
- [因子投资理论](https://en.wikipedia.org/wiki/Factor_investing)

---

## 📄 版本信息

```
项目名称：A股港股量化选股回测系统
版本：1.0.0
创建日期：2024年
最后更新：2024年
Python版本：3.8+
```

---

## 📋 检查清单

- ✅ 三因子筛选逻辑实现
- ✅ Stocki API集成
- ✅ 月度等权组合回测
- ✅ 性能指标计算
- ✅ HTML交互式报告
- ✅ CSV数据导出
- ✅ 演示数据生成
- ✅ 完整文档编写
- ✅ 错误处理
- ✅ 风险提示

---

**准备好开始了吗？** 

选择一个场景开始：
1. 📊 [查看演示报告](backtest_report.html)
2. 🚀 [运行演示数据生成](generate_demo_results_simple.py)
3. 📖 [阅读完整指南](IMPLEMENTATION_GUIDE.md)
4. 💻 [集成API运行](stock_quant_backtest.py)

---

**免责声明**：本项目仅供学习研究，不构成投资建议。使用者需自行承担风险。
