import requests
from feishu_bot.config import Config
from feishu_bot.core.auth import token_manager
from feishu_bot.utils.logger import logger


class FeishuAPIClient:
    """Low-level Feishu API client for messaging and document access."""

    # ── Messaging ──

    def reply_message(self, message_id: str, msg_type: str, content: str):
        """Reply to a specific message."""
        url = f"{Config.SEND_MESSAGE_URL}/{message_id}/reply"
        payload = {"msg_type": msg_type, "content": content}
        return self._post(url, payload)

    def send_message(self, receive_id: str, msg_type: str, content: str,
                     receive_id_type: str = "chat_id"):
        """Send a message to a chat."""
        url = Config.SEND_MESSAGE_URL
        params = {"receive_id_type": receive_id_type}
        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content,
        }
        return self._post(url, payload, params=params)

    # ── Wiki / Knowledge Base ──

    def list_wiki_spaces(self, page_size=50, page_token=""):
        """List all wiki spaces the app can access."""
        url = Config.WIKI_SPACE_LIST_URL
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._get(url, params=params)

    def list_wiki_nodes(self, space_id: str, parent_node_token="",
                        page_size=50, page_token=""):
        """List nodes (docs) under a wiki space."""
        url = Config.WIKI_NODE_LIST_URL.format(space_id=space_id)
        params = {"page_size": page_size}
        if parent_node_token:
            params["parent_node_token"] = parent_node_token
        if page_token:
            params["page_token"] = page_token
        return self._get(url, params=params)

    def get_document_raw_content(self, document_id: str):
        """Get raw text content of a document."""
        url = Config.DOC_RAW_CONTENT_URL.format(document_id=document_id)
        return self._get(url)

    def get_document_blocks(self, document_id: str, page_size=500,
                            page_token=""):
        """Get document block-level content."""
        url = Config.DOC_CONTENT_URL.format(document_id=document_id)
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._get(url, params=params)

    # ── Drive / File search ──

    def list_files(self, folder_token="", page_size=200, page_token="",
                   order_by="EditedTime", direction="DESC"):
        """List files in a drive folder."""
        params = {
            "page_size": page_size,
            "order_by": order_by,
            "direction": direction,
        }
        if folder_token:
            params["folder_token"] = folder_token
        if page_token:
            params["page_token"] = page_token
        return self._get(Config.DRIVE_FILE_LIST_URL, params=params)

    # ── Helpers ──

    def _get(self, url, params=None):
        try:
            resp = requests.get(
                url, headers=token_manager.get_headers(),
                params=params, timeout=30,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.warning("API GET %s failed: %s", url, data.get("msg"))
            return data
        except Exception as e:
            logger.error("API GET %s error: %s", url, e)
            return {"code": -1, "msg": str(e)}

    def _post(self, url, payload, params=None):
        try:
            resp = requests.post(
                url, headers=token_manager.get_headers(),
                json=payload, params=params, timeout=30,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.warning("API POST %s failed: %s", url, data.get("msg"))
            return data
        except Exception as e:
            logger.error("API POST %s error: %s", url, e)
            return {"code": -1, "msg": str(e)}


api_client = FeishuAPIClient()
