"""实时新闻抓取、规则分类，以及资产与经济周期影响聚合。"""

from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os
import re
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from openai import OpenAI


NEWS_FILE = Path(__file__).parent / "data" / "news_intelligence.json"
GOOGLE_NEWS_URL = "https://news.google.com/rss/search"
NEWSAPI_URL = "https://newsapi.org/v2/everything"
USER_AGENT = "MacroAllocationResearchAgent/1.0"

load_dotenv()

RSS_QUERIES = [
    ("AI与科技", '("artificial intelligence" OR AI) (investment OR earnings OR chips OR datacenter) when:2d'),
    ("宏观经济", '("Federal Reserve" OR inflation OR jobs OR GDP OR recession OR tariffs) economy when:2d'),
    ("市场与地缘", '(oil OR gold OR bonds OR stocks OR geopolitics OR trade) markets when:2d'),
]

CATEGORY_RULES = {
    "AI与科技": ["ai", "artificial intelligence", "chip*", "gpu*", "semiconductor*", "data center", "datacenter*", "cloud", "model*", "openai", "nvidia"],
    "货币政策": ["federal reserve", "fed ", "interest rate", "rate cut", "rate hike", "central bank", "yield", "powell", "monetary"],
    "增长与就业": ["gdp", "growth", "recession", "jobs", "employment", "unemployment", "payroll", "layoff", "consumer", "retail sales"],
    "通胀与大宗商品": ["inflation", "cpi", "ppi", "oil", "energy", "commodity", "gold", "wage", "price pressure"],
    "地缘政治与贸易": ["war", "sanction*", "tariff*", "trade", "geopolit*", "conflict*", "export control", "china", "russia", "middle east"],
    "企业盈利与资本开支": ["earnings", "revenue", "profit", "guidance", "capex", "capital expenditure", "investment", "cash flow", "margin"],
}

POSITIVE_GROWTH = ["beats", "accelerat*", "record revenue", "revenue growth", "sales growth", "strong demand", "buoyant demand", "productivity", "adoption", "expansion", "soft landing"]
NEGATIVE_GROWTH = ["misses", "slowdown", "recession", "layoff*", "default*", "cuts forecast", "weak demand", "weak jobs", "jobs data weak", "contraction", "downgrade"]
INFLATION_UP = ["inflation rises", "price pressure", "tariff", "oil surge", "energy shock", "wage pressure", "supply disruption"]
INFLATION_DOWN = ["inflation cool", "disinflation", "oil falls", "price pressure eases", "supply improves"]
EASING = ["rate cut", "easing", "dovish", "lower rates", "liquidity injection"]
TIGHTENING = ["rate hike", "hawkish", "higher for longer", "yield rises", "tightening"]
BUBBLE_UP = ["bubble", "overvalued", "speculation", "capex surge", "investment surge", "investment boom", "debt financing", "spending boom", "capacity glut", "overbuild", "cash burn", "retail investors", "meme stocks"]
BUBBLE_DOWN = ["ai revenue", "monetization", "productivity gain", "utilization rises", "profitable", "return on investment", "cost falls", "demand exceeds"]

BLOCKED_SOURCES = [
    "indexbox", "openpr", "ein presswire", "globe newswire", "marketsandmarkets",
    "research and markets", "business wire", "pr newswire", "accesswire",
]


def _contains(text, terms):
    count = 0
    for raw_term in terms:
        term = raw_term.strip().lower()
        if term.endswith("*"):
            matched = re.search(rf"\b{re.escape(term[:-1])}\w*", text)
        elif " " in term:
            matched = term in text
        else:
            matched = re.search(rf"\b{re.escape(term)}\b", text)
        count += bool(matched)
    return count


def _iso_time(value):
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except ValueError:
            return datetime.now(timezone.utc).isoformat()


def _request_json(url, headers=None, timeout=18):
    request = Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _request_text(url, timeout=18):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _fetch_newsapi(api_key, hours=48):
    query = '(AI OR "artificial intelligence" OR inflation OR recession OR "Federal Reserve" OR geopolitics OR tariffs)'
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "from": (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(),
        "apiKey": api_key,
    }
    payload = _request_json(f"{NEWSAPI_URL}?{urlencode(params)}")
    if payload.get("status") != "ok":
        raise RuntimeError(payload.get("message", "NewsAPI returned an error"))
    return [
        {
            "title": item.get("title") or "",
            "url": item.get("url") or "",
            "source": (item.get("source") or {}).get("name") or "NewsAPI",
            "published_at": _iso_time(item.get("publishedAt")),
        }
        for item in payload.get("articles", [])
    ], "NewsAPI", "https://newsapi.org/"


