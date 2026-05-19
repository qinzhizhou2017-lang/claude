<!-- stocki-financial-reader v0.3.0 -->
---
name: stocki-financial-reader
version: 0.3.0
description: "Institutional-grade financial data skill for OpenClaw. Real-time quotes, financials, valuation time series, OHLCV history, industry membership, consensus forecasts, composite analysis. Covers cn/hk/us markets and stock/index/etf/futures/crypto. For structured market/financial data, use this skill."
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: [python3]
      env: [STOCKI_GATEWAY_URL, STOCKI_API_KEY]
      os: [linux, darwin]
    primaryEnv: STOCKI_API_KEY
    envVars: [STOCKI_GATEWAY_URL, STOCKI_API_KEY]
---

# stocki-financial-reader

Institutional-grade financial data analyst skill. Aggregates 8 reference docs that teach the LLM how to retrieve structured market/financial data via HTTP. Routes user queries to the right reference, handles output discipline (no data-vendor leakage), and ships self-diagnostic scripts.

## Core Principle

**For structured market/financial data, use this skill.** Examples: real-time prices, OHLCV history, financial statements, valuation time series, industry membership, consensus forecasts, composite company analysis.

**Do NOT use this skill for**: general financial knowledge questions ("what is P/E ratio?"), news commentary without data backing, or anything requiring fabricated numbers.

**Never fabricate market data.** If a value is not in a real response, say so. Completeness and output discipline are non-negotiable.

**Stay non-advisory.** Relay numbers and the response's own context fields (percentiles / industry comparisons). Do NOT append buy/sell/hold ratings, target-price opinions, or personalized recommendations on top of the data.

## HTTP Convention

All references share these conventions. The router enforces them globally; individual references may override only with explicit justification.

- **Base URL**: `$STOCKI_GATEWAY_URL` (env var). Set to `http://localhost:9996` in dev or `https://api.stocki.com.cn` in prod.
- **Auth**: every request carries `Authorization: Bearer $STOCKI_API_KEY`. localhost dev mode does not validate but the header MUST still be sent (no environment-conditional code paths).
- **Content-Type**: `application/json` for all POST.
- **Error code mapping** (mirrors `scripts/_http.py` exit codes):

  | HTTP | Mapped error code | Exit code |
  |---|---|---|
  | 401 | `auth_invalid` | 1 |
  | 503 / 504 / 5xx / timeout | `stocki_unavailable` | 3 |
  | 429 / quota | `rate_limited` | 4 |
  | TCP/DNS refused | `unreachable` | 2 |

## Inline Threshold (`/api/v3/datareader/read` only)

The stocki gateway v3 默认按 50 行截断 `response.data`;超过部分目前 runtime 不读取
外部存储。Body 参数 `inline_threshold`(max 1000)可把 inline 上限抬到 1000,
覆盖绝大部分时序需求。

**Scope**:仅 `/api/v3/datareader/read` 读此参数。其他 v3/v2/executor 端点静默忽略,
**禁止**给 `financial_context/*` / `quotes/*` / `market/*` / `executor/*` / v2
端点传 `inline_threshold`(会误导对响应结构的理解)。

**估算先行**:`N = unique_symbols × time_window_trading_days × unique_metrics`。
形态特化:
- `index_member` panel:`成分股数 × 时间窗交易日`
- `fundamental` / `indicator`:`symbols × 时间窗内财报期数`(年 1 / 季 4)
- `consensus` / `estimate`:`symbols × 时间窗内有发布的交易日`(稀疏)
- `revenue_breakdown`:`symbols × 期数 × 估 5-15 segments`
- `company_info`:`symbols`(静态)

**Margin 表**(中心化):

| data_type | margin |
|---|---|
| `price` / `fundamental` / `indicator` / `company_info` | ×1.2 |
| `consensus` / `estimate` / `forecast` | ×1.5 |
| `index_member` | ×1.33 |
| `revenue_breakdown` | ×2.0 |

**四档分支**:

| N | 行为 |
|---|---|
| ≤ 50 | 不设 `inline_threshold`,默认 50 已覆盖 |
| 50 < N ≤ 1000 | 设 `inline_threshold = min(ceil(N × margin), 1000)` |
| > 1000 | 先 narrow query(单日 / 单 symbol / 显式 metrics);仍 >1000 → fail-loud「当前只能返回前 1000 行预览,完整数据请联系数据团队」 |
| 未知 | 设 `inline_threshold = 1000`;响应后校验 `total_records ≤ 1000`;>1000 走 narrow / fail-loud |

**禁止**:
- ✗ 一律设 1000(token 浪费)
- ✗ N>1000 继续用截断数据回答(误导用户)
- ✗ 用户层文本出现内部存储术语(`data_path` / 内部 bucket 路径 / 文件后缀 等)

## Routing Table

8 references, organized in 3 tiers. Trigger keywords are multilingual (Chinese / English / mixed).

| Tier | Trigger keywords (CN / EN) | Reference |
|---|---|---|
| 0 (preprocessor) | metric name not in `fundamentals-panel` cheatsheet | `references/metric-resolver.md` |
| 1 (composite-first, cn/hk only) | analyze X / 分析 / 综合 / 贵不贵 / 健康吗 / 业务结构 / 哪条业务最快 / 为什么涨/跌 / 共识修正轨迹 | `references/financial-context.md` |
| 2 (current snapshot) | now / 现价 / 实时 / intraday / "PE 现在" / "ROE 现在" | `references/realtime-quote.md` |
| 2 (price time series) | history / K 线 / OHLCV / 区间收益 / 复权 / 走势 | `references/price-history.md` |
| 2 (fundamentals panel) | "营收 8 季度" / "PE 历史时序" / "ROE 4 季趋势" / "三表 Q4" / 总市值时序 / 单季 / 累计 / TTM | `references/fundamentals-panel.md` |
| 2 (forecast snapshot) | consensus / 一致预期 / 目标价 / 分部 (when financial-context unavailable) | `references/consensus-and-target.md` |
| 2 (registry) | industry / 行业 / 成分股 / 公司简介 / 上市日期 / 股本注册表 | `references/industry-and-symbols.md` |
| 2 (calendar) | trading days / 交易日 / availability / 开盘了吗 / N 月有几个交易日 | `references/market-calendar.md` |

### Routing Decision Rules (R1–R8)

Apply in order. Later rules can override earlier ones if user intent is specific.

- **R1. Open-ended fundamentals analysis → `financial-context`** (cn/hk only). User asks generically without naming a specific metric ("分析下 X / X 基本面怎么样 / X 贵不贵 / X 健康吗 / 业务结构 / 哪条业务最快 / 为什么涨跌 / 共识修正轨迹"). Pick L1 / L2 / L3 by depth. Do NOT chain `fundamentals-panel + consensus-and-target + price-history` to recreate what one composite call returns.

- **R2. `financial-context` only ships pre-computed 5-year valuation percentile fields** (`pe_ttm_percentile_5y` / `pb_percentile_5y` / `ps_ttm_percentile_5y` etc.). It does NOT compute arbitrary windows. User asks 5y percentile → use these fields directly (even when a specific metric like PE/PB is named, do NOT go to `fundamentals-panel` to recompute). User asks any other window (3y / 10y / "历史" without specifying) → upstream does NOT serve this directly. Pull raw daily series via `fundamentals-panel` `data_type=valuation` and EITHER (a) compute percentile rank from the series and label clearly as "approximation from raw series", OR (b) tell the user only 5y is directly supported.

- **R3. Full consensus time series is exclusive to `financial-context` L3** (≥132 records). When using L3, do NOT additionally call `consensus-and-target`.

- **R4. Current single value (PE/ROE/PB now)** → `realtime-quote` with `include_fundamentals=true`. Lighter than `fundamentals-panel` with `extra.daily=true` and carries an explicit freshness signal.

- **R5. Specific named metric(s), multi-period panel → `fundamentals-panel`**. User explicitly names one or more financial / derived indicator / valuation metric(s) and wants a time-series panel ("8 季度营收 / ROE 4 季 / 毛利率历史 / PE 时序 / 总市值历史 / 三表 Q4"). Pick `data_type` ∈ {financial, indicator, market_cap, valuation} by metric kind.

- **R6. us:stock fallback.** `financial-context` and most `fundamentals-panel` data_types are unavailable for us. Surface upstream `availability` warning to user; fall back to `realtime-quote` for current value, `fundamentals-panel data_type=market_cap` (only us-supported), `price-history` for OHLCV.

- **R7. Multi-call is allowed and expected.** A query like "AAPL 现价 + 一致预期 + 行业" correctly results in 3 reference calls. Do NOT collapse into a single reference at the cost of correctness.

- **R8. `metric-resolver` is a preprocessor, not a routing target.** Runs *before* `fundamentals-panel` (or `financial-context` field lookup) when user mentions a metric name not in the cheatsheet, returning canonical raw key + EN/CN label for the actual data call.

**R1 vs R5 litmus test**: Did user name a specific metric? No → R1; yes + single point → R4; yes + multi-period panel → R5; any + 5y percentile → R2 override.

## Output Discipline

When relaying response content to user-visible text, **never expose** any data-vendor identifiable artifacts:

| Category | Forbidden form | Required form |
|---|---|---|
| symbol | pipe-delimited (`AAPL\|ST\|USA`) | bare code (`AAPL`, `600519`) |
| metric | uppercase canonical (`OPER_REV`, `WAA_ROE`) | EN label ("Total Revenue") or CN label ("营业总收入") by user language |
| industry | vendor prefix (`wind-`, `sw-`, `申万-`, `中信-`) | category itself ("食品饮料") |

**Why**: data-vendor identity is implementation detail. Leaking it locks the output format and prevents future source switches. Each reference's `Response Fields — Raw → User-Facing Label` table is the source of truth for label mappings; metric-resolver's `name` field is fallback when not in the cheatsheet.

## Doctor / Diagnose

Run before reporting any setup issue or after install:

```bash
python3 {baseDir}/scripts/doctor.py     # env / version / file integrity / workspace
python3 {baseDir}/scripts/diagnose.py   # gateway reachability + auth + read smoke test
```

Exit codes (uniform across all scripts):
- `0` ok
- `1` auth invalid
- `2` unreachable (TCP/DNS layer)
- `3` stocki unavailable (5xx / timeout)
- `4` rate limited / quota exceeded

When a script fails, **report the exit code verbatim and stop**. Do not retry.

## Cross-ref

See `INSTALL.md` for setup. See `references/<n>.md` for per-endpoint contracts.

---

## Reference Documents

# consensus-and-target

## Overview

Packages 3 related data_types: (A) `consensus_forecast` — sell-side consensus estimates; (B) `target_price` — broker-merged target price; (C) `revenue_breakdown` — primary-business segment composition. All go through `/api/v3/datareader/read`, covered only for `cn:stock`. Default columns are sufficient (no need to route through metric-resolver).

## Trigger Vocabulary

- 中文："市场对 X 预期 / 卖方预期 / 一致预期 / 隐含 PE / 隐含 PB / 分析师上调 / 下调 / 业绩预测 / 目标价 / 券商目标价 / 主营业务 / 业务分部 / 分产品 / 分地区 / 分渠道 / 营收构成 / 占比"
- English: "consensus forecast / sell-side estimate / target price / implied PE / implied valuation / segment / revenue breakdown / by product / by region"
- Boundaries:
  - Historical realised financials ("revenue of the past 4 quarters") → `fundamentals-panel.md`
  - One-shot composite "give me an overview of Moutai" → `financial-context.md` L1 (includes a lite consensus block)
  - Need the full 9–16 field segments + by_dimension grouping for business structure → `financial-context.md` L2/L3 (**avoid calling this skill plus financial-context twice**)
  - "What is PE right now / PE time series" → `fundamentals-panel.md` (valuation)

## Endpoint

| Method | Path | data_type | Purpose |
|---|---|---|---|
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `consensus_forecast` | Sell-side consensus, multi con_year × multi date snapshots |
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `target_price` | Broker-merged target-price time series |
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `revenue_breakdown` | Primary-business segments (by channel / product / region dimension) |

## Input schema

### A. consensus_forecast

