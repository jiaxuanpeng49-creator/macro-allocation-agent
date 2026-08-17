"""一次性为已有新闻归档补录可可靠回算的主题趋势字段。"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from news_archive import archive_daily_report, list_archive_dates, load_archived_report


def main():
    updated = 0
    skipped = 0
    for report_date in reversed(list_archive_dates()):
        report = load_archived_report(report_date)
        if not report or not report.get("articles"):
            skipped += 1
            print(f"跳过 {report_date}：没有可用于可靠回算的标题证据")
            continue
        archive_daily_report(report)
        updated += 1
        print(f"已补录 {report_date}：{len(report.get('articles', []))} 条标题证据")
    print(f"补录完成：更新 {updated} 天，跳过 {skipped} 天")


if __name__ == "__main__":
    main()
