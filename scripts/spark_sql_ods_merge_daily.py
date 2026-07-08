from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.spark_sql_ods_merge_loop import binlog_partitions, run_one_merge
from storage.hdfs_web import is_hdfs_root


def default_biz_dt() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def run_daily_merge(
    metadata_root: Path,
    lake_root: str | Path,
    biz_dt: str,
    engine: str,
    progress_root: Path,
    max_delay_seconds: int,
) -> list[str]:
    messages: list[str] = []
    for metadata_path in sorted(metadata_root.glob("*.json")):
        available_dt = {process_dt for process_dt, _ in binlog_partitions(metadata_path, lake_root)}
        if biz_dt not in available_dt:
            messages.append(f"{metadata_path.name} dt={biz_dt} skipped:no_binlog_partition")
            continue
        result = run_one_merge(metadata_path, lake_root, biz_dt, engine, progress_root, max_delay_seconds)
        messages.append(f"{metadata_path.name} dt={biz_dt} {result}")
    return messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily offline ODS merge task. Default biz_dt is yesterday.")
    parser.add_argument("--metadata-root", default="metadata/tables")
    parser.add_argument("--lake-root", default="data/lake")
    parser.add_argument("--biz-dt", default=default_biz_dt())
    parser.add_argument("--engine", choices=["auto", "pyspark", "local"], default="pyspark")
    parser.add_argument("--progress-root", default="data/progress")
    parser.add_argument("--max-delay-seconds", type=int, default=9999999999)
    args = parser.parse_args()

    for message in run_daily_merge(
        Path(args.metadata_root),
        args.lake_root if is_hdfs_root(args.lake_root) else Path(args.lake_root),
        args.biz_dt,
        args.engine,
        Path(args.progress_root),
        args.max_delay_seconds,
    ):
        print(f"spark-sql-daily-merge {message}", flush=True)


if __name__ == "__main__":
    main()