```json
{
  "area": "cn",
  "asset_type": "stock",
  "data_type": "consensus_forecast",
  "symbols": ["600519"],
  "start_date": "2026-01-01",
  "end_date": "2026-04-30",
  "extra": {"con_years": [2026, 2027]}
}
```

| Field | Required | Description |
|---|---|---|
| `start_date / end_date` | yes | Snapshot date range; server defaults to a 90-day lookback cap (observed: omitting still works, but the behaviour is undocumented) |
| `extra.con_years` | no | list[int]; pull multiple con_years in one call; omit = all fiscal years with data |
| `inline_threshold` | no | int, range `[1, 1000]`, default 50 (silently clamped). Pass when expected `total_records > 50` to avoid truncation; consensus is sparse — estimate `N = symbols × posted_days_in_window` and set `min(ceil(N × 1.5), 1000)`. **Full decision rule: SKILL.md §Inline Threshold.** |

Multiple `date` snapshots = consensus-revision trajectory (track `con_eps / con_np_yoy` evolution for the same con_year).

### B. target_price

```json
{
  "area": "cn",
  "asset_type": "stock",
  "data_type": "target_price",
  "symbols": ["600519"],
  "start_date": "2026-01-01",
  "end_date": "2026-04-30"
}
```

Returns only the merged `con_target_price`. Use multiple dates to see upgrades / downgrades.

### C. revenue_breakdown

```json
{
  "area": "cn",
  "asset_type": "stock",
  "data_type": "revenue_breakdown",
  "symbols": ["600519"],
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "extra": {"report_periods": ["20241231"]}
}
```

⚠️ **`extra.report_periods` is required** (list[str] YYYYMMDD; sourced from `dataLoader_v2/estimate/revenue_breakdown.py` "REQUIRED").
⚠️ **`start_date / end_date` are also required** (verified 2026-05-08: the old spec said "ignored" — formally they do not participate in time filtering, but omitting them still triggers a NaTType crash. Pass placeholders, e.g. start = 1 Jan of the earliest report_periods year / end = 1 Jan of the year after the latest report_periods; see notes §11).
⚠️ **`metrics` is also ignored** (safer to omit; passing any metric does not filter columns — the response is always 17 columns).

Typical cross-year / cross-half-year `report_periods`: `["20231231","20240630","20241231"]`; supply multiple year-ends to inspect annual trends.

## E2E examples

**(a) consensus_forecast — single stock latest consensus**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"consensus_forecast","symbols":["600519"],"start_date":"2026-04-01","end_date":"2026-04-30","extra":{"con_years":[2026]}}'
```
Expected: `data[*] = {code, date, stock_name, con_year, con_or, con_np, con_eps, con_pe, con_pb, con_peg, con_roe, con_or_yoy, con_np_yoy}`. **Units**: `con_or / con_np` in 万元 (ten-thousand yuan); `con_pe / con_pb / con_peg / con_roe` dimensionless; `con_or_yoy / con_np_yoy` percent.

**(b) Revision trajectory — multi-date snapshots tracking consensus evolution**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"consensus_forecast","symbols":["600519"],"start_date":"2026-01-01","end_date":"2026-04-30","extra":{"con_years":[2026]}}'
```
Take `con_eps / con_np_yoy` at each date; the time-series change = analyst upgrade / downgrade trajectory. Note: the server defaults to a 90-day lookback, longer ranges get truncated.

**(c) target_price — target-price time series**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"target_price","symbols":["600519"],"start_date":"2026-01-01","end_date":"2026-04-30"}'
```
Expected: `data[*] = {code, date, stock_name, con_target_price}` (unit: yuan). Compare against current close → implied upside.

**(d) revenue_breakdown — primary-business segments**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"revenue_breakdown","symbols":["600519"],"start_date":"2024-01-01","end_date":"2025-01-01","extra":{"report_periods":["20241231"]}}'
```
Expected: `data[*]` with 17 fields: `code / date / ann_dt / currency / segment / segment_type / segment_itemcode / sales / sales_percentage / sales_yoy / profit / profit_percentage / profit_yoy / cost / cost_percentage / cost_yoy / gross_profit_margin / gross_profit_margin_yoy`. `segment_type` ∈ `channel / product / region / industry`; to group by dimension, client-side group-by `segment_type`. `ann_dt` is the announcement disclosure date (PIT-critical).

**(e) Upstream error pass-through — revenue_breakdown missing report_periods**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"revenue_breakdown","symbols":["600519"],"start_date":"2024-01-01","end_date":"2025-01-01"}'
```
Expected: `action=error`; the skill teaches the LLM that on seeing this error it should automatically retry once with `extra.report_periods` added (typically the most recent 4 annual / semi-annual reports, e.g. `["20231231","20240630","20241231"]`), and only surface the error to the user if the retry still fails.

## Response Fields — Raw → User-Facing Label

### data_type=consensus_forecast (consensus across analysts)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Symbol code | 代码 | |
| `data[*].date` | Snapshot date | 快照日期 | |
| `data[*].stock_name` | Stock name | 股票名称 | |
| `data[*].con_year` | Forecast year | 预测财年 | int |
| `data[*].con_or` | Consensus Revenue | 一致预期营收 | unit: 万元 |
| `data[*].con_np` | Consensus Net Profit | 一致预期净利润 | unit: 万元 |
| `data[*].con_eps` | Consensus EPS | 一致预期 EPS | unit: 元 |
| `data[*].con_pe` | Consensus PE | 一致 PE | implied; dimensionless |
| `data[*].con_pb` | Consensus PB | 一致 PB | implied; dimensionless |
| `data[*].con_peg` | Consensus PEG | 一致 PEG | implied; dimensionless |
| `data[*].con_roe` | Consensus ROE | 一致 ROE | percent |
| `data[*].con_or_yoy` | Revenue YoY (consensus) | 营收同比预期 | percent |
| `data[*].con_np_yoy` | Net Profit YoY (consensus) | 净利同比预期 | percent |

### data_type=target_price (merged sell-side target)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Symbol code | 代码 | |
| `data[*].date` | Snapshot date | 快照日期 | |
| `data[*].stock_name` | Stock name | 股票名称 | |
| `data[*].con_target_price` | Consensus Target Price | 一致目标价 | unit: 元; compare to current close for implied upside/downside |

### data_type=revenue_breakdown (segment composition)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Symbol code | 代码 | |
| `data[*].date` | Date | 日期 | |
| `data[*].ann_dt` | Announcement Date | 公告披露日 | PIT-critical |
| `data[*].currency` | Currency | 币种 | |
| `data[*].segment` | Segment name | 分部名称 | strip `wind-` / `sw-` / `申万-` prefix if present |
| `data[*].segment_type` | Segment type | 分部维度 | enum: channel / product / region / industry |
| `data[*].segment_itemcode` | Segment item code | 分部代码 | |
| `data[*].sales` | Sales | 销售额 | unit: 元 |
| `data[*].sales_percentage` | Sales share | 销售占比 | percent |
| `data[*].sales_yoy` | Sales YoY | 销售同比 | percent |
| `data[*].profit` | Profit | 利润 | unit: 元 |
| `data[*].profit_percentage` | Profit share | 利润占比 | percent |
| `data[*].profit_yoy` | Profit YoY | 利润同比 | percent |
| `data[*].cost` | Cost | 成本 | unit: 元 |
| `data[*].cost_percentage` | Cost share | 成本占比 | percent |
| `data[*].cost_yoy` | Cost YoY | 成本同比 | percent |
| `data[*].gross_profit_margin` | Gross Margin | 毛利率 | percent |
| `data[*].gross_profit_margin_yoy` | Gross Margin YoY | 毛利率同比 | percentage points |

### Common envelope

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `metadata.data_path` | CSV Path | CSV 路径 | triggered when `total_records > inline_threshold` (default 50). CSV not directly fetchable from the runtime — **prefer raising `inline_threshold` (max 1000) on the request** rather than relying on this path. |
| `metadata.warnings` | Warnings | 警告 | upstream errors / truncation; MUST be surfaced to the user |

**Target-price presentation discipline**: when comparing `con_target_price` to current close, surface "implied upside +X%" / "implied downside −X%" prose rather than echoing the raw field name.

**Segment-prefix discipline**: if `segment` values carry `申万-` / `wind-` / `sw-` prefix, strip the prefix before showing to the user (same rule as `industry-and-symbols.md`).

**Output discipline**: never pass raw key (`con_or`, `con_target_price`, `segment_type`, pipe-delim symbol like `AAPL|ST|USA`, `wind-`/`sw-`/`申万-` industry prefix) to user-visible text. Agent picks EN or CN label based on the user's language.

## Cross-ref

- Composite + L2 segments + L3 full consensus 138-record time series → `financial-context.md` (avoid calling this skill plus financial-context twice)
- Historical three-statement financials / valuation / metrics → `fundamentals-panel.md`
- Company industry / sector mapping → `industry-and-symbols.md`
- Current PE realtime value → `realtime-quote.md` `include_fundamentals=true`

# financial-context

## Overview

Stocki gateway one-shot composite view: a single call returns 11 sections (`meta` / `valuation` with 5y percentiles / `income` / `balance_sheet` / `cashflow` / `indicator` / `consensus` / `segments` / `field_descriptions` / `_source_map` / `history`). `layer` ∈ {1, 2, 3} controls depth. **The `metrics` parameter is NOT accepted** — the column set is decided server-side.

## Trigger Vocabulary

- 中文："分析一下 / 综合分析 / 看下基本面 / X 贵不贵 / X 财务健康 / 业务结构 / 哪条业务增长最快 / 主营拆解 / 销售涨利润跌为什么 / 多角度 / 一键 / 深度追因 / 5 年分位 / 历史分位"
- English: "analyze X / fundamentals overview / financial context / valuation percentile / business segments / why revenue up profit down"
- Boundaries:
  - Single-field time series ("PE history / revenue over 8 quarters") → `fundamentals-panel.md`
  - Sell-side estimates / target price only (no financial cross-check) → `consensus-and-target.md`
  - Realtime price + current PE only → `realtime-quote.md`
  - Company industry / sector / listing date → `industry-and-symbols.md`
  - **L1 already answers "analyze Moutai" — DO NOT instinctively jump to `fundamentals-panel.md` and chain multiple calls.**

## Endpoint

| Method | Path | Purpose |
|---|---|---|
| POST | `$STOCKI_GATEWAY_URL/api/v3/financial_context/cn` | A-share composite single-stock view |
| POST | `$STOCKI_GATEWAY_URL/api/v3/financial_context/hk` | HK composite single-stock view |

## Input schema

```json
{
  "symbol": "600519",
  "layer": 1,
  "current_date": "2026-05-08",
  "pit": false
}
```

| Field | Required | Description |
|---|---|---|
| `symbol` | yes | bare code ("600519" / "00700"), no exchange suffix |
| `layer` | yes | `1 / 2 / 3`, depth (see table below) |
| `current_date` | no | YYYY-MM-DD, PIT cutoff; omitted = server uses today (server tz) |
| `pit` | no | true = segments strictly filtered by `ann_dt <= current_date`; default false (friendlier for realtime analysis) |

⚠️ **Do NOT pass `inline_threshold` to this endpoint.** `/api/v3/financial_context/{cn,hk}` returns a composite dict (`valuation` / `income` / `balance_sheet` / `cashflow` / `indicator` / `consensus` / `segments` / `field_descriptions` / ...), not a paginated `data` list — the parameter is silently ignored. `inline_threshold` only applies to `/api/v3/datareader/read` (see SKILL.md §Inline Threshold).

## Layer differences

| Layer | Segments detail | Consensus records | Suitable for |
|---|---|---|---|
| 1 | stub (only `available_at_layer=2` + `dimensions[]`) | ≤ 2 (current_fy + next_fy) | "analyze Moutai / is Moutai expensive" generic composite view |
| 2 | 9-field records + `by_dimension` grouping | ≤ 3 | "Moutai business structure / which segment is growing fastest" |
| 3 | 16-field records (cost / profit / yoy cross-validation) | **132+ records, full time series** | "Why is Moutai revenue up but profit down / consensus revision trajectory" |

⚠️ **L3 already contains the complete consensus time series — do not call `consensus-and-target.md` again.**

## E2E examples

**(a) L1 composite analysis — "analyze Moutai"**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/financial_context/cn" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"symbol":"600519","layer":1}'
```
Expected: 11 sections. Key fields:
- `meta.{symbol, name, area, report_period, report_date, query_date, data_freshness}`
- `valuation` with 5y percentiles (e.g. `pe_ttm_percentile_5y`) — use this when the user asks "is it expensive"
- `income / balance_sheet / cashflow / indicator` are each a dict containing the latest report-period values + YoY + QoQ

