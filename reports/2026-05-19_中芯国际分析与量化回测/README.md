# A股港股量化选股回测系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-brightgreen.svg)](releases)

一个完整的**量化投资选股与回测分析系统**，用于在A股和港股市场中自动筛选满足多因子条件的股票，进行历史回测分析，并生成交互式可视化报告。

## ✨ 核心特性

- 🎯 **三因子智能选股**：低估值（PB）+ 高动量（RSI）+ 盈利向上修正（EPS）
- 📊 **完整回测分析**：月度等权调仓，计算收益率、波动率、夏普比率、最大回撤等
- 📈 **交互式报告**：HTML5 + Chart.js 生成的可视化报告
- 🔌 **API集成**：与 Stocki 机构级财务数据平台集成
- 📉 **详细数据输出**：CSV格式的净值、股票、指标数据
- 🚀 **开箱即用**：演示数据、示例报告已包含

## 🎯 快速开始

### 1️⃣ 查看演示报告（无需任何依赖）

```bash
# 直接在浏览器打开报告
open backtest_report.html
# 或
firefox backtest_report.html
```

### 2️⃣ 生成演示数据

```bash
# 生成演示用的回测数据（不需要API）
python3 generate_demo_results_simple.py
```

### 3️⃣ 运行完整系统（需要API）

```bash
# 配置API环境变量
export STOCKI_GATEWAY_URL="https://api.stocki.com.cn"
export STOCKI_API_KEY="your-api-key"

# 执行选股和回测
python3 stock_quant_backtest.py

# 生成图表（需要pandas）
python3 visualize_backtest.py
```

## 📊 策略说明

### 三因子筛选模型

```
选股条件 = (PB分位 ≤ 30%) AND (RSI > 60) AND (EPS修正向上)
```

| 因子 | 指标 | 条件 | 说明 |
|------|------|------|------|
| 低估值 | 市净率 (PB) | 历史30%分位以下 | 价格相对便宜 |
| 高动量 | 相对强弱指数 (RSI) | 过去6个月 > 60 | 市场关注度高 |
| 盈利向上 | EPS共识预期 | 过去30天向上修正 | 基本面改善 |

### 组合策略

- **组合方式**：等权重分配
- **调仓频率**：每月末最后一个交易日
- **市场覆盖**：A股（主板、科创板、创业板）+ 港股

## 📁 项目文件

```
├── backtest_report.html              ✨ 交互式回测报告（推荐首先查看）
├── stock_quant_backtest.py           选股和回测主程序
├── visualize_backtest.py             可视化图表生成脚本
├── generate_demo_results_simple.py   演示数据生成脚本
├── README.md                         项目说明（本文件）
├── PROJECT_SUMMARY.md                项目总结与快速参考
├── QUANT_BACKTEST_README.md          详细使用手册
├── IMPLEMENTATION_GUIDE.md           实现细节与自定义指南
├── backtest_results.csv              月度净值数据
├── screened_stocks.csv               筛选结果列表
└── backtest_summary.csv              性能指标汇总
```

## 📈 演示结果

### 性能指标

```
总收益率        : +26.19%
年化收益率      : +12.67%
年化波动率      : 14.82%
夏普比率        : 0.72
最大回撤        : -20.82%
回测周期        : 24个月 (2024.05 - 2026.04)
```

### 筛选结果

**符合条件的14只股票：**

A股 (9只)：茅台、招商银行、工商银行、浦发银行、民生银行、中国银行、三一重工、中国石油、海螺水泥

港股 (5只)：腾讯、中国移动、阿里巴巴、美团、JD.com

## 🔧 环境配置

### 最小依赖（查看HTML报告）
- 网络浏览器（Chrome、Firefox等）

### 运行主程序
```bash
# Python 3.8+
python3 --version

# 仅运行演示数据生成（无外部依赖）
python3 generate_demo_results_simple.py
```

### 完整功能（包括图表生成）
```bash
pip install pandas numpy matplotlib requests
```

### API配置
```bash
export STOCKI_GATEWAY_URL="http://localhost:9996"      # 开发环境
export STOCKI_GATEWAY_URL="https://api.stocki.com.cn"  # 生产环境
export STOCKI_API_KEY="your-api-key-here"
```

## 📚 文档导航

| 文档 | 内容 | 适合人群 |
|------|------|--------|
| [backtest_report.html](backtest_report.html) | 交互式可视化报告 | 所有用户 |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | 项目总结与快速参考 | 新用户快速了解 |
| [QUANT_BACKTEST_README.md](QUANT_BACKTEST_README.md) | 详细使用手册 | 想要了解每个文件的作用 |
| [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | 完整实现指南 | 想要深入理解或自定义 |

## 💡 使用场景

### 场景1：快速了解项目
```bash
# 1. 打开报告
open backtest_report.html

# 2. 阅读项目总结
cat PROJECT_SUMMARY.md
```

### 场景2：测试系统
```bash
# 1. 生成演示数据
python3 generate_demo_results_simple.py

# 2. 生成图表（可选）
pip install pandas numpy matplotlib
python3 visualize_backtest.py

# 3. 查看CSV结果
cat backtest_results.csv
cat screened_stocks.csv
```

### 场景3：运行完整系统
```bash
# 1. 配置API
export STOCKI_API_KEY="your-key"

# 2. 运行选股和回测
python3 stock_quant_backtest.py

# 3. 生成可视化
python3 visualize_backtest.py

# 4. 检查结果
open backtest_report.html
```

### 场景4：自定义策略
```bash
# 1. 阅读实现指南
cat IMPLEMENTATION_GUIDE.md

# 2. 修改 stock_quant_backtest.py
vim stock_quant_backtest.py

# 3. 调整筛选条件或回测参数

# 4. 重新运行
python3 stock_quant_backtest.py
```

## ⚠️ 重要提示

### 风险声明

- 📌 **仅供学习和研究使用**，不构成任何投资建议
- 📌 **历史表现不代表未来收益**，市场存在风险
- 📌 **本框架不考虑交易成本**，实际收益会低于回测结果
- 📌 **实盘交易需专业咨询**，建议寻求金融顾问指导

### 局限性

- ❌ 假设完全流动性
- ❌ 假设无交易成本和滑点
- ❌ 无风险率假设为2%
- ❌ 不考虑股票停牌等特殊情况

## 🎉 开始使用

### 最快的方式（2秒）
```bash
open backtest_report.html
```

### 推荐的方式（2分钟）
```bash
python3 generate_demo_results_simple.py
open backtest_report.html
```

### 完整的方式（需要API）
```bash
export STOCKI_API_KEY="your-key"
python3 stock_quant_backtest.py
python3 visualize_backtest.py
open backtest_report.html
```

---

**版本**：v1.0.0 | **更新**：2024年 | **维护状态**：活跃 ✅

Made with ❤️ for quantitative investing enthusiasts
