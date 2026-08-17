"""把自然语言投资理念转换成可验证、可回测的股债金规则。"""

from datetime import datetime, timezone
import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

CYCLES = ("复苏", "过热", "滞胀", "衰退", "中性")
ASSET_KEYS = ("stock", "bond", "gold")


def _parse_json(text):
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.I)
    return json.loads(cleaned)


def _validate_strategy(payload):
    if not isinstance(payload, dict):
        raise ValueError("模型没有返回策略对象")
    raw_weights = payload.get("cycle_weights") or {}
    validated = {}
    for cycle in CYCLES:
        allocation = raw_weights.get(cycle)
        if not isinstance(allocation, dict):
            raise ValueError(f"模型没有给出“{cycle}”配置")
        values = {asset: float(allocation.get(asset, 0)) for asset in ASSET_KEYS}
        if any(value < 0 for value in values.values()):
            raise ValueError(f"“{cycle}”配置包含负权重；当前回测不允许做空")
        total = sum(values.values())
        if total <= 0:
            raise ValueError(f"“{cycle}”配置权重合计为0")
        validated[cycle] = {asset: value / total for asset, value in values.items()}
    return {
        "name": str(payload.get("name") or "自定义投资逻辑")[:80],
        "summary": str(payload.get("summary") or "")[:1200],
        "cycle_weights": validated,
        "assumptions": [str(item)[:300] for item in (payload.get("assumptions") or [])[:8]],
        "interpreted_at": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    }


def interpret_investment_idea(investment_idea):
    idea = str(investment_idea or "").strip()
    if len(idea) < 12:
        raise ValueError("请至少用一句完整的话描述投资思想和配置逻辑")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY，无法解释自然语言策略")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=55.0)
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "你是投资规则翻译器，不负责预测收益。把用户理念转换成仅包含股票、债券、黄金的"
                    "长期多头配置规则。必须返回JSON，字段为name、summary、assumptions、cycle_weights。"
                    "cycle_weights必须完整包含复苏、过热、滞胀、衰退、中性五个键；每个键必须包含"
                    "stock、bond、gold三个非负数。允许原始合计不是1，后端会归一化。"
                    "不能加入现金、个股、期权、杠杆、做空或不存在的数据规则。若用户表述不完整，"
                    "用最少且保守的假设补齐，并写入assumptions。不要输出Markdown。"
                ),
            },
            {"role": "user", "content": idea},
        ],
    )
    content = response.choices[0].message.content
    try:
        return _validate_strategy(_parse_json(content))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeError(f"模型返回的策略结构无法回测：{exc}") from exc
