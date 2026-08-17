"""供本地任务或GitHub Actions调用的每日新闻更新入口。"""

import os
import subprocess

from bubble_history import append_news_snapshot
from news_archive import archive_daily_report, list_reports_needing_analysis
from news_intelligence import (
    generate_deepseek_news_analysis,
    load_news_intelligence,
    refresh_news_intelligence,
)


if __name__ == "__main__":
    print("开始每日情报更新")
    # Actions 每次从干净环境启动。先把仓库里上一期的缓存归档，确保
    # SQLite 首次启用时也不会丢掉切换日前的历史记录。
    previous_report = load_news_intelligence()
    if previous_report:
        previous_date = archive_daily_report(previous_report)
        print(f"已有快照归档完成：{previous_date}")

    report = refresh_news_intelligence(force=True)
    if report.get("stale"):
        print(f"新闻抓取未获得新数据，保留缓存日期：{report.get('as_of_date')}")
    else:
        print(f"新闻抓取完成：{report['news_count']} 条有效新闻")
    snapshot = append_news_snapshot(report)
    saved_date = archive_daily_report(report)
    print(f"趋势历史数据保存完成；保存日期：{saved_date}")
    try:
        report = generate_deepseek_news_analysis(report)
        saved_date = archive_daily_report(report)
        print(f"AI分析完成；综合研判与趋势字段已更新：{saved_date}")
        ai_status = f"；DeepSeek综合研判已更新（{report['deepseek_model']}）"
    except Exception as exc:
        print(f"AI分析失败：{exc}；保留已保存的透明规则评分，不写入伪造的零分记录")
        ai_status = f"；DeepSeek综合研判跳过：{exc}"

    backfilled = 0
    if os.getenv("DEEPSEEK_API_KEY"):
        for historical_report in list_reports_needing_analysis(limit=7):
            if historical_report["as_of_date"] == report.get("as_of_date"):
                continue
            try:
                historical_report = generate_deepseek_news_analysis(
                    historical_report,
                    persist_cache=False,
                )
                archive_daily_report(historical_report)
                backfilled += 1
            except Exception as exc:
                print(f"历史研判补齐失败 {historical_report['as_of_date']}：{exc}")

    # 兼容已经在线运行的旧工作流：预先暂存数据库文件，后续工作流的
    # git commit 会自动把它一并提交，无需等待 workflow 文件同步。
    if os.getenv("GITHUB_ACTIONS") == "true":
        subprocess.run(
            ["git", "add", "data/news_archive.sqlite3"],
            check=True,
        )
    print(
        f"任务执行成功：{report['news_count']}条新闻；泡沫分数 "
        f"{snapshot['score']}/100{ai_status}；补齐历史研判 {backfilled} 天"
    )
