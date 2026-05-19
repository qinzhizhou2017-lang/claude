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
