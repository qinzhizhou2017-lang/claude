"""
Doubao (豆包) LLM client for natural language understanding.
Uses Volcano Engine ARK API (OpenAI-compatible).
"""

import requests
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger

_NO_PROXY = {"http": None, "https": None}

SYSTEM_PROMPT = """你是一个专业的研报文档助手。用户会向你提问关于研究报告的问题。

你会收到一组从文档库中搜索到的相关文档列表。请根据这些文档和用户的问题，给出有用的回答。

规则：
1. 如果搜索结果能回答用户的问题，用简洁清晰的方式列出相关文档，并说明为什么这些文档与问题相关。
2. 如果搜索结果不太匹配，诚实告知，并建议用户尝试其他关键词。
3. 回复使用中文，格式简洁，适合在聊天窗口阅读。
4. 不要编造不存在的文档。只基于提供给你的搜索结果回答。
5. 如果用户问的是非文档搜索的问题（比如闲聊），友好回复即可。"""


def ask_doubao(user_query: str, search_results: list[dict]) -> str:
    """Send query + search context to Doubao, return response text."""
    if not Config.DOUBAO_API_KEY or not Config.DOUBAO_ENDPOINT_ID:
        return ""

    # Build context from search results
    if search_results:
        context_lines = ["以下是从文档库中搜索到的相关文档：\n"]
        for i, doc in enumerate(search_results, 1):
            title = doc.get("title", "无标题")
            url = doc.get("url", "")
            space = doc.get("space_name", "")
            line = f"{i}. 《{title}》"
            if space:
                line += f" - 文件夹: {space}"
            if url:
                line += f" - 链接: {url}"
            context_lines.append(line)
        context = "\n".join(context_lines)
    else:
        context = "文档库中未找到相关文档。"

    user_message = f"用户提问：{user_query}\n\n{context}"

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
                "max_tokens": 1000,
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
            return ""
    except Exception as e:
        logger.error("Doubao API error: %s", e)
        return ""
