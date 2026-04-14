"""
Search engine with Chinese-English term aliases, date parsing, and jieba tokenization.
Designed for a research report library with date-based folder structure.

Folder naming convention:
  - 2025 folders: "month.day" (e.g., "8.15" = August 15)
  - 2026 folders: "year.month.day" (e.g., "26.4.10" = April 10)
"""

import re
import jieba
from feishu_bot.services.doc_indexer import doc_index
from feishu_bot.utils.logger import logger

# ── Chinese → English term aliases ──
# Maps Chinese terms to possible English appearances in PDF filenames
TERM_ALIASES = {
    "高盛": ["goldman", "sachs", "gs"],
    "摩根士丹利": ["morgan stanley", "ms"],
    "大摩": ["morgan stanley", "ms"],
    "摩根大通": ["jpmorgan", "jp morgan", "jpm"],
    "小摩": ["jpmorgan", "jp morgan", "jpm"],
    "美银": ["bofa", "bank of america", "merrill", "baml"],
    "花旗": ["citi", "citigroup"],
    "瑞银": ["ubs"],
    "瑞信": ["credit suisse", "cs"],
    "德银": ["deutsche bank", "db"],
    "巴克莱": ["barclays", "barc"],
    "野村": ["nomura"],
    "贝莱德": ["blackrock", "blk"],
    "桥水": ["bridgewater"],
    "伯恩斯坦": ["bernstein"],
    "麦格理": ["macquarie"],
    "汇丰": ["hsbc"],
    "渣打": ["standard chartered"],
    "法兴": ["societe generale", "socgen"],
    "法巴": ["bnp paribas", "bnp"],
    "富达": ["fidelity"],
    "先锋": ["vanguard"],
    "景顺": ["invesco"],
    "人工智能": ["ai", "artificial intelligence"],
    "新能源": ["new energy", "renewable", "clean energy"],
    "半导体": ["semiconductor", "chip"],
    "芯片": ["chip", "semiconductor"],
    "宏观": ["macro"],
    "固收": ["fixed income", "bond"],
    "策略": ["strategy"],
    "量化": ["quant", "quantitative"],
}

# Stopwords to ignore in search queries (Chinese filler / question words)
STOPWORDS = {
    "的", "了", "吗", "呢", "吧", "啊", "呀", "哦", "嗯",
    "帮", "我", "你", "他", "她", "它",
    "找", "搜", "搜索", "查", "查找", "查询", "看",
    "有", "没有", "什么", "哪些", "哪个", "这个", "那个", "那些",
    "相关", "关于", "给我", "帮我", "能不能", "可以", "可不可以",
    "请", "一下", "看看", "找找", "一些", "所有",
    "份", "篇", "个", "些", "多少", "几", "条",
    "年", "日", "号", "月", "月份",
    "最新", "最近", "近期",
}

# Generic terms that match everything (all docs are research reports)
GENERIC_TERMS = {
    "研报", "报告", "文档", "文件", "资料", "研究", "分析",
    "pdf", "report", "document", "research",
}

# Chinese month name → number
_MONTH_CN = {
    "一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
    "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12,
}


