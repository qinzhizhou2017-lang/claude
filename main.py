#!/usr/bin/env python3
"""
Entry point for the Feishu Document Bot (Long-Connection mode).

Usage:
    python main.py              # Start the bot (WebSocket long-connection)
    python main.py --sync       # Run a one-time document sync only
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

    logger.info("=" * 50)
    logger.info("  Feishu Doc Bot — Long-Connection Mode")
    logger.info("  App ID: %s", Config.APP_ID[:8] + "..." if Config.APP_ID else "NOT SET")
    logger.info("  Doc sync interval: %ds", Config.DOC_SYNC_INTERVAL)
    logger.info("=" * 50)

    from feishu_bot.app import start_bot
    start_bot()


if __name__ == "__main__":
    main()
