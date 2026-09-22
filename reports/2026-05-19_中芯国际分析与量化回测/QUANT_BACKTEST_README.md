# A股港股量化选股与回测框架

## 项目概述

这是一个完整的量化投资选股和回测系统，用于在A股和港股市场中筛选满足特定条件的股票，并进行历史回测分析。

### 核心策略

选股条件（同时满足以下三个条件）：

1. **低估值**：PB估值处于历史30%分位以下
2. **高动量**：过去6个月RSI > 60
3. **盈利向上修正**：过去30天内有分析师上调EPS预期

投资组合构建与回测：
- 等权投资组合
- 月度调仓（每月重新平衡）
- 最大回撤、夏普比率、年化收益等性能指标计算

---

## 环境配置

### 系统需求

- Python 3.8+
- 依赖包：
  ```bash
  pip install pandas numpy requests matplotlib
  ```

### API配置

需要配置Stocki财务数据API的访问凭据：

```bash
# 设置环境变量
export STOCKI_GATEWAY_URL="https://api.stocki.com.cn"  # 或本地开发地址 http://localhost:9996
export STOCKI_API_KEY="your-api-key-here"
```

或在运行脚本前在当前Shell中设置：
```bash
export STOCKI_GATEWAY_URL="http://localhost:9996"
export STOCKI_API_KEY="test-key"
```

---

## 文件说明

### 1. `stock_quant_backtest.py` - 主分析脚本

**功能**：
- 获取A股和港股股票列表
- 获取PB估值和历史分位数据
- 获取RSI技术指标数据（6个月）
- 获取分析师EPS预期修正数据（30天）
- 按条件筛选股票
- 获取筛选股票的历史价格数据
- 进行等权组合的月度调仓回测
- 计算性能指标并生成报告

**核心类**：
```python
class StockQuantAnalyzer:
    - get_stock_universe()         # 获取股票列表
    - screen_stocks()              # 按条件筛选
    - get_price_history()          # 获取价格历史
    - backtest_strategy()          # 回测策略
    - generate_report()            # 生成报告
```

**输出文件**：
- `backtest_results.csv` - 月度组合净值数据
- `screened_stocks.csv` - 筛选出的股票列表

### 2. `visualize_backtest.py` - 可视化脚本

**功能**：
- 加载回测结果数据
- 计算性能指标
- 生成4合1可视化图表：
  - 净值曲线
  - 最大回撤曲线
  - 月度收益率直方图
  - 性能指标汇总表

**输出文件**：
- `backtest_chart.png` - 完整的回测结果图表
- `backtest_summary.csv` - 性能指标汇总表

---

## 使用方法

### 方法一：完整执行流程

```bash
# 1. 先运行主分析脚本（进行选股和回测）
python3 stock_quant_backtest.py

# 2. 再运行可视化脚本（生成图表）
python3 visualize_backtest.py
```

### 方法二：独立运行可视化

如果已有回测结果文件，可直接进行可视化：

```bash
python3 visualize_backtest.py
```

---

## 数据来源与API调用

### 使用的Stocki API端点

| 功能 | 端点 | 数据类型 |
|------|------|--------|
| 股票列表 | `/api/v3/market/stock_list` | 股票代码 |
| PB估值与分位 | `/api/v3/financial_context/read` | 估值分位 |
| RSI指标 | `/api/v3/datareader/read` (indicator) | 技术指标 |
| EPS预期 | `/api/v3/datareader/read` (estimate) | 分析师预期 |
| 价格历史 | `/api/v3/datareader/read` (price) | OHLCV数据 |

### 数据周期

- **PB分位**：5年历史分位
- **RSI**：过去180天（6个月）
- **EPS修正**：过去30天
- **价格历史**：过去730天（2年）用于回测

---

## 输出结果说明

### 回测汇总指标

| 指标 | 说明 | 单位 |
|------|------|------|
| 总收益率 | 回测期间的累计收益 | % |
| 年化收益率 | 月度收益率年化 | % |
| 年化波动率 | 月度收益率标准差年化 | % |
| 夏普比率 | 超额收益/风险（无风险率2%） | - |
| 最大回撤 | 历史最大的净值回撤 | % |

