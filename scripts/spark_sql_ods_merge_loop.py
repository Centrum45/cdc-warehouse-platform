from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from warehouse.jobs.merge_ods_snapshot import run_merge
from storage.hdfs_web import HdfsPath, WebHdfsLake, is_hdfs_root


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def binlog_partitions(metadata_path: Path, lake_root: str | Path) -> list[tuple[str, object]]:
    metadata = load_json(metadata_path)
    if is_hdfs_root(lake_root):
        lake = WebHdfsLake(str(lake_root))
        base = lake.root / "ods_binlog" / f"db={metadata['source_database']}" / f"table={metadata['source_table']}"
        partitions: list[tuple[str, object]] = []
        for item in sorted(lake.list_status(base), key=lambda row: row.get("pathSuffix", "")):
            suffix = item.get("pathSuffix", "")
            if not suffix.startswith("dt="):
                continue
            dt = suffix.split("=", 1)[1]
            file_path = base / suffix / "part-00000.jsonl"
            if lake.exists(file_path):
                partitions.append((dt, file_path))
        return partitions
    base = lake_root / "ods_binlog" / f"db={metadata['source_database']}" / f"table={metadata['source_table']}"
    if not base.exists():
        return []
    partitions: list[tuple[str, Path]] = []
    for dt_dir in sorted(base.glob("dt=*")):
        file_path = dt_dir / "part-00000.jsonl"
        if file_path.exists():
            partitions.append((dt_dir.name.split("=", 1)[1], file_path))
    return partitions


def file_signature(path: object) -> dict[str, int | str]:
    if isinstance(path, HdfsPath):
        lake_root = path.value.split("/ods_binlog/", 1)[0]
        lake = WebHdfsLake(lake_root)
        parsed_status = lake.list_status(path.parent)
        match = next((item for item in parsed_status if item.get("pathSuffix") == path.value.rsplit("/", 1)[1]), {})
        return {"path": path.value, "size": int(match.get("length", 0)), "mtime_ns": int(match.get("modificationTime", 0))}
    stat = path.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def checkpoint_key(metadata_path: Path, process_dt: str) -> str:
    return f"{metadata_path.stem}:{process_dt}"


def should_merge(checkpoint: dict[str, Any], metadata_path: Path, process_dt: str, binlog_file: Path) -> bool:
    key = checkpoint_key(metadata_path, process_dt)
    return checkpoint.get(key, {}).get("binlog") != file_signature(binlog_file)


def run_one_merge(
    metadata_path: Path,
    lake_root: str | Path,
    process_dt: str,
    engine: str,
    progress_root: Path,
    max_delay_seconds: int,
) -> str:
    if engine in ("auto", "pyspark"):
        try:
            from spark_runtime.session import has_pyspark
            if has_pyspark():
                from warehouse.jobs.pyspark_ods_merge import run_pyspark_merge
                return f"pyspark:{run_pyspark_merge(str(metadata_path), str(lake_root), process_dt)}"
            if engine == "pyspark":
                raise RuntimeError("pyspark not available")
        except Exception:
            if engine == "pyspark":
                raise

    written = run_merge(metadata_path, lake_root, process_dt, progress_root, max_delay_seconds)
    return "local:" + ",".join(str(path) for path in written)


def run_once(
    metadata_root: Path,
    lake_root: str | Path,
    checkpoint_path: Path,
    engine: str,
    progress_root: Path,
    max_delay_seconds: int,
) -> list[str]:
    checkpoint = load_json(checkpoint_path)
    messages: list[str] = []
    for metadata_path in sorted(metadata_root.glob("*.json")):
        for process_dt, binlog_file in binlog_partitions(metadata_path, lake_root):
            if not should_merge(checkpoint, metadata_path, process_dt, binlog_file):
                continue
            result = run_one_merge(metadata_path, lake_root, process_dt, engine, progress_root, max_delay_seconds)
            key = checkpoint_key(metadata_path, process_dt)
            checkpoint[key] = {
                "binlog": file_signature(binlog_file),
                "engine": result.split(":", 1)[0],
                "merged_at": int(time.time()),
            }
            messages.append(f"{metadata_path.name} dt={process_dt} {result}")
    write_json(checkpoint_path, checkpoint)
    return messages


def run_loop(
    metadata_root: Path,
    lake_root: str | Path,
    checkpoint_path: Path,
    engine: str,
    progress_root: Path,
    max_delay_seconds: int,
    interval_seconds: int,
) -> None:
    while True:
        try:
            messages = run_once(metadata_root, lake_root, checkpoint_path, engine, progress_root, max_delay_seconds)
            if messages:
                for message in messages:
                    print(f"spark-sql-merge {message}", flush=True)
            else:
                print("spark-sql-merge idle", flush=True)
        except Exception as exc:
            print(f"spark-sql-merge error: {exc}", flush=True)
        time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ODS binlog merge as a SparkSQL-style scheduled loop.")
    parser.add_argument("--metadata-root", default="metadata/tables")
    parser.add_argument("--lake-root", default="data/lake")
    parser.add_argument("--checkpoint", default="data/checkpoints/ods_merge_scheduler.json")
    parser.add_argument("--engine", choices=["auto", "pyspark", "local"], default="auto")
    parser.add_argument("--progress-root", default="data/progress")
    parser.add_argument("--max-delay-seconds", type=int, default=999999999)
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if args.once:
        for message in run_once(
            Path(args.metadata_root),
            args.lake_root if is_hdfs_root(args.lake_root) else Path(args.lake_root),
            Path(args.checkpoint),
            args.engine,
            Path(args.progress_root),
            args.max_delay_seconds,
        ):
            print(f"spark-sql-merge {message}")
        return

    run_loop(
        Path(args.metadata_root),
        args.lake_root if is_hdfs_root(args.lake_root) else Path(args.lake_root),
        Path(args.checkpoint),
        args.engine,
        Path(args.progress_root),
        args.max_delay_seconds,
        args.interval_seconds,
    )


if __name__ == "__main__":
    main()
