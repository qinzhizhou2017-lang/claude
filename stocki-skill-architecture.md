# Stocki Skill 完整架构（超越 MD 文档）

## 概览：4 层组成结构

```
stocki-financial-reader/
├─ [层1] 顶级配置 + 元数据
│  ├─ SKILL.md (v0.3.0 Frontmatter + 路由表)
│  ├─ README.md (使用说明 + 数据来源声明)
│  └─ INSTALL.md (安装步骤)
│
├─ [层2] 8 个知识库文档 (references)
│  ├─ realtime-quote.md       (实时行情)
│  ├─ price-history.md        (历史价格)
│  ├─ fundamentals-panel.md   (财务数据)
│  ├─ financial-context.md    (综合分析)
│  ├─ consensus-and-target.md (一致预期)
│  ├─ industry-and-symbols.md (行业成分)
│  ├─ market-calendar.md      (交易日历)
│  └─ metric-resolver.md      (指标解析)
│
├─ [层3] 执行脚本 (scripts)
│  ├─ _http.py        (HTTP 通讯层)
│  ├─ doctor.py       (自诊断脚本 #1)
│  └─ diagnose.py     (自诊断脚本 #2)
│
└─ [层4] 隐含部分 (LLM 路由 + 提示词)
   ├─ 动态路由逻辑 (R1-R8 规则映射)
   ├─ 输出规范化 (去除 Wind API 痕迹)
   └─ 错误处理流程
```

---

## 详细分解

### 🟦 **层1：顶级配置（3 个 MD）**

#### `SKILL.md`（核心配置）
```yaml
name: stocki-financial-reader
version: 0.3.0
requires:
  bins: [python3]
  env: [STOCKI_GATEWAY_URL, STOCKI_API_KEY]
  os: [linux, darwin]
```
- **frontmatter**：OpenClaw 框架元数据（emoji、依赖声明）
- **核心内容**：
  - HTTP 约定（Base URL、Auth header、Content-Type）
  - 错误代码映射（401→auth_invalid, 503→stocki_unavailable 等）
  - **inline_threshold 决策树**（关键！决定数据截断行为）
  - **8 个 reference 的路由表 R1-R8**（哪个查询该去哪个 endpoint）
  - 输出规范化规则（禁止暴露 `OPER_REV` / `wind-` 前缀等）

#### `README.md`（用户文档）
- 架构说明（4 层结构）
- 8 个 reference 的简表
- 安装/设置步骤
- **免责声明**（重要！数据可能延迟、不构成投资建议）

#### `INSTALL.md`（部署说明）
- 环境变量设置 (`STOCKI_GATEWAY_URL`、`STOCKI_API_KEY`)
- doctor/diagnose 脚本运行方法

---

### 🟩 **层2：8 个知识库（References）**

每个 `.md` 都是 **endpoint 合约文档**：

| Reference | HTTP 端点 | 职责 | 特点 |
|-----------|----------|------|------|
| **realtime-quote** | `POST /api/v3/quotes/get_latest_quotes` | 实时快照 + fundamentals | 跨市场单次查询 |
| **price-history** | `POST /api/v3/datareader/read (price)` | OHLCV + 复权 | 注意期货滚动日污染 |
| **fundamentals-panel** | `POST /api/v3/datareader/read (financial/indicator/valuation/market_cap)` | 三表 + 财务指标 + 估值 | 最复杂；CN/HK YTD 陷阱 |
| **financial-context** | `POST /api/v3/financial_context/{cn,hk}` | 一键综合分析 (L1/L2/L3) | CN/HK only；L3 含全量 consensus |
| **consensus-and-target** | `POST /api/v3/datareader/read (consensus_forecast/target_price/revenue_breakdown)` | 分析师预期 + 业务分部 | CN only；稀疏数据 |
| **industry-and-symbols** | `POST /api/v3/datareader/read + /api/v2/market_symbol/get_symbols` | 行业分类 + 指数成分 + 公司基本信息 | 无选股能力 |
| **market-calendar** | `GET /api/v3/market/*` | 交易日 + 市场状态 + 数据可用性 | 全局查询 |
| **metric-resolver** | `POST /api/v2/market_metric/get_metrics` | 指标名解析 (CN/EN/别名 → canonical) | 二步流程的第一步 |

**每个 reference 文档包含**：
1. 触发词汇（中英混合）
2. Input schema（JSON 参数合约）
3. E2E 示例（curl 命令）
4. 响应字段映射表（Raw → User-Facing Label）
5. 路由边界条件（这个 endpoint 不该处理什么）

