"""
Local search engine with jieba Chinese tokenization.
"""

import jieba
from feishu_bot.services.doc_indexer import doc_index


class SearchEngine:

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip():
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scored = []
        for doc in doc_index.get_all_docs():
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

    def _tokenize(self, text: str) -> list[str]:
        return [t.lower() for t in jieba.lcut(text) if len(t.strip()) > 1]

    def _score(self, doc: dict, tokens: list[str], raw_query: str) -> float:
        title = doc.get("title", "").lower()
        content = doc.get("content_preview", "").lower()

        score = 0.0

        # Exact phrase match (highest weight)
        if raw_query in title:
            score += 10.0
        if raw_query in content:
            score += 5.0

        # Token overlap
        title_tokens = set(self._tokenize(title))
        content_tokens = set(self._tokenize(content))
        query_set = set(tokens)

        title_hits = query_set & title_tokens
        content_hits = query_set & content_tokens
        score += len(title_hits) * 3.0
        score += len(content_hits) * 1.0

        # Coverage bonus
        if query_set:
            coverage = len(title_hits | content_hits) / len(query_set)
            score *= (0.5 + 0.5 * coverage)

        return score

    def _format(self, doc: dict) -> dict:
        return {
            "title": doc.get("title", ""),
            "url": doc.get("url", ""),
            "space_name": doc.get("space_name", ""),
            "obj_type": doc.get("obj_type", ""),
            "content_preview": doc.get("content_preview", "")[:300],
            "updated_at": doc.get("updated_at", ""),
        }


search_engine = SearchEngine()
