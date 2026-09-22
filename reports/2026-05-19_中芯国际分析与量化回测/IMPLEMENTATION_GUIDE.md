# A股港股量化选股回测系统 - 完整实现指南

## 📌 项目概览

本项目提供了一个完整的量化投资分析系统，用于筛选满足多因子条件的股票并进行历史回测。

### 核心功能

✅ **智能选股**：基于三个量化因子的股票筛选
✅ **历史回测**：月度调仓的等权组合回测
✅ **性能分析**：完整的回测指标计算
✅ **可视化报告**：交互式HTML图表报告

---

## 🎯 选股策略详解

### 三因子筛选条件

#### 因子1：低估值（PB处于历史30%分位以下）
- **含义**：选择价格相对账面价值较便宜的公司
- **数据来源**：Stocki API `financial_context` 端点
- **计算方式**：PB = 总市值 / 股东权益
- **阈值**：历史5年PB 30%分位数
- **理由**：低估值通常代表安全边际较高

#### 因子2：高动量（过去6个月RSI > 60）
- **含义**：选择技术面强势的股票
- **数据来源**：Stocki API `datareader` 端点 (indicator)
- **指标**：RSI (14日相对强弱指标)
- **阈值**：RSI > 60（强势区间）
- **理由**：高动量反映市场关注和买方力量

#### 因子3：盈利向上修正（过去30天EPS预期修正向上）
- **含义**：选择业绩预期持续改善的公司
- **数据来源**：Stocki API `datareader` 端点 (estimate)
- **指标**：分析师一致预期EPS
- **判断**：过去30天内最新EPS > 30天前EPS
- **理由**：预期修正向上通常是股价上涨的前兆

### 三因子的组合逻辑

```
选股条件 = (PB分位 ≤ 30%) AND (RSI > 60) AND (EPS修正向上)
```

这个组合代表寻找：
- 估值便宜的公司
- 但市场关注度高（强势）
- 且基本面在改善（分析师持续上调）

---

## 📂 项目文件结构

```
/home/user/claude/
├── stock_quant_backtest.py          # 主分析脚本
├── visualize_backtest.py            # 可视化脚本（依赖pandas）
├── generate_demo_results_simple.py  # 演示数据生成
├── backtest_report.html             # HTML交互式报告
├── QUANT_BACKTEST_README.md         # 详细使用说明
├── IMPLEMENTATION_GUIDE.md          # 本文件
├── backtest_results.csv             # 生成的净值数据
├── screened_stocks.csv              # 生成的筛选结果
└── backtest_summary.csv             # 生成的指标汇总
```

---

## 🚀 快速开始

### 第一步：配置环境

```bash
# 设置Stocki API环境变量
export STOCKI_GATEWAY_URL="http://localhost:9996"  # 开发环境
export STOCKI_API_KEY="your-api-key"

# 或生产环境
export STOCKI_GATEWAY_URL="https://api.stocki.com.cn"
export STOCKI_API_KEY="your-api-key"
```

### 第二步：运行选股和回测

```bash
# 方法一：完整流程
python3 stock_quant_backtest.py

# 这将：
# 1. 获取A股和港股股票列表
# 2. 按三个条件进行筛选
# 3. 获取价格历史数据
# 4. 进行月度等权组合回测
# 5. 生成两个输出文件：
#    - backtest_results.csv (月度净值)
#    - screened_stocks.csv (筛选股票)
```

### 第三步：查看结果

**方式一：HTML交互式报告**
```bash
# 在浏览器中打开
open backtest_report.html
# 或
firefox backtest_report.html
```

**方式二：查看CSV数据**
```bash
# 查看净值数据
cat backtest_results.csv

# 查看筛选结果
cat screened_stocks.csv

# 查看指标汇总
cat backtest_summary.csv
```

**方式三：生成matplotlib图表**（需要pandas）
```bash
pip install pandas numpy matplotlib
python3 visualize_backtest.py
```

---

## 📊 回测方法论

### 组合构建
- **方式**：等权分配
- **股票数**：所有通过筛选的股票
- **权重**：1/n，其中n为筛选出的股票数

### 调仓策略
- **频率**：每个自然月末最后一个交易日
- **方式**：重新筛选 + 重新等权分配
- **成本**：本演示不考虑交易成本和滑点

### 性能指标计算