### 输出文件格式

**backtest_results.csv**：
```
Date,Portfolio_Value
2022-01-31,1.0000
2022-02-28,1.0234
2022-03-31,0.9876
...
```

**screened_stocks.csv**：
```
Symbol,Stock_Count
600519,1
0700.HK,1
...
```

**backtest_summary.csv**：
```
指标,数值
总收益率(%),25.34
年化收益率(%),12.67
...
```

---

## 性能与注意事项

### 数据获取注意事项

1. **API速率限制**：如果获取股票数过多，可能触发速率限制。脚本默认处理前100只股票进行演示。

2. **缺失数据处理**：
   - 某些股票可能缺失特定指标数据，会自动跳过
   - 价格数据缺失会被向前填充

3. **市场覆盖**：
   - A股：沪深主板、科创板、创业板
   - 港股：主要上市公司

### 计算说明

1. **月度调仓**：
   - 每个自然月最后一个交易日进行调仓
   - 等权分配资金到筛选出的股票

2. **回撤计算**：
   - 最大回撤 = (当前净值 - 历史最高净值) / 历史最高净值

3. **夏普比率**：
   - (年化收益率 - 无风险率) / 年化波动率
   - 无风险率假设为2%

---

## 故障排除

### 问题1：API连接失败

```
错误: API请求失败: Connection refused
```

**解决方案**：
- 检查 `STOCKI_GATEWAY_URL` 环境变量是否正确
- 确认Stocki API服务是否运行
- 开发环境：`export STOCKI_GATEWAY_URL="http://localhost:9996"`

### 问题2：认证失败

```
错误: API请求失败: 401 Unauthorized
```

**解决方案**：
- 检查 `STOCKI_API_KEY` 环境变量是否设置
- 确认API密钥是否有效

### 问题3：未找到股票数据

**解决方案**：
- 检查符合条件的股票是否真实存在（脚本会输出详细的筛选过程）
- 某些股票可能缺失必要的数据指标，会被自动过滤

### 问题4：回测结果为空

**解决方案**：
- 确保至少有1只股票通过筛选
- 检查价格历史数据是否成功获取

---

## 扩展与自定义

### 修改筛选条件

编辑 `screen_stocks()` 方法中的条件：

```python
# 修改PB分位阈值（当前30%）
if pb_percentile > 40:  # 改为40%分位
    continue

# 修改RSI阈值（当前60）
if rsi_latest <= 70:  # 改为70
    continue

# 修改EPS修正时间窗口（当前30天）
get_eps_revisions(symbol, days=60)  # 改为60天
```

### 修改回测参数

在 `run()` 方法中调整：

```python
# 修改为季度调仓
backtest_results = self.backtest_strategy(screened, price_df, rebalance_freq="Q")

# 修改回测窗口（当前2年）
price_df = self.get_price_history(screened, 
                                   start_date="2020-01-01",
                                   end_date="2024-01-01")
```

### 添加额外指标

```python
def get_custom_metric(self, symbol: str) -> Optional[Dict]:
    """获取自定义指标"""
    endpoint = "/api/v3/datareader/read"
    params = {
        "symbol": symbol,
        "data_type": "indicator",
        "metrics": ["your_metric_here"]
    }
    # ... API调用逻辑
```

---

## 参考资源

- [Stocki API文档](https://docs.stocki.com.cn)
- [Pandas文档](https://pandas.pydata.org)
- [Matplotlib文档](https://matplotlib.org)
- [技术分析指标说明](https://en.wikipedia.org/wiki/Relative_strength_index)

---

## 许可证与免责声明

此代码仅供学习和研究用途。

**重要免责声明**：
- 本框架用于教育目的，不构成投资建议
- 历史回测不能保证未来表现
- 实盘交易需谨慎，建议寻求专业人士指导
- 使用者对自己的投资决策负责

---

## 更新日志

### v1.0.0 (2024年)
- 初始版本发布
- 实现三因子选股策略
- 支持月度等权组合回测
- 生成完整的性能指标和图表

---

## 联系与支持

如有问题或建议，请提交Issue或联系开发者。