**(b) L2 business structure — "which Moutai segment grows fastest"**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/financial_context/cn" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"symbol":"600519","layer":2}'
```
Expected: `segments.data` ≥ 5 records (one per segment), each with 9 fields (`ann_dt, currency, segment, segment_type, sales, sales_percentage, sales_yoy, profit_percentage, gross_profit_margin`) + `segments.by_dimension` containing `channel / product / region / industry` groups.

**(c) L3 consensus time series — "in the last 3 months have analysts revised Moutai up or down"**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/financial_context/cn" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"symbol":"600519","layer":3}'
```
Expected: `consensus` ≥ 100 records (ascending by date) + `segments.data` with the richer 16-field shape. **Do NOT additionally call `consensus-and-target.md`.**

**(d) Multi-market — hk Tencent**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/financial_context/hk" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"symbol":"00700","layer":1}'
```
Expected: action=success, `meta` contains `name_eng` "TENCENT". Note: when hk `data_freshness.indicator_is_fallback=true`, indicator data used the previous-period fallback — surface to the user as "indicators are one period behind financials".

**(e) Upstream error pass-through — symbol does not exist**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/financial_context/cn" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"symbol":"999999","layer":1}'
```
Expected: 4xx / error JSON; the skill surfaces the error message to the user and suggests first confirming the symbol exists via `industry-and-symbols.md` `get_symbols`.

## Response Fields — Raw → User-Facing Label

The response is a single JSON object with 11 top-level sections; depth scales with `layer`. The tables below break out the sections by layer (L1 always returned; L2 adds segment detail; L3 adds full consensus time series). Note: switching `layer` never introduces a new endpoint, only changes return depth — the LLM always makes ONE curl call.

### Always returned (regardless of layer)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `meta.symbol` | Symbol | 代码 | |
| `meta.name` | Stock name (CN) | 中文名 | |
| `meta.name_eng` | Stock name (EN) | 英文名 | hk only |
| `meta.area` | Market | 市场 | enum: cn / hk |
| `meta.report_period` | Report period | 报告期 | most recent financial period end |
| `meta.report_date` | Report date | 报告日期 | |
| `meta.query_date` | Query date | 查询日期 | |
| `meta.data_freshness.financial_report_date` | Financial PIT | 财报披露日 | PIT-critical |
| `meta.data_freshness.indicator_report_date` | Indicator PIT | 指标披露日 | PIT-critical |
| `meta.data_freshness.indicator_is_fallback` | Indicator fallback flag | 指标 fallback 标志 | true = indicator uses previous period; surface to user as "indicators are one period behind financials" |
| `meta.data_freshness.valuation_data_date` | Valuation date | 估值日期 | |
| `field_descriptions` | Field descriptions (CN) | 字段说明 | upstream-supplied CN gloss per returned field; **prefer this as the authoritative CN label source over hand-mapping** |
| `_source_map` | Source map | 数据源映射 | **debug-only** (contains internal table names like `AShareIncome` / `wind_*`); NEVER show to user |
| `history` | History | 历史 | reserved for future expansion |

**HK 币种不可见(数据缺口必须主动告知)**:HK `income / balance_sheet / cashflow / valuation` 各 dict **无 `currency` 字段**;且 hk financial_context response 的 `segments` 字段**始终为 `null`**(layer 1/2/3 均测过——不同于 cn 端 layer ≥ 2 segments.data 实存且带 currency=CNY)。**HK 端没有任何 currency 信号可取**——LLM 必须按公司归属 / 股票类型推断币种:

- H 股内地公司(如腾讯 00700、中广核电力 01816)按 IFRS 用 **RMB** 报表
- 本港公司(如汇丰 00005)用 **HKD**
- 跨上市公司(如东方海外 00316)可能用 **USD**

**展示数值时必须标注币种**;若不确定,显式告知用户"币种基于公司归属推断,请核对最新年报披露",**不要默认 HKD**——默认 HKD 给 H 股内地公司会出大错(RMB 与 HKD 相差近 10% + 长期趋势)。

### L1 / L2 / L3 — Valuation, Income, Balance Sheet, Cashflow, Indicator

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `valuation.pe_ttm` / `valuation.pb` / `valuation.ps_ttm` | Current PE / PB / PS | 当前 市盈率 / 市净率 / 市销率 | trailing-12-month for TTM variants |
| `valuation.pe_ttm_percentile_5y` | PE 5y Percentile | 市盈率 5 年分位 | 5-year rolling rank; surface as "current PE sits at X% of the past 5 years" |
| `valuation.pb_percentile_5y` | PB 5y Percentile | 市净率 5 年分位 | same |
| `valuation.ps_ttm_percentile_5y` | PS 5y Percentile | 市销率 5 年分位 | same |
| `income.*` | Income statement (latest) | 利润表(最新) | dict; latest report period + YoY + QoQ |
| `balance_sheet.*` | Balance sheet (latest) | 资产负债表(最新) | dict; latest snapshot |
| `cashflow.*` | Cash flow statement (latest) | 现金流量表(最新) | dict; latest |
| `indicator.*` | Indicators (latest) | 财务指标(最新) | dict; ROE / margins / turnover etc. |

### L1 (consensus light)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `consensus[*]` | Consensus records | 一致预期记录 | ≤ 2 records (current_fy + next_fy) |
| `segments` | Segments (stub) | 业务分部(stub) | only `available_at_layer=2` + `dimensions[]` placeholders |

### L2 (segments expanded)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `consensus[*]` | Consensus records | 一致预期记录 | ≤ 3 records |
| `segments.data[*]` | Segment records (9 fields) | 业务分部记录(9 字段) | each record: ann_dt, currency, segment, segment_type, sales, sales_percentage, sales_yoy, profit_percentage, gross_profit_margin |
| `segments.by_dimension` | Segments grouped by dimension | 按维度分组 | groups by `segment_type` ∈ channel / product / region / industry |

**Segments YoY 口径陷阱(数据缺口必须主动告知)**:`segments.data[*].sales_yoy` 在公司**并购 / 分拆 / 业务线重组**的当期可能产生**非业务原因**的数字断层。当 `|sales_yoy|` 异常(如 > 200% 或 < -50%)或某 segment 名前期有当期无 / 前期无当期有,展示给用户时**必须主动提示** "该 segment 同比可能因口径变化(并购 / 分拆 / 重组),请核对当期公告",**不要直接解读为业务剧变**。

数据层无法自动识别"是否口径变化"——只能识别"数字异常 / segment 名变更"作为触发信号。最终解读需用户自行核对公告;LLM 的职责是 surface 触发信号,**不**默认按业务逻辑下结论。

### L3 (full consensus time series + 16-field segments)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `consensus[*]` | Consensus time series | 一致预期时序 | ≥ 100 records, ascending by date; DO NOT additionally call `consensus-and-target.md` |
| `segments.data[*]` | Segment records (16 fields) | 业务分部记录(16 字段) | adds cost / profit / cost_yoy / profit_yoy / cost_percentage / gross_profit_margin_yoy for cross-validation |

**5y-window exclusivity**: this endpoint exposes ONLY fixed 5-year percentile fields (`pe_ttm_percentile_5y` etc.). It does NOT compute arbitrary-window percentiles. For 3y / 10y / custom-window questions, fall back to `fundamentals-panel.md` to pull the raw valuation series and compute client-side, and clearly tell the user the figure is an approximation.

**Routing discipline**: L1 already answers generic "analyze X" / "is X expensive" / "X fundamentals" prompts. Do NOT instinctively call `fundamentals-panel.md` and chain multiple endpoints for these questions.

**Field-label sourcing**: prefer `field_descriptions` from the response as the authoritative CN label per field. The hand-mapped section names below cover the high-frequency top-level keys when speed is wanted.

**Top-level section names**: `meta` → 元信息; `valuation` → 估值; `income` → 利润表; `balance_sheet` → 资产负债表; `cashflow` → 现金流量表; `indicator` → 财务指标; `consensus` → 一致预期; `segments` → 业务分部; `field_descriptions` → 字段说明; `_source_map` → 数据源映射 (debug); `history` → 历史.

**Segment-prefix discipline**: segment text with `申万-` / `wind-` / `sw_` / `中信-` prefix MUST be stripped before showing to the user (same rule as `industry-and-symbols.md`).

**Debug-field discipline**: `_source_map`, `_source`, and any other underscore-prefixed internal fields are debug-only — NEVER surface to the user (they contain underlying table names like `AShareIncome` / `wind_*` which would leak data-supplier identity).

**Output discipline**: never pass raw key (`pe_ttm_percentile_5y`, `indicator_is_fallback`, `_source_map`, pipe-delim symbol like `AAPL|ST|USA`, `wind-`/`sw-`/`申万-`/`中信-` industry prefix) to user-visible text. Agent picks EN or CN label based on the user's language; if the response's `field_descriptions` covers a field, prefer that label.

## Cross-ref

- Single-stock price trajectory → `price-history.md`
- Single-field time series (PE history / ROE 4-quarter trend) → `fundamentals-panel.md`
- Full consensus time series → use this skill's **L3**, not `consensus-and-target.md` (avoid duplicate calls)
- Realtime price + current PE → `realtime-quote.md`
- Industry mapping / company profile → `industry-and-symbols.md`
- us single-stock is currently unavailable on v3 and will return error; check live via `market-calendar.md` `/availability`

# fundamentals-panel

## Overview

Stocki gateway v3 unifies the financial statements (3 statements) + derived indicators + valuation time series + market cap behind one endpoint: `/api/v3/datareader/read`, partitioned by `data_type`. **Key LLM decision**: first identify which of the 4 `data_type`s the user is asking about; if a specific metric is needed (instead of the default columns), decide whether to hit the high-frequency cheatsheet below or fall back to `metric-resolver.md`.

Underlying `/api/v3/datareader/read` requires `start_date` / `end_date` and returns multi-period panels for all 4 `data_type`s. For a single-point query use `realtime-quote` with `include_fundamentals=true` instead.

## Trigger Vocabulary

- 中文："营业收入 / 营业利润 / 净利润 / 毛利 / 总资产 / 净资产 / 资产负债率 / 经营现金流 / ROE / ROA / 毛利率 / 净利率 / 周转率 / 杠杆 / PE / 市盈率 / PB / 市净率 / PS / 市销率 / TTM / 总市值 / 流通市值 / 自由流通 / 解禁 / 单季 / 累计 / 年报 / 季报 / 半年报 / 三季报"
- English: "revenue / net income / gross profit / total assets / equity / debt ratio / OCF / ROE / ROA / margin / turnover / leverage / P/E / P/B / P/S / TTM / market cap / free float"
- Boundaries:
  - Consensus estimates / analyst target price / business segments → `consensus-and-target.md`
  - One-shot composite + 5y percentile → `financial-context.md` L1 (preferred for "analyze Moutai"-style questions)
  - "What's Moutai's PE right now?" — real-time single value → `realtime-quote.md` with `include_fundamentals=true` (one call covers it + carries freshness)
  - User's metric name is not in the cheatsheet below → call `metric-resolver.md` first to obtain the canonical symbol, then come back to this skill

## Endpoint

| Method | Path | data_type | Purpose |
|---|---|---|---|
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `financial` | Three statements (income / balance / cashflow), **quarterly panel**, date = period end |
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `indicator` | Derived indicators (ROE / turnover / leverage etc.), quarterly panel |
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `market_cap` | Total / float market cap (`extra.total=true/false` controls scope) |
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `valuation` | Valuation time series + 52w + share counts, **daily panel** |

