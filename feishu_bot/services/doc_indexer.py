"""
Document indexer: sync Feishu wiki documents into a local searchable index.
"""

import json
import os
import time
import threading
from feishu_bot.config import Config
from feishu_bot.core.api_client import api_client
from feishu_bot.utils.logger import logger


class DocumentIndex:
    """Thread-safe in-memory document index backed by JSON on disk."""

    def __init__(self):
        self._docs = {}
        self._lock = threading.Lock()
        self._load_from_disk()

    def _load_from_disk(self):
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        if os.path.exists(Config.DOC_INDEX_PATH):
            try:
                with open(Config.DOC_INDEX_PATH, "r", encoding="utf-8") as f:
                    self._docs = json.load(f)
                logger.info("Loaded %d docs from index", len(self._docs))
            except Exception as e:
                logger.error("Failed to load index: %s", e)

    def save(self):
        with self._lock:
            try:
                with open(Config.DOC_INDEX_PATH, "w", encoding="utf-8") as f:
                    json.dump(self._docs, f, ensure_ascii=False, indent=2)
                logger.info("Saved %d docs to index", len(self._docs))
            except Exception as e:
                logger.error("Failed to save index: %s", e)

    def upsert(self, token: str, doc_info: dict):
        with self._lock:
            self._docs[token] = doc_info

    def get_all_docs(self) -> list:
        with self._lock:
            return list(self._docs.values())

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._docs)


doc_index = DocumentIndex()


class DocumentSyncer:
    """Sync documents from all Feishu wiki spaces."""

    def __init__(self):
        self._syncing = False

    def sync_all(self):
        if self._syncing:
            return
        self._syncing = True
        start = time.time()
        logger.info("Starting document sync...")

        try:
            spaces = self._fetch_all_spaces()
            total = 0
            for space in spaces:
                sid = space.get("space_id", "")
                sname = space.get("name", "Unknown")
                logger.info("Syncing space: %s (%s)", sname, sid)
                total += self._sync_space(sid, sname)

            doc_index.save()
            logger.info("Sync completed: %d docs in %.1fs",
                        total, time.time() - start)
        except Exception as e:
            logger.error("Sync failed: %s", e, exc_info=True)
        finally:
            self._syncing = False

    def _fetch_all_spaces(self) -> list:
        spaces = []
        page_token = ""
        while True:
            data = api_client.list_wiki_spaces(page_token=page_token)
            if data.get("code") != 0:
                logger.error("Failed to list spaces: %s", data.get("msg"))
                break
            items = data.get("data", {}).get("items", [])
            spaces.extend(items)
            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")
        return spaces

    def _sync_space(self, space_id: str, space_name: str,
                    parent_node_token: str = "") -> int:
        count = 0
        page_token = ""
        while True:
            data = api_client.list_wiki_nodes(
                space_id, parent_node_token=parent_node_token,
                page_token=page_token,
            )
            if data.get("code") != 0:
                logger.warning("Failed to list nodes in space %s: %s",
                               space_id, data.get("msg"))
                break

            for node in data.get("data", {}).get("items", []):
                node_token = node.get("node_token", "")
                obj_token = node.get("obj_token", "")
                obj_type = node.get("obj_type", "")
                title = node.get("title", "")

                content_preview = ""
                if obj_type in ("doc", "docx"):
                    content_preview = self._fetch_content(obj_token)

                doc_index.upsert(node_token, {
                    "node_token": node_token,
                    "obj_token": obj_token,
                    "title": title,
                    "obj_type": obj_type,
                    "space_id": space_id,
                    "space_name": space_name,
                    "content_preview": content_preview[:2000],
                    "url": node.get("url", ""),
                    "updated_at": node.get("edit_time", ""),
                    "synced_at": int(time.time()),
                })
                count += 1

                if node.get("has_child", False):
                    count += self._sync_space(space_id, space_name, node_token)

            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")
        return count

    def _fetch_content(self, document_id: str) -> str:
        data = api_client.get_document_raw_content(document_id)
        if data.get("code") == 0:
            return data.get("data", {}).get("content", "")
        return ""


doc_syncer = DocumentSyncer()
