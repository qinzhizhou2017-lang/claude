"""
Flask application: receives Feishu webhook events and dispatches them.
"""

import threading
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from feishu_bot.config import Config
from feishu_bot.handlers.event_handler import event_handler
from feishu_bot.handlers.message_handler import message_handler
from feishu_bot.services.doc_indexer import doc_syncer
from feishu_bot.utils.logger import logger


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def health():
        from feishu_bot.services.doc_indexer import doc_index
        return jsonify({
            "status": "ok",
            "bot": "feishu-doc-bot",
            "indexed_docs": doc_index.count,
        })

    @app.route("/webhook/event", methods=["POST"])
    def handle_event():
        """Main webhook endpoint for Feishu event subscriptions."""
        raw_body = request.json
        if not raw_body:
            return jsonify({"code": 400, "msg": "empty body"}), 400

        # Parse (and decrypt if needed)
        body = event_handler.parse_request(raw_body)

        # URL verification challenge
        if event_handler.is_url_verification(body):
            challenge = event_handler.get_challenge(body)
            logger.info("URL verification challenge received")
            return jsonify({"challenge": challenge})

        # Handle v2 events
        if event_handler.is_event_v2(body):
            msg_event = event_handler.extract_message_event(body)
            if msg_event:
                # Process in background thread to return 200 quickly
                threading.Thread(
                    target=_safe_handle_message,
                    args=(msg_event,),
                    daemon=True,
                ).start()

        return jsonify({"code": 0, "msg": "ok"})

    def _safe_handle_message(msg_event):
        try:
            message_handler.handle(msg_event)
        except Exception as e:
            logger.error("Error handling message: %s", e, exc_info=True)

    # Schedule document sync
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        doc_syncer.sync_all,
        "interval",
        seconds=Config.DOC_SYNC_INTERVAL,
        id="doc_sync",
        next_run_time=None,  # Don't run immediately; see startup below
    )
    scheduler.start()

    # Initial sync on startup (in background)
    threading.Thread(target=doc_syncer.sync_all, daemon=True).start()
    logger.info("Initial document sync started in background")

    return app
