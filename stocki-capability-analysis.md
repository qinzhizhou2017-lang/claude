# Stocki Skill 能力范围逆向工程分析

## 核心能力范围（8 个 reference 模块）

### ✅ 已实现的数据能力

| 模块 | 能力 | 数据来源 | 市场覆盖 |
|------|------|--------|--------|
| **realtime-quote** | 实时/延时行情快照 | `/api/v3/quotes/get_latest_quotes` | CN/HK/US/Crypto |
| **price-history** | OHLCV 历史、复权价格 | `/api/v3/datareader/read (data_type=price)` | CN/HK/US (Stock/Index/ETF/Futures) |
| **fundamentals-panel** | 三表、财务指标、估值序列、市值 | `/api/v3/datareader/read (financial/indicator/valuation/market_cap)` | CN/HK ✅, US ⚠️(仅 market_cap) |
| **financial-context** | 一键综合分析（L1-L3 深度） | `/api/v3/financial_context/{cn,hk}` | CN/HK only |
| **consensus-and-target** | 一致预期、目标价、营收分部 | `/api/v3/datareader/read (consensus_forecast/target_price/revenue_breakdown)` | CN only |
| **industry-and-symbols** | 行业分类、指数成分、公司基本信息 | `/api/v3/datareader/read + /api/v2/market_symbol/get_symbols` | CN/HK/US (行业); CN/HK (成分) |
| **market-calendar** | 交易日历、市场状态、数据可用性 | `/api/v3/market/*` | Global |
| **metric-resolver** | 指标别名解析 | `/api/v2/market_metric/get_metrics` | Global |

---

## 能力缺口详细列表

### 🔴 **一级缺口**（完全不支持）

#### 1. **选股/筛选功能** ⭐ 最严重
- **缺失内容**：
  - 无法按条件筛选（"PE < 20"、"ROE > 15%"、"市值 > 100 亿"）
  - 无排序/排名功能（"PE 最低的 20 只股"、"涨幅前 10"）
- **当前限制**：skill 仅能按 symbol 查询，不能按 metric 反向查询
- **文档提示**：`references/industry-and-symbols.md` 明确标注 "stock-screening skill **not yet delivered** (upstream limitation)"
- **业务影响**：量化选股、多因子模型等核心需求完全无法满足

#### 2. **概念/板块聚合**
- **缺失内容**：无法解析"白酒板块"、"AI 概念股"、"新能源"等集合名称 → 股票列表
- **文档提示**：`references/industry-and-symbols.md` 明确说 "requires `match_collection`; this skill does not implement it"
- **业务影响**：板块轮动分析无法进行

#### 3. **策略回测/历史表现计算** ⭐ 次严重
- **缺失内容**：
  - 无法计算长期累计收益（期货有滚动合约价格跳跃问题）
  - 无回测框架（无法处理调仓、费用、滑点等）
- **文档提示**：
  ```
  "Strategy backtest performance → backtest skill **not yet delivered** 
  (upstream limitation, tracked separately)"
  ```
  仅能返回原始 adj_close 给 LLM 客户端自行计算
- **陷阱**：期货 `close` 头尾比较会被滚动日跳跃污染，精度严重受损

#### 4. **新闻/事件/公告**
- 完全无新闻、重大公告、重组、停牌等事件数据
- 仅在 `avail_date` 字段间接提示财报披露日期

#### 5. **技术指标**
- 仅提供 OHLCV，无 MACD、RSI、布林带、移动平均线等技术指标
- 用户需要在客户端自行计算

---

### 🟠 **二级缺口**（部分支持或支持不完整）

#### 6. **债券/固收数据**
- 完全无债券数据（收益率曲线、信用债等）

#### 7. **衍生品**
- 无期权、权证、转债数据

#### 8. **宏观经济指标**
- 无 GDP、CPI、失业率、利率等宏观数据
- 无行业景气指数等先行指标

#### 9. **盘口深度数据**
- 仅有 OHLCV 和成交额/成交量
- 无分时数据、五档盘口、委托单等实时深度数据
- 无主力资金流向等特殊数据

