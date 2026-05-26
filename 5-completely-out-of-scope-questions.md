# 5 个 Stocki Skill 完全无法跑出任何结果的问题

这些问题 **100% 超出 skill 能力**，无论怎样都无法从 API 获取数据或计算结果。

---

## 问题 1：技术指标计算

### 用户问法
```
"茅台现在是 MACD 金叉吗？
5 日均线、20 日均线、60 日均线各是多少？
RSI 现在是 30（超卖）还是 70（超买）？"
```

### 为什么完全无法做

| 层级 | 是否可能 | 说明 |
|------|---------|------|
| **Skill 直接提供** | ❌ | skill 无 MACD、RSI、均线端点 |
| **Skill 提供原始数据，LLM 计算** | ❌ | LLM 在会话中无法进行复杂数学计算（MACD 需要 EMA 两次平滑、信号线、直方图） |
| **用户端 workaround** | ✅ | 用户自己用 TA-Lib、pandas-ta 计算 |

### 尝试会得到什么
- Skill 返回 OHLCV 数据
- LLM 说"根据数据，应该是..."（猜测，非计算）
- 用户得到错误答案

### 正确处理
```
❌ "根据我的分析，RSI 现在大约是..."

✅ "我可以提供茅台的历史 K 线数据（OHLCV），
    你用 TA-Lib 或看盘软件的内置指标查看 MACD/RSI。
    
    stocki-financial-reader 不包含技术指标计算能力。"
```

### 文档依据
- `price-history.md`：明确说"Do NOT use this skill for strategy backtest"
- SKILL.md：无任何指标计算的 endpoint

---

## 问题 2：加密货币历史价格

### 用户问法
```
"比特币过去一年的日 K 线给我一份。
以太坊 2024 年的周线数据。
BNB 最高价是多少？"
```

### 为什么完全无法做

| 操作 | 结果 | 说明 |
|------|------|------|
| **调用 price-history 的 crypto 端点** | 🔴 Error | API 明确返回：`"fetch failed: Missing config: database_url - crypto"` |
| **用 realtime-quote 获取实时价格** | ✅ | 可以，但 freshness 可能是 `latest_close`（延迟数小时） |
| **通过 fundamentals-panel 获取** | ❌ | crypto 不支持此 endpoint |

### API 返回的错误信息
```json
{
  "action": "error",
  "data": [],
  "metadata": {
    "warnings": ["fetch failed: Missing config: database_url - crypto"]
  }
}
```

### 尝试会得到什么
```
❌ 空数据 + 错误提示
   "fetch failed: Missing config..."
```

### 正确处理
```
❌ "根据 stocki API，比特币过去一年..."（无数据，无法说）

✅ "Stocki skill 不支持加密货币历史价格查询。
    
    推荐使用：
    - CoinGecko API（免费，有历史 K 线）
    - Binance API（币安官方数据）
    - Kraken API
    - 看盘软件的加密行情"
```

### 文档依据
- `price-history.md`：
  ```
  "crypto:crypto:price is currently **unavailable** 
  (response passes through server error + warnings; 
  do not pretend it works)"
  ```

---

## 问题 3：宏观经济指标

### 用户问法
```
"中国最新 CPI 是多少？
美联储现在的基准利率是多少？
中国 GDP 增速预测是多少？
全球失业率数据？"
```

### 为什么完全无法做

| 数据类型 | Skill 能否提供 | 理由 |
|---------|---------------|------|
| **股票价格** | ✅ | realtime-quote, price-history |
| **股票财务数据** | ✅ | fundamentals-panel (CN/HK) |
| **经济指标（CPI、失业率、GDP）** | ❌ | 完全超出 Wind API 股票模块范围 |
| **利率曲线** | ❌ | 不在 datareader endpoint 中 |
| **PMI、景气指数** | ❌ | 不在数据源中 |

### API 的覆盖范围
```python
# ✅ 可查询的市场
areas = ["cn", "hk", "us", "crypto"]
asset_types = ["stock", "index", "etf", "futures"]

# ❌ 无法查询的数据类型
macro_indicators = [
  "CPI", "GDP", "unemployment", "interest_rate",
  "PMI", "industrial_production", "retail_sales"
]
```

### 尝试会得到什么
- 没有对应的 endpoint
- 无法构造有效请求
- LLM 会说"无此数据"或猜测（错误）

### 正确处理
```
❌ "根据最新经济数据，CPI 是..."（无数据源）

✅ "Stocki skill 仅提供股票市场数据，不覆盖宏观经济指标。
    
    获取渠道：
    - 中国数据：国家统计局 (stats.gov.cn)
    - 美国数据：Federal Reserve (federalreserve.gov)、FRED
    - 全球数据：CEIC、IMF、World Bank"
```

### 文档依据
- SKILL.md：无 macro 相关 endpoint
- references：全部聚焦于"股票/指数/期货/ETF"

---

## 问题 4：策略回测与性能计算

### 用户问法
```
"我有个策略：每月初买入前 10 大流动性股票，月末卖出。
过去 5 年年化收益多少？最大回撤？夏普比率？

或者：双均线策略（5 日 > 20 日时买入，反之卖出）的历史表现。"
```

### 为什么完全无法做