def _fetch_google_rss():
    articles = []
    for query_theme, query in RSS_QUERIES:
        params = urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
        root = ET.fromstring(_request_text(f"{GOOGLE_NEWS_URL}?{params}"))
        for item in root.findall("./channel/item")[:35]:
            source = item.find("source")
            articles.append({
                "title": (item.findtext("title") or "").strip(),
                "url": (item.findtext("link") or "").strip(),
                "source": (source.text if source is not None else "Google News") or "Google News",
                "published_at": _iso_time(item.findtext("pubDate")),
                "query_theme": query_theme,
            })
    return articles, "Google News RSS", "https://news.google.com/"


def _category(text):
    scores = {name: _contains(text, terms) for name, terms in CATEGORY_RULES.items()}
    return max(scores, key=scores.get) if max(scores.values(), default=0) else "其他宏观新闻"


def _analyze_article(article):
    text = f" {article['title'].lower()} "
    growth = _contains(text, POSITIVE_GROWTH) - _contains(text, NEGATIVE_GROWTH)
    inflation = _contains(text, INFLATION_UP) - _contains(text, INFLATION_DOWN)
    easing = _contains(text, EASING)
    tightening = _contains(text, TIGHTENING)
    bubble = _contains(text, BUBBLE_UP) - _contains(text, BUBBLE_DOWN)
    risk = _contains(text, ["war", "sanction", "default", "crisis", "conflict", "tariff", "export control"])

    gold_up = _contains(text, ["gold surge*", "gold rally", "gold rises", "gold jumps"])
    gold_down = _contains(text, ["gold falls", "gold drops", "gold slides"])
    stock = 2 * growth + 2 * easing - tightening - risk - max(bubble, 0)
    bond = -growth + 2 * easing - 2 * tightening - 2 * inflation + risk
    gold = inflation + risk + easing - tightening + max(bubble, 0) + 2 * gold_up - 2 * gold_down
    impacts = {"股票": max(-3, min(3, stock)), "债券": max(-3, min(3, bond)), "黄金": max(-3, min(3, gold))}
    strongest = max(impacts, key=lambda asset: abs(impacts[asset]))
    direction = "利多" if impacts[strongest] > 0 else "利空" if impacts[strongest] < 0 else "中性"
    article.update({
        "category": _category(text) if _category(text) != "其他宏观新闻" else article.get("query_theme", "其他宏观新闻"),
        "asset_impact": impacts,
        "growth_impact": max(-2, min(2, growth - risk)),
        "inflation_impact": max(-2, min(2, inflation)),
        "bubble_impact": max(-2, min(2, bubble)),
        "impact_summary": f"对{strongest}{direction}；增长影响 {growth - risk:+d}，通胀影响 {inflation:+d}",
        "relevance_score": min(10, 3 + sum(abs(value) for value in impacts.values()) + abs(bubble)),
    })
    return article


def _deduplicate(articles):
    seen = set()
    results = []
    for item in articles:
        if any(blocked in item.get("source", "").lower() for blocked in BLOCKED_SOURCES):
            continue
        normalized = re.sub(r"\W+", " ", item.get("title", "").lower()).strip()
        key = " ".join(normalized.split()[:12])
        if not key or key in seen or not item.get("url"):
            continue
        seen.add(key)
        results.append(item)
    return results


