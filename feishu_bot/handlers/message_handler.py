"""
Message handler: route user queries and generate replies.
Uses Doubao LLM for natural language understanding when available.
"""

import json
from feishu_bot.core.api_client import api_client
from feishu_bot.services.search_engine import search_engine
from feishu_bot.services.llm_client import ask_doubao
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger

HELP_KW = {"帮助", "help", "指令", "功能", "菜单", "怎么用"}
SUMMARY_KW = {"概览", "统计", "summary", "文档库"}
LATEST_KW = {"最新", "最近", "latest", "recent"}


class MessageHandler:

    def handle(self, msg: dict):
        chat_type = msg.get("chat_type", "")
        is_mentioned = msg.get("is_mentioned", False)

        # In group chat, only respond to @mentions
        if chat_type == "group" and not is_mentioned:
            return

        text = msg.get("text", "").strip()
        mid = msg.get("message_id", "")

        if not text:
            self._reply_help(mid)
            return

        logger.info("Query: '%s' from chat=%s", text, msg.get("chat_id"))
        tl = text.lower()

        # Simple keyword commands (no LLM needed)
        if any(k in tl for k in HELP_KW):
            self._reply_help(mid)
        elif any(k in tl for k in SUMMARY_KW):
            self._reply_summary(mid)
        elif any(k in tl for k in LATEST_KW):
            self._reply_latest(mid)
        else:
            # For all other queries: search + LLM
            self._reply_smart(mid, text)

    def _reply_smart(self, mid: str, query: str):
        """Search documents, then use LLM to generate intelligent response."""
        query = query[:200]
        results = search_engine.search(query, top_k=10)

        # Try LLM response
        if Config.DOUBAO_API_KEY and Config.DOUBAO_ENDPOINT_ID:
            llm_answer = ask_doubao(query, results)
            if llm_answer:
                self._send(mid, llm_answer)
                return

        # Fallback: plain search results (no LLM)
        if not results:
            self._send(mid, (
                f"未找到与「**{query}**」相关的文档。\n\n"
                "建议：尝试不同的关键词，或输入 `帮助` 查看功能。"
            ))
            return

        lines = [f"搜索「**{query}**」找到 {len(results)} 条结果：\n"]
        for i, r in enumerate(results, 1):
            title = r["title"] or "无标题"
            url = r.get("url", "")
            line = f"**{i}. [{title}]({url})**" if url else f"**{i}. {title}**"
            lines.append(line)
        self._send(mid, "\n\n".join(lines))

    def _reply_help(self, mid: str):
        has_ai = bool(Config.DOUBAO_API_KEY and Config.DOUBAO_ENDPOINT_ID)
        if has_ai:
            self._send(mid, (
                "**你好！我是AI研报助手**\n\n"
                "你可以直接 @我 用自然语言提问，例如：\n\n"
                "- `帮我找1月份Goldman Sachs的宏观研报`\n"
                "- `最近有什么新能源相关的报告`\n"
                "- `搜索 人工智能`\n"
                "- `最新` — 查看最近文档\n"
                "- `概览` — 文档库统计\n\n"
                "我能理解你的问题，智能搜索文档库！"
            ))
        else:
            self._send(mid, (
                "**你好！我是文档助手机器人**\n\n"
                "你可以 @我 + 关键词来搜索文档：\n\n"
                "- `@机器人 关键词` — 搜索文档\n"
                "- `@机器人 最新` — 最新文档\n"
                "- `@机器人 概览` — 文档库统计\n"
                "- `@机器人 帮助` — 查看帮助"
            ))

    def _reply_latest(self, mid: str):
        results = search_engine.get_latest_docs(count=5)
        if not results:
            self._send(mid, "暂无文档记录。文档库可能还在同步中，请稍后再试。")
            return

        lines = ["**最新文档（Top 5）：**\n"]
        for i, r in enumerate(results, 1):
            title = r["title"] or "无标题"
            url = r.get("url", "")
            line = f"**{i}. [{title}]({url})**" if url else f"**{i}. {title}**"
            lines.append(line)
        self._send(mid, "\n\n".join(lines))

    def _reply_summary(self, mid: str):
        s = search_engine.get_summary()
        type_labels = {
            "doc": "文档", "docx": "新版文档", "sheet": "表格",
            "bitable": "多维表格", "mindnote": "思维导图",
            "slides": "幻灯片", "pdf": "PDF",
        }
        lines = [
            "**文档库概览**\n",
            f"总文档数：**{s['total_docs']}**",
            f"知识空间：{', '.join(s['spaces'][:10]) if s['spaces'] else '暂无'}",
            "\n**文档类型分布：**",
        ]
        for t, c in sorted(s["type_counts"].items(), key=lambda x: -x[1]):
            lines.append(f"- {type_labels.get(t, t)}: **{c}** 篇")
        self._send(mid, "\n".join(lines))

    def _send(self, message_id: str, text: str):
        """Reply with an interactive card (fallback to plain text)."""
        card = json.dumps({
            "config": {"wide_screen_mode": True},
            "elements": [{"tag": "markdown", "content": text}],
        }, ensure_ascii=False)

        result = api_client.reply_message(message_id, "interactive", card)
        if result.get("code") != 0:
            logger.warning("Card reply failed, falling back to text: %s",
                           result.get("msg"))
            plain = json.dumps({"text": text}, ensure_ascii=False)
            api_client.reply_message(message_id, "text", plain)


message_handler = MessageHandler()