| 指标 | 公式 | 说明 |
|------|------|------|
| **总收益率** | (P_final / P_initial - 1) × 100% | 整个回测期间的收益 |
| **年化收益率** | 月收益率 × 12 | 月度收益率年化 |
| **年化波动率** | 月收益率std × √12 | 风险衡量 |
| **最大回撤** | min((P - P_max) / P_max) × 100% | 历史最大跌幅 |
| **夏普比率** | (年化收益 - 无风险率) / 年化波动 | 风险调整收益 |

### 假设条件
- 无交易成本
- 完全流动性
- 无滑点
- 无风险率 = 2%

---

## 🔍 数据来源与API调用

### 使用的Stocki API

#### 1. 股票列表获取
```
端点: /api/v3/market/stock_list
参数: market=["cn_sh", "cn_sz", "hk"]
返回: 股票代码、名称、行业等
```

#### 2. PB估值和分位
```
端点: /api/v3/financial_context/read
参数: symbol, include_percentiles=true
返回: pb_ttm, pb_percentile_5y (5年历史分位)
```

#### 3. RSI技术指标
```
端点: /api/v3/datareader/read
参数: symbol, data_type="indicator", metrics=["rsi_14"]
      start_date, end_date (过去180天)
返回: 每日RSI值
```

#### 4. EPS预期修正
```
端点: /api/v3/datareader/read
参数: symbol, data_type="estimate", metrics=["eps_consensus"]
      start_date, end_date (过去30天)
返回: 分析师一致EPS预期的变化
```

#### 5. 价格历史
```
端点: /api/v3/datareader/read
参数: symbol, data_type="price"
      start_date, end_date (过去2年)
返回: OHLCV数据
```

---

## 📈 回测结果示例

### 演示数据统计

```
┌─────────────────────────────────────────┐
│        性能指标总结                      │
├─────────────────────────────────────────┤
│ 总收益率        : +26.19%               │
│ 年化收益率      : +12.67%               │
│ 年化波动率      : +14.82%               │
│ 夏普比率        : 0.72                  │
│ 最大回撤        : -20.82%               │
│ 回测周期        : 24个月                │
│ 开始日期        : 2024-05-31            │
│ 结束日期        : 2026-04-30            │
└─────────────────────────────────────────┘
```

### 筛选结果示例

通过筛选的14只股票：
```
A股 (9只):
- 600519 贵州茅台     (低估+高动量+EPS向上)
- 600036 招商银行     (低估+高动量+EPS向上)
- 601398 工商银行     (低估+高动量+EPS向上)
- 600000 浦发银行     (低估+高动量+EPS向上)
- 600016 民生银行     (低估+高动量+EPS向上)
- 601988 中国银行     (低估+高动量+EPS向上)
- 600031 三一重工     (低估+高动量+EPS向上)
- 601857 中国石油     (低估+高动量+EPS向上)
- 600585 海螺水泥     (低估+高动量+EPS向上)

港股 (5只):
- 0700.HK 腾讯控股    (低估+高动量+EPS向上)
- 0941.HK 中国移动    (低估+高动量+EPS向上)
- 9988.HK 阿里巴巴    (低估+高动量+EPS向上)
- 3690.HK 美团        (低估+高动量+EPS向上)
- 6078.HK JD.com      (低估+高动量+EPS向上)
```

---

## 🛠️ 自定义与扩展

### 修改筛选条件

#### 降低估值阈值（更严格）
```python
# 在 screen_stocks() 方法中修改
# 原来：if pb_percentile > 30:
if pb_percentile > 20:  # 改为20%分位
    continue
```

#### 提高RSI阈值
```python
# 原来：if rsi_latest <= 60:
if rsi_latest <= 70:  # 改为70，更严格
    continue
```

#### 扩展EPS修正时间窗口
```python
# 原来：get_eps_revisions(symbol, days=30)
get_eps_revisions(symbol, days=60)  # 改为60天
```

### 修改回测参数

#### 更改调仓频率为季度
```python
# 在 backtest_strategy() 中修改
# 原来：rebalance_freq: str = "M"  (M = 月)
rebalance_freq: str = "Q"  # Q = 季度
```

#### 修改回测窗口
```python
# 获取更长历史数据（3年）
price_df = self.get_price_history(
    screened,
    start_date="2021-05-19",
    end_date="2024-05-19"
)
```

