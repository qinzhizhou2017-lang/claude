# stocki-financial-reader 能力拆解与数据缺口报告

> 面向程序员同事的逆向拆解 / 汇报反馈
> 审计对象:`.claude/skills/stocki-financial-reader` (v0.3.0)
> 出具日期:2026-05-26
> 方法:8 份 reference 契约 + SKILL.md + 3 个脚本逐行通读 **＋ 对生产网关 `skill.stocki.com.cn` 的只读实测交叉验证**(非纯文档推断)

---

## 0. 一句话结论

stocki skill 是一层"LLM 路由 + 输出纪律"的薄壳,它本身不接 Wind,而是调用 **stocki 网关**,网关再去取 **Wind(万得)** 数据。所以它的"能力范围"= **网关已为 Wind 建了 loader 的那一小块子集**。

缺口分两类,**都存在**:
1. **Wind 有 → 网关没建 loader → skill 更没路由**(占绝大多数:债券/期权/资金流/股东/分红明细/宏观/分钟线…)。
2. **网关有 → skill 没暴露**(实测发现:`global:commodity:price`、quotes 的 `concept_index/index_futures/major_index`)——这是 skill 自己"漏接"。

外加一批**实测出来的契约/文档偏差**(US 兜底已宕、`market/status?area=all` 返 403、host 不一致、完整性校验形同虚设),详见 §4。

---

## 1. 架构拆解(三层)

```
用户自然语言("分析下茅台贵不贵")
        │
        ▼
┌─────────────────────────────────────────────┐
│  Layer 1  stocki skill(本仓 .claude/skills) │  ← 纯 prompt/文档:路由表 R1–R8 + 输出纪律 + inline_threshold 估算
│  8 references + SKILL.md + scripts/*.py       │     不含任何取数逻辑,只"教 LLM 怎么拼 HTTP"
└─────────────────────────────────────────────┘
        │  HTTP (Bearer $STOCKI_API_KEY)
        ▼
┌─────────────────────────────────────────────┐
│  Layer 2  stocki 网关 (skill.stocki.com.cn)   │  ← 真正决定"能查什么":为部分 (area,asset,data_type) 建了 loader
│  12 类端点                                     │     /availability 是它的能力自述
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│  Layer 3  Wind 万得(被刻意隐藏)               │  ← 证据:_source_map 含 AShareIncome/HKShareValuation/wind_*;
│                                               │     字段码 OPER_REV/WAA_ROE/S_FA_*/S_QFA_*/con_*;
│                                               │     行业前缀 申万-/中信-/wind-。输出纪律专门要求剥离这些以防锁死数据源。
└─────────────────────────────────────────────┘
```

**关键认知**:skill 的"输出纪律"(禁止泄漏 `wind-`/`申万-`/`OPER_REV`/`AShareIncome` 等)证明底层就是 Wind,且团队有意做源切换准备。因此本报告把"能力边界"等价于"**网关暴露出来的 Wind 子集**"。

### 端点清单(Layer 2 实际暴露的 12 类)

| # | 方法 | 路径 | 对应 reference | 备注 |
|---|---|---|---|---|
| 1 | GET | `/api/v3/market/status` | market-calendar | ⚠ 实测:`?area=all` 返 **403**,`?area=cn` 返 200 |
| 2 | GET | `/api/v3/market/trading_days` | market-calendar | |
| 3 | GET | `/api/v3/market/nearest_trading_date` | market-calendar | |
| 4 | GET | `/api/v3/market/next_trading_date` | market-calendar | |
| 5 | GET | `/api/v3/availability` | market-calendar | 能力矩阵自述(本报告 §2 真相来源) |
| 6 | POST | `/api/v3/quotes/get_latest_quotes` | realtime-quote | 多资产组批量 |
| 7 | POST | `/api/v3/quotes/get_all_latest_quotes` | realtime-quote | 单市场全量 5000+ |
| 8 | POST | `/api/v3/datareader/read` | price/fundamentals/industry/consensus | **主力端点**,按 `data_type` 分流 11 种 |
| 9 | POST | `/api/v3/financial_context/{cn,hk}` | financial-context | 复合视图 L1/L2/L3 |
| 10 | POST | `/api/v2/market_symbol/get_symbols` | industry-and-symbols | 注册表 + 公司简介 |
| 11 | POST | `/api/v2/market_metric/get_metrics` | metric-resolver | ⚠ 标注 "pending",契约可能在 v0.3.0 变 |

---

## 2. 完整能力清单(权威矩阵,来自 `/availability` 实测)

