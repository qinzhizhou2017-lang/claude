# AI 产品经理知识归档（Mark 的 AI 产品经理知识库）

> 为入职产品经理岗位准备的知识归档。后续任何 Claude 会话中，直接说
> 「读取 knowledge/ai-pm 下的归档」即可调用本目录全部内容。

## 归档对象

| 来源 | 链接 | 状态 |
|---|---|---|
| 飞书社区文章《Mark的AI产品经理知识库「持续更新」》 | https://www.feishu.cn/community/article?id=7444818740039909395 | ⚠️ 框架已归档，全文待抓取 |
| Mark 的飞书 Wiki 知识库（主入口） | https://qqs7y1hozd1.feishu.cn/wiki/DzlJw541diset0kFeYJcTlH3nRh | ⚠️ 框架已归档，全文待抓取 |

## 归档状态说明（重要）

本次归档在 Claude Code 云端环境中进行。该环境的**网络策略为白名单模式**，
仅放行 GitHub / npm / PyPI 等开发域名，所有到 `*.feishu.cn` 的请求
（网页、API、代理阅读服务）均被网关以 403 拦截，因此**无法直接抓取原文**。

已完成的部分（通过搜索引擎公开快照与镜像转载还原）：

- 知识库的定位、作者、整体结构
- AI 产品经理转岗学习路径（3 天 / 1 周 / 30 天 / 面试自测）
- 大模型技术主题图谱（知识库覆盖的全部技术主题清单）
- 面试四大技术模块及考点速览
- 已发现的全部子链接与镜像转载索引

## 目录

| 文件 | 内容 |
|---|---|
| `01-links-index.md` | 主链接、已发现子链接、镜像转载全索引 |
| `02-overview-and-path.md` | 知识库总览 + 转岗学习路径（30 天实战计划） |
| `03-llm-tech-map.md` | 大模型技术主题图谱（PM 视角速览） |
| `04-interview-prep.md` | AI 产品经理面试准备（四大模块考点） |
| `raw/` | 爬虫抓取的原文存放处（待网络放开后生成） |
| `../../tools/crawl_feishu_kb.py` | 一键补全爬虫脚本（见下） |

## 如何补全原文（两条路径，任选其一）

### 路径 A：放开网络后自动抓取（推荐）

1. 打开 https://claude.ai/code → 环境（Environment）设置 → 网络访问策略，
   改为「允许所有域名」，或将以下域名加入白名单：
   `*.feishu.cn`、`*.feishucdn.com`、`*.larksuitecdn.com`
2. 新开一个会话，对 Claude 说：
   「运行 tools/crawl_feishu_kb.py，把抓到的内容整理进 knowledge/ai-pm/raw 并更新归档」
3. 脚本会用环境内置的 Chromium 渲染页面、遍历 Wiki 侧边栏全部子页面、
   抽取正文存为 Markdown。

### 路径 B：手动导出上传

在飞书客户端中打开 Wiki，右上角「···」→ 导出为 Word/PDF（或全选复制正文），
把文件传给 Claude 并说「按 knowledge/ai-pm 的结构归档这份内容」。

## 入职速用索引

- 下周入职前速览：先读 `02-overview-and-path.md` 的「3 天行业生态」部分
- 补技术底子：按 `03-llm-tech-map.md` 的主题顺序，每天 2-3 个主题
- 面试/答辩/汇报被问到技术：查 `04-interview-prep.md`
- 找原文出处：查 `01-links-index.md`
