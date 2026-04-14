"""
Document indexer: sync documents from Feishu Wiki spaces AND Drive folders.
Optimization: only index titles/metadata during sync (fast).
"""

import json
import os
import time
import threading
from feishu_bot.config import Config
from feishu_bot.core.api_client import api_client
from feishu_bot.utils.logger import logger


class DocumentIndex:
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

    def upsert(self, token, doc_info):
        with self._lock:
            self._docs[token] = doc_info

    def get_all_docs(self):
        with self._lock:
            return list(self._docs.values())

    @property
    def count(self):
        with self._lock:
            return len(self._docs)


doc_index = DocumentIndex()


class DocumentSyncer:
    def __init__(self):
        self._syncing = False
        self._counter = 0
        self._folder_counter = 0
        self._visited_folders = set()  # Prevent re-scanning same folder

    def sync_all(self):
        if self._syncing:
            return
        self._syncing = True
        self._counter = 0
        self._folder_counter = 0
        self._visited_folders = set()
        start = time.time()
        logger.info("Starting document sync (metadata only)...")
        total = 0
        try:
            total += self._sync_wiki()
            total += self._sync_drive()
            doc_index.save()
            elapsed = time.time() - start
            logger.info("=" * 50)
            logger.info("  Sync completed!")
            logger.info("  Documents indexed: %d (unique)", total)
            logger.info("  Folders scanned: %d", self._folder_counter)
            logger.info("  Duplicate folders skipped: %d",
                        len(self._visited_folders) - self._folder_counter
                        if len(self._visited_folders) > self._folder_counter else 0)
            logger.info("  Time: %.1f seconds", elapsed)
            logger.info("=" * 50)
        except Exception as e:
            logger.error("Sync failed: %s", e, exc_info=True)
            doc_index.save()
        finally:
            self._syncing = False

    # ── Wiki sync ──

    def _sync_wiki(self):
        spaces = []
        page_token = ""
        while True:
            data = api_client.list_wiki_spaces(page_token=page_token)
            if data.get("code") != 0:
                break
            items = data.get("data", {}).get("items", [])
            spaces.extend(items)
            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")
        total = 0
        for space in spaces:
            sid = space.get("space_id", "")
            sname = space.get("name", "Unknown")
            total += self._sync_wiki_space(sid, sname)
        return total

    def _sync_wiki_space(self, space_id, space_name, parent_node_token=""):
        count = 0
        page_token = ""
        while True:
            data = api_client.list_wiki_nodes(
                space_id, parent_node_token=parent_node_token,
                page_token=page_token)
            if data.get("code") != 0:
                break
            for node in data.get("data", {}).get("items", []):
                node_token = node.get("node_token", "")
                doc_index.upsert(node_token, {
                    "token": node_token, "title": node.get("title", ""),
                    "obj_type": node.get("obj_type", ""), "source": "wiki",
                    "space_name": space_name, "content_preview": "",
                    "url": node.get("url", ""),
                    "updated_at": node.get("edit_time", ""),
                    "synced_at": int(time.time()),
                })
                count += 1
                if node.get("has_child", False):
                    count += self._sync_wiki_space(space_id, space_name, node_token)
            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data["data"].get("page_token", "")
        return count

    # ── Drive folder sync ──

    def _sync_drive(self):
        folder_tokens = Config.DRIVE_FOLDER_TOKENS
        if not folder_tokens:
            return 0
        total = 0
        for ft in folder_tokens:
            logger.info("Syncing drive folder: %s", ft)
            total += self._sync_drive_folder(ft, "")
        return total

    def _sync_drive_folder(self, folder_token, folder_name, depth=0):
        if depth > 10:
            return 0

        # Skip already-visited folders (prevent circular scanning)
        if folder_token in self._visited_folders:
            logger.info("  SKIP already visited folder: %s (%s)", folder_name, folder_token[:8])
            return 0
        self._visited_folders.add(folder_token)

        self._folder_counter += 1
        count = 0
        page_num = 0
        page_token = ""

        while True:
            page_num += 1
            data = api_client.list_drive_files(folder_token, page_token=page_token)

            if data.get("code") != 0:
                logger.warning("Failed to list folder %s (page %d): %s",
                               folder_token[:8], page_num, data.get("msg"))
                break

            files = data.get("data", {}).get("files", [])
            has_more = data.get("data", {}).get("has_more", False)
            # Feishu Drive API uses "next_page_token", other APIs use "page_token"
            next_token = (data.get("data", {}).get("next_page_token", "")
                          or data.get("data", {}).get("page_token", ""))

            logger.info("  [d=%d] %s: page %d got %d items, has_more=%s",
                        depth, folder_name or "ROOT", page_num, len(files), has_more)

            for f in files:
                token = f.get("token", "")
                name = f.get("name", "")
                ftype = f.get("type", "")
                url = f.get("url", "")

                if ftype == "folder":
                    sub = f"{folder_name}/{name}" if folder_name else name
                    count += self._sync_drive_folder(token, sub, depth + 1)
                    continue

                # Index file
                doc_index.upsert(f"drive_{token}", {
                    "token": token, "title": name, "obj_type": ftype,
                    "source": "drive", "space_name": folder_name or "云盘",
                    "content_preview": "", "url": url,
                    "updated_at": f.get("modified_time", ""),
                    "synced_at": int(time.time()),
                })
                count += 1
                self._counter += 1
                if self._counter % 500 == 0:
                    doc_index.save()
                    logger.info("Progress: %d unique docs indexed...", doc_index.count)

            if not has_more:
                break
            if not next_token:
                logger.warning("  has_more=True but no page_token! Stopping pagination.")
                break
            page_token = next_token

        return count


doc_syncer = DocumentSyncer()