> 以下为 2026-05-26 17:14 实测 `GET /api/v3/availability` 的真实返回,**比 skill 文档更权威**(文档是 2026-05-08 的快照,已漂移)。

### 2.1 datareader/read 可用组合

| area:asset | 可用 data_type | 状态 |
|---|---|---|
| **cn:stock** | price, financial, indicator, valuation, market_cap, industry, share, consensus_forecast, target_price, revenue_breakdown | ✅ 全量(唯一全功能市场) |
| **cn:index** | price, index_member | ✅ |
| **cn:etf** | price | ✅ 仅价格 |
| **cn:futures** | price | ✅ 仅价格(有换月噪声,见 H2) |
| **hk:stock** | price, financial, indicator, valuation, market_cap, industry, share | ✅ 但**无** consensus/target/revenue_breakdown |
| **hk:index** | price, index_member | ✅ |
| **us:stock** | price ✅, industry ✅ | ⚠ market_cap **已宕**(Code 60);financial/indicator/valuation/consensus 全部 **Unsupported** |
| **us:index** | price | ✅ |
| **global:commodity** | price | ✅ **⚠ skill 完全未文档化/未路由**(实测组合有效,见 §4-④) |
| **crypto:crypto** | price | ❌ `Missing config: database_url - crypto` |

### 2.2 quotes(实时行情)可用组合

| area | 可用 asset_type |
|---|---|
| cn | stock, index, etf, futures, **concept_index**, **index_futures**, **major_index** |
| hk | stock, index, major_index |
| us | stock, index, major_index |
| crypto | crypto(可能 latest_close) |

> **⚠ skill 未文档化的 asset_type**:`concept_index`(概念板块指数)、`index_futures`(股指期货)、`major_index`(主要指数)——quotes 端点支持,但 skill 的 asset_type 枚举只有 `stock/index/etf/futures/crypto`,这三类**实时行情查不到**(路由层根本不会拼出来)。

---

## 3. 能力边界与数据缺口(核心:它会缺失哪些数据)

> 标注图例:【声明】= skill 文档已自认缺失;【实测】= 本次实测验证;【新】= 文档未提、实测/矩阵新发现。

### A. 入口能力缺失(直接打断自然语言可用性)

| 编号 | 缺什么 | 影响 | 来源 |
|---|---|---|---|
| **A1** | **证券名称 → 代码** 解析(`match_asset` 未暴露) | "分析下茅台" 里 "茅台"→`600519` 无法自动解析,只能让 LLM 拿 `get_symbols` 手动挑。**最高频入口从第一步就断** | 【声明】metric-resolver Cross-ref |
| **A2** | **板块/概念名 → 成分列表**(`match_collection` OUT-OF-SCOPE) | "白酒板块都有哪些 / AI 概念股" 无法解析为代码列表 | 【声明】industry-and-symbols |
| **A3** | **选股 / 筛选**(stock-screening 未交付) | "ROE>15% 的 / PE 最低 20 只" 无服务端筛选,只能拉全市场客户端排序(还卡 1000 行上限) | 【声明】industry-and-symbols |
| **A4** | **策略回测**(backtest 未交付) | 只能做纯算术首尾收益;带调仓/止损/再平衡的回测做不了 | 【声明】price-history |

### B. 市场 / 资产类别覆盖缺口

| 编号 | 缺什么 | 细节 | 来源 |
|---|---|---|---|
| **B1** | **美股基本面整体缺失** | `financial_context` 不支持美股;datareader 美股 financial/indicator/valuation/consensus 全 `Unsupported`,网关直接建议"web search"。美股**只剩** price(OHLCV)+ industry + realtime 快照 | 【实测】P1 |
| **B2** | **美股唯一兜底 market_cap 当前已宕** | 文档(R6/fundamentals-panel)称 market_cap 是"美股唯一可用",实测返 `Code: 60` 失败。**美股事实上连市值时序都取不到** | 【新·实测】P2 |
| **B3** | **港股业务分部完全缺失** | `financial_context/hk` 的 `segments` 三层(L1/L2/L3)恒为 `null`;`consensus-and-target` 仅 cn。港股**没有任何**营收拆解/分部数据 | 【实测】P4 |
| **B4** | **港股/美股一致预期·目标价** | `consensus_forecast/target_price/revenue_breakdown` 仅 `cn:stock`。港股一致预期或可经 financial_context 取(实测 hk response 有 `consensus` 块),但 standalone 端点取不到;美股完全无 | 【实测】矩阵 |
| **B5** | **港股币种信号缺失** | hk income/balance/cashflow/valuation **无 `currency` 字段**,segments 恒 null → **无任何币种信号**,LLM 必须按公司归属猜 RMB/HKD/USD。H 股内地公司(腾讯)默认 HKD 会差近 10% | 【实测】P4 |
| **B6** | **加密货币历史价不可用** | `crypto:crypto:price` = `Missing config: database_url`。只有 realtime(可能 latest_close);且 crypto 无任何财务 metric | 【实测】矩阵 |
| **B7** | **HK/US 的 ETF、期货实时行情** | quotes 矩阵里 hk/us 只有 stock/index/major_index,**无 etf/futures**;datareader 也只有 cn:etf/cn:futures | 【新·实测】矩阵 |

