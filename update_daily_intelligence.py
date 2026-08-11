"""供本地任务或GitHub Actions调用的每日新闻更新入口。"""

from bubble_history import append_news_snapshot
from news_archive import archive_daily_report
from news_intelligence import generate_deepseek_news_analysis, refresh_news_intelligence


if __name__ == "__main__":
    report = refresh_news_intelligence(force=True)
    snapshot = append_news_snapshot(report)
    archive_daily_report(report)
    try:
        report = generate_deepseek_news_analysis(report)
        archive_daily_report(report)
        ai_status = f"；DeepSeek综合研判已更新（{report['deepseek_model']}）"
    except Exception as exc:
        ai_status = f"；DeepSeek综合研判跳过：{exc}"
    print(f"更新完成：{report['news_count']}条新闻；泡沫分数 {snapshot['score']}/100{ai_status}")