Availability matrix (measured 2026-05-08; re-check with `market-calendar.md` `/availability` before assuming a change):
- `cn:stock × {financial, indicator, market_cap, valuation}` ✅
- `hk:stock × {financial, indicator, market_cap, valuation}` ✅
- `us:stock × market_cap` ✅; most other us combos are unavailable — pass server `error + warnings` through to the user

<!-- These sections document the upstream API payload contract; canonical metric names below are intentional and not user-visible. -->
<!-- lint:disable rule=canonical-metric -->
## Input schema

```json
{
  "area": "cn",
  "asset_type": "stock",
  "data_type": "financial",
  "symbols": ["600519"],
  "metrics": ["OPER_REV","NET_PROFIT"],
  "start_date": "2024-01-01",
  "end_date": "2025-12-31",
  "extra": {"report_type": "Q4", "daily": false}
}
```

| Field | Required | Description |
|---|---|---|
| `area / asset_type / data_type / symbols` | yes | Same as the v3 datareader common contract |
| `start_date / end_date` | **yes** | The docs say some `data_type`s ignore these, but in practice **omitting them crashes** (NaTType bug, see notes) |
| `metrics` | no | Omit → server returns the default column set; if passed → must be the canonical symbol (not the Chinese name, not a colloquial English name), a miss yields a MySQL `Unknown column` error |
| `extra.report_type` | no | `Q1 / Q2 / Q3 / Q4 / Y` (financial / indicator) |
| `extra.daily` | no | true = **PIT daily frequency** (most recent report period announced as of that day); false = quarterly panel (default) |
| `extra.pit` | no | A different PIT flag from `daily`; mainly affects segments and is generally unused by this skill |
| `extra.total` | no | `market_cap`-only: true=total market cap (default share=total_shares), false=float (default share=float_a_shares). Measured: default share is `float_a_shares`, not total |
| `inline_threshold` | no | int, range `[1, 1000]`, default 50 (silently clamped). Pass when expected `total_records > 50` to avoid truncation; for fundamental/indicator estimate `N = symbols × report_periods` and set `min(ceil(N × 1.2), 1000)`. **Full decision rule: SKILL.md §Inline Threshold.** |

⚠️ **`extra.daily=true` failure handling**: the server returns a regular `error + suggestion`. The skill teaches the LLM to pass the error through to the user; **do not silently retry with daily=false** — this is a client-side convention, the gateway endpoint does not make decisions for the client.

## Mandatory two-step flow (when metrics is semantic, not canonical)

The `metrics` field of `/api/v3/datareader/read` **only accepts canonical symbols** (e.g. `OPER_REV` / `WAA_ROE`). Passing Chinese ("营业收入") or colloquial English ("ROE" / "revenue") → the server's MySQL reports `Unknown column`, the response has `action=error`, and the user sees a failure with no obvious cause.

| Step | Action | Skip consequence |
|---|---|---|
| **1** | Scan the cheatsheet section below. Hit → take the canonical symbol directly. **Miss** → cross-ref `metric-resolver.md` to query the registry and pick one | Skipping `metric-resolver` and passing Chinese directly → guaranteed failure |
| **2** | Put the canonical symbol into `metrics=[...]` and call this skill | — |

> ⚠️ Omitting `metrics` is also legal (the server returns the default column set), but when the user explicitly names a metric you **must resolve** it — do not fall back to default columns and make the user pick.

## `use_ytd_value` 累计/单季陷阱 + CN/HK 默认相反(b1 caveat)

`/api/v3/datareader/read` 对**普通财务 metric**(`OPER_REV` / `NET_PROFIT` / `ROE` / `S_FA_*` 等)走 panel 查询时:

| 市场 | `use_ytd_value` 默认 | 含义 |
|---|---|---|
| CN | **`False`**(单季)| Q1 行 = Q1 单季 / Q2 行 = Q2 单季 / Q3 行 = Q3 单季 / Q4 行 = Q4 单季 |
| HK | **`True`**(累计)| Q1 行 = 3 个月累计 / Q2 行 = 6 个月累计 / Q3 行 = 9 个月累计 / Q4 行 = 12 个月累计 = 全年 |

LLM 路由决策:

- **用户问"全年 / 年报 / 累计营收"** → 必须显式传 `extra.use_ytd_value=true`(CN 必传,HK 默认即是)。否则 CN 拿到 Q4 单季当年报,数字差 ~4 倍。
- **用户问"Q4 单季营收"** → CN 走默认(False)直接拿到;HK 必须显式传 `use_ytd_value=false` + `report_type="Q4"`。
- **`S_QFA_*` 系列在 `data_type=financial` 下不可用**(如 `S_QFA_OPER_REV` / `S_QFA_NET_PROFIT`;实测返 `data=[] + error="No data found"`)——CN 拿单季营收 / 净利润 **直接用 `OPER_REV` / `NET_PROFIT` 默认** 即可。**注意范围**:`S_QFA_*` 在 `data_type=indicator` 下**可用**(如 `S_QFA_ROE_DEDUCTED`,2026-05-12 实测返非空),caveat 边界**仅限 financial reader**,不要扩到 indicator。
- **`report_type` 参数是 HK-only**:CN reader **不解析**该字段(`Q1`/`Q2`/`Q3`/`Q4` 行由 panel 时间窗 + `use_ytd_value` 决定);HK 必须传以选报告期。

**LLM 路由这类 query 时必须显式声明累计/单季并传对应 `use_ytd_value`,不依赖隐式默认。** 向用户回复时只说"单季营收 / 全年累计营收 / 年报营收"等中文表述,**不**把 `OPER_REV` / `S_QFA_*` / `use_ytd_value` / `report_type` 等 canonical 名 / 参数名出现在 user-visible response。

## E2E examples

**(a) Happy path — financial Q4 statement items**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"financial","symbols":["600519"],"metrics":["OPER_REV","NET_PROFIT"],"start_date":"2024-01-01","end_date":"2025-12-31","extra":{"report_type":"Q4"}}'
```
Expected: `data[*] = {code, date, report_period, oper_rev, net_profit, avail_date}`. **Note**: `avail_date` is the announcement date (a PIT-critical field), use it to tell the user when a report "became visible".

**(b) PIT daily=true — backtest preflight**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"valuation","symbols":["600519"],"start_date":"2025-01-01","end_date":"2025-03-31","extra":{"daily":true}}'
```
Expected: `total_records ~90` (one row per day, weekends included); each row carries the full valuation column set. `pe_ttm / pb_new` reflect the TTM valuation as seen by the market on that trading day.

**(c) Multi-market batch — cn vs hk statement comparison** (Rule 7 multi-market coverage):
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"hk","asset_type":"stock","data_type":"financial","symbols":["00700"],"start_date":"2024-01-01","end_date":"2025-12-31"}'
```

**(d) Upstream-error pass-through — us:stock:financial unavailable**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"us","asset_type":"stock","data_type":"financial","symbols":["AAPL"],"start_date":"2024-01-01","end_date":"2025-12-31"}'
```
Expected: `action=error`, `metadata.warnings` carries the reason. Pass warnings through to the user: suggest falling back to `data_type=market_cap` (the only us option that works) or switching to the `realtime-quote` fundamentals snapshot (if only the current value is needed).