### C. 整类资产缺席(asset_type 枚举里就没有)

skill 的 asset_type 只有 `stock/index/etf/futures/crypto`(+ 实测的 commodity)。以下 Wind 有、但无任何路由:

- **C1 债券 / 可转债** — 无
- **C2 期权** — 无
- **C3 场外基金 / 基金净值 NAV / 基金持仓** — ETF 仅 OHLCV 价格,无持仓、无 NAV、无基金经理
- **C4 外汇 / 利率衍生品** — 无

### D. 整个数据域缺席(Wind 有,网关没建 loader)

| 编号 | 缺失数据域 | 说明 |
|---|---|---|
| **D1** | 资讯 / 公告全文 / 事件流 | 无新闻、无公告正文、无增发/回购/重组事件 |
| **D2** | 分红送转明细 | 无分红历史端点(金额/除权除息日/股息率/分红率时序);adj_close 隐含但**不可拆解** |
| **D3** | 股东 / 持股结构 | 无十大股东、无机构持仓、无股东户数、无股权质押(`share` 只给股本总数,不给持有人) |
| **D4** | 资金流向 | 无主力资金、无北向/南向(沪深港通)、无龙虎榜 |
| **D5** | 融资融券 | 无 |
| **D6** | 大宗交易 | 无 |
| **D7** | 宏观经济 | 无 GDP/CPI/利率/货币供应/PMI |
| **D8** | ESG | 无 |
| **D9** | **指数权重** | `index_member` 只给成分**代码**,无**权重** → 无法按市值加权重构指数,只能等权算术 |
| **D10** | 分析师颗粒度 | 一致预期是**合并值**,无单家券商报告、无评级分布、无个体预测修正 |
| **D11** | 解禁日历 | 触发词提了"解禁",但 `share` 是**历史**变动事件,无前瞻解禁时间表 |

### E. 频率 / 粒度缺口

| 编号 | 缺什么 | 说明 |
|---|---|---|
| **E1** | 分钟线 / Tick / L2 盘口 | price-history 仅日频;realtime 仅快照 OHLCV+量,**无买卖五档/委托队列/逐笔** |
| **E2** | 周线 / 月线参数 | price-history 的 schema **无 `freq` 参数**,触发词虽提"月线/周线"但只能日频拉回客户端重采样 |

### F. 计算 / 时间窗口缺口

| 编号 | 缺什么 | 说明 |
|---|---|---|
| **F1** | 任意窗口估值分位 | `financial_context` 只给**固定 5 年**分位,且仅 `pe/pb/ps` 三项。3y/10y/自定义窗口、以及 ROE/股息率等其它指标的分位**全无**,只能拉原始序列客户端近似 | 
| **F2** | 长区间一致预期修正史 | `consensus_forecast` standalone 默认 **90 天回看**,更长被截断(L3 可给 132+ 条作为唯一例外) |

### G. 体量 / 分页天花板(架构级硬限制)

| 编号 | 限制 | 说明 |
|---|---|---|
| **G1** | **>1000 行结果无法完整取回** | `inline_threshold` 上限 1000,超出部分进 CSV(`data_path`),但 **runtime 读不了外部存储**。后果:`index_member` 全年面板(沪深300×1年≈7万行)只能取**当日快照**;多标的长日频序列/全市场面板被硬截断 |

### H. 历史完整性 / PIT 缺口

| 编号 | 缺什么 | 说明 |
|---|---|---|
| **H1** | index_member 幸存者偏差 | 只返回**当前**成分,无历史调入/调出轨迹 → 需要历史成分的回测做不准 |
| **H2** | 期货换月噪声 | `cn:futures` 是主力连续合约,含换月跳空(1–5% 价差),**无单独复权连续序列** → 长周期收益失真 |

---

