# 仓库指引

本仓库包含两部分内容：

## 1. 飞书文档知识库机器人（`feishu_bot/`）

飞书群聊机器人，长连接模式，支持文档搜索/最新研报等指令。部署方式见 `README.md`。

## 2. AI 产品经理知识归档（`knowledge/ai-pm/`）

用户为入职产品经理岗位归档的「Mark 的 AI 产品经理知识库」（飞书）。
当用户提到「知识归档」「AI 产品经理知识库」「入职学习资料」时，从这里读取：

- `knowledge/ai-pm/README.md` — 归档说明与状态（部分内容待补全，原因见该文件）
- `knowledge/ai-pm/01-links-index.md` — 原始链接、子链接、镜像全索引
- `knowledge/ai-pm/02-overview-and-path.md` — 知识库总览 + 转岗学习路径
- `knowledge/ai-pm/03-llm-tech-map.md` — 大模型技术主题图谱
- `knowledge/ai-pm/04-interview-prep.md` — 面试/技术对话准备
- `knowledge/ai-pm/raw/` — 爬虫抓取的原文（待生成）

补全原文：在能访问 `*.feishu.cn` 的环境中运行 `python3 tools/crawl_feishu_kb.py`
（需 `pip install playwright`），然后把 `raw/` 中的内容整理回上述归档文件。