---

### 🟦 **层3：执行脚本（Python）**

#### `scripts/_http.py`（通讯基础库）
```python
def gateway_request(method, path, body=None, timeout=30) -> dict
```
- **职责**：封装所有 HTTP 请求到 stocki gateway
- **功能**：
  - 读取 `STOCKI_GATEWAY_URL` + `STOCKI_API_KEY` 环境变量
  - 构造 `Authorization: Bearer {key}` header
  - 统一错误处理 (HTTP 401/429/5xx → exit code 1/4/3)
  - JSON 请求/响应序列化
- **Exit Code 映射**（stdlib only, 无外部依赖）：
  ```
  0 = 成功
  1 = auth_invalid (401)
  2 = unreachable (TCP/DNS error)
  3 = stocki_unavailable (5xx / timeout)
  4 = rate_limited (429)
  ```

#### `scripts/doctor.py`（自诊断脚本 #1）
```bash
python3 scripts/doctor.py
```
执行 **4 项检查**：
1. **Env vars** - 检查 `STOCKI_GATEWAY_URL` + `STOCKI_API_KEY` 存在 + 格式是否为 `sk_*` 或 `eyJ*` (JWT)
2. **Skill version** - 从 `SKILL.md` 读取本地版本号，可选对比远程
3. **File integrity** - 校验 SHA256（如存在 `checksums.sha256`）
4. **Workspace** - 确认工作目录状态（不会创建文件）

Exit: 0 = 全部 OK；1 = 任何检查失败

#### `scripts/diagnose.py`（自诊断脚本 #2）
```bash
python3 scripts/diagnose.py
```
执行 **2 项烟雾测试**：
1. **Reachability** - `GET /api/v3/market/status?area=all` (测连通性，10s 超时)
2. **Auth + Read** - `POST /api/v3/quotes/get_latest_quotes` for 600519 (茅台)
   - 验证返回 JSON 包含 `symbol` + `close` 字段
   - 测试认证 + 真实数据读取

Exit code 同 `_http.py` 映射

#### `scripts/__init__.py`
空文件，使 scripts 成为 Python package

---

### 🟨 **层4：隐含部分（LLM 框架侧）**

这些不在文件系统中，而是由 Claude Code / OpenClaw 框架提供：

#### 路由框架 (R1-R8)
```
用户查询
    ↓
[SKILL.md 路由表]
    ↓
选择目标 reference (realtime-quote / fundamentals-panel / ...)
    ↓
调用对应 endpoint + 格式化请求
    ↓
处理响应 + 输出规范化
```

#### 动态 Prompting
SKILL.md 的内容被编码成 LLM 的上下文，包括：
- 8 个 endpoint 各自的使用场景
- 路由决策规则 (用户问"现价"→realtime-quote；问"PE 历史"→fundamentals-panel)
- 禁止事项 (不要传 Wind API 内部列名、不要虚构数据等)

#### 输出规范化
```python
# ❌ 禁止输出
"OPER_REV: 5000万元"
"wind-食品饮料"
"AAPL|ST|USA"
"_source_map: AShareIncome"

# ✅ 正确输出
"营业总收入：5000 万元"
"食品饮料"
"AAPL"
```

---

## 执行流程图

```
┌─────────────────────────┐
│   用户提问              │
│ "茅台现在 PE 多少"      │
└────────────┬────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ LLM 匹配 SKILL.md 路由表             │
│ 触发词汇: "现价", "PE", "现在"      │
│ 规则 R4: 现价 + 基本面 snapshot    │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 选择 Reference: realtime-quote.md   │
│ 构造 POST /api/v3/quotes/get_latest │
│ Body: {                             │
│   "assets": [{                      │
│     "symbols": ["600519"],          │
│     "area": "cn",                   │
│     "asset_type": "stock"           │
│   }],                               │
│   "include_fundamentals": true      │
│ }                                   │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ scripts/_http.py                    │
│ gateway_request(method="POST",      │
│   path="/api/v3/quotes/...",        │
│   body={...})                       │
│                                     │
│ 读 env: STOCKI_GATEWAY_URL + KEY   │
│ 拼接 Authorization header          │
│ urlopen → JSON 响应                 │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Stocki Gateway (外部 HTTP API)     │
│ 调用 Wind API 获取数据             │
│ 返回 JSON 响应                      │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 响应处理                            │
│ {                                   │
│   "data": [{                        │
│     "symbol": "600519",             │
│     "close": 1234.56,               │
│     "fundamentals.pe_ttm":          │
│       "12.34|市盈率(TTM)|2026-05-26│... │
│   }],                               │
│   "data_context.freshness":         │
│     "cn:stock/realtime",            │
│   "market_status.cn": "open"        │
│ }                                   │
└────────────┬────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│ 输出规范化 (SKILL.md 规则)          │
│ • strip _source_map                  │
│ • 解析 pipe-delim 基本面字段        │
│ • 标注 freshness: realtime          │
│ • 映射 metric raw key → CN label    │
│                                      │
│ 最终输出:                            │
│ "茅台（600519）                     │
│  实时价格：1234.56 元               │
│  市盈率(TTM)：12.34                 │
│  市场状态：开盘（实时数据）"        │
└──────────────────────────────────────┘
```

