"""
Local search engine with jieba Chinese tokenization.
Supports keyword + date/folder path matching.
"""

import re
import jieba
from feishu_bot.services.doc_indexer import doc_index


# Map Chinese month names to numbers
_MONTH_MAP = {
    "1月": "1.", "一月": "1.", "2月": "2.", "二月": "2.",
    "3月": "3.", "三月": "3.", "4月": "4.", "四月": "4.",
    "5月": "5.", "五月": "5.", "6月": "6.", "六月": "6.",
    "7月": "7.", "七月": "7.", "8月": "8.", "八月": "8.",
    "9月": "9.", "九月": "9.", "10月": "10.", "十月": "10.",
    "11月": "11.", "十一月": "11.", "12月": "12.", "十二月": "12.",
}


class SearchEngine:

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip():
            return []

        tokens = self._tokenize(query)
        date_filter = self._extract_date_filter(query)

        scored = []
        for doc in doc_index.get_all_docs():
            # If date filter exists, check folder path first
            if date_filter and not self._match_date(doc, date_filter):
                continue

            score = self._score(doc, tokens, query.lower())
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._format(doc) for _, doc in scored[:top_k]]

    def get_latest_docs(self, count: int = 5, doc_type: str = "") -> list[dict]:
        docs = doc_index.get_all_docs()
        if doc_type:
            docs = [d for d in docs if d.get("obj_type") == doc_type]
        docs.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        return [self._format(d) for d in docs[:count]]

    def get_summary(self) -> dict:
        docs = doc_index.get_all_docs()
        type_counts = {}
        spaces = set()
        for doc in docs:
            type_counts[doc.get("obj_type", "unknown")] = (
                type_counts.get(doc.get("obj_type", "unknown"), 0) + 1
            )
            spaces.add(doc.get("space_name", ""))
        return {
            "total_docs": len(docs),
            "type_counts": type_counts,
            "spaces": [s for s in spaces if s],
        }

    def _extract_date_filter(self, query: str) -> str:
        """Extract date pattern from query.

        Recognizes: '2026年1月', '26年1月', '1月份', '26.1', etc.
        Returns a prefix like '26.1.' or '1.' to match against folder paths.
        """
        # Match '2026年1月' or '26年1月'
        m = re.search(r'(\d{2,4})\s*年\s*(\d{1,2})\s*月', query)
        if m:
            year = m.group(1)
            if len(year) == 4:
                year = year[2:]  # 2026 -> 26
            return f"{year}.{m.group(2)}."

        # Match '1月份' or '1月'
        for cn, prefix in _MONTH_MAP.items():
            if cn in query:
                return prefix

        # Match '26.1' pattern directly
        m = re.search(r'(\d{2})\.(\d{1,2})(?:\.|$|\s)', query)
        if m:
            return f"{m.group(1)}.{m.group(2)}."

        return ""

    def _match_date(self, doc: dict, date_filter: str) -> bool:
        """Check if doc's folder path contains the date filter."""
        folder = doc.get("space_name", "").lower()
        title = doc.get("title", "").lower()
        return date_filter in folder or date_filter in title

    def _tokenize(self, text: str) -> list[str]:
        # Filter out date-related tokens to avoid noise
        return [t.lower() for t in jieba.lcut(text)
                if len(t.strip()) > 1 and not re.match(r'^\d{1,4}$', t.strip())]

    def _score(self, doc: dict, tokens: list[str], raw_query: str) -> float:
        title = doc.get("title", "").lower()
        folder = doc.get("space_name", "").lower()
        # Combine title and folder for searching
        full_text = f"{title} {folder}"

        score = 0.0

        # Exact phrase match in title (highest weight)
        if raw_query in title:
            score += 10.0

        # Token overlap
        text_tokens = set(self._tokenize(full_text))
        query_set = set(tokens)

        hits = query_set & text_tokens
        score += len(hits) * 3.0

        # Title-specific hits get extra weight
        title_tokens = set(self._tokenize(title))
        title_hits = query_set & title_tokens
        score += len(title_hits) * 2.0

        # Coverage bonus
        if query_set:
            coverage = len(hits) / len(query_set)
            score *= (0.5 + 0.5 * coverage)

        return score

    def _format(self, doc: dict) -> dict:
        folder = doc.get("space_name", "")
        title = doc.get("title", "")
        display_title = f"{title}"
        if folder:
            display_title = f"{title} | {folder}"

        return {
            "title": display_title,
            "url": doc.get("url", ""),
            "space_name": folder,
            "obj_type": doc.get("obj_type", ""),
            "content_preview": doc.get("content_preview", "")[:300],
            "updated_at": doc.get("updated_at", ""),
        }


search_engine = SearchEngine()
