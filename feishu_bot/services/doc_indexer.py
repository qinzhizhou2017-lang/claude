"""
Document indexer: syncs Feishu wiki/knowledge base documents into a local
searchable index. Runs on a schedule to keep content up-to-date.
"""

import json
import os
import time
import threading
from feishu_bot.config import Config
from feishu_bot.core.api_client import api_client
from feishu_bot.utils.logger import logger


class DocumentIndex:
    """In-memory document index backed by a JSON file on disk."""

    def __init__(self):
        self._docs = {}  # token -> doc_info
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
                self._docs = {}

    def _save_to_disk(self):
        try:
            with open(Config.DOC_INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump(self._docs, f, ensure_ascii=False, indent=2)
            logger.info("Saved %d docs to index", len(self._docs))
        except Exception as e:
            logger.error("Failed to save index: %s", e)

    def upsert(self, token: str, doc_info: dict):
        with self._lock:
            self._docs[token] = doc_info

    def save(self):
        with self._lock:
            self._save_to_disk()

    def get_all_docs(self) -> list:
        with self._lock:
            return list(self._docs.values())

    def get_doc(self, token: str) -> dict | None:
        with self._lock:
            return self._docs.get(token)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._docs)


doc_index = DocumentIndex()


class DocumentSyncer:
    """Periodically sync documents from all Feishu wiki spaces."""

    def __init__(self):
        self._syncing = False

    def sync_all(self):
        """Full sync: iterate all wiki spaces and their nodes."""
        if self._syncing:
            logger.info("Sync already in progress, skipping")
            return
        self._syncing = True
        start = time.time()
        logger.info("Starting document sync...")

        try:
            spaces = self._fetch_all_spaces()
            total_docs = 0
            for space in spaces:
                space_id = space.get("space_id", "")
                space_name = space.get("name", "Unknown")
                logger.info("Syncing wiki space: %s (%s)", space_name, space_id)
                count = self._sync_space(space_id, space_name)
                total_docs += count

            doc_index.save()
            elapsed = time.time() - start
            logger.info(
                "Document sync completed: %d docs in %.1fs", total_docs, elapsed
            )
        except Exception as e:
            logger.error("Document sync failed: %s", e)
        finally:
            self._syncing = False

    def _fetch_all_spaces(self) -> list:
        spaces = []
        page_token = ""
        while True:
            data = api_client.list_wiki_spaces(page_token=page_token)
            if data.get("code") != 0:
                logger.error("Failed to list wiki spaces: %s", data.get("msg"))
                break
            items = data.get("data", {}).get("items", [])
            spaces.extend(items)
            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")
        return spaces

    def _sync_space(self, space_id: str, space_name: str,
                    parent_node_token: str = "") -> int:
        """Recursively sync all nodes in a wiki space."""
        count = 0
        page_token = ""
        while True:
            data = api_client.list_wiki_nodes(
                space_id, parent_node_token=parent_node_token,
                page_token=page_token,
            )
            if data.get("code") != 0:
                break
            items = data.get("data", {}).get("items", [])
            for node in items:
                node_token = node.get("node_token", "")
                obj_token = node.get("obj_token", "")
                title = node.get("title", "")
                obj_type = node.get("obj_type", "")
                node_type = node.get("node_type", "")

                # Fetch raw content for documents
                content_preview = ""
                if obj_type in ("doc", "docx"):
                    content_preview = self._fetch_doc_content(obj_token)

                doc_info = {
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
                }
                doc_index.upsert(node_token, doc_info)
                count += 1

                # Recurse into child nodes
                if node.get("has_child", False):
                    count += self._sync_space(
                        space_id, space_name, parent_node_token=node_token
                    )

            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")
        return count

    def _fetch_doc_content(self, document_id: str) -> str:
        """Fetch raw text content of a document."""
        data = api_client.get_document_raw_content(document_id)
        if data.get("code") == 0:
            return data.get("data", {}).get("content", "")
        return ""


doc_syncer = DocumentSyncer()
