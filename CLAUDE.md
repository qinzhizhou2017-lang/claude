# 仓库指引

本仓库只保留 `main` 一个分支，所有产出都按目录归档在这里。

## 目录结构

| 目录 | 内容 |
|---|---|
| `.claude/skills/stocki-financial-reader/` | 港股 / 美股 / A股行情、财务、估值、一致预期数据 Skill（v0.4.0） |
| `.claude/skills/yanbao-visual-digest/` | 研报可视化 Skill：机构研报 → 3–4 页 A4 可视化精华 PDF |
| `research_visual_digest/` | 研报可视化成品，按 `日期_主题/` 归档 |
| `reports/` | 一次性分析报告（行情日报、个股、基金、Skill 测试），按 `日期_主题/` 归档 |
| `docs/` | 业务文档：资讯与行情技术文档、活水计划、卓锐产品分析（OST） |
| `knowledge/ai-pm/` | AI 产品经理知识库归档（框架、学习路径、面试考点） |
| `feishu_bot/`、`main.py` | 飞书文档知识库机器人，部署方式见 `README.md` |
| `tools/` | 辅助脚本（飞书知识库爬虫） |

## 归档约定

- 新的研报可视化成品放进 `research_visual_digest/<YYYY-MM-DD>_<主题>/`。
- 新的一次性分析报告放进 `reports/<YYYY-MM-DD>_<主题>/`。
- 不要为了单个报告长期保留分支；产出归档进 main 后即可删除会话分支。

## AI 产品经理知识库

当用户提到「知识归档」「AI 产品经理知识库」「入职学习资料」时，从 `knowledge/ai-pm/` 读取：

- `README.md` — 归档说明与状态（部分内容待补全，原因见该文件）
- `01-links-index.md` — 原始链接、子链接、镜像全索引
- `02-overview-and-path.md` — 知识库总览 + 转岗学习路径
- `03-llm-tech-map.md` — 大模型技术主题图谱
- `04-interview-prep.md` — 面试 / 技术对话准备

补全原文：在能访问 `*.feishu.cn` 的环境中运行 `python3 tools/crawl_feishu_kb.py`
（需 `pip install playwright`），然后把 `knowledge/ai-pm/raw/` 中的内容整理回上述归档文件。
