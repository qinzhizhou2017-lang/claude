"""
Handle Feishu event callbacks: URL verification, message events, etc.
"""

import json
import re
from feishu_bot.utils.crypto import AESCipher
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger


class EventHandler:
    """Parse and dispatch incoming Feishu event payloads."""

    def __init__(self):
        self._processed_ids = set()  # Deduplicate events
        self._max_cache = 1000

    def parse_request(self, raw_body: dict) -> dict:
        """
        Parse the incoming request body. Handles encryption if configured.
        Returns a normalized event dict.
        """
        # Handle encrypted payloads
        if "encrypt" in raw_body and Config.ENCRYPT_KEY:
            cipher = AESCipher(Config.ENCRYPT_KEY)
            decrypted = cipher.decrypt(raw_body["encrypt"])
            raw_body = json.loads(decrypted)

        return raw_body

    def is_url_verification(self, body: dict) -> bool:
        """Check if this is a URL verification challenge."""
        # Schema v2
        if body.get("type") == "url_verification":
            return True
        # Schema v1
        if body.get("schema") is None and body.get("challenge"):
            return True
        return False

    def get_challenge(self, body: dict) -> str:
        return body.get("challenge", "")

    def is_event_v2(self, body: dict) -> bool:
        return body.get("schema") == "2.0"

    def is_duplicate(self, event_id: str) -> bool:
        """Check and register event ID for deduplication."""
        if event_id in self._processed_ids:
            return True
        self._processed_ids.add(event_id)
        if len(self._processed_ids) > self._max_cache:
            # Trim oldest entries (set doesn't preserve order, but good enough)
            excess = len(self._processed_ids) - self._max_cache // 2
            for _ in range(excess):
                self._processed_ids.pop()
        return False

    def extract_message_event(self, body: dict) -> dict | None:
        """
        Extract a normalized message event.
        Returns None if this isn't a message event or should be skipped.
        """
        header = body.get("header", {})
        event = body.get("event", {})
        event_type = header.get("event_type", "")

        # Only handle im.message.receive_v1
        if event_type != "im.message.receive_v1":
            logger.debug("Ignoring event type: %s", event_type)
            return None

        event_id = header.get("event_id", "")
        if self.is_duplicate(event_id):
            logger.debug("Duplicate event: %s", event_id)
            return None

        message = event.get("message", {})
        sender = event.get("sender", {})

        # Only handle text messages
        msg_type = message.get("message_type", "")
        if msg_type != "text":
            return None

        # Check if bot was mentioned
        mentions = message.get("mentions", [])
        is_mentioned = any(
            m.get("id", {}).get("union_id") or m.get("key")
            for m in mentions
        )

        # Parse message content
        content_str = message.get("content", "{}")
        try:
            content_data = json.loads(content_str)
        except json.JSONDecodeError:
            content_data = {"text": content_str}

        text = content_data.get("text", "")
        # Remove @mention tags to get the actual query
        clean_text = re.sub(r"@_user_\d+", "", text).strip()

        return {
            "event_id": event_id,
            "message_id": message.get("message_id", ""),
            "chat_id": message.get("chat_id", ""),
            "chat_type": message.get("chat_type", ""),  # group / p2p
            "sender_id": sender.get("sender_id", {}).get("open_id", ""),
            "msg_type": msg_type,
            "text": clean_text,
            "raw_text": text,
            "is_mentioned": is_mentioned,
            "mentions": mentions,
        }


event_handler = EventHandler()
