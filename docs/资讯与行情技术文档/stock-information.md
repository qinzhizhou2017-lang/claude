# stock\-information

# stock\-information 项目架构说明

> 本文与 stock\-information\-data 架构说明 / as\-stock\-information 架构说明 同一格式。`stock-information` 是 cms 平台资讯链路的**主存储 \+ 业务服务**，承担绝大多数 Feign 接口（被 `as-stock-information` 调用），同时持有所有数据库 / 缓存 / 消息的实际读写权。

> 与本仓库已有的 `01-fix-notification-timeout.md` / `02-fix-disturb-free-filter-missing-users.md`（缺陷修复说明）放在同一 `spec/` 目录下，命名 `03-...` 避免覆盖。

## 如何查看本文档的图

含 Mermaid 图：IDEA 装 *Mermaid* 插件、VSCode 装 *Markdown Preview Mermaid Support*、GitLab/GitHub 原生支持，或粘贴到 [https://mermaid\.live](https://mermaid.live) 临时预览。

---

## 1\. 项目概述

`stock-information` 是 cms 平台的**资讯/公告主服务**，端口 **1214**，应用名 / Apollo `app.id` 都是 `stock-information`。它是整条资讯链路上最早建立、生命周期最长的服务：

- **对内**：通过 Feign Facade 给 `as-stock-information`（对外网关）和其他兄弟服务提供 14 个接口；这些接口承载 APP 上几乎所有资讯/公告/主题/快讯/卓锐洞察的数据获取请求。

- **对外**：自身不直接被 APP 访问，所有 HTTP 入口由 `as-stock-information` 透传。

- **数据持有方**：11 个 MySQL 数据源、MongoDB（`t_news` 文档库）、Redis（去重/缓存/锁）、Aliyun OSS（图片/附件）；与 `stock-information-data` 共用同一套底层存储。

- **历史遗留**：保留了一份完整的资讯抓取代码（`scheduled/` / `xxljobhandler/`），与 `stock-information-data` 高度重复。当前实际生产里**新资讯源只在 \-data 跑**，本服务的抓取链路属于历史包袱，但仍可工作。详见 §10。

**启动类**：StockInformationApplication\.java，标准 Spring Cloud 装配（`@EnableEurekaClient` \+ `@EnableFeignClients(basePackages={"com.zhuorui.**.facade"})` \+ `@EnableHystrix` \+ `@EnableApolloConfig` \+ `@EnableAsync`），`@SpringBootApplication(exclude={DataSourceAutoConfiguration.class})` 表示数据源由 `MybatisPlusConfig` 手工装配。

---

## 2\. 数据流转

```Plaintext
flowchart LR
    subgraph EXT["外部"]
        APP[App / Web / 后台]
    end

    subgraph ENT["对外入口（不直连 APP）"]
        AS["as-stock-information :1217"]
        Sib["其他兄弟服务<br/>(community / ai-helper / ...)"]
    end

    subgraph SI["stock-information :1214"]
        Ctl["Controller 层<br/>10 个 Controller"]
        Svc["Service 层<br/>NewsDataService / AnnouncementInitDataService /<br/>StockInfoDetailService / TopicDataService ..."]
        Cache["caches: GalleryKeyWordCache /<br/>ImageCodeCache + InformationCacheUtil"]
        Jms["jms/<br/>AnnouncementConsumer / NewsImportantConsumer +<br/>AnnouncementPushProducer / NewsPushProducer"]
    end

    subgraph SH["共享存储"]
        My[("MySQL × 11<br/>information / hkiis / hknews /<br/>cnblt / cnstock / usnews / usreport /<br/>oss_a / oss_hk / oss_us / img_url")]
        Mg[("MongoDB t_news")]
        Rd[("Redis<br/>缓存/去重/锁")]
        OSS[("Aliyun OSS")]
    end

    subgraph PEER["平台中间件 / 兄弟服务"]
        RM[(RabbitMQ)]
        SID[stock-information-data :1959]
        NF[notification 消息中心]
        UA[user-account]
        SM[stock-market / hk / a]
    end

    APP --> AS
    AS -->|"14 Feign 接口"| Ctl
    Sib -.Feign.-> Ctl
    Ctl --> Svc
    Svc --> My
    Svc --> Mg
    Svc --> Rd
    Svc -.写.-> OSS
    Cache -.热数据.-> Rd
    Svc -.要闻自动推送.-> Jms
    Jms -->|RabbitMQ Push| RM
    RM -->|Notice 队列| NF
    NF --> APP
    Jms -.Feign.-> UA
    Jms -.Feign.-> SM
    SID -.抓取入库.-> My
    SID -.抓取入库.-> Mg
    SID -.抓取入库.-> Rd
```

**关键说明**

|流向|说明|
|---|---|
|**APP → AS → SI**|APP 流量永远经过 AS；SI 不暴露给公网。|
|**AS Feign → SI Controller**|14 个 Facade（`NewsInfoFacade` / `AnnouncementInfoFacade` / `TopicFacade` \.\.\.）路由到 10 个 Controller。当前 APP 主资讯页流量集中在 `NewsInfoFacade.getList`（7 个 Tab \+ 多个 chip 共用主列表）\+ `NewsInfoFacade.pullFastNewsList`（快讯 Tab）\+ `AnnouncementInfoFacade.announcementList`（公告 chip）；`NewsInfoFacade.getRecommend` 仅服务卓锐洞察 Tab 顶部首推副接口。详见 §5\.0。|
|**SI ↔ 共享存储**|SI 是这套存储的对外"主读者 \+ 业务写者"（更新资讯状态 / 推送报告 / 翻译结果等）。**抓取写入由 ****`-data`**** 独家承担**，SI 不再跑定时拉取。|
|**SID ↔ 共享存储**|`-data` 是新资讯源（路透 / CoinDesk / FiNet / Techub / 智通 / 格隆汇 / 凤凰网 / BlockBeats / 公告 …）的 XXL\-Job 抓取主体，结果直接写 MySQL\+Mongo\+Redis，不对外提供 API。|
|**SI JMS**|RabbitMQ 双向：消费 `ANNOUNCEMENT_PUSH` / `PUSH_INFORMATION_NEWS`（公告 / 要闻自动推送），生产 `NOTICE_EXCHANGE_DIRECT`（通知中心）。|

---

## 3\. 系统架构

```Plaintext
flowchart TB
    classDef ctl fill:#dff,stroke:#06c
    classDef svc fill:#fff8d6,stroke:#aa8
    classDef boot fill:#fde,stroke:#a36
    classDef store fill:#e8e0ff,stroke:#62a

    subgraph 接入层["对内 HTTP（Controller + Feign 入口）"]
        L1[NewsInfoController]:::ctl
        L2[AnnouncementInfoController<br/>+ ConAnnouncementInfoController]:::ctl
        L3[AllInformationListController]:::ctl
        L4[StockInfoDetailController]:::ctl
        L5[TopicInfoController + ConTopicInfoController]:::ctl
        L6[ConNewsInfoController<br/>+ ConGalleryInfoController]:::ctl
        L7[NewsPushReportController]:::ctl
    end

    subgraph 应用层["业务 Service"]
        S1[NewsInitDataService<br/>资讯入库 + 翻译 + 分类]:::svc
        S2[NewsDataService<br/>资讯查询 + 列表 + 详情]:::svc
        S3[AnnouncementInitDataService<br/>公告抓取 + 入库 + 查询]:::svc
        S4["NewsPushCentreService<br/>+ NewsPushReportService<br/>(卓锐洞察)"]:::svc
        S5["AllInformationListService<br/>+ StockInfoDetailService<br/>(聚合查询)"]:::svc
        S6[TopicDataService<br/>+ GalleryDataService]:::svc
        S7["oss/* (AOSS / HKOSS / USOSS /<br/>ImageCode / InformationUrl)"]:::svc
    end

    subgraph 启动消息层["启动 + 消息"]
        B1["boot/DefaultInitApplication<br/>启动时检查并初始化 Redis 缓存"]:::boot
        B2["jms/AnnouncementConsumer +<br/>NewsImportantConsumer<br/>(RabbitMQ 消费)"]:::boot
        B3["jms/producer/<br/>AnnouncementPushProducer +<br/>NewsPushProducer +<br/>NewsPushData"]:::boot
    end

    subgraph 存储层["存储 + 集成"]
        ST1[("MySQL × 11<br/>多数据源切面路由")]:::store
        ST2[("MongoDB<br/>t_news")]:::store
        ST3[("Redis<br/>缓存 / 去重 / 锁")]:::store
        ST4[("Aliyun OSS<br/>announcement / gallery")]:::store
        ST5[("RabbitMQ")]:::store
    end

    接入层 --> 应用层
    应用层 --> 存储层
    启动消息层 --> 应用层
    启动消息层 --> 存储层
```

> **注**：定时抓取（XXL\-Job `xxljobhandler/` \+ `scheduled/`）当前由 `stock-information-data` 承担，本服务仓库内仍保留同名包但**生产已不再调度**，因此不在系统架构图中体现。具体重复代码现状参见 §10。

**主要分层职责**

- **接入层（Controller）**：10 个 RestController，全部为 Feign 入口；URL 前缀按 `/api/news`、`/api/announcement`、`/api/info`、`/api/topic`、`/api/gallery` 等划分。

- **应用层（Service）**：

    - `news/`：`NewsInitDataService`（入库总入口）、`NewsDataService`（对外查询）、`NewsPushCentreService` / `NewsPushReportService`（卓锐洞察）、`TopicDataService` / `GalleryDataService`。

    - `announcement/`：`AnnouncementInitDataService`（A/HK/US 公告统一入口）。

    - `oss/`：`AOSSService` / `HKOSSService` / `USOSSService` / `ImageCodeService` / `InformationUrlService`，对应 5 个数据源的 OSS 同步。

    - `cnblt/` / `cnstock/` / `hkiis/` / `hknews/` / `usnews/` / `usreport/`：行情商落地库的只读 service（按数据源切分）。

    - 顶层接口：`AllInformationListService` / `StockInfoDetailService`（聚合查询）。

- **启动 \+ 消息层**：

    - `boot/DefaultInitApplication`：启动时若 `INFO_NEWS` / `INFO_ABNORMAL_NEWS` Redis ZSet 数量低于阈值（默认 100）则触发缓存初始化；同时调 `pullGalleryOssData()`。

    - `jms/`：2 个 RabbitMQ Consumer（公告推送、要闻自动推送）\+ 3 个 Producer 类（含 DTO）。

- **存储层**：与 `stock-information-data` 完全共用一套（11 数据源 / Mongo / Redis / OSS / RabbitMQ）。

    - 多数据源路由完全相同：`@DataSource(DataSourceEnum.XXX)` 切面 \+ `MultipleDataSource`（MybatisPlusConfig\.java），`@MapperScan(basePackages={"com.zhuorui.stockinformation.mapper.**.**"})`。

---

## 4\. 部署形态

```Plaintext
flowchart LR
    subgraph CL["Eureka / Apollo"]
      EU[("Eureka")]
      AP[("Apollo")]
    end

    subgraph SI["stock-information 实例（多实例）"]
      ND1[Node 1 :1214]
      ND2[Node 2 :1214]
      ND3[Node N :1214]
    end

    subgraph DEP["依赖"]
      MS[("MySQL × 11 库")]
      MG[("MongoDB")]
      RD[("Redis")]
      OS[("Aliyun OSS")]
      RM[("RabbitMQ")]
      XJ[XXL-Job 调度中心]
    end

    subgraph SIB["兄弟服务 / 调用方"]
      AS[as-stock-information :1217]
      SID[stock-information-data :1959]
      Other["community / ai-helper /<br/>其他业务服务"]
      NF[notification]
      UA[user-account]
      SM[stock-market / hk / a]
    end

    EU --- SI
    AP --- SI
    SI -.注册/订阅.-> EU
    SI -.拉配置.-> AP
    SI -->|JDBC| MS
    SI -->|Mongo Driver| MG
    SI -->|Redis Helper| RD
    SI -->|OSS SDK| OS
    SI -->|Producer + Consumer| RM
    SI -->|XXL Executor| XJ
    AS -.Feign.-> SI
    Other -.Feign.-> SI
    SI -.Feign.-> NF
    SI -.Feign.-> UA
    SI -.Feign.-> SM
    SID -.写共享存储.-> MS
    SID -.写共享存储.-> MG
    SID -.写共享存储.-> RD
```

**配置要点**（bootstrap\.yml）

- 端口 1214，应用名 `stock-information`，Apollo `app.id=stock-information`。

- Web 容器 Undertow：`io-threads=20, worker-threads=32`。

- Hystrix：`timeoutInMilliseconds=9000`，`coreSize=100`，`SEMAPHORE` 隔离，`maxConcurrentRequests=1000`。

- Ribbon：`ReadTimeout=3000ms, ConnectTimeout=1000ms`。

- MyBatis\-Plus：`mapper-locations=classpath*:/mapper/**/*Mapper.xml`，`MapperScan` 限定 `com.zhuorui.stockinformation.mapper.**.**`。

- Profile：`local / dev / pre / test / prod`，`prod` 仅注入 Eureka/Apollo 地址，DB / Redis / RabbitMQ 配置由 Apollo 下发。

- 不开启 Kafka 消费者（与 \-data 不同：本服务**不消费**路透 Kafka topic，`information_data_snapshot` 仅由 \-data 处理）。

---

## 5\. 业务范围

按"对外 API"和"后台任务/消息"两块组织。**对外 API 是本服务的主战场**（被 AS 调），后台任务部分目前主要由 \-data 承担（见 §10）。

### 5\.0 APP 资讯页 ↔ SI 服务调用 全链路对照

APP「资讯」一级 Tab 的页面结构（与原型图对照）：

```Plaintext
顶部一级 Tab    ：资讯 | 社区 | 视频           ← APP 主导航
资讯页二级 Tab  ：自选 | 卓锐洞察 | 要闻 | 快讯 | 加密货币 | 新股 | 宏观 [≡ 更多]
二级 Tab 下筛选 ：新闻 ▾ | 所有公告 ▾ | 评级       ← 内容类型筛选 chip
                                              右上：全部 ▾（市场筛选）
```

**整个资讯页只用 4 个核心接口**（合占 SI 流量的 80%\+；`/api/important_news/*` `/api/info/selected/*` 等历史接口虽仍提供，但当前 APP 主资讯页未使用）：

|APP UI 元素|AS Endpoint|SI Controller|SI Service 方法|数据来源（实际查询）|
|---|---|---|---|---|
|**Tab：自选 / 卓锐洞察 / 要闻 / 加密货币 / 新股 / 宏观（及 ≡ 展开的港股 / 美股 / 异动等）→ chip「新闻」「评级」**|`POST /api/news/v1/list`|NewsInfoController `/api/news`|`NewsDataService.pullNewsList(lang, vo)`|`NewsDao.pullNewsList` 查 Mongo `t_news`；筛选维度：`type`（NewsCategoryEnum，卓锐洞察 Tab 传 `14`）、`selectedCodes`（自选股 ts\_code 列表）、`market`、`code`、`subType`；`notLogin=true` 时 DAO 层过滤路透社等付费源|
|**Tab：快讯**|`POST /api/news/v1/fast_list`|同 `NewsInfoController`|`NewsDataService.pullFastNewsList(lang, vo)`|`NewsDao.pullNewsList` 查 Mongo `t_news`（`type=FAST(3)`，可带 `subType ∈ {GLOBAL, INDEX, HK, US, FUTURES, VA}`）；返回时 `removeHtmlTag(content)`|
|**Tab：自选 → chip「所有公告」**|`POST /api/announcement/v1/list`|AnnouncementInfoController `/api/announcement`|`AnnouncementInitDataService.listAnnouncement(lang, vo)`|按 `market`\(1 港 / 2 美 / 3 沪深\) 通过 `@DataSource` 切对应公告库 \(`hkiis` / `usreport` / `cnstock` …\)，查公告表；**必须带 ****`code`**** 或 ****`selectedCodes`** 否则 Controller 直接返回 `PARAM_NOT_VALID`|
|**Tab：卓锐洞察 → 顶部首推（banner \+ hot）**|`POST /api/news/v1/get_recommend`|同 `NewsInfoController`|`NewsDataService.getRecommend(lang, notLogin)`|构造 `NewsReqPageVo{isRecommend=1, type=14}` → `NewsDao.pullNewsList` 查 Mongo `t_news`；按 `recommended_bit` 拆 `banner(=1)` / `hot(=2)`；**只是 Tab 顶部首推模块，下半部分常规列表仍走 ****`/v1/list`**|
|**点列表项进详情页**|`POST /api/news/v1/content`|同 `NewsInfoController`|`NewsDataService.pullNewsContent(lang, vo)`|Mongo `t_news` 主体 \+ Redis 详情缓存；不命中则补查 MySQL `news` \+ `news_operate_log`|
|**详情页底部「AI 助手相关资讯」**|`POST /api/news/v1/ai_make_up`|同 `NewsInfoController`|`NewsDataService.makeUpNews(lang, vo)`|先 `pullNewsList(vo)` 取关联资讯列表，再 `batchPullNewsContent(newsIds)` 批量取详情，组装成 `MakeUpNewsDto`|
|**列表项关联个股价格**（如截图里 `谷歌-C 397.050 +0.44%`）|**不走 SI**|\-|\-|APP 拿到 `news.codes`（如 `US:GOOG`）后单独调 `stock-market-*` 服务实时刷价格|

#### 5\.0\.1 接口的等价模型

把 APP 看作一个无状态客户端，等价地理解为：所有列表请求最终都收敛到一个 DAO 方法。

```Plaintext
+-----------------------+
APP 资讯主页 ───[X-User-Id + Body]──> /v1/list          ──> NewsDao.pullNewsList(NewsReqPageVo)
                                |                       |     ↑
                                |   /v1/fast_list       |     └ 服务端预置 type=FAST，返回时剥 HTML
                                |   /v1/get_recommend   |     └ 服务端预置 isRecommend=1 + type=14
                                |                       |         并按 recommended_bit 拆 banner/hot
                                |   /announcement/v1/list ─── AnnouncementInitDataService.listAnnouncement
                                +-----------------------+

  Tab（含卓锐洞察 type=14）       => NewsReqPageVo.type
  filter chip「新闻 / 评级」      => NewsReqPageVo.type
  自选 Tab                        => NewsReqPageVo.selectedCodes
  右上「全部 ▾」市场筛选          => NewsReqPageVo.market
  访客 / 已登录                   => NewsReqPageVo.notLogin (由 AS 注入)
  快讯子分类（HK / US / 全球…）   => NewsReqPageVo.subType
  下拉 / 上拉游标                 => NewsReqPageVo.pubTime + newsId
```

- `/v1/list` 是真正承担流量的「通用列表」接口（7 个 Tab \+ 多个 chip 共用），卓锐洞察 Tab 的常规列表也是这条路径，靠 `type=14` 区分。

- `/v1/fast_list` / `/v1/get_recommend` **服务端帮 APP 预置了固定参数**（fast\_list 强制 `FAST(3)`，get\_recommend 强制 `isRecommend=1 + type=14`），并对返回结构做了不同包装；本质上仍走同一个 `NewsDao.pullNewsList`，只是 APP 不用自己拼那些参数。

- `/v1/get_recommend` 仅服务于"卓锐洞察 Tab 顶部首推"模块（一个 banner 横幅 \+ 一个 hot 推荐列表），不是 Tab 整体入口。

#### 5\.0\.2 历史链路与现行链路的对照

|维度|旧（资讯页历史）|现行（原型图所示）|
|---|---|---|
|「要闻」Tab|`/api/important_news/v1/all_info_list_new` `/_old`，命中 Redis ZSet `INFO_NEWS` 预热缓存|`/api/news/v1/list` \+ `type=MAJOR_NEWS(0)`|
|「自选」Tab|`/api/info/selected/v1/get_last` `/get_old`，SI 内部先 Feign 取自选股再查 Mongo|`/api/news/v1/list` \+ `selectedCodes=...`（自选股列表由 APP 自己传入）|
|「公告」筛选|（未独立）|`/api/announcement/v1/list` \+ `selectedCodes=...`|

> **现行链路下，****`AllInformationListController`**** / ****`StockInfoSelectController`**** 仍存在但 APP 不再调**——它们可能仍被 H5 / 老版本 APP / 内部页面引用，所以暂不能删。`InformationCacheScheduled` 预热的 Redis ZSet `INFO_NEWS` 也仍在跑，但只服务于历史链路。

#### 5\.0\.3 与「卓锐洞察推送」的区别

APP 顶部"卓锐洞察 Tab"和文档其他地方提到的「卓锐洞察推送」**是两件事**：

|维度|APP 卓锐洞察 Tab|卓锐洞察推送|
|---|---|---|
|入口|APP 主动拉 `/api/news/v1/get_recommend`|后台运营手工发起，写 `news_push_centre` 表|
|数据存储|Mongo `t_news`（`is_recommend=1` 且 `type=14`，按 `recommended_bit` 拆 banner / hot）|MySQL `news_push_centre`（关联到 `news.id`）|
|触发|用户打开 Tab|立即推送（push\_way=1）或定时（push\_way=2，XXL\-Job `PUSH_NEWS_ZY` 扫表）|
|推送通道|无（拉取式）|RabbitMQ → 通知中心 → APP 推送通知|
|收件人|任何打开 Tab 的用户|`news_push_centre.push_target` 决定（全部 / 大陆 / 非陆 / 群组）|

两者**数据可能交叉**（运营推一条洞察的同时也会把对应 `news` 记录的 `is_recommend` 置 1，让 Tab 也能看到），但代码路径完全独立。

#### 5\.0\.4 性能与缓存命中预期

|接口|走缓存|兜底|
|---|---|---|
|`/api/news/v1/list`|按 `type + codes + lang` 组合可能有 Redis cache|Mongo `t_news`（主路径）|
|`/api/news/v1/get_recommend`|推荐内容更新频率低，Redis cache 命中较好|Mongo|
|`/api/news/v1/fast_list`|快讯更新太快，缓存命中低|Mongo（主路径）|
|`/api/announcement/v1/list`|偶有按 `selectedCodes` hash 的 cache|MySQL（按 `market` 切分的公告库）|
|`/api/news/v1/content`|✅ Redis 详情 cache，命中率 80%\+|Mongo \+ MySQL `news` / `news_operate_log`|
|`/api/important_news/v1/all_info_list_*`|✅ Redis ZSet `INFO_NEWS`，几乎 100% 命中（仅历史链路）|启动时数量不足才查 Mongo|

### 5\.1 对外 API（Controller × Service × Facade）

> ⭐ 标记的 Controller 承载当前 APP 主资讯页 80%\+ 流量；其余按个股详情页 / 后台运营 / 历史链路使用。

|Controller|路径前缀|Service|Facade|主要接口|
|---|---|---|---|---|
|⭐ NewsInfoController|`/api/news`|`NewsDataService`|`NewsInfoFacade`|**主资讯页主力**：`list`（7 Tab \+ chip 共用列表，卓锐洞察传 type=14）/ `fast_list`（快讯 Tab）；`get_recommend` 仅卓锐洞察 Tab 顶部首推副接口；外加 `content` / `ai_make_up` / `topic_list` / `related_topic_news`|
|⭐ AnnouncementInfoController|`/api/announcement`|`AnnouncementInitDataService`|`AnnouncementInfoFacade`|**主资讯页公告 chip**：`list`（带 `selectedCodes` 拉自选股公告）；外加 `content` / `important_list`|
|ConAnnouncementInfoController|`/api/con/announcement`|`AnnouncementInitDataService`|`ConStockAnnouncementFacade`|后台运营对公告的增删改|
|AllInformationListController（历史）|`/api/important_news`|`AllInformationListService`|`AllInformationListFacade`|早期「要闻」Tab 走 Redis ZSet `INFO_NEWS` 预热缓存；当前 APP 已切到 `/api/news/v1/list`，保留供老端兼容|
|StockInfoDetailController|`/api/info`|`StockInfoDetailService`|`StockInfoDetailFacade`|资讯详情聚合（拼 H5 URL 等）|
|TopicInfoController|`/api/topic`|`TopicDataService`|`TopicFacade`|主题列表 / 主题详情|
|ConTopicInfoController|`/api/con/topic`|`TopicDataService`|`ConTopicFacade`|后台主题管理|
|ConNewsInfoController|`/api/con/news`|`NewsDataService` \+ `NewsInitDataService`|`ConNewsFacade`|后台资讯增删改、上下架、推荐位、审核|
|ConGalleryInfoController|`/api/con/gallery`|`GalleryDataService`|`ConGalleryFacade`|图库管理|
|NewsPushReportController|`/api/news/push_report`|`NewsPushReportService`|（内部）|卓锐洞察推送报告查询|

> 接口前缀 `/api/con/...` 是给后台管理（ConsoleAPI），`/api/...` 是给 AS 透传的 APP 接口；分布在不同 Controller，但都路由到同一份 Service。

#### 5\.1\.1 14 个 Feign Facade 一览（来自 stock\-information\-facade）

```Plaintext
NewsInfoFacade              资讯列表 / 详情 / 快讯 / 主题 / AI / 推荐
AnnouncementInfoFacade      公告查询
StockImportantNewsFacade    要闻、轮播
AllInformationListFacade    要闻聚合下拉/上拉
StockInfoDetailFacade       个股资讯详情
StockInfoSelectFacade       自选股资讯
StockInfoHoldPositionFacade 持仓资讯
StockNewsFlashFacade        快讯流
StockConomicCalendarFacade  经济日历
TopicFacade                 主题（APP 端）
ConTopicFacade              主题（后台）
ConNewsFacade               资讯（后台）
ConGalleryFacade            图库（后台）
ConStockAnnouncementFacade  公告（后台）
```

> 全部 `@FeignClient(value="stock-information")`；这意味着**只要 ****`stock-information`**** 不可用，资讯链路对外即全部不可用**——所以本服务的可用性最关键。

### 5\.2 启动初始化（DefaultInitApplication）

> 注：定时抓取（XXL\-Job）已统一由 `stock-information-data` 承担，本服务不再列出 XXL\-Job 任务清单。本仓库 `xxljobhandler/` / `scheduled/` 包内仍有同名代码，但**生产已不调度**——属于历史包袱，详见 §10。

- `@Order(Integer.MIN_VALUE)`，优先级最高；

- 检查 Redis ZSet `INFO_NEWS` / `INFO_ABNORMAL_NEWS` 大小，少于 `info.initMinSize`（默认 100）就触发缓存重建（从 Mongo 拉最近的要闻 / 异动新闻批量写 ZSet）；

- 启动时调 `pullGalleryOssData()` 把图库未转换条目过一遍 OSS。

> 本服务的启动预热**比 \-data 简洁很多**：没有 Kafka Listener、没有 DJL 向量库、没有股票分词器初始化，启动速度更快。

### 5\.3 消息（RabbitMQ 消费 \+ 生产）

#### Consumer

|类|监听队列|行为|
|---|---|---|
|AnnouncementConsumer|`MQConstant.Information.ANNOUNCEMENT_PUSH_INFORMATION`|收到公告推送事件 → `AnnouncementInitDataService.getByIdsAnnouncementDto` → 按股票分组 → `StockMarketSelectedFacade.getByTsCodeUserIds` 取关注用户 → `MessageCenterFacade.getDisturbFreeUserIds` 过滤资讯免打扰 → 调 `MessageCenterFacade` 发通知|
|NewsImportantConsumer|`MQConstant.Information.PUSH_INFORMATION_NEWS`|收到要闻自动推送事件 → 时段窗口判定（7\-9 / 12\-13 / 16\-21）→ Redis 计数限频 → `NewsPushProducer.sendSingleNewsImportantByCursor` 游标分页推送|

#### Producer

|类|用途|
|---|---|
|AnnouncementPushProducer|公告抓取后投递 `ANNOUNCEMENT_PUSH_INFORMATION` 队列|
|NewsPushProducer|卓锐洞察推送 / 要闻自动推送游标分页发送|
|NewsPushData|推送事件载体（DTO）|

> **本服务不消费 Kafka**（包括 `information_data_snapshot`）；Kafka 路透链路完全在 `-data` 内闭环。

---

## 6\. 代码模块

```Plaintext
stock-information/
├── pom.xml                                  # parent，packaging=pom
├── CLAUDE.md                                # 子项目级 Claude Code 指引
├── stock-information-facade/                # 14 个 Feign 契约 + Hystrix 兜底
│   └── com.zhuorui.stockinformation
│       ├── constant/  dto/  enums/
│       ├── facade/                          # 14 个 @FeignClient 接口
│       ├── fallback/                        # Hystrix FallbackFactory
│       ├── response/  vo/                   # 共享请求/响应体
└── stock-information-server/                # Spring Boot 应用
```

`server` 模块包视图：

```Plaintext
com.zhuorui.stockinformation
├── StockInformationApplication.java         # 启动类
├── boot/DefaultInitApplication.java         # 启动 Redis 缓存预热 + 图库 OSS 转换
├── cache/
│   ├── GalleryKeyWordCache.java             # 图库关键词
│   └── ImageCodeCache.java                  # 个股代码-图片 URL 映射
├── config/
│   ├── annotation/DataSource.java           # @DataSource(DataSourceEnum.XXX)
│   ├── datasource/                          # MultipleDataSource + Aspect + ContextHolder
│   ├── db/MybatisPlusConfig.java            # 11 个 DataSourceConfig + sqlSessionFactory
│   ├── httpconfig/                          # RestTemplate / OkHttp
│   └── machinetranslation/                  # 阿里翻译配置
├── controller/                              # 10 个 Controller
├── dao/                                     # NewsDao + impl
├── jms/                                     # 2 个 Consumer + 3 个 Producer 类
├── mapper/                                  # MyBatis-Plus mapper（按 9 个数据源分目录）
│   ├── news/  announcement/
│   ├── cnblt/ cnstock/  hkiis/ hknews/  usnews/ usreport/  oss/
├── po/                                      # 30 个实体（与 -data 完全相同）
├── scheduled/                               # 10 个 Scheduled 类（旧抓取链路）
├── service/
│   ├── AllInformationListService.java       # 接口
│   ├── InformationDetailService.java
│   ├── StockInfoDetailService.java
│   ├── impl/
│   │   ├── AllInformationListServiceImpl.java
│   │   └── StockInfoDetailServiceImpl.java
│   ├── news/                                # 资讯主链：NewsDataService /
│   │                                          NewsInitDataService /
│   │                                          NewsPushCentreService /
│   │                                          NewsPushReportService /
│   │                                          GalleryDataService / TopicDataService
│   ├── announcement/                        # AnnouncementInitDataService
│   ├── oss/                                 # 5 个 OSS 同步 service（A/HK/US/ImageCode/InformationUrl）
│   ├── cnblt/  cnstock/  hkiis/  hknews/  usnews/  usreport/
│                                            # 行情商落地库的只读 service
├── util/                                    # ConMD5Utils / ContentHandleUtil /
│                                              FtpOssUtils / HtmlNodeUtil / InformationCacheUtil
├── xxljobhandler/                           # 6 个 XXL-Job handler
└── resources/
    ├── bootstrap.yml + bootstrap-{profile}.yml
    ├── log4j2-boot-{profile}.xml
    └── mapper/                              # mapper xml（与 java mapper 同目录布局）
```

**与 stock\-information\-data 的关键差异**（包视图层面）：

|包|stock\-information|stock\-information\-data|说明|
|---|---|---|---|
|`xxljobhandler/`|6 个 handler|8 个 handler（多了 `NewsTempHandler` / `ReloadDeduplicatorHandler`）|\-data 多了路透补全和分词器重载|
|`scheduled/`|10 个|10 个（同名）|高度重复|
|`service/impl/`|2 个文件|8 个（含 `ReutersNewsServiceImpl` / `CoinDeskAjaxNewsImpl` / `FiNetNewsImpl` / `TechubNewsImpl` / `DeduplicatorServiceImpl` / `Main` 等）|\-data 持有所有新接资讯源的实现|
|`service/reuters/`|❌|✅（source / sink / model）|\-data 独有|
|`controller/`|10 个|2 个（`DeduplicatorController` / `ReutersTokenController`）|SI 是对外 API 主战场，\-data 只暴露技术接口|
|`jms/`|RabbitMQ Consumer \+ Producer|同上 \+ Kafka `InformationSnapshotReceive`|\-data 多 Kafka 消费|
|`cache/`|2 个|4 个（多 `StockCodeCache` / `ReutersMetadataCache`）|\-data 因路透处理需要|
|`boot/`|`DefaultInitApplication`|\+ `AppInitState` \+ Kafka Listener 拉起 \+ DJL 向量库 \+ 股票分词|\-data 启动逻辑更重|
|`config/kafka/`|❌|✅（双集群 producer \+ consumer）|\-data 独有|
|`config/reuters/`|❌|✅（Token 管理 \+ 拦截器）|\-data 独有|
|`util/`|5 个|18 个（去重器、智能正文抽取、股票分词、路透 Token Redis 工具等）|\-data 大幅扩展|
|`registry/`|❌|✅（`NewsPullServiceRegistry` / `NewsProcessorServiceRegistry`）|\-data 引入策略注册|

---

## 7\. 实体 ER 图

PO 列表与 ER 图与 stock\-information\-data 架构说明 §7 完全一致——两个服务共用同一份 `po/` 包（仅 package 名不同：`com.zhuorui.stockinformation.po` vs `com.zhuorui.stockinformationdata.po`，字段、`@TableName`、`@Document` 全部相同）。

为便于本文独立阅读，再列一次资讯主库 ER：

```Plaintext
erDiagram
    NEWS ||--o{ NEWS_TYPE          : "1-N 类型"
    NEWS ||--o{ NEWS_SUB_TYPE      : "1-N 子类型"
    NEWS ||--o{ NEWS_TAG           : "1-N 产品标签"
    NEWS ||--o{ NEWS_CODE          : "1-N 关联股票"
    NEWS ||--o{ NEWS_TOPIC         : "1-N 主题关联"
    NEWS ||--o{ NEWS_OPERATE_LOG   : "1-N 操作日志"
    NEWS ||--o| NEWS_PUSH_CENTRE   : "1-1 卓锐洞察推送"
    NEWS_PUSH_CENTRE ||--o{ NEWS_PUSH_REPORT : "1-N 推送报告"
    TOPIC ||--o{ NEWS_TOPIC        : "1-N"
    TOPIC_CATEGORY ||--o{ TOPIC    : "1-N"

    NEWS {
        int     id PK
        string  third_id
        int     source_id
        string  title
        string  title_tw
        string  title_en
        string  content
        string  content_tw
        string  content_en
        string  description
        string  description_tw
        string  description_en
        string  source
        string  pub_time
        string  theme_img
        string  original_url
        string  provider
        int     status
        string  codes
        int     important
        int     is_hot
        int     is_recommend
        int     is_audit
        string  banner_image
        string  key_words
        string  content_en_task_id
        string  content_cn_task_id
        int     translate_count
        datetime create_time
        datetime update_time
    }
    NEWS_TYPE {
        int id PK
        int news_id FK
        int type
    }
    NEWS_SUB_TYPE {
        int id PK
        int news_id FK
        int type
        int sub_type
    }
    NEWS_TAG {
        int id PK
        int news_id FK
        int tag
    }
    NEWS_CODE {
        int    id PK
        int    news_id FK
        string code
        string ts
        int    tag
    }
    NEWS_TOPIC {
        int id PK
        int news_id FK
        int topic_id FK
    }
    NEWS_OPERATE_LOG {
        int    id PK
        int    news_id FK
        int    status
        string remark
    }
    NEWS_PUSH_CENTRE {
        int    news_id PK
        string news_title
        string news_content
        int    push_status
        int    is_push
        int    push_target
        int    filter_dimension
        int    is_show_push
        int    push_way
        date   timer_push_time
        string group_id
        date   create_time
        date   update_time
    }
    NEWS_PUSH_REPORT {
        string id PK
        int    news_id FK
        string news_title
        int    total
        int    push_success_count
        int    push_fail_count
        date   push_time
    }
    TOPIC {
        int    id PK
        string name
        string description
        int    category_id FK
        string head_img
        string background_img
        int    status
        int    is_hot
        int    sort
        int    type
    }
    TOPIC_CATEGORY {
        int    id PK
        string name
    }
```

公告 ER 与 MongoDB `t_news` 文档结构详见 \-data 文档 §7\.1 / §7\.2。

**字段语义说明**（同 \-data 文档）：

|表 / 字段|取值|
|---|---|
|`news_type.type`|`NewsCategoryEnum`：FAST 快讯 / MAJOR\_NEWS 要闻 / HK / US / VA\_NEWS / BULLETIN / CHANGE / MACRO / RATING / NEW\_STOCK / NEWS 等|
|`news_sub_type.sub_type`|`NewsSubCategoryEnum`：HK / US / FUTURES / VA / INDEX / GLOBAL|
|`news_tag.tag`|1=股票，2=指数，3=基金|
|`news_push_centre.push_target`|1=全部用户，2=大陆用户，3=非大陆用户，4=指定群组|
|`news_push_centre.filter_dimension`|1=手机号，2=IP，3=证件|
|`news_push_centre.push_way`|1=立即推送，2=定时推送|
|`topic.type`|0=通用，1=风险早知道，2=机会风向标|

---

## 8\. 关键时序：APP 资讯页的 4 条链路

### 8\.1 通用资讯列表 `/api/news/v1/list` —— 7 个 Tab \+ 多个 chip 共用

> 自选 / **卓锐洞察（type=14）** / 要闻 / 加密货币 / 新股 / 宏观 / 港股 / 美股 / 异动 / chip「新闻」「评级」全部走这一条链路；差别在请求体的 `type` / `selectedCodes` / `market` / `subType` 等字段。

```Plaintext
sequenceDiagram
    autonumber
    participant App as App
    participant GW as zhuorui-gateway
    participant AS as as-stock-information :1217
    participant SI as stock-information :1214
    participant Rd as Redis 列表 cache
    participant Mg as MongoDB t_news

    App->>GW: POST /api/news/v1/list<br/>Header: X-User-Id / Accept-Language<br/>Body: {type, selectedCodes?, market?, subType?, pubTime?, newsId?}
    GW->>AS: 透传 (@NoToken)
    AS->>AS: VisitorContext.isVisitor(userId)<br/>→ vo.notLogin = true/false
    AS->>SI: Feign NewsInfoFacade.getList(lang, vo)
    SI->>SI: NewsInfoController → NewsDataService.pullNewsList
    SI->>SI: excludeNotHkFlagData(vo)<br/>(对 selectedCodes 中非 A 股通的代码做剔除)
    SI->>Rd: 试 Redis cache（按 type + codes + lang 组合）
    alt cache hit
        Rd-->>SI: List<NewsDto>
    else cache miss
        SI->>Mg: NewsDao.pullNewsList(vo)<br/>notLogin=true 时过滤路透社等付费源
        Mg-->>SI: List<NewsPo>
        SI->>Rd: 回写 cache
    end
    SI->>SI: 拼 H5 URL + 多语言裁剪 + 关联股票/主题
    SI-->>AS: ApiResponse<List<NewsDto>>
    AS-->>App: JSON

    Note over App,Mg: 渲染后 APP 用 news.codes (如 US:GOOG)<br/>独立调 stock-market 服务实时刷价格
```

### 8\.2 「卓锐洞察」Tab 顶部首推 `/api/news/v1/get_recommend`

> 只服务于卓锐洞察 Tab 顶部的"首推"模块（banner \+ hot），Tab 下半部分常规列表仍走 §8\.1 的 `/v1/list?type=14`。

```Plaintext
sequenceDiagram
    autonumber
    participant App as App
    participant AS as as-stock-information
    participant SI as stock-information
    participant Mg as MongoDB t_news

    App->>AS: POST /api/news/v1/get_recommend
    AS->>AS: VisitorContext.isVisitor(userId)
    AS->>SI: Feign NewsInfoFacade.getRecommend(lang, notLogin)
    SI->>SI: NewsInfoController.getRecommend
    SI->>SI: NewsDataService.getRecommend<br/>构造 vo: isRecommend=1, type=14(卓锐看市)
    SI->>Mg: NewsDao.pullNewsList(vo)
    Mg-->>SI: List<NewsPo>
    SI->>SI: 按 recommended_bit 拆分<br/>banner(=1) → themeImg 用 bannerImage 覆盖<br/>hot(=2) → 不替换图
    SI->>SI: 对每条 conversionNewsDto(lang) 多语言裁剪
    SI-->>AS: ApiResponse<NewsRecommendDTO {banner, hot}>
    AS-->>App: JSON
```

### 8\.3 「快讯」Tab `/api/news/v1/fast_list`

```Plaintext
sequenceDiagram
    autonumber
    participant App as App
    participant AS as as-stock-information
    participant SI as stock-information
    participant Mg as MongoDB t_news

    App->>AS: POST /api/news/v1/fast_list<br/>Body: {type=FAST(3), subType?, pubTime?, newsId?}
    AS->>SI: Feign NewsInfoFacade.pullFastNewsList(lang, vo)
    SI->>SI: NewsDataService.pullFastNewsList
    SI->>Mg: NewsDao.pullNewsList(vo)
    Mg-->>SI: List<NewsPo>
    SI->>SI: removeHtmlTag(content / contentTw / contentEn)<br/>+ conversionNewsDto(lang)<br/>(快讯不附主题 / 关联股票名)
    SI-->>AS: ApiResponse<List<NewsDto>>
    AS-->>App: JSON
```

### 8\.4 「自选 → 所有公告」chip `/api/announcement/v1/list`

```Plaintext
sequenceDiagram
    autonumber
    participant App as App
    participant AS as as-stock-information
    participant SI as stock-information
    participant My as MySQL 公告库<br/>(hkiis / usreport / cnstock / oss_*)

    App->>AS: POST /api/announcement/v1/list<br/>Body: {selectedCodes / code, market, category?, pubTime?}
    AS->>SI: Feign AnnouncementInfoFacade.announcementList(lang, vo)
    SI->>SI: AnnouncementInfoController 参数校验<br/>(code / selectedCodes 至少一个非空，否则 PARAM_NOT_VALID)
    SI->>SI: AnnouncementInitDataService.listAnnouncement<br/>按 market 选 @DataSource(港/美/A)
    SI->>My: 查公告主表 + 必要时拉 OSS 元数据
    My-->>SI: List<AnnouncementPo>
    SI->>SI: 拼 H5 URL + 多语言字段裁剪
    SI-->>AS: ApiResponse<List<AnnouncementDto>>
    AS-->>App: JSON
```

### 8\.5 列表项进详情 / AI 补全（旁支）

- `POST /api/news/v1/content` — 命中 Redis 详情缓存的概率最高（80%\+），未命中才查 Mongo \+ 回写缓存。

- `POST /api/news/v1/ai_make_up` — 等价于「`/list` 拉关联资讯列表」 \+「批量 `content`」组合，输出 `MakeUpNewsDto`。

> 历史链路（`/api/important_news/v1/all_info_list_*` 命中 Redis ZSet `INFO_NEWS` 预热缓存、`/api/info/selected/v1/get_last` 走 `stockMarketSelectedFacade` 两阶段 Feign）当前 APP 主页**已不再触发**，但接口仍保留，参见 §5\.0\.2。

---

## 9\. 与兄弟服务的关系

|维度|as\-stock\-information|**stock\-information**|stock\-information\-data|
|---|---|---|---|
|端口|1217|**1214**|1959|
|主要角色|对外 API 网关|**对内业务服务（被 Feign 调）**|后台拉取 / 批处理（XXL\-Job）|
|数据库|无|**11 个数据源**|11 个数据源（同库）|
|Mongo / Redis|无|**读写**|读写|
|Kafka|无|无|Kafka 双集群 producer \+ consumer|
|RabbitMQ|无|**Consumer \+ Producer**|Producer|
|抓取定时任务|无|6 个 handler（与 \-data 重复）|8 个 handler（路透 / CoinDesk / FiNet / Techub 主战场）|
|是否对外暴露 HTTP|是（经网关）|**否（内部 Feign）**|否（仅内部 Feign）|
|启动预热|无|Redis 缓存数量检查 \+ 图库 OSS|Kafka Listener \+ DJL 向量库 \+ 股票分词 \+ 路透 metadata|

---

## 10\. 关于"与 \-data 重复代码"

`stock-information-data` 是 2024 年从 `stock-information` 拷贝出来的新服务，初始版本与 SI 一致；之后所有新接的资讯源（路透社 / CoinDesk / FiNet / Techub）和大模型相关能力（DJL 向量去重、敏感词扫描、阿里翻译异步化）都只在 \-data 中开发。

**当前生产形态**（经验法则，请以运维端 XXL\-Job 调度配置为准）：

|链路|实际跑在哪|
|---|---|
|路透 / CoinDesk / FiNet / Techub|**\-data** 唯一|
|智通 / 格隆汇 / 凤凰网 / BlockBeats / 美股 / 公告 A/HK/US|**理论双跑**，但建议运维端的 XXL\-Job 执行器分组只指向其中一个，避免同一作业被两个服务并发执行（`RedisDistributedLock` 能兜住，但 cron 重叠会浪费资源）。|
|卓锐洞察定时推送 / 资讯翻译重试 / 资讯缓存预热|同上，建议**只在一侧**调度|
|对外 Feign 接口（被 AS 调）|**stock\-information** 唯一|
|Kafka 路透链路|**\-data** 唯一|
|RabbitMQ 公告 / 要闻推送消费|**stock\-information** 唯一（\-data 只生产，不消费这两个队列）|

**如何收敛重复代码**（后续重构方向，仅供参考）：

1. **保 SI 业务侧、迁 \-data 调度侧**：把 SI 中的 `xxljobhandler/` `scheduled/` `service/impl/CoinDesk*` 等清掉，让 SI 只承担对外 Feign \+ JMS 消费。

2. **保 \-data 调度侧、共享 service**：把 SI 与 \-data 共享的 `news/announcement` Service 抽到一个 jar，让两个 server 都依赖它（重构成本较大）。

3. **现状**：暂保留两份；新增功能放 \-data，老 bug 修复哪边出问题改哪边，PR 里建议同步改两边。

---

## 11\. 维护提示

- **加新对外接口**：先在 `stock-information-facade` 新建/扩 `*Facade` Feign 方法 → 在 SI 加 `@RestController` 实现 → AS 添加薄 controller 转发。

- **加新数据源（DB）**：`MybatisPlusConfig` 加 `DataSourceConfig` Bean、`MultipleDataSource.targetDataSources` 加映射、`DataSourceEnum` 加枚举、mapper 放到 `mapper/<新目录>/`，service 用 `@DataSource(DataSourceEnum.XX)`。

- **改 Mongo ****`t_news`**** 字段**：先在 `NewsPo` 加 `@Field`；同步在 `-data` 的 `NewsPo` 加同样字段（两边 PO 必须保持一致），并确认 AS 的 DTO 是否要透传该字段。

- **改 RabbitMQ Consumer 行为**：消费者位于 `jms/`，注意配合改下游 `MessageCenterFacade` 调用即可，不需要改 \-data。

- **本地启动**：`mvn spring-boot:run -pl stock-information/stock-information-server -Dspring-boot.run.profiles=local`，需要可达的 Apollo \+ Eureka \+ 11 库 \+ Redis \+ Mongo \+ RabbitMQ。

- **故障排查**：

    - 资讯列表为空 → 先看 Mongo `t_news` 是否有数据、再看 Redis 缓存是否过期（`InformationCacheHandler.NEWS_CACHE_UPDATE` 是否在跑）；

    - 公告推送丢失 → 看 RabbitMQ `ANNOUNCEMENT_PUSH_INFORMATION` 队列堆积、`AnnouncementConsumer` 日志、`messageCenterFacade.getDisturbFreeUserIds` 返回是否过滤过头（参考 `spec/02-fix-disturb-free-filter-missing-users.md`）；

    - 通知超时 → `spec/01-fix-notification-timeout.md` 已修。

---

*生成日期：2026\-05\-09 · 修订：2026\-05\-11（按 APP 原型图收敛主资讯页为 4 接口）*