---

## 数据流向总结

```
用户查询
  ↓
[SKILL.md 路由规则 R1-R8]
  ↓
[8 个 References 中选 1-3 个]
  ↓
[scripts/_http.py 构造 HTTP 请求]
  ↓
Stocki Gateway
  ↓
Wind API (底层数据源)
  ↓
[JSON 响应]
  ↓
[输出规范化（SKILL.md 规则 + Reference 字段映射）]
  ↓
用户可见的中文文本
```

---

## 关键参数传递链

| 参数 | 来源 | 用途 | 类型 |
|------|------|------|------|
| `STOCKI_GATEWAY_URL` | 环境变量 | gateway 基础 URL | string |
| `STOCKI_API_KEY` | 环境变量 | 认证 token | string |
| `inline_threshold` | SKILL.md 决策树 | 数据截断行为 | int [1-1000] |
| `metrics` | Reference 合约 | 查询哪些字段 | list[canonical_key] |
| `start_date / end_date` | Reference 合约 | 时间窗口 | YYYY-MM-DD |
| `data_type` | Reference 合约 | 数据类型 | enum |
| `extra.*` | Reference 细则 | 特殊参数 (YTD、PIT 等) | mixed |

---

## 层级职责划分

| 层 | 谁负责 | 职责 | 改动频率 |
|---|-------|------|---------|
| **层1** (SKILL.md + README) | Stocki 团队 | 框架定义、路由规则、规范化 | 低（版本更新时） |
| **层2** (8 个 References) | Stocki 团队 | Endpoint 合约、字段映射、示例 | 中（API 变更时） |
| **层3** (scripts) | Stocki 团队 | HTTP 通讯、自诊断 | 低 |
| **层4** (LLM 框架) | Claude / OpenClaw | 动态路由、提示词注入、输出处理 | 高（每次会话） |

---

## 不在文件系统中的部分

1. **具体的 HTTP 请求拼接逻辑** - LLM 在运行时基于 Reference 的 Input schema 拼接
2. **错误恢复流程** - 例如 `revenue_breakdown` 缺少 `report_periods` 时，LLM 应自动重试，不是脚本
3. **多 reference 联合查询** - R7 规则允许"AAPL 现价 + 一致预期 + 行业"三次调用，编排在 LLM 侧
4. **提示词注入** - 8 个 Reference 的内容被编码成 Claude 的上下文，作为"知识库"存在

---

## 自诊断工作流（用户视角）

```bash
# 安装后首次使用
export STOCKI_GATEWAY_URL=https://api.stocki.com.cn
export STOCKI_API_KEY=sk_xxxxx

# 检查1：环境配置
python3 ~/.claude/skills/stocki-financial-reader/scripts/doctor.py
# 输出: [1/4] Env vars OK, [2/4] Version OK, [3/4] Integrity OK, [4/4] Workspace OK

# 检查2：网络连通性 + API 测试
python3 ~/.claude/skills/stocki-financial-reader/scripts/diagnose.py
# 输出: [1/2] Reachability OK, [2/2] Auth+Read OK (sample: 600519 -> close)

# 如果失败，exit code 告诉你问题类别
```

---

## 总结

Stocki skill **不只是 MD 文档**，而是一个 **4 层系统**：

1. **文档层** (SKILL.md + 8 References) → 定义能力边界、路由规则、合约
2. **脚本层** (Python) → HTTP 通讯、自诊断工具
3. **框架层** (Claude Code) → 动态路由、提示词、输出规范化
4. **执行层** (Wind API) → 真实数据源

**核心创新**：通过详细的 Markdown 合约 + 路由规则，使得 LLM 可以自主决定调用哪个 endpoint、传什么参数、如何解释结果，而无需硬编码。
