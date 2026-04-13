#!/usr/bin/env python3
"""
Feishu Document Bot

Usage:
    python main.py              # Start the bot
    python main.py --auth       # One-time OAuth authorization
    python main.py --sync       # One-time document sync
"""

# ── Proxy bypass (must be first) ──
import os
import sys
import urllib.request

for _k in list(os.environ.keys()):
    if "proxy" in _k.lower():
        del os.environ[_k]
os.environ["NO_PROXY"] = "*"
urllib.request.getproxies = lambda: {}

# ── Imports ──
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger


def main():
    if not Config.APP_ID or not Config.APP_SECRET:
        print("Error: FEISHU_APP_ID or FEISHU_APP_SECRET not set in .env")
        sys.exit(1)

    # --auth: One-time OAuth flow
    if len(sys.argv) > 1 and sys.argv[1] == "--auth":
        from feishu_bot.core.user_auth import run_oauth_flow
        run_oauth_flow()
        return

    # --sync: One-time sync
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        logger.info("Running one-time document sync...")
        from feishu_bot.services.doc_indexer import doc_syncer
        doc_syncer.sync_all()
        return

    # Check if user is authorized
    from feishu_bot.core.user_auth import user_token_manager
    if not user_token_manager.is_authorized:
        print("\n" + "=" * 50)
        print("  First time setup: OAuth authorization needed")
        print("=" * 50)
        print("\nThe bot needs your permission to read documents.")
        print("Run this command first:\n")
        print("  python3 main.py --auth\n")
        sys.exit(1)

    # Start bot
    logger.info("=" * 50)
    logger.info("  Feishu Doc Bot - Long-Connection Mode")
    logger.info("  App ID: %s", Config.APP_ID[:10] + "...")
    logger.info("  User authorized: YES")
    logger.info("  Doc sync interval: %ds", Config.DOC_SYNC_INTERVAL)
    logger.info("=" * 50)

    from feishu_bot.app import start_bot
    start_bot()


if __name__ == "__main__":
    main()