#### 10. **美国市场支持不完整**
```
cn/hk:stock × {financial, indicator, market_cap, valuation} ✅
us:stock × {market_cap} ✅; 其他组合 ❌
```
- US 仅支持市值数据，无财务报表、指标、估值序列
- US 期权、债券等都不支持
- 文档提示：`financial-context` 仅覆盖 cn/hk 市场

#### 11. **加密货币**
- **realtime-quote**：支持获取最新价格（freshness 可能是 latest_close）
- **price-history**：明确不可用，返回 error
  ```
  "metadata.warnings": ["fetch failed: Missing config: database_url - crypto"]
  ```
- 几乎无实际用途

---

### 🟡 **三级缺口**（数据陷阱/需要特殊处理）

#### 12. **HK 股票币种缺失**
- HK `income / balance_sheet / cashflow / valuation` 无 `currency` 字段
- 无 `segments` 数据（CN 有，HK 始终返回 null）
- **需人工推断**：
  - H 股内地公司（腾讯 00700）→ RMB
  - 本港公司（汇丰 00005）→ HKD
  - 跨上市公司（东方海外 00316）→ USD
- 文档明确警告：**"不要默认 HKD — 默认 HKD 给 H 股内地公司会出大错"**

#### 13. **CN/HK 市场累计/单季逻辑相反** ⚠️
```
市场 | use_ytd_value 默认
CN   | False (单季)
HK   | True  (累计)
```
- `OPER_REV` 在 CN 下默认返回单季数据，HK 下默认累计
- 容易导致 ~4 倍的数据错误
- 仅限 `data_type=financial`；`indicator` 下无此问题

#### 14. **期货滚动合约价格跳跃**
- 返回"主合约"连续序列，但合约交割日会产生 **1-5% 的非市场价格跳跃**
- 无法直接用 `close` 头尾计算长期收益
- 需要识别 `oi`（持仓量）陡降作为滚动信号、或使用 `pct_change` 字段
- 文档明确标注：**"Do not compute daily return directly on continuous series"**

#### 15. **业务分部数据口径变化**
- 公司发生并购、分拆、重组时，`segments.data[*].sales_yoy` 会产生 **非业务原因的数字断层**
- `|sales_yoy| > 200%` 或某分部前有后无/前无后有 → 需主动告知用户
- 无自动识别机制，需 LLM 识别异常并提示

#### 16. **指数成分幸存者偏差**
- `index_member` 仅返回当前成分股，无历史增删轨迹
- 用户无法追踪"过去 5 年所有曾经在 CSI 300 里的股票"
- 只能问"CSI 300 今天有哪些"

#### 17. **指标数据稀疏性**
- `consensus_forecast / estimate` 是稀疏时间序列，不是每个交易日都有数据
- 某个 symbol 可能只有特定交易日的预期更新，其他日期无记录

#### 18. **inline_threshold 截断问题**
- 默认仅返回 50 行，超过需手动指定 `inline_threshold` (最大 1000)
- 大规模查询（如"5 年内所有财报"）可能被截断成无用的 preview
- 需 LLM 判断是否会超过 1000 行，如超则需 fail-loud 或分片查询

#### 19. **股本/流通股定义差异**
- `market_cap` endpoint 的 `extra.total` 参数：
  - `false` = 流通 A 股（默认）
  - `true` = 总股本
- 文档：**"Measured: default share is `float_a_shares`, not total"**
- 容易与用户预期不符

---

### 🟢 **特殊限制**（工程约束）

#### 20. **Wind API 内部实现细节暴露**
- Response 中有 `_source_map` 字段暴露底层表名（`AShareIncome` / `wind_*`）
- Skill 严格要求 **"NEVER show to user"** (会锁定数据源切换灵活性)
- 同样约束：metric 别名、industry 前缀（`申万-` / `wind-` / `sw-`）

#### 21. **API 响应时间未暴露**
- 仅返回 `elapsed_ms`，无法预测什么时候会 timeout
- 大规模查询的失败处理较为被动

#### 22. **PIT (Point-In-Time) 数据复杂性** ⚠️
- `avail_date` (财报披露日) 与 `report_date` (报告期末) 不同
- L2/L3 `financial-context` 中有 `indicator_is_fallback` 标志（指标用了上期数据）
- 需谨慎处理，否则会产生 look-ahead bias