### 添加额外的筛选因子

```python
def get_custom_factor(self, symbol: str) -> Optional[Dict]:
    """获取自定义因子，例如ROE"""
    endpoint = "/api/v3/financial_context/read"
    params = {"symbol": symbol}
    response = self._make_request(endpoint, method="POST", data=params)

    if "error" not in response and "data" in response:
        data = response.get("data", {})
        return {
            "symbol": symbol,
            "roe": data.get("roe_ttm"),
            "roe_percentile": data.get("roe_percentile_5y")
        }
    return None

# 在 screen_stocks() 中添加到筛选条件中
def screen_stocks(self, symbols: List[str]) -> List[str]:
    # ... 前面的代码 ...
    
    # 添加ROE筛选
    roe_data = self.get_custom_factor(symbol)
    if roe_data and roe_data.get("roe_percentile", 50) < 30:
        continue
```

---

## 🐛 故障排除

### 问题1：API连接失败
```
错误: API请求失败: Connection refused
```
**原因**：Stocki API服务未运行或地址配置错误

**解决方案**：
```bash
# 检查环境变量
echo $STOCKI_GATEWAY_URL
echo $STOCKI_API_KEY

# 测试连接
curl -H "Authorization: Bearer $STOCKI_API_KEY" \
     "$STOCKI_GATEWAY_URL/api/v3/market/stock_list"

# 本地开发环境应该用
export STOCKI_GATEWAY_URL="http://localhost:9996"
```

### 问题2：没有股票通过筛选
```
筛选完成，符合条件的股票数: 0
```
**原因**：
- 筛选条件过于严格
- 市场当前没有同时满足三个条件的股票
- API数据不完整

**解决方案**：
```python
# 调整条件，使用更宽松的阈值
if pb_percentile > 40:  # 改为40%
    continue

if rsi_latest <= 55:  # 改为55
    continue

# 查看详细的筛选日志，了解为什么股票被排除
```

### 问题3：历史数据不足
```
获取到 0 个交易日数据
```
**原因**：
- 某些股票缺少历史价格数据
- API返回的数据为空

**解决方案**：
```python
# 增加内联阈值以获取更多数据
params = {
    "symbol": symbol,
    "data_type": "price",
    "inline_threshold": 500  # 增大到500或1000
}
```

---

## 📚 相关资源

### 技术指标参考
- [RSI相对强弱指标](https://en.wikipedia.org/wiki/Relative_strength_index)
- [PB估值指标](https://en.wikipedia.org/wiki/Price-to-book_ratio)
- [EPS盈利预期](https://en.wikipedia.org/wiki/Earnings_per_share)

### 量化投资理论
- [因子投资](https://en.wikipedia.org/wiki/Factor_investing)
- [动量策略](https://en.wikipedia.org/wiki/Momentum_investing)
- [价值投资](https://en.wikipedia.org/wiki/Value_investing)

### 开发工具
- [Stocki API文档](https://docs.stocki.com.cn)
- [Pandas教程](https://pandas.pydata.org/docs/)
- [Matplotlib绘图](https://matplotlib.org)

---

## ⚠️ 重要风险提示

### 历史回测的局限性

1. **未考虑交易成本**
   - 实际交易涉及佣金、手续费等
   - 会降低实际收益

2. **完全流动性假设**
   - 实际市场存在流动性限制
   - 大额交易可能无法按预期价格成交

3. **前瞻偏差**
   - 本演示未考虑时间错配
   - 实际交易信息会有延迟

4. **参数优化偏差**
   - 筛选条件在历史数据上优化
   - 可能不适用于未来市场

### 风险管理建议

- 使用本框架的输出作为参考，不作为直接投资建议
- 实盘交易前应进行充分的风险评估
- 建议分仓位、分时间段入场
- 设置止损止盈规则
- 定期审视和调整策略

---

## 📞 支持与反馈

如有问题或建议：

1. **查看日志**：运行脚本时输出的信息会有详细的筛选过程
2. **调整参数**：根据市场情况调整筛选条件
3. **寻求帮助**：咨询专业的量化投资或金融顾问

---

## 📄 许可证

本项目仅供学习和研究用途。使用者对自己的投资决策负完全责任。

---

**最后更新**：2024年 | **版本**：1.0.0
