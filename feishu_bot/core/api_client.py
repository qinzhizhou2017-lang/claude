import requests
from feishu_bot.config import Config
from feishu_bot.core.auth import token_manager
from feishu_bot.utils.logger import logger

# Explicitly bypass proxy for all API calls
_NO_PROXY = {"http": None, "https": None}


class FeishuAPIClient:
    """Feishu API client for messaging and document access."""

    def reply_message(self, message_id: str, msg_type: str, content: str):
        url = f"{Config.SEND_MESSAGE_URL}/{message_id}/reply"
        return self._post(url, {"msg_type": msg_type, "content": content})

    def send_message(self, receive_id: str, msg_type: str, content: str,
                     receive_id_type: str = "chat_id"):
        return self._post(
            Config.SEND_MESSAGE_URL,
            {"receive_id": receive_id, "msg_type": msg_type, "content": content},
            params={"receive_id_type": receive_id_type},
        )

    def list_wiki_spaces(self, page_size=50, page_token=""):
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._get(Config.WIKI_SPACE_LIST_URL, params=params)

    def list_wiki_nodes(self, space_id: str, parent_node_token="",
                        page_size=50, page_token=""):
        url = Config.WIKI_NODE_LIST_URL.format(space_id=space_id)
        params = {"page_size": page_size}
        if parent_node_token:
            params["parent_node_token"] = parent_node_token
        if page_token:
            params["page_token"] = page_token
        return self._get(url, params=params)

    def get_document_raw_content(self, document_id: str):
        url = Config.DOC_RAW_CONTENT_URL.format(document_id=document_id)
        return self._get(url)

    def list_drive_files(self, folder_token: str, page_size=200,
                         page_token=""):
        """List files in a Drive folder."""
        params = {
            "folder_token": folder_token,
            "page_size": page_size,
            "order_by": "EditedTime",
            "direction": "DESC",
        }
        if page_token:
            params["page_token"] = page_token
        return self._get(Config.DRIVE_FILE_LIST_URL, params=params)

    def _get(self, url, params=None):
        try:
            resp = requests.get(
                url, headers=token_manager.get_headers(),
                params=params, timeout=30, proxies=_NO_PROXY,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.warning("GET %s: %s", url, data.get("msg"))
            return data
        except Exception as e:
            logger.error("GET %s error: %s", url, e)
            return {"code": -1, "msg": str(e)}

    def _post(self, url, payload, params=None):
        try:
            resp = requests.post(
                url, headers=token_manager.get_headers(),
                json=payload, params=params, timeout=30, proxies=_NO_PROXY,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.warning("POST %s: %s", url, data.get("msg"))
            return data
        except Exception as e:
            logger.error("POST %s error: %s", url, e)
            return {"code": -1, "msg": str(e)}


api_client = FeishuAPIClient()