---

## 核心限制总结表

| 能力类别 | 支持度 | 关键限制 |
|---------|------|---------|
| **行情数据** | ✅ 完整 | 无深度盘口数据 |
| **财务报表** | ⚠️ CN/HK 完整，US 无 | |
| **估值序列** | ⚠️ 仅 5y 分位预设，其他窗口需手算 | |
| **一致预期** | ⚠️ CN only | 稀疏数据，无全量信号 |
| **行业分类** | ✅ CN/HK/US | 无板块聚合(match_collection) |
| **选股/筛选** | ❌ 完全不支持 | |
| **回测框架** | ❌ 完全不支持 | |
| **技术指标** | ❌ 无内置 | |
| **宏观数据** | ❌ 完全无 | |
| **新闻事件** | ❌ 完全无 | |

---

## 使用建议

### ✅ 擅长场景
1. **单个公司深度分析** - 一键财务+估值+预期分析
2. **实时价格查询** - 跨市场批量行情
3. **历史价格计算** - 累计收益、区间涨跌（需用 adj_close）
4. **行业分类查询** - 某公司属于哪个行业、某指数成分是谁
5. **财务对标** - 同行业公司的财务指标对比

### ❌ 无法满足的场景
1. 量化选股、因子研究（无条件筛选）
2. 策略回测、历史表现评估（无回测框架）
3. 技术面分析（无技术指标）
4. 实时对冲、盘口交易（无深度数据）
5. 美国市场深度分析（US 数据不完整）
6. 加密货币分析（price-history 不可用）
7. 宏观分析、债券分析（完全无此类数据）

---

## 关键代码陷阱（LLM 需规避）

```python
# ❌ 错误1：期货长期收益直接计算
return (close[-1] / close[0]) - 1  # 被滚动日跳跃污染

# ✅ 正确：
return (pct_change.sum())  # 使用 pct_change 字段，或识别滚动日后排除

# ❌ 错误2：CN 全年营收用默认单季
oper_rev = call_fundamentals(symbol, "2024-01-01", "2024-12-31")  # 返回 Q4 单季

# ✅ 正确：
oper_rev = call_fundamentals(symbol, "2024-01-01", "2024-12-31", use_ytd_value=True)

# ❌ 错误3：HK 股票不标注币种
f"Tencent 净利润：{np:.2f}"  # 用户不知道是 RMB 还是 HKD

# ✅ 正确：
f"Tencent 净利润：{np:.2f} RMB（H股内地公司，按 IFRS 用人民币报表）"

# ❌ 错误4：大规模查询不设 inline_threshold
datareader(symbols=csi_300, data_type="financial")  # 默认 50 行截断

# ✅ 正确：
datareader(symbols=csi_300, data_type="financial", inline_threshold=1000)
# 如果仍 > 1000 则分片或 fail-loud
```

---

## 文档中的关键警告

| 警告 | 位置 | 影响 |
|-----|------|------|
| 期货滚动日污染 | `price-history.md` | 长期回测无法信任 |
| HK 币种无信号 | `financial-context.md` | 需人工推断，易出错 |
| CN/HK 累计逻辑反向 | `fundamentals-panel.md` (b1 caveat) | ~4 倍精度错误风险 |
| 选股不支持 | `industry-and-symbols.md` | 无法按条件查询 |
| 回测不支持 | `price-history.md` | 无 backtest framework |
| 业务分部口径变化 | `financial-context.md` | 并购重组数据不可信 |
| US 财务数据缺失 | `fundamentals-panel.md` | US 仅能看市值/实时价格 |
| Crypto price 不可用 | `price-history.md` | 加密货币价格历史查不到 |

---

## 与 Wind API 的映射关系

Stocki skill 是 Wind API 的一层轻量包装：
- ✅ 实时行情 → 直接 pass-through
- ✅ 历史价格/财务 → `/api/v3/datareader/read` 包装
- ✅ 综合分析 → `/api/v3/financial_context` 聚合
- ❌ Wind 本身无选股/回测 → Skill 也无
- ❌ Wind 无债券/期权 → Skill 也无

数据质量/覆盖范围完全继承 Wind API 的限制。
