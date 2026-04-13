"""
Document indexer: sync documents from Feishu Wiki spaces AND Drive folders.
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
    """Sync documents from Wiki spaces AND Drive folders."""

    def __init__(self):
        self._syncing = False
        self._counter = 0  # running count for periodic save

    def sync_all(self):
        if self._syncing:
            return
        self._syncing = True
        self._counter = 0
        start = time.time()
        logger.info("Starting document sync...")

        total = 0
        try:
            # 1. Sync Wiki spaces
            total += self._sync_wiki()

            # 2. Sync Drive folders
            total += self._sync_drive()

            doc_index.save()
            logger.info("Sync completed: %d docs in %.1fs",
                        total, time.time() - start)
        except Exception as e:
            logger.error("Sync failed: %s", e, exc_info=True)
            # Save whatever we got so far
            doc_index.save()
            logger.info("Partial save: %d docs indexed before error", self._counter)
        finally:
            self._syncing = False

    def _tick(self):
        """Increment counter, save every 50 docs."""
        self._counter += 1
        if self._counter % 50 == 0:
            doc_index.save()
            logger.info("Progress: %d docs indexed so far...", self._counter)

    # ── Wiki sync ──

    def _sync_wiki(self) -> int:
        spaces = self._fetch_all_spaces()
        total = 0
        for space in spaces:
            sid = space.get("space_id", "")
            sname = space.get("name", "Unknown")
            logger.info("Syncing wiki space: %s (%s)", sname, sid)
            total += self._sync_wiki_space(sid, sname)
        return total

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

    def _sync_wiki_space(self, space_id: str, space_name: str,
                         parent_node_token: str = "") -> int:
        count = 0
        page_token = ""
        while True:
            data = api_client.list_wiki_nodes(
                space_id, parent_node_token=parent_node_token,
                page_token=page_token,
            )
            if data.get("code") != 0:
                break

            for node in data.get("data", {}).get("items", []):
                node_token = node.get("node_token", "")
                obj_token = node.get("obj_token", "")
                obj_type = node.get("obj_type", "")
                title = node.get("title", "")

                content = ""
                if obj_type in ("doc", "docx"):
                    content = self._fetch_content(obj_token)

                doc_index.upsert(node_token, {
                    "token": node_token,
                    "title": title,
                    "obj_type": obj_type,
                    "source": "wiki",
                    "space_name": space_name,
                    "content_preview": content[:2000],
                    "url": node.get("url", ""),
                    "updated_at": node.get("edit_time", ""),
                    "synced_at": int(time.time()),
                })
                count += 1
                self._tick()

                if node.get("has_child", False):
                    count += self._sync_wiki_space(space_id, space_name, node_token)

            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")
        return count

    # ── Drive folder sync ──

    def _sync_drive(self) -> int:
        folder_tokens = Config.DRIVE_FOLDER_TOKENS
        if not folder_tokens:
            logger.info("No FEISHU_FOLDER_TOKENS configured, skipping drive sync")
            return 0

        total = 0
        for folder_token in folder_tokens:
            logger.info("Syncing drive folder: %s", folder_token)
            total += self._sync_drive_folder(folder_token, folder_name="")
        return total

    def _sync_drive_folder(self, folder_token: str, folder_name: str,
                           depth: int = 0) -> int:
        if depth > 10:  # prevent infinite recursion
            return 0

        count = 0
        page_token = ""
        while True:
            data = api_client.list_drive_files(
                folder_token, page_token=page_token,
            )
            if data.get("code") != 0:
                logger.warning("Failed to list drive folder %s: %s",
                               folder_token, data.get("msg"))
                break

            files = data.get("data", {}).get("files", [])
            for f in files:
                token = f.get("token", "")
                name = f.get("name", "")
                ftype = f.get("type", "")
                url = f.get("url", "")

                # Recurse into subfolders
                if ftype == "folder":
                    sub_name = f"{folder_name}/{name}" if folder_name else name
                    logger.info("  Entering subfolder: %s", sub_name)
                    count += self._sync_drive_folder(token, sub_name, depth + 1)
                    continue

                # Index documents
                content = ""
                if ftype in ("doc", "docx"):
                    content = self._fetch_content(token)

                display_path = f"{folder_name}/{name}" if folder_name else name
                doc_index.upsert(f"drive_{token}", {
                    "token": token,
                    "title": name,
                    "obj_type": ftype,
                    "source": "drive",
                    "space_name": folder_name or "云盘",
                    "content_preview": content[:2000],
                    "url": url,
                    "updated_at": f.get("modified_time", ""),
                    "synced_at": int(time.time()),
                })
                count += 1
                self._tick()

            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")

        return count

    # ── Shared ──

    def _fetch_content(self, document_id: str) -> str:
        data = api_client.get_document_raw_content(document_id)
        if data.get("code") == 0:
            return data.get("data", {}).get("content", "")
        return ""


doc_syncer = DocumentSyncer()
