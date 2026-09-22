# 资讯与行情技术文档（归档）

> 来源：用户 2026-07-09 提供的 8 份公司文档（原件在 Downloads，此处为持久归档）。
> 供资讯产品侧 PRD 工作引用。配套记忆卡：`news-backend-architecture` / `market-data-cost` / `fiu-quote-interface-docs`。

## 一、资讯后端"三件套"架构文档（2026-05-09 生成，05-11 修订）

| 文件 | 服务 | 说明 |
|---|---|---|
| `stock-information.md` | stock-information :1214 | 资讯/公告主存储+业务服务，14 个 Feign Facade 全部指向它 |
| `stock-information-data.md` | stock-information-data :1959 | 资讯抓取/加工/分发（10 个资讯源、翻译、向量去重、敏感词、推送），最详尽的一份（含全量枚举表） |
| `as-stock-information.pdf`（+文本提取版） | as-stock-information :1217 | 对外 API 网关，无存储纯转发，访客判定 |

**去重说明**：用户同时提供的 `stock-information.pdf`、`stock-information-data.pdf` 经比对（标题/正文/生成日期一致）确认为上述两份 .md 的 PDF 导出版，未重复归档，以 .md 为准。

## 二、行情侧文档

| 文件 | 说明 |
|---|---|
| `行情成本梳理.pdf`（+文本提取版） | 行情业务成本：牌照/押金/人头费、FIU 四份数据采购合同（合计 ¥144.6 万/年）、2025 全年按月浮动成本报送数据、降本优化方案（含责任人） |
| `FIU金融数据服务_多源行情系统_港股OMDC_json&pb_V2.26(20250722).pdf`（+文本提取版） | FIU 港股 OMD-C 标准证券数据接口规范：码表/快照/逐笔/10档挂单/经纪席位/北向额度/港股通成交额/VCM/指数/IEP 等 17+ 协议 |
| `FIU金融数据服务_多源行情系统_NASDAQ_V_json&pb_1.17(20241119).pdf`（+文本提取版） | FIU 纳斯达克 Nasdaq Basic & NLS Plus 接口规范：码表/快照/挂单(仅买一卖一)/EOD/系统事件，含成交类型与停牌原因附录 |

注：《行情成本梳理》《FIU 接口文档》属于**行情(quote)域**而非资讯(news)抓取域——FIU 是行情数据供应商（合同编号 ZR-FIU*），资讯源供应商是融聚客等；两域在"个股页/资讯列表关联报价"处交汇。

## 三、快速导航

- 想知道 **APP 资讯页某个 Tab 调哪个接口** → `stock-information.md` §5.0 / `as-stock-information` §5
- 想知道 **某资讯源怎么抓、落哪张表** → `stock-information-data.md` §4.1（新闻）/ §4.2（公告）
- 想知道 **卓锐洞察推送全流程** → `stock-information-data.md` §4.5
- 想知道 **资讯分类/子类/状态枚举全量取值** → `stock-information-data.md` §6.3
- 想知道 **行情能力边界（如美股有没有十档）** → 两份 FIU 接口文档（美股 Nasdaq Basic 仅 BBO 买一卖一；港股 OMD-C 有 10 档+经纪席位）
- 想核 **行情成本/人头费/降本方向** → `行情成本梳理`