## 4. 实测发现的契约 / 文档偏差(opus 本轮新增,纯文档读不出)

这几条是只读实测才暴露的,**对程序员排障最有价值**:

**① `diagnose.py` 探活端点用了会 403 的参数**
- `GET /api/v3/market/status?area=all` → **HTTP 403**;`?area=cn` → 200。
- 后果:skill 自带的 `diagnose.py`(reachability 步骤硬编码 `?area=all`)在生产网关上**恒失败**,给出假"网关不可达/宕机"(exit 3),而网关其实是好的。market-calendar 文档的 happy-path 示例 (a) 也用了 `?area=all`,同样踩坑。
- 根因待查:可能 `area=all` 在该 host 被 WAF/权限网关拦了,或已废弃。

**② 文档号称的"美股唯一可用 data_type"已宕**
- `us:stock:market_cap` 在 `/availability` 标 `available:false`(`Code: 60`),实测 datareader 也返回失败。
- 后果:R6 把美股兜底指向 market_cap,该路径当前**断的**;skill 无探测,只会把 error 透传给用户。

**③ 网关 host 与文档不一致**
- 实际 `STOCKI_GATEWAY_URL=https://skill.stocki.com.cn`;INSTALL.md / 所有 reference 写的是 `https://api.stocki.com.cn`。文档需更新,否则照文档配置会连错域名。

**④ `global:commodity:price` 是真实能力,但 skill 零覆盖**
- `/availability` 明确 `global:commodity:price=true`,实测组合有效(返回的是"未指定 metrics"而非"组合不支持")。
- 但 skill 没有 `global` area、没有 `commodity` asset_type、无任何 reference 提及 → **商品现货/连续价(黄金/原油等)网关能查,skill 永远拼不出请求**。属于 skill 漏接网关能力。

**⑤ 完整性校验形同虚设**
- `doctor.py` 的 `[3/4] File integrity` 依赖 `scripts/checksums.sha256`,但该文件**在包里不存在**(实测 `NO checksums.sha256`)。`verify_integrity` 在文件缺失时直接 `return True, "(skipped)"` → 这一步**永远显示 OK**,给人"已做完整性校验"的错觉。

**⑥ HK 字段名与 CN 不同构(隐性复杂度)**
- 实测 hk income 字段是 `TOT_OPER_REV` / `NP_BELONGTO_COMMONSH`,而非 CN 的 `OPER_REV` / `NET_PROFIT`。跨市场 metric 解析比文档 cheatsheet 呈现的更复杂。

---

## 5. 优化建议(给程序员,按优先级)

### P0 — 直接决定可用性,建议优先

- **[P0-1] 补齐入口解析层(最高频痛点,对应 A1/A2)**
  暴露 `match_asset`(名称→代码)与 `match_collection`(板块/概念→成分)为正式端点,或做一个统一 `/api/v3/resolve`。当前"分析下茅台/白酒板块"类查询从第一步就断,是体验最大短板。

- **[P0-2] 修 `diagnose.py` 的探活(对应 §4-①)**
  把 reachability 探测从 `/api/v3/market/status?area=all` 换成已验证可用的 `/api/v3/availability`(或 `?area=cn`)。否则自检工具在生产上恒报假宕机。顺带:把 403 纳入 `code_map`(当前落到 `unknown`→3,语义错位)。

- **[P0-3] 美股契约对齐(对应 B1/B2/§4-②)**
  market_cap 已宕需排查上游 `Code: 60`;短期补不齐就**前置降级声明**——skill 层先告知"美股仅支持价格/行业/实时快照",并让 `/availability` 的 false+reason 成为路由前置检查,减少试错往返。

### P1 — 架构健壮性

- **[P1-1] 服务端游标分页取代 `inline_threshold` 估算(对应 G1)**
  当前把 `N = symbols × days × metrics` + 按 data_type 的 margin 表这套复杂算术压给 LLM(易错、费 token),且 >1000 行 + runtime 取不到 CSV = 死路。建议网关出 `next_cursor` 游标分页,或让 runtime 能直取 `data_path`(签名 URL)。一举解决体量天花板。

- **[P1-2] 修 NaTType 系列上游 bug**
  `industry/share/index_member` 缺 date 崩、`revenue_breakdown` 缺 `report_periods`/占位日期崩。当前靠"教 LLM retry 一次"在 prompt 层兜底,脆弱。应在网关入参层给默认值或返回结构化 `action=error + suggestion`,而非内部 `strftime` 崩。