class SearchEngine:

    def search(self, query: str, top_k: int = 30) -> list[dict]:
        """Search documents. Returns up to top_k results."""
        if not query.strip():
            return []

        # 1. Parse date criteria from query
        date_criteria = self._extract_date_criteria(query)

        # 2. Extract meaningful keywords (with alias expansion)
        keywords = self._extract_keywords(query)

        logger.info("Search: date=%s, keywords=%s", date_criteria, keywords)

        # 3. Score each document
        scored = []
        for doc in doc_index.get_all_docs():
            score = self._score_doc(doc, keywords, date_criteria, query.lower())
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [self._format(doc) for _, doc in scored[:top_k]]
        logger.info("Search returned %d results (from %d candidates)",
                     len(results), len(scored))
        return results

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
            t = doc.get("obj_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
            spaces.add(doc.get("space_name", ""))
        return {
            "total_docs": len(docs),
            "type_counts": type_counts,
            "spaces": [s for s in spaces if s],
        }

    # ── Date Extraction ──

    def _extract_date_criteria(self, query: str) -> dict | None:
        """Parse date info from query into structured criteria.

        Returns dict with keys: year (optional), month, day/day_start/day_end.
        Folder naming: 2025 = "month.day", 2026+ = "year.month.day".
        """
        # Range: "7月1日-7月10日", "7月1号到10号", "7月1-10日"
        m = re.search(
            r'(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]?\s*[-—~到至]\s*'
            r'(?:(\d{1,2})\s*月\s*)?(\d{1,2})\s*[日号]?',
            query
        )
        if m:
            return {
                "month": int(m.group(1)),
                "day_start": int(m.group(2)),
                "day_end": int(m.group(4)),
            }

        # Year+Month+Day: "2026年4月10日"
        m = re.search(
            r'(\d{2,4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]', query
        )
        if m:
            y = int(m.group(1))
            if y < 100:
                y += 2000
            return {"year": y, "month": int(m.group(2)), "day": int(m.group(3))}

        # Year+Month: "2026年4月" or "26年4月"
        m = re.search(r'(\d{2,4})\s*年\s*(\d{1,2})\s*月', query)
        if m:
            y = int(m.group(1))
            if y < 100:
                y += 2000
            return {"year": y, "month": int(m.group(2))}

        # Month+Day: "4月10日"
        m = re.search(r'(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]', query)
        if m:
            return {"month": int(m.group(1)), "day": int(m.group(2))}

        # Month only: "8月" or "8月份"
        m = re.search(r'(\d{1,2})\s*月', query)
        if m:
            return {"month": int(m.group(1))}

        # Chinese month names: "八月"
        for cn, num in _MONTH_CN.items():
            if cn in query:
                return {"month": num}

        return None

    def _parse_folder_date(self, folder_name: str):
        """Parse folder name into (year, month, day) tuple.

        '8.15'    → (2025, 8, 15)   -- 2025 folders lack year prefix
        '26.4.10' → (2026, 4, 10)   -- 2026+ folders have year prefix
        """
        first = folder_name.split("/")[0] if folder_name else ""
        parts = first.split(".")
        try:
            if len(parts) == 3:
                return (2000 + int(parts[0]), int(parts[1]), int(parts[2]))
            elif len(parts) == 2:
                return (2025, int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            pass
        return None

    def _doc_matches_date(self, doc: dict, criteria: dict) -> bool:
        """Check if doc's folder matches date criteria."""
        folder = doc.get("space_name", "")
        date = self._parse_folder_date(folder)
        if not date:
            return False

        year, month, day = date

        # Check year if specified
        if "year" in criteria and year != criteria["year"]:
            return False

        # Check month
        if month != criteria.get("month", month):
            return False

        # Check day or day range
        if "day_start" in criteria and "day_end" in criteria:
            if not (criteria["day_start"] <= day <= criteria["day_end"]):
                return False
        elif "day" in criteria:
            if day != criteria["day"]:
                return False

        return True

    # ── Keyword Extraction ──

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords from query with alias expansion.

        1. Jieba tokenization
        2. Remove stopwords, generic terms, pure numbers
        3. Scan raw query for TERM_ALIASES keys (handles jieba mis-splits)
        4. Expand all Chinese terms to their English aliases
        """
        tokens = jieba.lcut(query)

        keywords = []
        for t in tokens:
            t = t.strip()
            if not t:
                continue
            if t in STOPWORDS:
                continue
            if t.lower() in GENERIC_TERMS or t in GENERIC_TERMS:
                continue
            if re.match(r'^\d+$', t):
                continue
            keywords.append(t.lower())

        # Scan raw query for alias keys (catches terms jieba might split)
        query_lower = query.lower()
        for chinese_term, english_aliases in TERM_ALIASES.items():
            if chinese_term in query_lower and chinese_term not in keywords:
                keywords.append(chinese_term)

        # Expand: add English aliases for any matched Chinese terms
        expanded = list(keywords)
        for kw in keywords:
            if kw in TERM_ALIASES:
                for alias in TERM_ALIASES[kw]:
                    if alias not in expanded:
                        expanded.append(alias)

        # Deduplicate while preserving order
        seen = set()
        result = []
        for kw in expanded:
            if kw not in seen:
                seen.add(kw)
                result.append(kw)

        return result

    # ── Scoring ──

    def _score_doc(self, doc: dict, keywords: list[str],
                   date_criteria: dict | None, raw_query: str) -> float:
        """Score a document against the query.

        Rules:
        - If date_criteria exists, doc MUST match the date (hard filter)
        - If keywords exist, doc MUST match ≥1 keyword in title (hard filter)
        - Score is based on number of keyword hits
        """
        title = doc.get("title", "").lower()
        folder = doc.get("space_name", "").lower()

        # Date filter: must match if specified
        if date_criteria:
            if not self._doc_matches_date(doc, date_criteria):
                return 0.0

        # No keywords → return all date-matched docs (or nothing if no date)
        if not keywords:
            if date_criteria:
                return 1.0
            return 0.0

        # Keyword matching: must match at least one in title
        score = 0.0
        matched_in_title = False

        for kw in keywords:
            if self._keyword_in_text(kw, title):
                score += 5.0
                matched_in_title = True
            elif self._keyword_in_text(kw, folder):
                score += 1.0

        if not matched_in_title:
            return 0.0

        # Bonus: exact query phrase in title
        if raw_query in title:
            score += 10.0

        # Bonus: date criteria matched (already confirmed above)
        if date_criteria:
            score += 3.0

        return score

    def _keyword_in_text(self, keyword: str, text: str) -> bool:
        """Check if keyword appears in text.

        Short ASCII keywords (≤3 chars) use word-boundary matching to avoid
        false positives like 'ai' matching 'bait'.
        Multi-word aliases like 'morgan stanley' also match 'Morgan_Stanley'.
        """
        if not keyword or not text:
            return False

        # Short ASCII-only keywords: require word boundaries
        if len(keyword) <= 3 and keyword.isascii() and keyword.isalpha():
            pattern = (r'(?<![a-zA-Z])'
                       + re.escape(keyword)
                       + r'(?![a-zA-Z])')
            return bool(re.search(pattern, text, re.IGNORECASE))

        # Multi-word: also match with common separators (_-) between words
        if " " in keyword:
            parts = keyword.split()
            pattern = r'[\s_\-]*'.join(re.escape(p) for p in parts)
            return bool(re.search(pattern, text, re.IGNORECASE))

        return keyword in text

    # ── Formatting ──

    def _format(self, doc: dict) -> dict:
        folder = doc.get("space_name", "")
        title = doc.get("title", "")
        display_title = f"{title} | {folder}" if folder else title

        return {
            "title": display_title,
            "url": doc.get("url", ""),
            "space_name": folder,
            "obj_type": doc.get("obj_type", ""),
            "content_preview": doc.get("content_preview", "")[:300],
            "updated_at": doc.get("updated_at", ""),
        }


search_engine = SearchEngine()
