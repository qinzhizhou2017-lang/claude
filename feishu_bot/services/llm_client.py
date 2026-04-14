"""
Doubao (豆包) LLM client for natural language understanding.
Uses Volcano Engine ARK API (OpenAI-compatible).
"""

import time
import requests
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger

_NO_PROXY = {"http": None, "https": None}

SYSTEM_PROMPT = """你是一个专业的研报文档助手，帮助用户在文档库中查找研究报告。

## 文档库结构
- 文档库包含约4000份PDF研究报告，按日期文件夹组织
- 文件夹命名：2025年格式为"月.日"（如 8.15 = 8月15日），2026年格式为"年.月.日"（如 26.4.10 = 4月10日）
- 研报文件名通常为英文，包含机构名、主题等

## 常见机构中英对照
高盛=Goldman Sachs, 大摩/摩根士丹利=Morgan Stanley, 小摩/摩根大通=JPMorgan,
美银=BofA/Merrill, 花旗=Citi, 瑞银=UBS, 巴克莱=Barclays, 野村=Nomura, 汇丰=HSBC

## 回复规则
1. 从搜索结果中**严格筛选**与用户问题最相关的文档
2. 如果用户指定了机构（如"高盛"），只列出该机构的研报，不要列出其他机构的
3. 如果用户指定了时间范围，只列出该时间段内的文档
4. 每条结果格式：序号 + 标题 + 文件夹路径 + 链接（如有）
5. 最多列出10条最相关的结果
6. 如果搜索结果与用户需求不匹配，诚实告知并建议调整关键词
7. 回复使用中文，简洁清晰，适合聊天窗口阅读
8. **不要编造不存在的文档**，只基于提供的搜索结果回答
9. 如果用户问非文档搜索的问题（闲聊），友好回复即可"""


def ask_doubao(user_query: str, search_results: list[dict]) -> str:
    """Send query + search context to Doubao, return response text.

    Retries once on transient failure.
    """
    if not Config.DOUBAO_API_KEY or not Config.DOUBAO_ENDPOINT_ID:
        return ""

    # Build context from search results
    if search_results:
        context_lines = [
            f"以下是从文档库中搜索到的 {len(search_results)} 条相关文档：\n"
        ]
        for i, doc in enumerate(search_results, 1):
            title = doc.get("title", "无标题")
            url = doc.get("url", "")
            line = f"{i}. {title}"
            if url:
                line += f"\n   链接: {url}"
            context_lines.append(line)
        context = "\n".join(context_lines)
    else:
        context = "文档库中未找到相关文档。"

    user_message = f"用户提问：{user_query}\n\n{context}"

    for attempt in range(2):
        try:
            resp = requests.post(
                Config.DOUBAO_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {Config.DOUBAO_API_KEY}",
                },
                json={
                    "model": Config.DOUBAO_ENDPOINT_ID,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3,
                },
                timeout=30,
                proxies=_NO_PROXY,
            )
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                answer = data["choices"][0]["message"]["content"]
                logger.info("Doubao response received (%d chars)", len(answer))
                return answer
            else:
                logger.warning("Doubao unexpected response: %s", data)
                if attempt == 0:
                    time.sleep(1)
                    continue
                return ""
        except Exception as e:
            logger.error("Doubao API error (attempt %d): %s", attempt + 1, e)
            if attempt == 0:
                time.sleep(1)
                continue
            return ""
    return ""
