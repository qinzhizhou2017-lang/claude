"""
Long-connection (WebSocket) mode using the official lark-oapi SDK.
No public IP / domain / SSL required — ideal for Mac Mini at home.
"""

import json
import re
import threading

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from apscheduler.schedulers.background import BackgroundScheduler

from feishu_bot.config import Config
from feishu_bot.handlers.message_handler import message_handler
from feishu_bot.services.doc_indexer import doc_syncer
from feishu_bot.utils.logger import logger


def _handle_im_message(data: P2ImMessageReceiveV1) -> None:
    """Callback for im.message.receive_v1 events via the SDK."""
    try:
        event = data.event
        message = event.message
        sender = event.sender

        # Only handle text messages
        if message.message_type != "text":
            return

        # Parse content JSON
        try:
            content_data = json.loads(message.content)
        except (json.JSONDecodeError, TypeError):
            content_data = {"text": ""}

        text = content_data.get("text", "")
        # Remove @mention placeholders
        clean_text = re.sub(r"@_user_\d+", "", text).strip()

        # Check if bot was mentioned
        mentions = message.mentions or []
        is_mentioned = len(mentions) > 0

        msg_event = {
            "event_id": data.header.event_id or "",
            "message_id": message.message_id or "",
            "chat_id": message.chat_id or "",
            "chat_type": message.chat_type or "",
            "sender_id": sender.sender_id.open_id if sender and sender.sender_id else "",
            "msg_type": message.message_type or "",
            "text": clean_text,
            "raw_text": text,
            "is_mentioned": is_mentioned,
            "mentions": mentions,
        }

        message_handler.handle(msg_event)
    except Exception as e:
        logger.error("Error handling message event: %s", e, exc_info=True)


def start_bot():
    """Start the bot using long-connection (WebSocket) mode."""

    # Build the event handler
    event_handler = (
        lark.EventDispatcherHandler.builder(
            Config.VERIFICATION_TOKEN,
            Config.ENCRYPT_KEY,
        )
        .register_p2_im_message_receive_v1(_handle_im_message)
        .build()
    )

    # Build the lark client with WebSocket (long-connection)
    cli = (
        lark.ws.Client(
            Config.APP_ID,
            Config.APP_SECRET,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO,
        )
    )

    # Start scheduled document sync
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        doc_syncer.sync_all,
        "interval",
        seconds=Config.DOC_SYNC_INTERVAL,
        id="doc_sync",
        next_run_time=None,
    )
    scheduler.start()

    # Initial document sync in background
    threading.Thread(target=doc_syncer.sync_all, daemon=True).start()
    logger.info("Initial document sync started in background")

    logger.info("Starting Feishu Bot in long-connection (WebSocket) mode...")
    logger.info("No public IP or domain needed. Bot is connecting to Feishu servers...")

    # This blocks and keeps the connection alive (auto-reconnect built-in)
    cli.start()
