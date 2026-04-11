"""
Bot message handler: processes user queries and generates responses.
Supports: keyword search, latest docs, summary, and help commands.
"""

import json
import re
from feishu_bot.core.api_client import api_client
from feishu_bot.services.search_engine import search_engine
from feishu_bot.services.doc_indexer import doc_index
from feishu_bot.utils.logger import logger

# Command patterns
HELP_PATTERNS = {"帮助", "help", "指令", "功能", "菜单", "怎么用"}
SEARCH_PATTERNS = {"搜索", "查找", "查询", "找", "搜", "search"}
LATEST_PATTERNS = {"最新", "最近", "今日", "今天", "latest", "recent", "新增"}
SUMMARY_PATTERNS = {"总结", "概览", "统计", "summary", "文档库"}
REPORT_PATTERNS = {"研报", "报告", "研究", "report", "analysis"}


class MessageHandler:

    def handle(self, msg_event: dict):
        """
        Route a message event to the appropriate handler and send a reply.
        In group chats, only respond when the bot is @mentioned.
        """
        chat_type = msg_event.get("chat_type", "")
        is_mentioned = msg_event.get("is_mentioned", False)

        # In group chat, only respond to @mentions
        if chat_type == "group" and not is_mentioned:
            return

        text = msg_event.get("text", "").strip()
        message_id = msg_event.get("message_id", "")

        if not text:
            self._reply_help(message_id)
            return

        logger.info("Processing query: '%s' from chat %s",
                     text, msg_event.get("chat_id"))

        # Route to handler
        text_lower = text.lower()

        if any(p in text_lower for p in HELP_PATTERNS):
            self._reply_help(message_id)
        elif any(p in text_lower for p in SUMMARY_PATTERNS):
            self._reply_summary(message_id)
        elif any(p in text_lower for p in LATEST_PATTERNS):
            # Check if user wants latest reports specifically
            if any(p in text_lower for p in REPORT_PATTERNS):
                self._reply_latest(message_id, doc_type="doc", label="研报")
            else:
                self._reply_latest(message_id)
        elif any(p in text_lower for p in REPORT_PATTERNS):
            # Search for reports
            query = text
            for p in REPORT_PATTERNS:
                query = query.replace(p, "").strip()
            if query:
                self._reply_search(message_id, query)
            else:
                self._reply_latest(message_id, doc_type="doc", label="研报")
        elif any(p in text_lower for p in SEARCH_PATTERNS):
            # Extract the actual search query
            query = text
            for p in SEARCH_PATTERNS:
                query = query.replace(p, "").strip()
            if query:
                self._reply_search(message_id, query)
            else:
                self._reply_help(message_id)
        else:
            # Default: treat entire text as search query
            self._reply_search(message_id, text)

    def _reply_help(self, message_id: str):
        content = (
            "👋 **你好！我是文档助手机器人**\n\n"
            "你可以通过 @我 + 指令来使用以下功能：\n\n"
            "🔍 **搜索文档**\n"
            "   `@机器人 搜索 关键词` 或直接 `@机器人 关键词`\n\n"
            "📄 **最新文档**\n"
            "   `@机器人 最新` — 查看最近更新的文档\n\n"
            "📊 **最新研报**\n"
            "   `@机器人 最新研报` — 查看最近的研究报告\n\n"
            "📈 **文档库概览**\n"
            "   `@机器人 概览` — 查看文档库的整体统计\n\n"
            "❓ **帮助**\n"
            "   `@机器人 帮助` — 显示本帮助信息\n\n"
            "---\n"
            "💡 **小提示**：你也可以直接 @我 然后输入任何关键词，"
            "我会在文档库中为你搜索相关内容！"
        )
        self._send_reply(message_id, content)

    def _reply_search(self, message_id: str, query: str):
        results = search_engine.search(query, top_k=5)

        if not results:
            content = (
                f"🔍 未找到与「**{query}**」相关的文档。\n\n"
                "建议：\n"
                "• 尝试使用不同的关键词\n"
                "• 使用更简短的搜索词\n"
                "• 输入 `帮助` 查看可用功能"
            )
        else:
            lines = [f"🔍 搜索「**{query}**」找到 {len(results)} 条结果：\n"]
            for i, r in enumerate(results, 1):
                title = r["title"] or "无标题"
                url = r.get("url", "")
                space = r.get("space_name", "")
                preview = r.get("content_preview", "")[:100]
                if preview:
                    preview = preview.replace("\n", " ")

                line = f"**{i}. [{title}]({url})**"
                if space:
                    line += f"  📁 {space}"
                if preview:
                    line += f"\n   > {preview}..."
                lines.append(line)

            content = "\n\n".join(lines)

        self._send_reply(message_id, content)

    def _reply_latest(self, message_id: str, doc_type: str = "",
                      label: str = "文档"):
        results = search_engine.get_latest_docs(count=5, doc_type=doc_type)

        if not results:
            content = f"📄 暂无{label}记录。文档库可能还在同步中，请稍后再试。"
        else:
            lines = [f"📄 最新{label} (最近更新 Top 5)：\n"]
            for i, r in enumerate(results, 1):
                title = r["title"] or "无标题"
                url = r.get("url", "")
                space = r.get("space_name", "")
                preview = r.get("content_preview", "")[:80]
                if preview:
                    preview = preview.replace("\n", " ")

                line = f"**{i}. [{title}]({url})**"
                if space:
                    line += f"  📁 {space}"
                if preview:
                    line += f"\n   > {preview}..."
                lines.append(line)
            content = "\n\n".join(lines)

        self._send_reply(message_id, content)

    def _reply_summary(self, message_id: str):
        summary = search_engine.get_summary()
        total = summary["total_docs"]
        spaces = summary["spaces"]
        type_counts = summary["type_counts"]

        lines = [
            f"📊 **文档库概览**\n",
            f"📚 总文档数：**{total}**",
            f"📁 知识空间：{', '.join(spaces) if spaces else '暂无'}",
            "",
            "📋 **文档类型分布：**",
        ]
        type_labels = {
            "doc": "文档(Doc)",
            "docx": "新版文档(Docx)",
            "sheet": "表格(Sheet)",
            "bitable": "多维表格",
            "mindnote": "思维导图",
            "slides": "幻灯片",
        }
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            label = type_labels.get(t, t)
            lines.append(f"   • {label}: **{c}** 篇")

        content = "\n".join(lines)
        self._send_reply(message_id, content)

    def _send_reply(self, message_id: str, text: str):
        """Send a rich text reply to the original message."""
        # Feishu interactive card for better formatting
        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": text,
                }
            ],
        }
        content = json.dumps(card, ensure_ascii=False)
        result = api_client.reply_message(
            message_id, msg_type="interactive", content=content,
        )
        if result.get("code") != 0:
            logger.error("Failed to reply message %s: %s",
                         message_id, result.get("msg"))
            # Fallback to plain text
            plain = json.dumps({"text": text}, ensure_ascii=False)
            api_client.reply_message(message_id, msg_type="text", content=plain)


message_handler = MessageHandler()