**(e) Bad metric — demonstrating why metric-resolver is mandatory**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"indicator","symbols":["600519"],"metrics":["ROE"],"start_date":"2024-01-01","end_date":"2025-12-31"}'
```
Expected: `metadata.warnings` contains `MySqlError ... Unknown column 'ROE' in 'field list'`. The skill teaches the LLM: on seeing this error → cross-ref `metric-resolver.md` to resolve "ROE" into `WAA_ROE` and retry; **do not just tell the user "not found"**.

<!-- lint:enable -->

## Response Fields — Raw → User-Facing Label

Each `data_type` has its own field set; the canonical symbol you put into `metrics=[...]` matches the response key in `data[*]`. Hit the table below → take the canonical symbol; miss → fall back to `metric-resolver.md` (per the two-step flow above).

### data_type=financial (quarterly panel)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `OPER_REV` | Total Revenue | 营业总收入 | unit: 元 |
| ~~`S_QFA_OPER_REV`~~ | ⚠️ Unavailable in `data_type=financial` | (已下架 — 实测返 `data=[]+error`) | CN 单季营收直接用 `OPER_REV` + `extra.use_ytd_value=False`(默认即是); see b1 caveat above |
| `NET_PROFIT` | Net Profit | 净利润 | unit: 元 |
| `NET_PROFIT_INCL_MIN_INT_INC` | Net Profit Incl. Minority | 净利润含少数股东 | unit: 元 |
| ~~`S_QFA_NET_PROFIT`~~ | ⚠️ Unavailable in `data_type=financial` | (已下架 — 实测返 `data=[]+error`) | CN 单季净利润直接用 `NET_PROFIT` + `extra.use_ytd_value=False`(默认即是); see b1 caveat |
| `LESS_OPER_COST` | Operating Cost | 营业成本 | unit: 元 |
| `OPER_PROFIT` | Operating Profit | 营业利润 | unit: 元 |
| `TOT_PROFIT` | Total Profit | 利润总额 | unit: 元 |
| `TOT_ASSETS` | Total Assets | 总资产 | unit: 元 |
| `TOT_LIAB` | Total Liabilities | 总负债 | unit: 元 |
| `TOT_EQUITY` | Total Equity | 所有者权益 | unit: 元 |
| `NET_CASH_FLOWS_OPER_ACT` | Net OCF | 经营活动现金流净额 | unit: 元 |
| `NET_CASH_FLOWS_INV_ACT` | Net Investing CF | 投资活动现金流 | unit: 元 |

### data_type=indicator (quarterly panel)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `WAA_ROE` | Weighted ROE | 加权平均净资产收益率 | percent |
| `S_FA_ROE_DEDUCTED` | Deducted ROE | ROE(扣非) | percent |
| `S_QFA_ROE_DEDUCTED` | Single-Quarter Deducted ROE | 单季 ROE(扣非) | percent |
| `S_FA_ROA` | ROA | ROA | percent |
| `S_FA_GROSSPROFITMARGIN` | Gross Margin | 毛利率 | percent |
| `S_FA_NETPROFITMARGIN` | Net Margin | 净利率 | percent |
| `S_FA_DEBTTOASSETS` | Debt-to-Assets | 资产负债率 | percent |
| `S_FA_CURRENT` | Current Ratio | 流动比率 | ratio |
| `S_FA_QUICK` | Quick Ratio | 速动比率 | ratio |
| `S_FA_YOYOR` | Revenue YoY | 营收同比 | percent |
| `S_FA_YOY_NETPROFIT` | Net Profit YoY | 净利同比 | percent |

### data_type=valuation (daily panel — default columns suffice; do not pass `metrics`)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `pe` | PE | 市盈率 | static |
| `pe_ttm` | PE (TTM) | 市盈率(TTM) | trailing-12-month |
| `pb_new` | PB | 市净率 | latest book value |
| `ps` | PS | 市销率 | static |
| `ps_ttm` | PS (TTM) | 市销率(TTM) | trailing-12-month |
| `pcf_ocf` | P/CF (OCF) | 市现率(经营现金流) | |
| `pcf_ocfttm` | P/CF (OCF TTM) | 市现率(经营现金流 TTM) | |
| `total_share` | Total Shares | 总股本 | |
| `float_a_share` | Float A Shares | 流通A股 | |
| `free_share` | Free-Float Shares | 自由流通股本 | |
| `size` | Total Market Cap | 总市值 | unit: 元 |
| `float_size` | Float Market Cap | 流通市值 | unit: 元 |
| `close` | Close Price | 收盘价 | for the trading day |
| `high_52week` | 52-Week High | 52周高 | |
| `low_52week` | 52-Week Low | 52周低 | |
| `net_assets` | Net Assets | 净资产 | unit: 元 |
| `oper_rev_ttm` | Revenue (TTM) | 营收(TTM) | unit: 元 |
| `net_profit_parent_comp_ttm` | Net Profit Parent (TTM) | 归母净利(TTM) | unit: 元 |
| `net_cash_flows_oper_act_ttm` | OCF (TTM) | 经营现金流(TTM) | unit: 元 |

### data_type=market_cap (daily)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `code` | Symbol code | 代码 | |
| `date` | Date | 日期 | YYYY-MM-DD |
| `close` | Close Price | 收盘价 | |
| `share` | Shares | 股本 | `extra.total` controls scope; default `float_a_shares` (not total_shares) |
| `size` | Market Cap | 市值 | unit: 元; size = close × share |

### Common envelope fields (all data_type)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Symbol code | 代码 | |
| `data[*].date` | Date | 日期 | |
| `data[*].report_period` | Report Period | 报告期 | financial / indicator only; format YYYY-MM-DD (period end) |
| `data[*].avail_date` | Announcement Date | 公告披露日 | PIT-critical; financial / indicator only |
| `metadata.data_path` | CSV Path | CSV 路径 | triggered when `total_records > inline_threshold` (default 50). CSV not directly fetchable from the runtime — **prefer raising `inline_threshold` (max 1000) on the request** rather than relying on this path. |
| `metadata.warnings` | Warnings | 警告 | upstream errors / truncation; MUST be surfaced to the user |

**Output discipline**: never pass raw key (`OPER_REV`, `WAA_ROE`, `pe_ttm`, pipe-delim symbol like `AAPL|ST|USA`, `wind-`/`sw-`/`申万-` industry prefix) to user-visible text. For metrics not covered by the tables above, look up the canonical symbol in `metric-resolver.md` and use its `name` field as the display label. Use readable units (e.g. "Revenue 2.3亿元 (+15% YoY)") rather than raw integers in 元. Agent picks EN or CN label based on the user's language.

## Cross-ref

- User says "analyze / composite / is it healthy / business structure" → `financial-context.md` L1/L2/L3 (one-shot composite, do not chain)
- "Market expectations / consensus / target price" → `consensus-and-target.md`
- User-given metric not in this cheatsheet → `metric-resolver.md` (pull the registry to pick the canonical symbol)
- "What's Moutai's PE now" / "What's Moutai's ROE now" — single value → `realtime-quote.md` with `include_fundamentals=true` (lighter + carries freshness)
- "How much did Moutai gain over the past year / price trend" → `price-history.md`
- "Since when is X's data available / availability" → `market-calendar.md`

# industry-and-symbols

## Overview

Three query categories bundled together: (A) industry / SW classification (datareader/read `industry`); (B) index constituents (datareader/read `index_member`); (C) registry + company briefing (`market_symbol/get_symbols`). All responses are pass-through — do not post-process on the client side.

## Trigger Vocabulary

- 中文："茅台是什么行业 / 食品饮料板块 / 申万分类 / 沪深 300 成分 / 中证 500 都有哪些 / 茅台公司简介 / 注册地 / 股本变动 / 流通 A 股 / 解禁 / 上市日期"
- English: "industry of X / sector / SW classification / CSI300 constituents / company briefing / registration / shareholding change / IPO date / list date"
- Boundaries:
  - "白酒板块都有哪些 / AI 概念股都有哪些" (sector / concept **name** → symbol list) → **OUT-OF-SCOPE** (requires `match_collection`; this skill does not implement it). Do not pretend you can resolve a collection name to a symbol list. Ask the user to supply a symbol list, or suggest stock-screening with a sector/concept filter (see next bullet for its current status).
  - "PE 最低 20 只 / ROE > 15%" → the stock-screening skill is **not yet delivered** (upstream limitation; tracked separately). Tell the user this capability is temporarily unavailable.
  - "茅台一键综合分析" → `financial-context.md`

## Endpoint

| Method | Path | Purpose |
|---|---|---|
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `data_type=industry` — industry membership (trading-day time series) |
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `data_type=share` — share structure (by change event) |
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `data_type=index_member` — index constituents (trading-day time series) |
| POST | `$STOCKI_GATEWAY_URL/api/v2/market_symbol/get_symbols` | Registry + company briefing |

Availability matrix (measured 2026-05-08; re-check with `market-calendar.md` `/availability` before assuming a change):
- `cn/hk/us:stock × industry`
- `cn/hk:stock × share`
- `cn/hk:index × index_member`

## Input schema

### A. industry / share / index_member (datareader/read)

```json
{
  "area": "cn",
  "asset_type": "stock",
  "data_type": "industry",
  "symbols": ["600519"],
  "start_date": "2024-01-01",
  "end_date": "2026-05-08"
}
```

⚠️ **`start_date` + `end_date` are required** (upstream bug: missing dates return `"Internal error: NaTType does not support strftime"` with `suggestion=null`. The skill forces all 4 fields to be passed.)

- `industry` returns the industry tag per trading day (the label can change across years). For "current industry" → `end_date` = latest trading day, take the last record.
- `share` returns share-structure **change events** (not a daily panel). NA fills are normal.
- `index_member` is a **panel time-series** (one record per constituent per day). CSI 300 over one year ≈ 73K records → **far exceeds `inline_threshold` max 1000, must narrow query**. For "current constituents" only → `start_date` = `end_date` = latest trading day, set `inline_threshold = 400` (300 × 1.33 margin) → `len(data) == total_records == ~300` inline, no truncation. Longer ranges → narrow further or fail-loud per SKILL.md §Inline Threshold.
- `index_member` symbols must carry the exchange suffix (`"000300.SH"` / `"399006.SZ"` / `"HSI.HI"`).

⚠️ **inline_threshold (same body param as price/fundamental)**: pass when expected `total_records > 50` to avoid 50-row truncation. `index_member` single-day on ~300-stock indices (CSI 300 / HSI) → `inline_threshold = 400`; `industry` / `share` single-symbol queries are typically <50 rows so the default suffices. **Full decision rule: SKILL.md §Inline Threshold.**

### B. get_symbols

```json
{"area": "cn", "asset_type": "stock", "symbols": ["600519"], "detail": true}
```

| Field | Required | Description |
|---|---|---|
| `area / asset_type / symbols` | yes | bare code (no exchange suffix) |
| `detail` | no | when true, returns ~20 fields (CN) / ~47 fields (HK, including a longer briefing) |
| `for_match` | no | when true, returns match-friendly shape (used by symbol_resolver; skip in normal scenarios) |
| `list_since` | no | filter by list date (YYYY-MM-DD) |

## E2E examples

**(a) industry — cn single stock**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"industry","symbols":["600519"],"start_date":"2024-01-01","end_date":"2026-05-08"}'
```
Expected: `data[*] = {code, date, industry}`; the last record's `industry` = "食品饮料".

**(b) Multi-market batch — hk industry**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"hk","asset_type":"stock","data_type":"industry","symbols":["00700"],"start_date":"2024-01-01","end_date":"2026-05-08"}'
```

**(c) index_member — CSI 300 current constituents**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"index","data_type":"index_member","symbols":["000300.SH"],"start_date":"2026-05-07","end_date":"2026-05-07","inline_threshold":400}'
```
Expected: `data[*] = {code, date, index_code}`; `total_records ~300` and `len(data) == total_records` (no truncation because `inline_threshold = 400 ≥ 300`). **Survivorship bias**: the response only contains currently-listed constituents — it does NOT carry the historical add/drop trail.

**(d) get_symbols detail — company briefing**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v2/market_symbol/get_symbols" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","symbols":["600519"],"detail":true}'
```
Expected: `data[0]` contains `name / comp_name / comp_name_eng / list_date / list_board / exch_market / briefing` (CN ~20 fields).

**(e) Upstream error pass-through — missing dates**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"industry","symbols":["600519"]}'
```
Expected: `{"action":"error","error":"Internal error: NaTType...","suggestion":null}`. The skill teaches the LLM: on this error, auto-retry once with a date range filled in; only surface to the user if it still fails.

## Response Fields — Raw → User-Facing Label

### data_type=industry (industry classification time series)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Symbol code | 代码 | |
| `data[*].date` | Date | 日期 | |
| `data[*].industry` | Industry | 行业 | string may carry supplier prefix; see prefix-stripping rule below |

### data_type=share (shareholding change events)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Symbol code | 代码 | |
| `data[*].date` | Date | 日期 | |
| `data[*].total_shares` | Total shares | 总股本 | |
| `data[*].float_shares` | Float shares | 流通股 | |
| `data[*].float_a_shares` | Float A shares | 流通 A 股 | |
| `data[*].non_tradable_shares` | Non-tradable shares | 非流通股 | |
| `data[*].free_float_a_shares` | Free-float A shares | 自由流通 A 股 | |
| `data[*].change_reason` | Change reason | 变动原因 | |
| `data[*].ann_date` | Announcement date | 公告日 | PIT-critical |
| `data[*].register_date` | Register date | 登记日 | |

NA values are normal — `share` is an event series, not a daily panel.

### data_type=index_member (index constituents time series)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Constituent symbol | 成分股代码 | |
| `data[*].date` | Date | 日期 | |
| `data[*].index_code` | Index symbol | 指数代码 | suffix like `.SH` / `.SZ` / `.HI` — present to user with the index Chinese / English name, NOT the raw code |

### get_symbols detail=true (registry + briefing)

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].name` | Short name | 简称 | |
| `data[*].comp_name` | Company name (CN) | 全称 | |
| `data[*].comp_name_eng` | Company name (EN) | 英文名 | |
| `data[*].list_date` | List date | 上市日 | |
| `data[*].list_board` | List board | 上市板 | |
| `data[*].exch_market` | Exchange | 交易所 | |
| `data[*].category` | Category | 分类 | may carry supplier prefix; strip per the prefix rule below |
| `data[*].briefing` | Briefing | 公司简介 | render directly; HK may include longer prose |

### Common envelope

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `metadata.data_path` | CSV Path | CSV 路径 | triggered when `total_records > inline_threshold` (default 50). CSV not directly fetchable from the runtime — **prefer raising `inline_threshold` (max 1000) on the request** rather than relying on this path. |
| `metadata.warnings` | Warnings | 警告 | upstream errors / truncation; MUST be surfaced to the user |

**Industry-prefix discipline (flagship case)**: `data[*].industry` and `data[*].category` values may arrive with supplier prefixes such as `申万-食品饮料` / `wind-Banking` / `中信-计算机` / `sw_食品饮料` / `gics-*` / `nbis-*` / `csrc-*`. ALWAYS strip the supplier prefix before showing the value to the user — surface only the classification itself ("食品饮料" / "Banking" / "计算机"). Leaking supplier identity (`申万-`, `wind-`, …) violates output discipline and locks the publish-form into a single upstream forever.

**Index-name presentation rule**: never show `.SH / .SZ / .HI / .GI` suffixes to the user. Map `000300.SH` → "沪深300" / CSI 300; `399006.SZ` → "创业板指" / ChiNext; `HSI.HI` → "恒生指数" / Hang Seng Index; etc. Pick CN or EN per user's language.

**Output discipline**: never pass raw key (`float_a_shares`, `comp_name_eng`, `index_code` suffixes like `.SH / .SZ / .HI`, supplier prefixes like `wind-` / `sw-` / `申万-` / `中信-` / `gics-`) to user-visible text. Agent picks EN or CN label based on the user's language.

## Cross-ref

- "茅台 PE / 营收 / ROE" → `fundamentals-panel.md`
- "茅台业务结构 / segments" → `consensus-and-target.md` (revenue_breakdown) or `financial-context.md` L2
- "茅台一键综合分析" → `financial-context.md`
- Sector / concept **name → symbol list** → `match_collection` (API Platform symbol_resolver; **OUT-OF-SCOPE**, not implemented in this skill batch). Ask the user for an explicit symbol list, or point them at stock-screening (see next bullet for its current status).
- High-PE screening / filtering by sector or concept → the stock-screening skill is **not yet delivered** (upstream limitation; tracked separately). For "top-30 highest-PE" style asks, suggest running a market-wide valuation pull and sorting client-side, or wait for stock-screening to land.
- Pure market status / trading-day queries → `market-calendar.md`

# market-calendar

## Overview

Stocki gateway market status + trading calendar + data availability lookup. 5 GET endpoints, no body, all parameters via query string. Responses pass through to the user directly — no client-side post-processing.

## Trigger Vocabulary

- 中文："今天 A 股开盘吗 / 美股开了没 / 港股星期六开吗 / 昨天是不是交易日 / 下个交易日 / 交易日历 / 五一假期 / 数据有没有 / X 能查到吗"
- 英文："is the market open / trading day today / next trading day / market calendar / availability / does the gateway have X"
- Boundary: "Is Moutai open?" → go to `realtime-quote.md` (the response already carries `market_status`, saving one call).

## Endpoint

| Method | Path | Purpose |
|---|---|---|
| GET | `$STOCKI_GATEWAY_URL/api/v3/market/status` | Current market status (is_trading / last_trading_date / timezone) |
| GET | `$STOCKI_GATEWAY_URL/api/v3/market/trading_days` | Trading days within a date range |
| GET | `$STOCKI_GATEWAY_URL/api/v3/market/nearest_trading_date` | Nearest trading day ≥ the given date (inclusive) |
| GET | `$STOCKI_GATEWAY_URL/api/v3/market/next_trading_date` | Next trading day > the given date (exclusive) |
| GET | `$STOCKI_GATEWAY_URL/api/v3/availability` | Data availability matrix (which area×asset_type×data_type are queryable) |

## Input schema

| Endpoint | Required query | Description |
|---|---|---|
| `/market/status` | `area` ∈ {`all`, `cn`, `hk`, `us`, `crypto`} | `area=all` returns all 4 markets in one call |
| `/market/trading_days` | `begin_date`, `end_date`, `area` | `area` does not accept `all`, single market only; dates in YYYY-MM-DD |
| `/market/nearest_trading_date` | `date`, `area` | Single market |
| `/market/next_trading_date` | `date`, `area` | Single market |
| `/availability` | none | Returns the full matrix in one shot |

The `crypto` market is open 7×24 (response is always `is_trading: true`); `/availability` currently shows `crypto:crypto:price` as `{available: false, reason: ...}`.

## E2E examples

**(a) Happy path — fetch all-market status in one call**:
```bash
curl -X GET "$STOCKI_GATEWAY_URL/api/v3/market/status?area=all" \
  -H "Authorization: Bearer $STOCKI_API_KEY"
