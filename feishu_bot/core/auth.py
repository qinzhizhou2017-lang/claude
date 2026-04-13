import time
import threading
import requests
from feishu_bot.config import Config
from feishu_bot.utils.logger import logger


class TokenManager:
    """Manage tenant_access_token with auto-refresh."""

    def __init__(self):
        self._token = ""
        self._expire_time = 0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        with self._lock:
            if time.time() >= self._expire_time - 300:
                self._refresh_token()
            return self._token

    def _refresh_token(self):
        try:
            resp = requests.post(
                Config.TENANT_ACCESS_TOKEN_URL,
                json={"app_id": Config.APP_ID, "app_secret": Config.APP_SECRET},
                timeout=10,
                proxies={"http": None, "https": None},
            )
            data = resp.json()
            if data.get("code") == 0:
                self._token = data["tenant_access_token"]
                self._expire_time = time.time() + data.get("expire", 7200)
                logger.info("Tenant access token refreshed successfully")
            else:
                logger.error("Failed to get token: %s", data)
        except Exception as e:
            logger.error("Token refresh error: %s", e)

    def get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }


token_manager = TokenManager()
