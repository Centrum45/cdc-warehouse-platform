from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from storage.hdfs_web import WebHdfsLake, is_hdfs_root
from warehouse.jobs.merge_ods_snapshot import run_merge
from warehouse.metadata_loader import load_table_metadata

DEFAULT_HDFS_ROOT = "hdfs://localhost:8020/warehouse"


def default_biz_dt() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def binlog_partitions(metadata_path: Path, lake_root: str | Path) -> list[str]:
    metadata = load_table_metadata(metadata_path)
    if is_hdfs_root(lake_root):
        lake = WebHdfsLake(str(lake_root))
        base = lake.root / "ods_binlog" / f"db={metadata['source_database']}" / f"table={metadata['source_table']}"
        partitions: list[str] = []
        for item in sorted(lake.list_status(base), key=lambda row: row.get("pathSuffix", "")):
            suffix = item.get("pathSuffix", "")
            if not suffix.startswith("dt="):
                continue
            partition_path = base / suffix
            has_parquet = any(
                child.get("type") == "FILE"
                and child.get("pathSuffix", "").startswith("part-")
                and child.get("pathSuffix", "").endswith(".parquet")
                for child in lake.list_status(partition_path)
            )
            if has_parquet:
                partitions.append(suffix.split("=", 1)[1])
        return partitions

    base = Path(lake_root) / "ods_binlog" / f"db={metadata['source_database']}" / f"table={metadata['source_table']}"
    if not base.exists():
        return []
    return [
        dt_dir.name.split("=", 1)[1]
        for dt_dir in sorted(base.glob("dt=*"))
        if any(dt_dir.glob("part-*.parquet"))
    ]


def run_one_merge(
    metadata_path: Path,
    lake_root: str | Path,
    process_dt: str,
    engine: str,
    progress_root: Path,
    max_delay_seconds: int,
    audit_root: str | None = "data/ops/merge_audit",
    backup_root: str | None = None,
) -> str:
    if engine in ("auto", "pyspark"):
        try:
            from spark_runtime.session import has_pyspark
            if has_pyspark():
                from warehouse.jobs.pyspark_ods_merge import run_pyspark_merge
                return f"pyspark:{run_pyspark_merge(str(metadata_path), str(lake_root), process_dt, audit_root=audit_root, backup_root=backup_root)}"
            if engine == "pyspark":
                raise RuntimeError("pyspark not available")
        except Exception:
            if engine == "pyspark":
                raise

    written = run_merge(metadata_path, Path(lake_root), process_dt, progress_root, max_delay_seconds)
    return "local:" + ",".join(str(path) for path in written)


def run_daily_merge(
    metadata_root: Path,
    lake_root: str | Path,
    biz_dt: str,
    engine: str,
    progress_root: Path,
    max_delay_seconds: int,
    audit_root: str | None = "data/ops/merge_audit",
    backup_root: str | None = None,
) -> list[str]:
    messages: list[str] = []
    for metadata_path in sorted(metadata_root.glob("*.json")):
        available_dt = set(binlog_partitions(metadata_path, lake_root))
        if biz_dt not in available_dt:
            messages.append(f"{metadata_path.name} dt={biz_dt} skipped:no_binlog_partition")
            continue
        result = run_one_merge(metadata_path, lake_root, biz_dt, engine, progress_root, max_delay_seconds, audit_root, backup_root)
        messages.append(f"{metadata_path.name} dt={biz_dt} {result}")
    return messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily offline ODS merge task. Default biz_dt is yesterday.")
    parser.add_argument("--metadata-root", default="metadata/tables")
    parser.add_argument("--lake-root", default=DEFAULT_HDFS_ROOT)
    parser.add_argument("--biz-dt", default=default_biz_dt())
    parser.add_argument("--engine", choices=["auto", "pyspark", "local"], default="pyspark")
    parser.add_argument("--progress-root", default="data/progress")
    parser.add_argument("--max-delay-seconds", type=int, default=9999999999)
    parser.add_argument("--audit-root", default="data/ops/merge_audit")
    parser.add_argument("--backup-root", default=None)
    args = parser.parse_args()

    for message in run_daily_merge(
        Path(args.metadata_root),
        args.lake_root if is_hdfs_root(args.lake_root) else Path(args.lake_root),
        args.biz_dt,
        args.engine,
        Path(args.progress_root),
        args.max_delay_seconds,
        args.audit_root,
        args.backup_root,
    ):
        print(f"spark-sql-daily-merge {message}", flush=True)


if __name__ == "__main__":
    main()
