"""可审计的本地 AI 泡沫观点知识库与轻量级检索器。"""

from collections import Counter
from pathlib import Path
import json
import math
import re

KNOWLEDGE_FILE = Path(__file__).parent / "knowledge" / "ai_bubble_views.json"


def load_knowledge():
    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _tokens(text):
    text = text.lower()
    english = re.findall(r"[a-z][a-z0-9.-]+", text)
    chinese = re.findall(r"[\u4e00-\u9fff]", text)
    chinese += re.findall(r"[\u4e00-\u9fff]{2,4}", text)
    return english + chinese


def _document(entry):
    fields = [
        entry["person"], entry["role"], entry["stance"], entry["summary"],
        *entry["arguments"], *entry["risks"], *entry["indicators"],
    ]
    return " ".join(fields)


def search_knowledge(query, top_k=5, stance=None, person=None):
    """用 BM25 风格相关度检索观点；可按立场或人物过滤。"""
    entries = load_knowledge()
    if stance:
        entries = [item for item in entries if stance in item["stance"]]
    if person:
        entries = [item for item in entries if person.lower() in item["person"].lower()]
    if not entries:
        return []

    docs = [_tokens(_document(item)) for item in entries]
    query_tokens = _tokens(query)
    if not query_tokens:
        return entries[:top_k]
    avg_len = sum(map(len, docs)) / len(docs)
    doc_freq = Counter(token for token in set(query_tokens) for doc in docs if token in doc)
    scored = []
    for entry, doc in zip(entries, docs):
        tf = Counter(doc)
        score = 0.0
        for token in query_tokens:
            n = doc_freq[token]
            idf = math.log(1 + (len(docs) - n + 0.5) / (n + 0.5))
            freq = tf[token]
            score += idf * freq * 2.2 / (freq + 1.2 * (0.25 + 0.75 * len(doc) / avg_len))
        # 人名的直接匹配优先。
        if entry["person"].lower() in query.lower():
            score += 10
        scored.append((score, entry))
    scored.sort(key=lambda pair: (pair[0], pair[1]["date"]), reverse=True)
    positive = [entry for score, entry in scored if score > 0]
    return (positive or [entry for _, entry in scored])[:top_k]


def knowledge_answer_context(query, top_k=5):
    """返回供 Agent 引用的紧凑上下文，保留来源链接。"""
    results = search_knowledge(query, top_k=top_k)
    return {
        "query": query,
        "result_count": len(results),
        "results": [
            {
                "person": item["person"],
                "role": item["role"],
                "date": item["date"],
                "stance": item["stance"],
                "summary": item["summary"],
                "arguments": item["arguments"],
                "risks": item["risks"],
                "indicators": item["indicators"],
                "source_title": item["source_title"],
                "source_url": item["source_url"],
                "confidence": item["confidence"],
            }
            for item in results
        ],
        "coverage_note": "知识库是有来源的观点样本，不代表市场共识；观点日期可能早于当前市场状态。",
    }

