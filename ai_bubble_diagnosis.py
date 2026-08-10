"""将人物观点与 Dalio 公开泡沫框架合成为一个统一诊断。"""

from pathlib import Path
import json

from knowledge_base import load_knowledge
from bubble_history import load_bubble_history
from technology_bubbles import ai_historical_conclusion, load_technology_bubbles

DIAGNOSIS_FILE = Path(__file__).parent / "knowledge" / "ai_bubble_diagnosis.json"


def load_diagnosis():
    with DIAGNOSIS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def unified_ai_bubble_diagnosis():
    diagnosis = load_diagnosis()
    views = load_knowledge()
    scores = [item["stance_score"] for item in views]
    diagnosis["expert_synthesis"] = {
        "view_count": len(views),
        "bubble_or_cautious": sum(score <= -1 for score in scores),
        "mixed": sum(score == 0 for score in scores),
        "bullish_or_underinvested": sum(score >= 1 for score in scores),
        "interpretation": "人物观点并非简单投票。投资人更关注估值与流动性，产业CEO更关注真实需求，AI从业者更强调应用层机会；统一结论以可观察指标而非人数多数决定。"
    }
    diagnosis["weighted_indicator_score"] = round(
        sum(item["score"] * item["weight"] for item in diagnosis["indicators"]) / 5 * 100
    )
    return diagnosis


def compact_diagnosis():
    result = unified_ai_bubble_diagnosis()
    keys = ["as_of_date", "model", "stage", "stage_score", "weighted_indicator_score", "confidence", "conclusion", "indicators", "expert_synthesis", "next_stage_triggers", "model_sources", "limitations"]
    compact = {key: result[key] for key in keys}
    history = load_bubble_history()
    compact["score_history"] = history["snapshots"]
    compact["history_methodology"] = history["methodology"]
    analogs = load_technology_bubbles()
    compact["technology_bubble_comparison"] = {
        "methodology": analogs["methodology"],
        "unified_conclusion": ai_historical_conclusion(result["stage_score"]),
        "analogs": [
            {
                "name": item["name"],
                "period": f"{item['start_year']}—{item['end_year']}",
                "capital_acceleration_year": item["capital_acceleration_year"],
                "confidence": item["confidence"],
                "classification": item["classification"],
                "anchors": item["anchors"],
            }
            for item in analogs["bubbles"]
        ],
    }
    return compact