- **[P1-3] 稳定并增强 metric-resolver(对应"pending"标注)**
  该端点标注可能换路径,且无服务端模糊匹配(要 LLM 拉整表本地扫,费 token)。建议网关做 `name/synonym/description` 模糊匹配直接返回 top-N 候选 + canonical symbol,并冻结契约。

- **[P1-4] CSV `data_path` 决断**
  要么实现 runtime 可取(签名直链),要么从 response 拿掉。当前返回一个 runtime 永远取不到的路径,纯增困惑,还要专门写输出纪律防它泄漏。

### P2 — 数据补强 / 文档

- **[P2-1] 港股补强(对应 B3/B5)**:补 `currency` 字段(至少给 `inferred_currency + confidence`,别让 LLM 裸猜);补 segments。
- **[P2-2] 暴露已有但漏接的能力(对应 §4-④ / B7)**:把 `global:commodity` 和 quotes 的 `concept_index/index_futures/major_index` 写进 reference + asset_type 枚举。零成本解锁(网关已支持)。
- **[P2-3] price-history 加 `freq` 参数(对应 E2)**:daily/weekly/monthly(乃至 minute),别让 LLM 客户端重采样(周/月对齐规则微妙易错)。
- **[P2-4] 指数权重(对应 D9)**:`index_member` 增 `weight` 字段,解锁市值加权重构/指数分析。
- **[P2-5] 分红/事件数据域(对应 D2)**:adj_close 已隐含分红,补一个 dividend/action 明细端点成本低、价值高。
- **[P2-6] 文档与校验修缮**:更新 host 为 `skill.stocki.com.cn`(§4-③);随包发 `checksums.sha256`,否则删掉 doctor 的完整性步骤以免误导(§4-⑤);`/availability` 快照已从 2026-05-08 漂移,reference 里的"measured"矩阵需重新生成。

---

## 6. 附录:能力速查

### 6.1 "能查 / 不能查" 一图速记

```
能查(cn 全功能):  价格·三表·指标·估值·市值·行业·股本·一致预期·目标价·营收分部·5年分位·复合视图
能查(hk):          价格·三表·指标·估值·市值·行业·股本   (无 分部/一致预期/目标价/币种字段)
能查(us):          价格·行业·实时快照                    (无 任何基本面;market_cap 当前宕)
能查(指数/ETF/期货):仅价格(+cn指数成分,无权重)
能查(global):      商品价格 ← skill 漏接

查不到(整域缺失):  名称解析·板块解析·选股·回测·债券·期权·基金净值/持仓·
                    分钟线/Tick/盘口·分红明细·股东持仓·资金流·融资融券·大宗·
                    宏观·ESG·指数权重·解禁日历·任意窗口分位·>1000行面板·历史成分
```

### 6.2 数据缺口 → 业务问句(帮快速判断"这个问题能不能答")

| 用户会问的 | 能否答 | 缺口编号 |
|---|---|---|
| "茅台"是哪只股票 | ❌ 需手动 get_symbols | A1 |
| 白酒板块 / AI 概念都有哪些股 | ❌ | A2 |
| 帮我筛 ROE>15% 的股票 | ❌ | A3 |
| 这个策略回测一下 | ❌(纯首尾收益可) | A4 |
| 苹果的营收/ROE/PE 时序 | ❌(美股无基本面) | B1/B2 |
| 腾讯各业务板块占比 | ❌(港股无分部) | B3 |
| 腾讯财报是人民币还是港币 | ⚠ 只能推断 | B5 |
| BTC 过去一年走势 | ❌(crypto 历史价不可用) | B6 |
| 十大股东 / 北向资金 / 融资余额 | ❌ | D3/D4/D5 |
| 茅台分红多少 / 股息率 | ❌(无分红明细) | D2 |
| 沪深300 各成分权重 | ❌(只有代码无权重) | D9 |
| 茅台 5 分钟 K 线 / 盘口 | ❌(仅日频快照) | E1 |
| 茅台 PE 处于近 3 年 / 近 10 年什么分位 | ❌(仅固定 5 年) | F1 |
| 沪深300 全年每日成分面板 | ❌(>1000 行截断) | G1 |
| 2020 年时沪深300 有哪些成分 | ❌(幸存者偏差) | H1 |
| 黄金/原油现货价 | ⚠ 网关有但 skill 没路由 | §4-④ |

---

*报告基于 skill v0.3.0 契约 + 2026-05-26 对 `skill.stocki.com.cn` 的只读实测。可用性矩阵会随上游漂移,生产判断请以实时 `/api/v3/availability` 为准。*
