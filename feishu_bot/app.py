"""
Long-connection (WebSocket) client using official lark-oapi SDK.
No public IP / domain / SSL required.
"""

import json
import re
import threading

import lark_oapi as lark
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

from apscheduler.schedulers.background import BackgroundScheduler

from feishu_bot.config import Config
from feishu_bot.handlers.message_handler import message_handler
from feishu_bot.services.doc_indexer import doc_syncer
from feishu_bot.utils.logger import logger

# Dedup: track recently processed message IDs
_processed_msgs = set()
_processed_lock = threading.Lock()


def _on_message(data: P2ImMessageReceiveV1) -> None:
    """Callback when a message is received via the SDK."""
    try:
        event = data.event
        message = event.message
        sender = event.sender

        msg_id = message.message_id or ""

        # Deduplicate: skip if already processed
        with _processed_lock:
            if msg_id in _processed_msgs:
                logger.debug("Skipping duplicate message: %s", msg_id)
                return
            _processed_msgs.add(msg_id)
            # Keep set from growing forever (max 1000)
            if len(_processed_msgs) > 1000:
                _processed_msgs.clear()

        if message.message_type != "text":
            return

        try:
            content_data = json.loads(message.content or "{}")
        except (json.JSONDecodeError, TypeError):
            content_data = {}

        text = content_data.get("text", "")
        clean_text = re.sub(r"@_user_\d+", "", text).strip()

        mentions = message.mentions or []

        msg_event = {
            "message_id": message.message_id or "",
            "chat_id": message.chat_id or "",
            "chat_type": message.chat_type or "",
            "sender_id": (sender.sender_id.open_id
                          if sender and sender.sender_id else ""),
            "text": clean_text,
            "is_mentioned": len(mentions) > 0,
        }

        message_handler.handle(msg_event)

    except Exception as e:
        logger.error("Error handling message: %s", e, exc_info=True)


def start_bot():
    """Start the bot with WebSocket long-connection + scheduled doc sync."""

    # Event dispatcher
    event_handler = (
        lark.EventDispatcherHandler.builder(
            Config.VERIFICATION_TOKEN,
            Config.ENCRYPT_KEY,
        )
        .register_p2_im_message_receive_v1(_on_message)
        .build()
    )

    # WebSocket client (auto-reconnect built-in)
    cli = lark.ws.Client(
        Config.APP_ID,
        Config.APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO,
    )

    # Scheduled document sync
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        doc_syncer.sync_all, "interval",
        seconds=Config.DOC_SYNC_INTERVAL, id="doc_sync",
    )
    scheduler.start()

    # Initial sync in background
    threading.Thread(target=doc_syncer.sync_all, daemon=True).start()
    logger.info("Document sync started in background")

    logger.info("Connecting to Feishu servers (WebSocket)...")

    # Blocks forever, auto-reconnects on disconnect
    cli.start()
