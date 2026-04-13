# 飞书文档知识库机器人

飞书群聊机器人，群成员 @机器人 即可搜索文档、查看最新研报。

采用长连接 (WebSocket) 模式，**无需公网 IP / 域名 / SSL 证书**。

## 功能

| 指令 | 说明 |
|---|---|
| `@机器人 关键词` | 搜索文档库 |
| `@机器人 最新` | 最近更新的文档 |
| `@机器人 最新研报` | 最近的研究报告 |
| `@机器人 概览` | 文档库统计 |
| `@机器人 帮助` | 功能菜单 |

## 在 Mac 上部署

```bash
# 1. 克隆并进入项目
git clone <your-repo-url>
cd claude
git checkout claude/feishu-bot-documents-HtF96

# 2. 创建 .env
cp .env.example .env
# 编辑 .env 填入 App ID 和 Secret

# 3. 安装依赖
pip3 install -r requirements.txt

# 4. 启动
python3 main.py
```

## 飞书开放平台配置

1. 开启 **机器人** 能力
2. 事件订阅 → **长连接** → 添加 `im.message.receive_v1`
3. 权限：`im:message` / `im:message:send_as_bot` / `wiki:wiki:readonly` / `docx:document:readonly`
4. 发布应用版本

## Docker 部署

```bash
cp .env.example .env  # 编辑填入凭证
docker-compose up -d
```
