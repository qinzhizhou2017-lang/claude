"""
Lightweight local search engine using jieba for Chinese text segmentation.
Supports keyword search and basic relevance ranking over the document index.
"""

import re
import jieba
from feishu_bot.services.doc_indexer import doc_index
from feishu_bot.utils.logger import logger


class SearchEngine:

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search indexed documents by query string.
        Returns top_k results sorted by relevance score.
        """
        if not query.strip():
            return []

        # Segment query into tokens
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        docs = doc_index.get_all_docs()
        scored = []

        for doc in docs:
            score = self._score_doc(doc, query_tokens, query)
            if score > 0:
                scored.append((score, doc))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored[:top_k]:
            results.append({
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "space_name": doc.get("space_name", ""),
                "obj_type": doc.get("obj_type", ""),
                "content_preview": doc.get("content_preview", "")[:300],
                "score": round(score, 3),
                "updated_at": doc.get("updated_at", ""),
            })
        return results

    def get_latest_docs(self, count: int = 5, doc_type: str = "") -> list[dict]:
        """Get the most recently updated documents."""
        docs = doc_index.get_all_docs()
        if doc_type:
            docs = [d for d in docs if d.get("obj_type") == doc_type]

        docs.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        results = []
        for doc in docs[:count]:
            results.append({
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "space_name": doc.get("space_name", ""),
                "obj_type": doc.get("obj_type", ""),
                "content_preview": doc.get("content_preview", "")[:300],
                "updated_at": doc.get("updated_at", ""),
            })
        return results

    def get_summary(self) -> dict:
        """Get a summary of indexed content."""
        docs = doc_index.get_all_docs()
        type_counts = {}
        spaces = set()
        for doc in docs:
            obj_type = doc.get("obj_type", "unknown")
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            spaces.add(doc.get("space_name", ""))
        return {
            "total_docs": len(docs),
            "type_counts": type_counts,
            "spaces": list(spaces),
        }

    def _tokenize(self, text: str) -> list[str]:
        """Segment text into meaningful tokens using jieba."""
        tokens = jieba.lcut(text)
        # Filter out stopwords and short tokens
        return [
            t.lower() for t in tokens
            if len(t.strip()) > 1 and not t.isspace()
        ]

    def _score_doc(self, doc: dict, query_tokens: list[str],
                   raw_query: str) -> float:
        """Score a document against query tokens."""
        title = doc.get("title", "").lower()
        content = doc.get("content_preview", "").lower()
        full_text = f"{title} {content}"

        score = 0.0
        raw_lower = raw_query.lower()

        # Exact phrase match in title (highest weight)
        if raw_lower in title:
            score += 10.0

        # Exact phrase match in content
        if raw_lower in content:
            score += 5.0

        # Token-level matching
        title_tokens = set(self._tokenize(title))
        content_tokens = set(self._tokenize(content))
        query_set = set(query_tokens)

        # Title token overlap
        title_overlap = query_set & title_tokens
        score += len(title_overlap) * 3.0

        # Content token overlap
        content_overlap = query_set & content_tokens
        score += len(content_overlap) * 1.0

        # Bonus for matching proportion of query tokens
        if query_set:
            all_overlap = title_overlap | content_overlap
            coverage = len(all_overlap) / len(query_set)
            score *= (0.5 + 0.5 * coverage)

        return score


search_engine = SearchEngine()