def _aggregate(articles, provider, source_url):
    category_counts = Counter(item["category"] for item in articles)
    weight_total = sum(max(1, item["relevance_score"]) for item in articles) or 1
    asset_impact = {
        asset: round(sum(item["asset_impact"][asset] * item["relevance_score"] for item in articles) / weight_total, 2)
        for asset in ["股票", "债券", "黄金"]
    }
    growth = round(sum(item["growth_impact"] * item["relevance_score"] for item in articles) / weight_total, 2)
    inflation = round(sum(item["inflation_impact"] * item["relevance_score"] for item in articles) / weight_total, 2)
    bubble = round(sum(item["bubble_impact"] * item["relevance_score"] for item in articles) / weight_total, 2)
    dominant = category_counts.most_common(1)[0][0] if category_counts else "暂无"
    cycle = "增长升温" if growth > 0.25 else "增长降温" if growth < -0.25 else "增长信号中性"
    price = "通胀升温" if inflation > 0.25 else "通胀降温" if inflation < -0.25 else "通胀信号中性"
    bubble_drivers = [item["title"] for item in sorted(articles, key=lambda item: (abs(item["bubble_impact"]), item["relevance_score"]), reverse=True) if item["bubble_impact"]][:4]
    return {
        "as_of_date": datetime.now(timezone.utc).date().isoformat(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "source_url": source_url,
        "news_count": len(articles),
        "category_counts": dict(category_counts),
        "asset_impact": asset_impact,
        "cycle_impact": {"growth": growth, "inflation": inflation, "interpretation": f"{cycle}；{price}"},
        "bubble_pressure": bubble,
        "bubble_summary": "新闻显示泡沫压力上升。" if bubble > 0.25 else "新闻显示盈利兑现有助于消化泡沫压力。" if bubble < -0.25 else "当日新闻尚未显著改变泡沫判断。",
        "bubble_drivers": bubble_drivers,
        "summary": f"本次聚合 {len(articles)} 条新闻，主导主题为“{dominant}”；{cycle}，{price}。",
        "articles": sorted(articles, key=lambda item: (item["relevance_score"], item["published_at"]), reverse=True)[:60],
        "limitations": [
            "资产与周期影响由可审计关键词规则生成，不等同于因果推断或交易建议。",
            "RSS只保存标题、来源、时间和链接；未抓取或复制新闻正文。",
            "突发事件可能在多家媒体重复出现，系统已按标题去重但不能保证完全消除重复。",
        ],
    }


def load_news_intelligence():
    if not NEWS_FILE.exists():
        return None
    with NEWS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def refresh_news_intelligence(force=False, max_age_hours=6):
    cached = load_news_intelligence()
    if cached and not force:
        fetched = datetime.fromisoformat(cached["fetched_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - fetched < timedelta(hours=max_age_hours):
            return cached

    try:
        api_key = os.getenv("NEWSAPI_KEY")
        raw, provider, source_url = _fetch_newsapi(api_key) if api_key else _fetch_google_rss()
        analyzed = [_analyze_article(item) for item in _deduplicate(raw)]
        report = _aggregate(analyzed, provider, source_url)
        with NEWS_FILE.open("w", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
        return report
    except Exception as exc:
        if cached:
            cached["stale"] = True
            cached["refresh_error"] = str(exc)
            return cached
        raise


def generate_deepseek_news_analysis(report=None, max_articles=24):
    """让DeepSeek基于规则底稿与精选标题生成可审计的综合研判，并写回缓存。"""
    report = report or load_news_intelligence()
    if not report:
        raise RuntimeError("暂无新闻快照，请先抓取最新新闻。")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY，请检查 .env 文件。")

    selected = report.get("articles", [])[:max_articles]
    evidence = [
        {
            "title": item["title"],
            "source": item["source"],
            "published_at": item["published_at"],
            "category": item["category"],
            "rule_asset_impact": item["asset_impact"],
            "url": item["url"],
        }
        for item in selected
    ]
    payload = {
        "snapshot_time": report["fetched_at"],
        "provider": report["provider"],
        "rule_summary": report["summary"],
        "rule_asset_impact": report["asset_impact"],
        "rule_cycle_impact": report["cycle_impact"],
        "rule_ai_bubble_pressure": report["bubble_pressure"],
        "category_counts": report["category_counts"],
        "evidence_titles": evidence,
    }
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=50.0)
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是宏观资产配置研究员。只能依据提供的新闻标题、来源、时间、链接与透明规则底稿进行综合研判。"
                    "不要假装读过正文，不要把相关性写成已证明的因果关系，不要给出个股买卖指令。"
                    "输出简洁中文Markdown，必须依次包含：总判断、主要新闻簇、股票/债券/黄金、经济周期、"
                    "AI泡沫影响、未来24—72小时观察清单、不确定性。要把分散新闻合成为一个结论，并指出相互抵消的信号。"
                ),
            },
            {
                "role": "user",
                "content": "请分析以下新闻快照：\n" + json.dumps(payload, ensure_ascii=False),
            },
        ],
    )
    analysis = (response.choices[0].message.content or "").strip()
    if not analysis:
        raise RuntimeError("DeepSeek 返回了空分析。")
    report["deepseek_analysis"] = analysis
    report["deepseek_analyzed_at"] = datetime.now(timezone.utc).isoformat()
    report["deepseek_model"] = model
    report["deepseek_evidence_count"] = len(selected)
    with NEWS_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    return report


def latest_news_context(top_k=12):
    report = load_news_intelligence()
    if not report:
        return {"status": "暂无新闻快照，请先在每日新闻情报页面执行刷新。"}
    return {
        "as_of_date": report["as_of_date"],
        "fetched_at": report["fetched_at"],
        "provider": report["provider"],
        "summary": report["summary"],
        "asset_impact": report["asset_impact"],
        "cycle_impact": report["cycle_impact"],
        "bubble_pressure": report["bubble_pressure"],
        "deepseek_analysis": report.get("deepseek_analysis"),
        "deepseek_analyzed_at": report.get("deepseek_analyzed_at"),
        "deepseek_model": report.get("deepseek_model"),
        "articles": report["articles"][:top_k],
        "limitations": report["limitations"],
    }