```
Expected: `{"cn":{"status":"post_market","is_trading":false,"last_trading_date":"2026-05-07","timezone":"Asia/Shanghai"}, "hk":{...},"us":{...},"crypto":{...}}`. Possible `status` values: `open / pre_market / post_market / closed`.

**(b) Cross-market batch — date-range trading days + single-day next (cn and us called separately)**:
```bash
curl -X GET "$STOCKI_GATEWAY_URL/api/v3/market/trading_days?begin_date=2026-05-01&end_date=2026-05-15&area=cn" \
  -H "Authorization: Bearer $STOCKI_API_KEY"

curl -X GET "$STOCKI_GATEWAY_URL/api/v3/market/next_trading_date?date=2026-05-08&area=us" \
  -H "Authorization: Bearer $STOCKI_API_KEY"
```
Expected (cn): `{"area":"cn","trading_days":["2026-05-06","2026-05-07",...],"count":8}`; US is similar.

**(c) Upstream error passthrough — unknown area**:
```bash
curl -X GET "$STOCKI_GATEWAY_URL/api/v3/market/status?area=invalid" \
  -H "Authorization: Bearer $STOCKI_API_KEY"
```
Expected: 4xx + JSON `{"detail":"..."}` or similar error; the skill instructs the LLM to surface the detail to the user without re-wrapping.

**(d) availability sample**:
```bash
curl -X GET "$STOCKI_GATEWAY_URL/api/v3/availability" \
  -H "Authorization: Bearer $STOCKI_API_KEY"
```
Expected: `{"datareader":{"cn:stock:price":true,"crypto:crypto:price":{"available":false,"reason":"..."},...},"quotes":{...},"probed_at":"..."}`.

## Response Fields — Raw → User-Facing Label

### `/market/status`

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `is_trading` | Is trading | 交易中 | bool; true = market currently open |
| `status` | Status | 状态 | enum: open / pre_market / post_market / closed |
| `last_trading_date` | Last trading date | 最近交易日 | YYYY-MM-DD; the most recent completed trading day |
| `timezone` | Timezone | 时区 | IANA tz id; show users a common name ("北京时间" / "美东时间" / "港时" / "UTC") |

### `/market/trading_days`

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `area` | Market | 市场 | echoed back |
| `trading_days` | Trading days | 交易日列表 | list of YYYY-MM-DD strings in the queried window |
| `count` | Count | 数量 | len(trading_days) |

### `/market/nearest_trading_date` and `/market/next_trading_date`

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `nearest_trading_date` | Nearest trading date | 最近交易日 | ≥ the given date (inclusive); applies to `/nearest_trading_date` only |
| `next_trading_date` | Next trading date | 下个交易日 | > the given date (exclusive); applies to `/next_trading_date` only |

### `/availability`

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `datareader.<area>:<asset_type>:<data_type>` | Availability flag | 可用性标志 | value is either `true` OR `{"available": false, "reason": "..."}`; handle both shapes |
| `quotes.<area>:<asset_type>` | Quotes availability | 行情可用性 | same shape rule |
| `probed_at` | Probed at | 探测时间 | ISO timestamp of last availability probe |

**Status enum presentation**: translate `status` enum for the user — `open` → "交易中" / "Open"; `pre_market` → "盘前" / "Pre-market"; `post_market` → "盘后" / "Post-market"; `closed` → "休市" / "Closed".

**Availability key presentation**: never echo the colon-joined raw key (`cn:stock:price`) to the user. Map to a phrase: `cn:stock:price` → "A 股价格数据" / "CN stock price data"; `crypto:crypto:price` → "加密货币价格数据" / "Crypto price data"; `hk:index:price` → "港股指数价格数据" / "HK index price data"; etc.

**Timezone presentation**: `timezone` field is an IANA tz id (`Asia/Shanghai` / `America/New_York` / `Asia/Hong_Kong` / `UTC`). Surface the common name to the user — "北京时间" / "美东时间" / "港时" / "UTC" — not the raw IANA id.

**Date presentation**: `last_trading_date` / `nearest_trading_date` / `next_trading_date` are YYYY-MM-DD strings; format as natural-language date when surfacing ("5 月 7 日" / "May 7").

**Output discipline**: never pass raw key (`is_trading`, `last_trading_date`, the colon-joined availability key like `cn:stock:price`, IANA tz id like `Asia/Shanghai`) to user-visible text. Agent picks EN or CN label based on the user's language.

## Cross-ref

- "Is Moutai open?" / "current price and also market status" → `realtime-quote.md` (response carries `market_status` + `data_context.<area>.freshness`)
- "When does X data start / how far back can I look?" → this skill's `/availability` only tells you **whether** data is queryable, **not the start date**; for the start date, call `price-history.md` or `fundamentals-panel.md` directly and inspect the actual date range in the response
- Crypto historical price unavailable → this skill's `/availability` flags `available:false`, but the concrete error passthrough is handled by `price-history.md`

> ⚠ **Pending**: This reference's upstream endpoint is under evaluation.
> The endpoint path/payload may switch to a different API in v0.3.0.
> Downstream agents should NOT rely on this reference's request/response shape
> being stable across versions. v0.3.0 may swap endpoint freely.
> For v0.2.0, env vars are renamed (mechanical) but request shape is unchanged.

# metric-resolver

## Overview

The stocki gateway's metric registry covers four markets: cn / hk / us / crypto. The HTTP layer **does NOT do fuzzy matching** — the LLM pulls the registry and picks from `name (CN)` / `symbol` / `synomnyms` / `description` itself. This is an intermediate step: once you have the canonical `symbol`, call `/api/v3/datareader/read` with `metrics=[...]`. The registry record count drifts with upstream patches; when you need a sense of scale, hit `kb_meta.record_counts` for the live number — do not freeze counts in the docs.

> ⚠️ The crypto area exposes only OHLCV basics (`open/high/low/close/volume/amount/rtn`) and not financial metrics. For the crypto case, **do not use this skill** — pass the fixed column names directly to datareader/read.

## When to use / When not to use

**Use this skill when**:
- The user mentions a semantic metric name like "ROE / 净资产收益率 / 毛利率 / 营收同比 / EPS / 自由现金流 / 速动比率 / 财务杠杆"
- You know the data_type (fundamentals / indicator / valuation, etc.) but are unsure of the canonical column name

**Do NOT use this skill when**:
- `realtime-quote` with `include_fundamentals=true` already returns a server-prepacked snapshot — use it directly, no resolution needed
- `price-history` uses fixed common columns (`metrics=["close","adj_close","open","high","low","volume"]`) — pass them directly
- `fundamentals-panel` / `consensus-and-target` ship their own high-frequency cheatsheets (~30 metrics). If your metric is on the cheatsheet, take the canonical name directly; **only on miss** do you fall back to this skill
- `market-calendar` / `industry-and-symbols` / `financial-context` do not accept a `metrics` parameter

## Endpoint

| Method | Path | Purpose |
|---|---|---|
| POST | `$STOCKI_GATEWAY_URL/api/v2/market_metric/get_metrics` | Pull the metric registry (filter by area / asset_type / kind / symbols) |

<!-- This file IS the canonical metric mapping source; canonical names below are intentional and request-side only, not user-visible output. -->
<!-- lint:disable rule=canonical-metric -->
## Input schema

```json
{
  "area": "cn",
  "asset_type": "stock",
  "kind": "profitability_and_earnings_quality",
  "symbols": null,
  "limit": 50,
  "offset": 0
}
```

| Field | Required | Description |
|---|---|---|
| `area` | no | `cn / hk / us / crypto`; omitted = all. **crypto is OHLCV only; do not use this skill for crypto.** |
| `asset_type` | no | `stock` (cn/hk/us) / `crypto` (crypto area) |
| `kind` | no | category filter; 13 kinds listed below |
| `symbols` | no | reverse-lookup by canonical symbol to fetch the registry record |
| `limit` / `offset` | no | pagination |

**13 `kind` values**: `balance_sheet`, `income_statement`, `cashflow_statement`, `valuation_multiples`, `profitability_and_earnings_quality`, `growth`, `solvency`, `per_share_metrics`, `capital_structure`, `market_data`, `cash_flow`, `operating_efficiency`, `capitalization`.

**User semantics → recommended `kind` filter** (narrows the scan):
- "营收 / 利润 / 成本 / 三表科目" / "revenue / profit / cost / statement items" → `kind=income_statement` or `cashflow_statement` or `balance_sheet`
- "ROE / ROA / 利润率 / 周转率" / "ROE / ROA / margin / turnover" → `kind=profitability_and_earnings_quality`
- "PE / PB / PS / EV/EBITDA" → `kind=valuation_multiples`
- "营收同比 / 利润增速 / 同比" / "YoY revenue / profit growth" → `kind=growth`
- "速动比率 / 资产负债率 / 利息保障" / "quick ratio / debt-to-assets / interest coverage" → `kind=solvency`
- "EPS / 每股净资产 / 每股现金流" / "EPS / book value per share / cashflow per share" → `kind=per_share_metrics`
- "市值 / 流通股 / 总股本" / "market cap / float shares / total shares" → `kind=capitalization`

## E2E examples

**(a) User asks for "ROE" → look under profitability**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v2/market_metric/get_metrics" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","kind":"profitability_and_earnings_quality"}'
```
The LLM scans `response.data` for records whose `name` contains "ROE" / "净资产收益率". Candidates: `WAA_ROE` (加权平均净资产收益率) / `S_FA_ROE_DEDUCTED` (扣非) / `S_QFA_ROE_DEDUCTED` (单季扣非) / `S_FA_YOYROE` (同比增长率). A bare "ROE" usually means `WAA_ROE` (the most common one); only switch if the user explicitly says "扣非 / 单季 / 同比" or the English equivalent.

