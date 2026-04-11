#!/usr/bin/env python3
"""
Entry point for the Feishu Document Bot.

Usage:
    python main.py              # Start the webhook server
    python main.py --sync       # Run a one-time document sync
"""

import sys
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        logger.info("Running one-time document sync...")
        from feishu_bot.services.doc_indexer import doc_syncer
        doc_syncer.sync_all()
        logger.info("Sync complete.")
        return

    logger.info("Starting Feishu Doc Bot on %s:%s", Config.HOST, Config.PORT)
    from feishu_bot.app import create_app
    app = create_app()
    app.run(host=Config.HOST, port=Config.PORT, debug=False)


if __name__ == "__main__":
    main()
