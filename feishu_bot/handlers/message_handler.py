"""
Message handler: route user queries and generate replies.
"""

import json
from feishu_bot.core.api_client import api_client
from feishu_bot.services.search_engine import search_engine
from feishu_bot.utils.logger import logger

HELP_KW = {"帮助", "help", "指令", "功能", "菜单", "怎么用"}
SEARCH_KW = {"搜索", "查找", "查询", "找", "搜", "search"}
LATEST_KW = {"最新", "最近", "今日", "今天", "latest", "recent"}
SUMMARY_KW = {"总结", "概览", "统计", "summary", "文档库"}
REPORT_KW = {"研报", "报告", "研究", "report"}


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

        if any(k in tl for k in HELP_KW):
            self._reply_help(mid)
        elif any(k in tl for k in SUMMARY_KW):
            self._reply_summary(mid)
        elif any(k in tl for k in LATEST_KW):
            if any(k in tl for k in REPORT_KW):
                self._reply_latest(mid, doc_type="doc", label="研报")
            else:
                self._reply_latest(mid)
        elif any(k in tl for k in REPORT_KW):
            q = text
            for k in REPORT_KW:
                q = q.replace(k, "").strip()
            self._reply_search(mid, q) if q else self._reply_latest(mid, label="研报")
        elif any(k in tl for k in SEARCH_KW):
            q = text
            for k in SEARCH_KW:
                q = q.replace(k, "").strip()
            self._reply_search(mid, q) if q else self._reply_help(mid)
        else:
            self._reply_search(mid, text)

    def _reply_help(self, mid: str):
        self._send(mid, (
            "**你好！我是文档助手机器人**\n\n"
            "你可以 @我 + 指令来使用以下功能：\n\n"
            "**搜索文档** — `@机器人 关键词`\n"
            "**最新文档** — `@机器人 最新`\n"
            "**最新研报** — `@机器人 最新研报`\n"
            "**文档库概览** — `@机器人 概览`\n"
            "**帮助** — `@机器人 帮助`\n\n"
            "直接 @我 输入任何关键词，即可在文档库中搜索！"
        ))

    def _reply_search(self, mid: str, query: str):
        query = query[:200]  # limit query length
        results = search_engine.search(query, top_k=5)

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
            space = r.get("space_name", "")
            preview = r.get("content_preview", "")[:100].replace("\n", " ")

            line = f"**{i}. [{title}]({url})**"
            if space:
                line += f"  | {space}"
            if preview:
                line += f"\n> {preview}..."
            lines.append(line)

        self._send(mid, "\n\n".join(lines))

    def _reply_latest(self, mid: str, doc_type: str = "", label: str = "文档"):
        results = search_engine.get_latest_docs(count=5, doc_type=doc_type)

        if not results:
            self._send(mid, f"暂无{label}记录。文档库可能还在同步中，请稍后再试。")
            return

        lines = [f"最新{label}（Top 5）：\n"]
        for i, r in enumerate(results, 1):
            title = r["title"] or "无标题"
            url = r.get("url", "")
            space = r.get("space_name", "")
            line = f"**{i}. [{title}]({url})**"
            if space:
                line += f"  | {space}"
            lines.append(line)
        self._send(mid, "\n\n".join(lines))

    def _reply_summary(self, mid: str):
        s = search_engine.get_summary()
        type_labels = {
            "doc": "文档", "docx": "新版文档", "sheet": "表格",
            "bitable": "多维表格", "mindnote": "思维导图", "slides": "幻灯片",
        }
        lines = [
            "**文档库概览**\n",
            f"总文档数：**{s['total_docs']}**",
            f"知识空间：{', '.join(s['spaces']) if s['spaces'] else '暂无'}",
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
