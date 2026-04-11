# 飞书文档知识库机器人

一个飞书群聊机器人，连接你的飞书知识库/文档库，群成员通过 @机器人 即可搜索文档、查看最新研报、获取文档摘要。

## 功能

- **关键词搜索** — `@机器人 搜索 XX` 或直接 `@机器人 XX`，在文档库中搜索相关内容
- **最新文档** — `@机器人 最新`，查看最近更新的文档
- **最新研报** — `@机器人 最新研报`，专门查看最近的研究报告
- **文档库概览** — `@机器人 概览`，查看文档总数、空间、类型分布
- **帮助** — `@机器人 帮助`，显示功能菜单
- **自动同步** — 定时从飞书知识库抓取文档，保持索引最新

## 架构

```
feishu_bot/
├── config.py              # 配置管理
├── app.py                 # Flask 应用 & webhook 路由
├── core/
│   ├── auth.py            # Token 管理 (自动刷新)
│   └── api_client.py      # 飞书 API 封装
├── handlers/
│   ├── event_handler.py   # 事件解析 & 分发
│   └── message_handler.py # 消息处理 & 回复逻辑
├── services/
│   ├── doc_indexer.py      # 文档索引 & 定时同步
│   └── search_engine.py   # 中文分词搜索引擎
└── utils/
    ├── logger.py           # 日志
    └── crypto.py           # 飞书事件解密
```

## 快速开始

### 1. 飞书开放平台配置

1. 登录 [飞书开放平台](https://open.feishu.cn/app)
2. 进入你的应用 → **事件订阅**
   - 请求地址: `https://your-domain.com/webhook/event`
   - 订阅事件: `im.message.receive_v1`（接收消息）
3. **权限管理** → 开通以下权限:
   - `im:message` / `im:message:send_as_bot` — 发送消息
   - `wiki:wiki:readonly` — 读取知识库
   - `docx:document:readonly` — 读取文档内容
   - `drive:drive:readonly` — 读取云文档
4. **机器人** → 开启机器人能力
5. 发布应用版本

### 2. 部署

#### 方式一：Docker (推荐)

```bash
# 编辑 .env 填入你的配置
cp .env.example .env
vi .env

# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 方式二：直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 编辑 .env
cp .env.example .env
vi .env

# 启动
python main.py
```

### 3. 一次性同步文档

```bash
python main.py --sync
```

### 4. 添加机器人到群聊

在飞书群中添加你的机器人应用，群成员即可 @机器人 使用文档搜索功能。

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---|---|---|
| `FEISHU_APP_ID` | 飞书应用 App ID | — |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret | — |
| `FEISHU_VERIFICATION_TOKEN` | 事件订阅验证 Token | — |
| `FEISHU_ENCRYPT_KEY` | 事件订阅加密 Key（可选） | — |
| `SERVER_PORT` | 服务端口 | `8080` |
| `DOC_SYNC_INTERVAL` | 文档同步间隔（秒） | `3600` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 使用流程

```
群成员 @机器人 关键词
       ↓
  Webhook 接收事件
       ↓
  解析消息 → 提取查询
       ↓
  本地文档索引搜索 (jieba 中文分词)
       ↓
  构建卡片消息 → 回复群聊
```
