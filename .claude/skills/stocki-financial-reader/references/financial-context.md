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
