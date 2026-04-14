import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_ID = os.getenv("FEISHU_APP_ID", "")
    APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
    VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
    ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

    FEISHU_HOST = "https://open.feishu.cn"

    # API endpoints
    TENANT_ACCESS_TOKEN_URL = f"{FEISHU_HOST}/open-apis/auth/v3/tenant_access_token/internal"
    APP_ACCESS_TOKEN_URL = f"{FEISHU_HOST}/open-apis/auth/v3/app_access_token/internal"
    SEND_MESSAGE_URL = f"{FEISHU_HOST}/open-apis/im/v1/messages"
    WIKI_SPACE_LIST_URL = f"{FEISHU_HOST}/open-apis/wiki/v2/spaces"
    WIKI_NODE_LIST_URL = f"{FEISHU_HOST}/open-apis/wiki/v2/spaces/{{space_id}}/nodes"
    DOC_RAW_CONTENT_URL = f"{FEISHU_HOST}/open-apis/docx/v1/documents/{{document_id}}/raw_content"
    DRIVE_FILE_LIST_URL = f"{FEISHU_HOST}/open-apis/drive/v1/files"

    # OAuth
    OAUTH_REDIRECT_URI = "http://127.0.0.1:9000/oauth/callback"
    OAUTH_AUTHORIZE_URL = f"{FEISHU_HOST}/open-apis/authen/v1/authorize"
    OAUTH_TOKEN_URL = f"{FEISHU_HOST}/open-apis/authen/v1/oidc/access_token"
    OAUTH_REFRESH_URL = f"{FEISHU_HOST}/open-apis/authen/v1/oidc/refresh_access_token"

    # Drive folder tokens to scan (comma-separated)
    DRIVE_FOLDER_TOKENS = [
        t.strip() for t in os.getenv("FEISHU_FOLDER_TOKENS", "").split(",")
        if t.strip()
    ]

    DOC_SYNC_INTERVAL = int(os.getenv("DOC_SYNC_INTERVAL", "3600"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Doubao (豆包) LLM API
    DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
    DOUBAO_ENDPOINT_ID = os.getenv("DOUBAO_ENDPOINT_ID", "")
    DOUBAO_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    DOC_INDEX_PATH = os.path.join(DATA_DIR, "doc_index.json")
    USER_TOKEN_PATH = os.path.join(DATA_DIR, "user_token.json")
