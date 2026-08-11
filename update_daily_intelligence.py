"""供本地任务或GitHub Actions调用的每日新闻更新入口。"""

import os
import subprocess

from bubble_history import append_news_snapshot
from news_archive import archive_daily_report
from news_intelligence import (
    generate_deepseek_news_analysis,
    load_news_intelligence,
    refresh_news_intelligence,
)


if __name__ == "__main__":
    # Actions 每次从干净环境启动。先把仓库里上一期的缓存归档，确保
    # SQLite 首次启用时也不会丢掉切换日前的历史记录。
    previous_report = load_news_intelligence()
    if previous_report:
        archive_daily_report(previous_report)

    report = refresh_news_intelligence(force=True)
    snapshot = append_news_snapshot(report)
    archive_daily_report(report)
    try:
        report = generate_deepseek_news_analysis(report)
        archive_daily_report(report)
        ai_status = f"；DeepSeek综合研判已更新（{report['deepseek_model']}）"
    except Exception as exc:
        ai_status = f"；DeepSeek综合研判跳过：{exc}"

    # 兼容已经在线运行的旧工作流：预先暂存数据库文件，后续工作流的
    # git commit 会自动把它一并提交，无需等待 workflow 文件同步。
    if os.getenv("GITHUB_ACTIONS") == "true":
        subprocess.run(
            ["git", "add", "data/news_archive.sqlite3"],
            check=True,
        )
    print(f"更新完成：{report['news_count']}条新闻；泡沫分数 {snapshot['score']}/100{ai_status}")