**(b) User asks for "营业收入" → look under income_statement**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v2/market_metric/get_metrics" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","kind":"income_statement","limit":20}'
```
Scan `name` for "营业收入" / "revenue" → `OPER_REV` (营业总收入) / `S_QFA_OPER_REV` (单季营收) / `OPER_REV_TTM` (TTM). Default to `OPER_REV`.

**注**:`S_QFA_OPER_REV` 在 `data_type=financial` 下**不可用**(实测返 `data=[]+error`),不要把它当作"单季营收"候选 — 单季营收用 `OPER_REV` + `extra.use_ytd_value=False`(CN 默认即是),见 `fundamentals-panel.md` b1 caveat 与 Selection logic #3 `S_QFA_*` 适用域边界。

**(c) Reverse lookup — given `S_FA_ROE_DEDUCTED`, fetch its metadata**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v2/market_metric/get_metrics" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","symbols":["S_FA_ROE_DEDUCTED"]}'
```
Returns 1 record. Read `period / table / unit / description` to decide how to query (e.g. `period=quarter` → set `extra.report_type=Q4` / `Y`).

**(d) HK metric — user asks for "派息率" / dividend payout**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v2/market_metric/get_metrics" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"hk","asset_type":"stock"}'
```
Locally grep `name` / `description` / `synomnyms` for "派息" / "dividend".

## Response Fields — Raw → User-Facing Label

Each record carries 18 fields:
- `symbol` — **canonical name** (this is what you put into `metrics` on datareader/read)
- `name` — CN display name (the primary battleground for user-semantic matching)
- `area` / `asset_type` / `kind` — classification
- `period` — `daily / quarter / yearly` — determines how `extra.report_type` is filled at query time
- `table` — underlying data table (e.g. `AShareIncome` / `AShareValuationIndicator` / `AShareCashFlow`); implies which data_type to route through
- `unit / displayUnit` — unit (万元 / % / 元)
- `synomnyms` — synonyms (mostly empty, but a hit catches colloquial names)
- `description` — English gloss
- `is_derived` — whether the metric is derived
- `v3_alias` — v3 alias (mostly null)

If `response.kb_meta.source_drift` is non-empty, surface a note to the user: "the registry is out of sync with the underlying source; results may be stale".

## Selection logic (how the LLM should pick)

1. **Prefer exact `name` match** (the user's phrase appears literally in the record's `name`)
2. **Next: `description` / `synomnyms` contains** the user's phrase or a near-synonym
3. **Multiple candidates → pick by time granularity**:
   - "latest / TTM" → choose `period=daily` or a `name` containing "TTM"
   - "quarterly / single-quarter" → choose `name` containing "单季" or `symbol` starting with `S_QFA_*`
   - "annual / full year" → choose `name` containing "全年" or the unmodified main variant

**`S_QFA_*` 适用域边界**:`S_QFA_*` 系列前缀仅在 `data_type=indicator` 下可用(如 `S_QFA_ROE_DEDUCTED`、`S_QFA_EPS`,2026-05-13 实测可拉数据);`data_type=financial` **不接受** `S_QFA_*`(如 `S_QFA_OPER_REV` / `S_QFA_NET_PROFIT` 返 `data=[]+error="No data found"`)。单季营收 / 净利润直接用 `OPER_REV` / `NET_PROFIT` + `extra.use_ytd_value=False`(CN 默认即是);参见 `fundamentals-panel.md` b1 caveat。

4. **Special qualifiers**:
   - "扣非" / "deducted" → `name` contains "扣除非经常" or `symbol` contains `_DEDUCTED`
   - "稀释" / "diluted" → `name` contains "稀释" or `symbol` contains `_DILUTED`
   - "母公司 / 归母" / "parent company" → `name` contains "归属于母公司"

**c1: EPS 默认选 Basic,显式说 diluted 才换**(cn/hk 一致):

| 市场 | BASIC | DILUTED | 单季 EPS |
|---|---|---|---|
| CN | `S_FA_EPS_BASIC` | `S_FA_EPS_DILUTED`(+ `S_FA_EPS_DILUTED2` 期末摊薄)| `S_QFA_EPS` |
| HK | `EPS_BASIC` | `EPS_DILUTED`(+ `EPS_DILUTED2` / `EPS_DILUTED3` 期末摊薄变体)| **无**(hk registry 不提供单季 EPS,L2 已锁) |

规则:

- 用户说 "EPS / 每股收益":**cn/hk 一律默认 BASIC**(`S_FA_EPS_BASIC` / `EPS_BASIC`)
- 用户明说 "稀释 / diluted / 摊薄":用 DILUTED 主变体(`S_FA_EPS_DILUTED` / `EPS_DILUTED`);若用户说"期末摊薄"再换 `_DILUTED2` 变体
- 用户说 "单季 EPS":cn 用 `S_QFA_EPS`;**hk 需 fail-loud**:告知用户"hk 不提供单季 EPS,请确认是否要全年 BASIC"——**不要静默 fallback 到全年 BASIC 当作单季返回**

**不要猜**:有歧义时按本表退而向用户列 2 个候选(`BASIC` vs `DILUTED`),让用户确认;不假设"BASIC 总是对的"。

5. If you cannot narrow to a unique answer → list 2-3 candidates for the user to confirm. **Do not guess.**

<!-- lint:enable -->

## Output discipline (this skill IS the mapping source)

This skill's core output IS the raw → user-facing mapping table; downstream skills apply the output discipline based on what this skill returns.

- **`symbol` field (e.g. `OPER_REV` / `WAA_ROE` / `S_FA_ROE_DEDUCTED`)** — used ONLY as a downstream `metrics=[...]` request parameter; **never enters user replies**
- **`name` field (CN-friendly display name)** — this is the label to show to the user
- When presenting multiple candidates, surface `name + description`; **do not let the user see `symbol`** (except in debug or when the user explicitly asks for the canonical column name)
- The `table` field in each record carries an underlying database table name (e.g. `AShareIncome` / `HKShareValuation`) — this is a debug field, never shown to the user
- Downstream skills (`fundamentals-panel`, `consensus-and-target`, future `stock-screening` / `backtest`) consistently surface `name` rather than `symbol` to the user

## Cross-ref

- Once resolved, take the canonical symbol → `fundamentals-panel.md` (financial / indicator / valuation / market_cap data_type)
- Consensus-related fields (`con_or` / `con_np` / `con_eps`) are already canonical → no resolution needed; go straight to `consensus-and-target.md`
- Valuation snapshot (current PE/PB/ROE) → `realtime-quote.md` with `include_fundamentals=true`; do not use this skill
- Sector / company-name resolution ("茅台" → `600519`) → **OUT-OF-SCOPE** (this batch of skills assumes the user supplies a symbol; asset resolution would require `match_asset` which the HTTP layer does not expose — fall back to `/api/v2/market_symbol/get_symbols` and pick manually)

# price-history

## Overview

Stocki gateway v3 unified historical-price query, via `POST /api/v3/datareader/read` with `data_type=price`. Supports single stock / multi-stock batch / index / ETF / futures. **Adjustment-price semantics** is the first pitfall of this skill: OHLCV is unadjusted by default; for cross-ex-date comparison you must explicitly pass `metrics=["adj_close"]`.

## Trigger Vocabulary

- 中文："历史价 / 历史走势 / 月线 / 周线 / 日 K / K 线 / 过去一年涨 / 三年回报 / 区间收益 / OHLCV / 成交量 / 收盘价 / 后复权 / 前复权 / adj_close / 累计收益"
- English: "price history / OHLCV / candle / weekly chart / yearly return / cumulative return / adjusted close / forward return"
- Boundaries:
  - Realtime / intraday / movers leaderboard → `realtime-quote.md` (response carries `data_context.freshness`)
  - PE / PB / ROE historical time series → `fundamentals-panel.md`
  - Valuation history percentile (5y) → `financial-context.md` L1
  - Strategy backtest performance → backtest skill **not yet delivered** (upstream limitation, tracked separately). For pure-arithmetic, no-strategy questions like "how much did CSI 300 equal-weight gain in one year", this skill can take head and tail of `metrics=["adj_close"]`; for backtests with strategy / rebalancing / stop-loss, tell the user it is currently unavailable.

## Endpoint

| Method | Path | Purpose |
|---|---|---|
| POST | `$STOCKI_GATEWAY_URL/api/v3/datareader/read` | `data_type=price` historical OHLCV / adjusted |

Availability matrix (re-check with `market-calendar.md` `/availability` before assuming a change; currently known working combinations):
- `cn/hk/us:stock × price`
- `cn:etf × price`
- `cn:futures × price`
- `cn:index / hk:index / us:index × price`
- `crypto:crypto:price` is currently **unavailable** (response passes through server `error + warnings`; do not pretend it works)

## Input schema

```json
{
  "area": "cn",
  "asset_type": "stock",
  "data_type": "price",
  "symbols": ["600519"],
  "metrics": ["open","high","low","close","volume"],
  "start_date": "2026-04-01",
  "end_date": "2026-04-30"
}
```

| Field | Required | Description |
|---|---|---|
| `area` | yes | `cn / hk / us / crypto` |
| `asset_type` | yes | `stock / index / etf / futures / crypto` |
| `data_type` | yes | fixed `"price"` |
| `symbols` | yes | list; stocks use bare code ("600519"); **indexes carry exchange suffix** ("000300.SH" / "399006.SZ" / "HSI.HI") |
| `metrics` | no | defaults to the full OHLCV set; for cumulative return you must explicitly pass `["adj_close"]` |
| `start_date / end_date` | yes | YYYY-MM-DD |
| `inline_threshold` | no | int, range `[1, 1000]`, default 50 (silently clamped). Pass when expected `total_records > 50` to avoid 50-row truncation; estimate `N = symbols × trading_days × metrics` and set `min(ceil(N × 1.2), 1000)`. **Full decision rule: SKILL.md §Inline Threshold.** |

⚠️ **Adjusted-price is mandatory for cross-ex-date math**: default `metrics` does not include adjusted prices. **For cumulative return / cross-ex-date comparison → you must pass `metrics=["adj_close"]`** (works for CN/HK; US `adj_close` is occasionally NA → fall back to `close` but the LLM must explicitly tell the user precision is limited).

## ⚠️ Futures continuous-contract roll-over warning (required for asset_type=futures)

`cn:futures × price` returns the **main-contract (XXmain) continuous series**, which contains **non-market-driven** price jumps on contract switch days (a calendar spread of 1–5% between the old contract's last-day close and the new contract's first-day close).

- ❌ **Do not** compute daily return as `(close_t / close_{t-1}) - 1` directly — roll days will contaminate the series and long-horizon cumulative returns will be wildly wrong.
- ❌ **Do not** use head-vs-tail `close` to compute an N-year cumulative return — the roll-day jump does not cancel.
- ✅ Short-horizon analysis that does not cross a roll day can use `close` normally.
- ✅ Return series that crosses roll days: use the `pct_change` carried in the response (when available); or on the client side identify days with a sharp drop in `oi` (open interest) as a roll signal and exclude them.
- ✅ Long-horizon cumulative return / backtest: v3 currently does **not** expose a separately adjusted continuous series. Tell the user the result contains roll-over noise — do not pretend it is precise.

Typical roll nodes: the few trading days before contract expiry; financial futures (IF/IC/IH) roll monthly; commodity futures (I/CF etc.) roll per product-specific rules.

## E2E examples

**(a) Happy path — cn single-stock monthly OHLCV**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"price","symbols":["600519"],"metrics":["open","high","low","close","volume"],"start_date":"2026-04-01","end_date":"2026-04-30"}'
```
Expected: `data[*] = {code, date, open, high, low, close, volume}`, ~22 trading days.

**(b) Batch + long window + adj_close (cumulative-return scenario)**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","data_type":"price","symbols":["600519","000858"],"metrics":["adj_close"],"start_date":"2025-05-01","end_date":"2026-05-01","inline_threshold":600}'
```
Expected: `total_records ~484` (2 stocks × 242 trading days). **`inline_threshold = 600` is set explicitly** (484 × 1.2 margin per SKILL.md §Inline Threshold) so `len(data) == total_records == 484` and the 50-row truncation does not apply. To compute a 1-year cumulative return → take per-stock last `adj_close` / first `adj_close` - 1. **Do not use `close` for 1-year comparisons** (ex-date events will introduce series jumps).

**(c) Multi-market — us / hk index comparison**:
```bash
# us SPY index proxy
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"us","asset_type":"index","data_type":"price","symbols":["SPX.GI"],"metrics":["close"],"start_date":"2025-05-01","end_date":"2026-05-01"}'

