#!/usr/bin/env python3
"""
Feishu Document Bot — Entry Point

IMPORTANT: Proxy bypass MUST happen before any other import.
macOS reads SOCKS proxy from System Preferences, which breaks WebSocket.
"""

# ── Step 0: Kill ALL proxy detection (must be first) ──
import os
import sys
import urllib.request

for _k in list(os.environ.keys()):
    if "proxy" in _k.lower():
        del os.environ[_k]
os.environ["NO_PROXY"] = "*"
urllib.request.getproxies = lambda: {}

# ── Now safe to import everything else ──
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        logger.info("Running one-time document sync...")
        from feishu_bot.services.doc_indexer import doc_syncer
        doc_syncer.sync_all()
        logger.info("Sync complete.")
        return

    if not Config.APP_ID or not Config.APP_SECRET:
        logger.error("FEISHU_APP_ID or FEISHU_APP_SECRET not set in .env")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("  Feishu Doc Bot - Long-Connection Mode")
    logger.info("  App ID: %s", Config.APP_ID[:10] + "...")
    logger.info("  Doc sync interval: %ds", Config.DOC_SYNC_INTERVAL)
    logger.info("=" * 50)

    from feishu_bot.app import start_bot
    start_bot()


if __name__ == "__main__":
    main()
