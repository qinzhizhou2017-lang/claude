# 飞书文档知识库机器人

一个飞书群聊机器人，连接你的飞书知识库/文档库，群成员通过 @机器人 即可搜索文档、查看最新研报、获取文档摘要。

**采用长连接 (WebSocket) 模式，无需公网 IP / 域名 / SSL 证书，Mac Mini 挂机即可运行。**

## 功能

- **关键词搜索** — `@机器人 搜索 XX` 或直接 `@机器人 XX`
- **最新文档** — `@机器人 最新`，查看最近更新的文档
- **最新研报** — `@机器人 最新研报`，专门查看研究报告
- **文档库概览** — `@机器人 概览`，总数、空间、类型分布统计
- **帮助** — `@机器人 帮助`，显示功能菜单
- **自动同步** — 定时从飞书知识库抓取文档，保持索引最新

## 架构

```
feishu_bot/
├── config.py              # 配置管理
├── app.py                 # 长连接客户端 (lark-oapi SDK)
├── core/
│   ├── auth.py            # Token 管理 (自动刷新)
│   └── api_client.py      # 飞书 API 封装
├── handlers/
│   └── message_handler.py # 消息处理 & 回复逻辑
├── services/
│   ├── doc_indexer.py     # 文档索引 & 定时同步
│   └── search_engine.py   # 中文分词搜索引擎
└── utils/
    └── logger.py          # 日志
```

## 快速开始

### 1. 飞书开放平台配置

1. 登录 [飞书开放平台](https://open.feishu.cn/app)，进入你的应用
2. **机器人** → 开启机器人能力
3. **事件订阅**：
   - 订阅方式选择 **「使用长连接接收事件」**
   - 添加事件：`im.message.receive_v1`（接收消息）
4. **权限管理** → 开通以下权限：
   - `im:message` — 获取与发送消息
   - `im:message:send_as_bot` — 以应用身份发消息
   - `wiki:wiki:readonly` — 获取知识库信息
   - `docx:document:readonly` — 查看文档内容
   - `drive:drive:readonly` — 查看云文档
5. 发布应用版本

### 2. 在 Mac Mini 上部署

#### 方式一：Docker（推荐）

```bash
git clone <your-repo-url>
cd claude

# 编辑 .env 填入你的 App ID 和 Secret
cp .env.example .env
vi .env

# 启动（后台运行，开机自启）
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

在飞书群设置中添加你的机器人应用，群成员即可 @机器人 开始搜索文档。

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---|---|---|
| `FEISHU_APP_ID` | 飞书应用 App ID | — |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret | — |
| `DOC_SYNC_INTERVAL` | 文档同步间隔（秒） | `3600` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 长连接模式优势

- 无需公网 IP / 域名 / SSL 证书
- SDK 内置自动断线重连
- 家里网络 IP 变化不影响运行
- 适合 Mac Mini 7x24 小时挂机

## 使用流程

```
群成员 @机器人 关键词
       ↓
SDK 长连接收到事件 (WebSocket)
       ↓
解析消息 → 提取查询
       ↓
本地文档索引搜索 (jieba 中文分词)
       ↓
构建卡片消息 → 回复群聊
```