# hk Hang Seng
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"hk","asset_type":"index","data_type":"price","symbols":["HSI.HI"],"metrics":["close"],"start_date":"2025-05-01","end_date":"2026-05-01"}'
```
Note: us single-stock response also carries redundant fields like `pre_close / change / pct_change / amount` (spec does not force consumption; take as needed).

**(d) Upstream-error pass-through — crypto unavailable**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/datareader/read" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"crypto","asset_type":"crypto","data_type":"price","symbols":["BTCUSDT"],"start_date":"2026-04-01","end_date":"2026-04-30"}'
```
Expected: `{"action":"error","data":[],"metadata":{"warnings":["fetch failed: Missing config: database_url - crypto. "]}}` — the skill teaches the LLM to pass `metadata.warnings` through to the user and state plainly "crypto historical price is currently unavailable from the data source"; do not fabricate.

## Response Fields — Raw → User-Facing Label

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `data[*].code` | Symbol code | 代码 | bare code for stocks/ETFs; index includes exchange suffix |
| `data[*].date` | Date | 日期 | YYYY-MM-DD |
| `data[*].open` | Open | 开盘 | |
| `data[*].high` | High | 最高 | |
| `data[*].low` | Low | 最低 | |
| `data[*].close` | Close | 收盘 | NOT adjusted; do not use for cross-ex-date comparisons |
| `data[*].volume` | Volume | 成交量 | |
| `data[*].amount` | Turnover | 成交额 | US stocks only |
| `data[*].pre_close` | Previous Close | 昨收 | US stocks only |
| `data[*].change` | Price change | 涨跌额 | US stocks only |
| `data[*].pct_change` | Percent change | 涨跌幅 | US stocks; also valid for futures roll-aware return |
| `data[*].adj_close` | Adjusted Close | 复权收盘价 | MUST use for cumulative-return / cross-ex-date comparisons (CN/HK reliable; US occasionally NA — fallback to close with explicit precision caveat) |
| `data[*].oi` | Open interest | 持仓量 | futures only; roll-day signal (sharp drop = roll) |
| `total_records` | Total rows | 总行数 | expected ≈ N_symbols × N_trading_days |
| `metadata.data_path` | CSV path | CSV 路径 | triggered when `total_records > inline_threshold` (default 50). CSV not directly fetchable from the runtime — **prefer raising `inline_threshold` (max 1000) on the request** rather than relying on this path. |
| `metadata.elapsed_ms` | Elapsed (ms) | 耗时(毫秒) | |
| `metadata.row_count` | Row count | 行数 | |
| `metadata.symbol_requested` | Requested symbols | 请求标的 | |
| `metadata.symbol_returned` | Returned symbols | 返回标的 | |
| `metadata.missing_symbols` | Missing symbols | 缺失标的 | symbols asked for but no data returned |
| `metadata.warnings` | Warnings | 警告 | upstream-fetch failure / data-source issues; MUST be surfaced to the user |

**Index symbol presentation rule**: never show suffix `.SH / .SZ / .HI / .GI` to the user. Map to display name instead: `000300.SH` → "沪深300" / CSI 300; `399006.SZ` → "创业板指" / ChiNext; `HSI.HI` → "恒生指数" / Hang Seng Index; `SPX.GI` → "标普500" / S&P 500. Pick CN or EN display per user's language.

**Futures roll-over discipline**: when surfacing return / cumulative-pnl figures for `asset_type=futures`, explicitly note any roll-overs in the window — never silently use raw `close` head-vs-tail to claim a long-horizon return.

**Output discipline**: never pass raw key (`adj_close`, `pct_change`, pipe-delim symbol like `AAPL|ST|USA`, `wind-`/`sw-`/`申万-` industry prefix) to user-visible text. Agent picks EN or CN label based on the user's language.

## Cross-ref

- Realtime intraday → `realtime-quote.md`
- Valuation time series (PE/PB/PS) → `fundamentals-panel.md`
- Combined 5y percentile → `financial-context.md` L1
- Strategy backtest → not yet delivered (upstream limitation, tracked separately)
- BTC/ETH historical price → this skill passes the `crypto:crypto:price` unavailable error through (does not pretend it works); for crypto realtime, use `realtime-quote.md` (freshness may be `latest_close`)

# realtime-quote

## Overview

Stocki gateway v3 realtime quote snapshot. Two endpoint shapes: `get_latest_quotes` takes multi-asset groups (mixed across markets in one call); `get_all_latest_quotes` returns the full single-market panel (5000+ records). The response carries `market_status` + `data_context.freshness`, telling the LLM whether the data is realtime or latest_close.

## Trigger Vocabulary

- 中文："现在多少钱 / 现价 / 涨多少 / 跌多少 / 涨停 / 跌停 / 开盘了吗 / 收盘价 / 实时行情 / 涨幅榜 / 跌幅榜 / 量能 / 茅台 PE 现在"
- 英文："real-time price / intraday quote / latest price / pct change / market open / today's gainers / day high / current PE"
- 边界：用户问"昨天交易日吗 / 下个交易日" → `market-calendar.md`。"过去一年涨多少 / K 线" → `price-history.md`。"PE 历史时序 / 5y 分位" → `fundamentals-panel.md` / `financial-context.md`。"今天开盘吗" 也可走本 skill（response 自带 `market_status`）。

## Endpoint

| Method | Path | Purpose |
|---|---|---|
| POST | `$STOCKI_GATEWAY_URL/api/v3/quotes/get_latest_quotes` | Specified symbols, multi-asset groups (mix markets in a single call) |
| POST | `$STOCKI_GATEWAY_URL/api/v3/quotes/get_all_latest_quotes` | Single area×asset_type full panel (5000+ records, 60s server-side cache) |

## Input schema

### A. `get_latest_quotes` (QuotesV2Request)

```json
{
  "assets": [
    {"symbols": ["600519"], "area": "cn", "asset_type": "stock"}    
  ],
  "include_fundamentals": true,
  "timeout": 5.0
}
```

| Field | Required | Description |
|---|---|---|
| `assets[*].symbols` | yes | bare code list (no exchange suffix) |
| `assets[*].area` | yes | `cn / hk / us / crypto` |
| `assets[*].asset_type` | yes | `stock / index / etf / futures / crypto` |
| `include_fundamentals` | no | when true, CN stock response carries PE/PB/ROE/gross-margin/EPS snapshot |
| `timeout` | no | seconds, default 5.0 |

`assets` may contain multiple groups, allowing **one cross-market pull** (cn:stock + hk:stock + us:stock + crypto:crypto).

### B. `get_all_latest_quotes` (QuotesV2SimpleRequest)

```json
{"area": "cn", "asset_type": "stock", "include_fundamentals": false}
```

Flat top-level, single area×asset_type full panel; multiple markets require multiple calls. With `include_fundamentals=true`, 5000+ records all carry fundamentals — payload is large, use with care.

## E2E examples

**(a) Happy path — single stock + fundamentals**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/quotes/get_latest_quotes" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"assets":[{"symbols":["600519"],"area":"cn","asset_type":"stock"}],"include_fundamentals":true}'
```
Expected: `data[0]` contains `pct_change / close / pre_close / volume / fundamentals.{pe_ttm, pb_mrq, ps_ttm, roe, gross_margin_qfa, eps_qfa, sales_yoy_qfa, ...}`.

**(b) Batch across markets — cn + hk + us in one call**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/quotes/get_latest_quotes" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"assets":[
    {"symbols":["600519"],"area":"cn","asset_type":"stock"},
    {"symbols":["00700"],"area":"hk","asset_type":"stock"},
    {"symbols":["AAPL"],"area":"us","asset_type":"stock"}
  ]}'
```
Expected: `data` list contains 3 records; `data_context` carries three freshness keys `cn:stock / hk:stock / us:stock`.

**(c) Full-market + top gainers (client-side sort)**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/quotes/get_all_latest_quotes" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"area":"cn","asset_type":"stock","include_fundamentals":false}'
```
Expected: `data` has 5000+ records; the LLM can sort client-side by `pct_change` and take top-N (one of the few cases where client-side processing is acceptable, since the server has no dedicated ranking endpoint).

**(d) Upstream error / invalid area**:
```bash
curl -X POST "$STOCKI_GATEWAY_URL/api/v3/quotes/get_latest_quotes" \
  -H "Authorization: Bearer $STOCKI_API_KEY" -H "Content-Type: application/json" \
  -d '{"assets":[{"symbols":["BAD"],"area":"invalid","asset_type":"stock"}]}'
```
Expected: 4xx / empty `data` / explanatory `message` field; the skill instructs the LLM to surface the server-side error message to the user.

## Response Fields — Raw → User-Facing Label

All `data[*].fundamentals.*` values are pipe-delim strings of shape `"<value>|<CN label>|<as_of_date>|<extra>"`. Extract: `split("|")[0]` for the numeric value, `[1]` for the embedded CN label (matches the CN label column below), `[2]` for the PIT date.

| Raw key | EN label | CN label | Note |
|---|---|---|---|
| `market_status.<area>` | Market status | 市场状态 | enum: open / pre_market / post_market / closed |
| `data_context.<area>:<asset_type>.freshness` | Data freshness | 数据时效 | enum: realtime / latest_close / previous_close; MUST be surfaced to the user |
| `data_context.<area>:<asset_type>.context` | Context description | 状态说明 | natural-language string from upstream; can render directly |
| `data[*].pct_change` | Percent change | 涨跌幅 | |
| `data[*].open` | Open | 开盘 | |
| `data[*].high` | High | 最高 | |
| `data[*].low` | Low | 最低 | |
| `data[*].close` | Close | 收盘 | |
| `data[*].pre_close` | Previous Close | 昨收 | |
| `data[*].volume` | Volume | 成交量 | |
| `data[*].time` | Timestamp | 时间 | |
| `data[*].fundamentals.pe_ttm` | PE (TTM) | 市盈率(TTM) | pipe-delim |
| `data[*].fundamentals.pb_mrq` | PB (MRQ) | 市净率(MRQ) | pipe-delim |
| `data[*].fundamentals.ps_ttm` | PS (TTM) | 市销率(TTM) | pipe-delim |
| `data[*].fundamentals.roe` | ROE | 净资产收益率 | pipe-delim |
| `data[*].fundamentals.gross_margin_qfa` | Gross Margin (QFA) | 毛利率(单季) | pipe-delim |
| `data[*].fundamentals.net_margin_qfa` | Net Margin (QFA) | 净利率(单季) | pipe-delim |
| `data[*].fundamentals.eps_qfa` | EPS (QFA) | 每股收益(单季) | pipe-delim |
| `data[*].fundamentals.sales_yoy_qfa` | Revenue YoY (QFA) | 营收同比(单季) | pipe-delim |
| `data[*].fundamentals.np_yoy_qfa` | Net Profit YoY (QFA) | 净利润同比(单季) | pipe-delim |
| `data[*].fundamentals.price_chg_5d` | 5-Day Price Change | 5日涨跌幅 | pipe-delim |
| `data[*].fundamentals.price_chg_20d` | 20-Day Price Change | 20日涨跌幅 | pipe-delim |

**Output discipline**: never pass raw key (`pe_ttm`, `gross_margin_qfa`, pipe-delim symbol like `AAPL|ST|USA`, `wind-`/`sw-`/`申万-` industry prefix) to user-visible text. Agent picks EN or CN label based on the user's language. For fundamentals pipe-delim values: surface `split("|")[0]` as the number; the embedded `split("|")[1]` Chinese label can be used directly OR mapped to the EN label above.

## Cross-ref

- Historical OHLCV / interval returns → `price-history.md` (use `metrics=["adj_close"]` to compute cumulative returns)
- PE/PB historical time series / valuation percentile → `fundamentals-panel.md` or `financial-context.md` L1 (5y percentile)
- One-shot composite view (financials + valuation + business structure + consensus) → `financial-context.md`
- Plain trading-day / market-holiday lookup → `market-calendar.md` (if the user is already asking about quotes, the `market_status` in this skill's response is sufficient — don't make a second call)
