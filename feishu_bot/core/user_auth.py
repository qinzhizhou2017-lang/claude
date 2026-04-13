"""
OAuth user authorization: one-time flow to get user_access_token.
This allows the bot to access documents as the user (not as the app).
"""

import json
import os
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests

from feishu_bot.config import Config
from feishu_bot.utils.logger import logger

_NO_PROXY = {"http": None, "https": None}


class UserTokenManager:
    """Manage user_access_token with auto-refresh."""

    def __init__(self):
        self._token = ""
        self._refresh_token = ""
        self._expire_time = 0
        self._lock = threading.Lock()
        self._load_from_disk()

    @property
    def is_authorized(self) -> bool:
        return bool(self._refresh_token)

    def get_headers(self) -> dict:
        """Get headers with user_access_token for document API calls."""
        with self._lock:
            if time.time() >= self._expire_time - 300:
                self._refresh()
            return {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json; charset=utf-8",
            }

    def save_tokens(self, access_token: str, refresh_token: str, expires_in: int):
        with self._lock:
            self._token = access_token
            self._refresh_token = refresh_token
            self._expire_time = time.time() + expires_in
            self._save_to_disk()
            logger.info("User tokens saved successfully")

    def _refresh(self):
        if not self._refresh_token:
            logger.warning("No refresh token available, need re-authorization")
            return

        try:
            # Get app_access_token first
            app_resp = requests.post(
                Config.APP_ACCESS_TOKEN_URL,
                json={"app_id": Config.APP_ID, "app_secret": Config.APP_SECRET},
                timeout=10, proxies=_NO_PROXY,
            )
            app_data = app_resp.json()
            if app_data.get("code") != 0:
                logger.error("Failed to get app_access_token: %s", app_data)
                return
            app_token = app_data["app_access_token"]

            # Refresh user token
            resp = requests.post(
                Config.OAUTH_REFRESH_URL,
                headers={
                    "Authorization": f"Bearer {app_token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
                timeout=10, proxies=_NO_PROXY,
            )
            data = resp.json()
            if data.get("code") == 0:
                d = data["data"]
                self._token = d["access_token"]
                self._refresh_token = d["refresh_token"]
                self._expire_time = time.time() + d.get("expires_in", 7200)
                self._save_to_disk()
                logger.info("User access token refreshed successfully")
            else:
                logger.error("Failed to refresh user token: %s", data)
        except Exception as e:
            logger.error("User token refresh error: %s", e)

    def _load_from_disk(self):
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        if os.path.exists(Config.USER_TOKEN_PATH):
            try:
                with open(Config.USER_TOKEN_PATH, "r") as f:
                    d = json.load(f)
                self._token = d.get("access_token", "")
                self._refresh_token = d.get("refresh_token", "")
                self._expire_time = d.get("expire_time", 0)
                if self._refresh_token:
                    logger.info("User token loaded from disk")
            except Exception as e:
                logger.error("Failed to load user token: %s", e)

    def _save_to_disk(self):
        try:
            with open(Config.USER_TOKEN_PATH, "w") as f:
                json.dump({
                    "access_token": self._token,
                    "refresh_token": self._refresh_token,
                    "expire_time": self._expire_time,
                }, f)
        except Exception as e:
            logger.error("Failed to save user token: %s", e)


user_token_manager = UserTokenManager()


def run_oauth_flow():
    """Run one-time OAuth authorization flow."""
    print("\n" + "=" * 50)
    print("  Feishu OAuth Authorization")
    print("=" * 50)

    # Step 1: Get app_access_token
    resp = requests.post(
        Config.APP_ACCESS_TOKEN_URL,
        json={"app_id": Config.APP_ID, "app_secret": Config.APP_SECRET},
        timeout=10, proxies=_NO_PROXY,
    )
    data = resp.json()
    if data.get("code") != 0:
        print(f"Error getting app token: {data}")
        return False
    app_token = data["app_access_token"]

    # Step 2: Start local callback server
    auth_code_holder = {"code": None}

    class OAuthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/oauth/callback":
                params = parse_qs(parsed.query)
                code = params.get("code", [None])[0]
                if code:
                    auth_code_holder["code"] = code
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        "<h1>授权成功！</h1><p>你可以关闭这个页面了。</p>".encode()
                    )
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"No code received")

        def log_message(self, format, *args):
            pass  # Suppress default logging

    server = HTTPServer(("127.0.0.1", 9000), OAuthHandler)

    # Step 3: Open browser for authorization
    auth_url = (
        f"{Config.OAUTH_AUTHORIZE_URL}"
        f"?app_id={Config.APP_ID}"
        f"&redirect_uri={Config.OAUTH_REDIRECT_URI}"
        f"&scope=drive:drive:readonly%20wiki:wiki:readonly%20docx:document:readonly%20space:document:retrieve%20drive:drive"
        f"&state=auth"
    )

    print(f"\nOpening browser for authorization...")
    print(f"If browser doesn't open, visit this URL manually:\n")
    print(f"  {auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for callback
    print("Waiting for authorization...")
    while auth_code_holder["code"] is None:
        server.handle_request()

    code = auth_code_holder["code"]
    print(f"Authorization code received!")

    # Step 4: Exchange code for tokens
    resp = requests.post(
        Config.OAUTH_TOKEN_URL,
        headers={
            "Authorization": f"Bearer {app_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "grant_type": "authorization_code",
            "code": code,
        },
        timeout=10, proxies=_NO_PROXY,
    )
    data = resp.json()
    if data.get("code") == 0:
        d = data["data"]
        user_token_manager.save_tokens(
            d["access_token"],
            d["refresh_token"],
            d.get("expires_in", 7200),
        )
        print(f"\nAuthorization successful!")
        print(f"Now run: python3 main.py")
        return True
    else:
        print(f"\nAuthorization failed: {data}")
        return False