| 需求 | Skill 能否提供 | 理由 |
|------|---------------|------|
| **历史 K 线数据** | ✅ | price-history 提供 OHLCV |
| **逐日调仓逻辑** | ❌ | 无 backtest framework |
| **手续费/滑点计算** | ❌ | 不在 API 范围 |
| **风险指标（夏普、最大回撤）** | ❌ | LLM 无法精确计算 |
| **期货连续合约处理** | ❌ | 有滚动日价格跳跃（1-5%），污染结果 |

### 关键限制：期货滚动日问题
```python
# ❌ 错误做法
return (close[-1] / close[0]) - 1  # 被滚动日跳跃污染！

# 期货主合约在交割前会产生 1-5% 的非市场价格跳
# 长期累计收益计算会严重错误
```

### 尝试会得到什么
```
✅ 提供原始 K 线数据
❌ 无法进行"回测"（backtest 需要框架）
❌ 无法计算 Sharpe Ratio、最大回撤等风险指标
```

### 正确处理
```
❌ "根据回测，你这个策略年化收益 15%，最大回撤 8%..."
   （无回测框架，无法计算）

✅ "我可以提供历史 K 线数据。回测需要专门的框架：
    
    选择一个回测工具：
    - vnpy（开源，国内广泛使用）
    - backtrader（Python 标准）
    - zipline（专业级）
    - 掌上财经 / 聚宽（SaaS 工具）
    
    ⚠️ 注意：期货数据有滚动日污染，需要处理"
```

### 文档依据
- `price-history.md`：
  ```
  "Strategy backtest performance → backtest skill 
  **not yet delivered** (upstream limitation, tracked separately)"
  ```
- `price-history.md` 期货部分：
  ```
  "Do not compute daily return directly on continuous series 
  — roll days will contaminate long-horizon cumulative returns"
  ```

---

## 问题 5：债券与衍生品数据

### 用户问法
```
"国债收益率曲线现在是什么样？
10 年期国债收益率是多少？

或者：

AAPL 看跌期权现在多少钱？
沪深 300 50 ETF 看涨权证怎么交易？
可转债数据给我看看。"
```

### 为什么完全无法做

| 资产类型 | Skill 支持 | 说明 |
|---------|----------|------|
| **股票、指数、ETF、期货** | ✅ | 全力支持（CN/HK/US/部分Crypto） |
| **债券** | ❌ | 完全无数据源 |
| **期权** | ❌ | 无任何 option endpoint |
| **权证** | ❌ | 无 warrant endpoint |
| **可转债** | ❌ | 虽然是债券衍生物，仍无 |

### API 覆盖的 asset_type
```python
supported_assets = [
  "stock",      # ✅
  "index",      # ✅
  "etf",        # ✅
  "futures",    # ✅
  "crypto"      # ✅ (仅实时价格)
]

unsupported_assets = [
  "bond",           # ❌
  "option",         # ❌
  "warrant",        # ❌
  "convertible",    # ❌
  "commodity",      # ❌ (除期货外)
]
```

### 尝试会得到什么
- 无对应 endpoint
- API 返回 error 或空数据
- 无法获取任何价格/合约数据

### 正确处理
```
❌ "根据 stocki API，国债收益率是..."
   （完全无此数据）

✅ "Stocki skill 只支持股票、指数、ETF、期货。
    债券和衍生品需要专门的数据源：
    
    债券数据：
    - 中国债券信息网 (chinabond.com.cn)
    - Wind 债券模块
    - Bloomberg Terminal
    
    期权数据：
    - 各交易所官网（CBOE、中金所等）
    - Bloomberg、FactSet
    - 专业期权平台（Interactive Brokers）
    
    可转债数据：
    - 交易所公告
    - Wind 可转债模块"
```

### 文档依据
- SKILL.md - Endpoint 列表：仅覆盖 stock/index/etf/futures/crypto
- README.md：无债券、期权、衍生品字样
- 所有 reference 均聚焦于"价格、财务、估值"

---

## 总结表

| # | 问题类型 | 能否返回任何结果 | 为什么 | 备选方案 |
|---|---------|-----------------|-------|---------|
| **1** | 技术指标（MACD、RSI） | ❌ | 无计算能力 | TA-Lib、看盘软件 |
| **2** | Crypto 历史价格 | ❌ | API error: Missing config | CoinGecko、Binance API |
| **3** | 宏观数据（CPI、GDP、利率） | ❌ | 超出 Wind 股票模块范围 | 国统局、Fed、CEIC |
| **4** | 策略回测 + 风险指标 | ❌ | 无回测框架；期货有污染 | vnpy、backtrader、聚宽 |
| **5** | 债券 + 衍生品（期权、权证） | ❌ | 无对应 asset_type | 中国债券网、CBOE、Bloomberg |

---

## 给用户的最终说明文案

```markdown
⚠️ **Stocki Skill 的硬边界**

以下 5 类问题无论如何都无法从 Skill 获得答案：

### 完全无法做
1. **技术指标** — MACD、RSI、均线等；无计算库
2. **加密货币历史** — API 明确返回 error
3. **宏观经济数据** — CPI、GDP、利率；超出 Wind 范围
4. **策略回测** — 无框架；期货有滚动日污染
5. **债券 + 衍生品** — 期权、权证、可转债；无数据源

### 推荐
- 不要问这些问题
- 这些数据需要专门的工具和数据源
- Skill 的强项是：**单个公司深度分析 + 实时行情 + 历史价格**
```
