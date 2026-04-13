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
    SEND_MESSAGE_URL = f"{FEISHU_HOST}/open-apis/im/v1/messages"
    WIKI_SPACE_LIST_URL = f"{FEISHU_HOST}/open-apis/wiki/v2/spaces"
    WIKI_NODE_LIST_URL = f"{FEISHU_HOST}/open-apis/wiki/v2/spaces/{{space_id}}/nodes"
    DOC_RAW_CONTENT_URL = f"{FEISHU_HOST}/open-apis/docx/v1/documents/{{document_id}}/raw_content"

    DOC_SYNC_INTERVAL = int(os.getenv("DOC_SYNC_INTERVAL", "3600"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    DOC_INDEX_PATH = os.path.join(DATA_DIR, "doc_index.json")
