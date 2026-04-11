# Hermes Agent 搭建指南

[Hermes Agent](https://github.com/NousResearch/hermes-agent) 是 Nous Research 开发的自我进化 AI Agent，具备自主技能学习、持久化记忆、多平台消息接入等能力。

## 核心特性

- **自主学习** — 从复杂任务中自动生成和优化技能
- **持久记忆** — 跨会话记忆管理，全文搜索历史
- **多平台接入** — Telegram / Discord / Slack / WhatsApp / Signal / Email
- **灵活部署** — 支持本地、Docker、SSH、Daytona、Modal 等 6 种终端后端
- **40+ 内置工具** — MCP 服务器集成、子代理并行、Cron 定时任务
- **低成本运行** — 支持 serverless 模式，空闲时接近零成本

## 快速安装

### 方式一：一键安装（推荐）

```bash
# 使用官方安装脚本
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 或使用本仓库的安装脚本（带更多自定义选项）
bash hermes-agent/scripts/install.sh
```

安装完成后：
```bash
source ~/.bashrc  # 或 ~/.zshrc
hermes setup      # 运行交互式设置向导
hermes            # 开始对话
```

### 方式二：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 2. 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 创建虚拟环境
uv venv venv --python 3.11
source venv/bin/activate

# 4. 安装依赖
uv pip install -e ".[all]"

# 5. 运行
hermes setup
```

### 方式三：Docker 部署

```bash
cd hermes-agent

# 配置环境变量
cp config/env.example .env
# 编辑 .env，填入你的 API Key

# 启动
docker-compose -f docker-compose.yaml up -d

# 查看日志
docker-compose -f docker-compose.yaml logs -f
```

### 方式四：开发者模式

适合想要修改或贡献代码的开发者：

```bash
bash hermes-agent/scripts/dev-setup.sh [目标目录]

# 默认会安装到当前目录下的 hermes-agent-dev/
```

## 配置

### LLM 模型配置

Hermes Agent 支持多种 LLM 提供商：

| 提供商 | 环境变量 | 说明 |
|--------|----------|------|
| Nous Portal | `NOUS_API_KEY` | Nous 官方，推荐 |
| OpenRouter | `OPENROUTER_API_KEY` | 200+ 模型可选 |
| OpenAI | `OPENAI_API_KEY` | GPT 系列 |
| z.ai / GLM | — | 智谱 AI |
| Kimi / Moonshot | — | 月之暗面 |
| MiniMax | — | MiniMax |
| 自定义端点 | — | 任何 OpenAI 兼容 API |

使用命令切换模型：
```bash
hermes model              # 交互式选择
hermes model openrouter   # 指定提供商
```

### 配置文件

主配置文件位于 `~/.hermes/config/settings.yaml`，参考模板：

```bash
cp hermes-agent/config/settings.example.yaml ~/.hermes/config/settings.yaml
```

详细配置项说明见 [config/settings.example.yaml](config/settings.example.yaml)。

### 消息网关配置

连接消息平台需要对应的 Bot Token：

```bash
hermes gateway            # 交互式配置消息网关
```

**Telegram 示例：**
1. 在 @BotFather 创建 Bot，获取 Token
2. 设置环境变量 `TELEGRAM_BOT_TOKEN=your-token`
3. 运行 `hermes gateway`

## 常用命令

| 命令 | 说明 |
|------|------|
| `hermes` | 启动交互式对话 |
| `hermes setup` | 运行完整设置向导 |
| `hermes model` | 选择 LLM 模型 |
| `hermes tools` | 管理工具集 |
| `hermes config set` | 修改配置 |
| `hermes gateway` | 配置消息网关 |
| `hermes doctor` | 系统健康检查 |
| `hermes update` | 更新到最新版本 |

### 对话中的斜杠命令

| 命令 | 说明 |
|------|------|
| `/new` `/reset` | 开始新对话 |
| `/model [name]` | 切换模型 |
| `/personality [name]` | 切换人设 |
| `/retry` `/undo` | 重试/撤销 |
| `/compress` | 压缩上下文 |
| `/skills` | 浏览已学技能 |
| `/insights` | 使用分析 |
| `Ctrl+C` / `/stop` | 停止当前任务 |

## 系统要求

- **操作系统**: Linux / macOS / WSL2 / Android (Termux)
- **Python**: 3.11+
- **包管理器**: uv（安装脚本会自动安装）
- **网络**: 需要访问 LLM API（根据选择的提供商）

## 目录结构

```
hermes-agent/
├── scripts/
│   ├── install.sh              # 自动化安装脚本
│   └── dev-setup.sh            # 开发者设置脚本
├── config/
│   ├── settings.example.yaml   # 配置模板
│   └── env.example             # 环境变量模板
├── docker-compose.yaml         # Docker 部署配置
└── README.md                   # 本文档
```

安装后的用户目录：
```
~/.hermes/
├── repo/           # Hermes Agent 源码
├── venv/           # Python 虚拟环境
├── config/         # 配置文件
│   └── settings.yaml
├── skills/         # 学习到的技能
├── memory/         # 持久化记忆
└── logs/           # 运行日志
```

## 从 OpenClaw 迁移

如果之前使用过 OpenClaw，可以一键迁移：

```bash
hermes claw migrate              # 交互式迁移
hermes claw migrate --dry-run    # 预览变更
hermes claw migrate --preset user-data  # 仅迁移用户数据
```

## 相关链接

- [Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
- [官方文档](https://hermes-agent.nousresearch.com/docs)
- [技能市场](https://agentskills.io)
- [Nous Research Discord](https://discord.gg/NousResearch)

## 许可证

Hermes Agent 使用 MIT 许可证。
