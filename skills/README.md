# 券商产品经理 Claude Skills 合集

为券商/证券行业产品经理精选的 12 个 Claude Skills。`../skill-zips/` 目录下有每个 skill 对应的 zip 包，**直接把 zip 拖进 claude.ai → Settings → Skills 面板即可使用**（也可拖整个 skill 文件夹）。

## 定制 Skill（本仓库原创）

| Skill | 用途 |
|---|---|
| `broker-pm-assistant` | 券商产品经理助手（中文）：券商 App 功能 PRD、竞品分析（同花顺/东财/富途等）、合规适当性检查清单、行情/交易/两融/理财/投顾模块设计 |

## 产品经理通用（来源：[phuryn/pm-skills](https://github.com/phuryn/pm-skills)，MIT）

| Skill | 用途 |
|---|---|
| `create-prd` | 8 段式 PRD 模板，撰写/评审需求文档 |
| `competitor-analysis` | 竞品分析：竞争格局、优劣势、差异化机会 |
| `prioritization-frameworks` | 需求优先级排序（RICE/ICE 等框架） |
| `user-personas` | 用户画像构建 |
| `customer-journey-map` | 用户旅程图 |
| `summarize-interview` | 用户访谈纪要与洞察提炼 |
| `ab-test-analysis` | A/B 实验设计与结果分析 |
| `north-star-metric` | 北极星指标制定 |

## 券商领域知识（来源：[JoelLewis/finance_skills](https://github.com/JoelLewis/finance_skills)，MIT）

| Skill | 用途 |
|---|---|
| `order-lifecycle` | 订单生命周期/OMS：委托状态机、FIX 消息流、撤改单、审计留痕 |
| `margin-operations` | 保证金/融资融券业务：保证金计算、追保、强平逻辑 |
| `pre-trade-compliance` | 事前合规风控：限制名单、集中度限制、委托前置校验规则引擎 |

> 注：finance_skills 三个 skill 以美国监管体系（Reg T、FINRA 等）为背景，机制原理通用，境内规则请结合 `broker-pm-assistant` 的合规清单使用。

## 使用方式

1. 打开 claude.ai → 设置 → Capabilities / Skills
2. 将 `skill-zips/` 中的 zip 文件拖入 Skills 面板（每个 zip 是一个独立 skill）
3. 对话中描述相关任务（如"帮我写一个两融开通流程的 PRD"），Claude 会自动调用匹配的 skill
