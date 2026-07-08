from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingestion.bootstrap.mysql_bootstrap import bootstrap_table
from storage.local_lake import LocalLake
from streaming.offline_sink.kafka_to_local_lake import sink_events
from warehouse.jobs.merge_ods_snapshot import run_merge


def replace_ods_binlog(metadata_path: Path, lake_root: Path, event_file: Path) -> list[Path]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    database = metadata["source_database"]
    table = metadata["source_table"]
    partition_column = metadata["partition_column"]
    grouped: dict[str, list[dict]] = defaultdict(list)

    with event_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            if not line.strip():
                continue
            event = json.loads(line)
            dt = str(event["data"][partition_column])[:10]
            grouped[dt].append({"content": event})

    lake = LocalLake(lake_root)
    written: list[Path] = []
    for dt, rows in grouped.items():
        output_path = lake.binlog_partition(database, table, dt) / "part-00000.jsonl"
        lake.write_jsonl(output_path, rows)
        written.append(output_path)
    return written


def replace_ods_snapshot(metadata_path: Path, lake_root: Path, event_file: Path) -> list[Path]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    database = metadata["source_database"]
    table = metadata["source_table"]
    partition_column = metadata["partition_column"]
    columns = [column["name"] for column in metadata["columns"]] + ["dt"]
    grouped: dict[str, list[dict]] = defaultdict(list)

    with event_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            if not line.strip():
                continue
            event = json.loads(line)
            row = {column["name"]: event["data"].get(column["name"]) for column in metadata["columns"]}
            row["dt"] = str(event["data"][partition_column])[:10]
            grouped[row["dt"]].append(row)

    lake = LocalLake(lake_root)
    written: list[Path] = []
    for dt, rows in grouped.items():
        output_path = lake.ods_partition(database, table, dt) / "part-00000.csv"
        lake.write_csv(output_path, rows, columns)
        written.append(output_path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a MySQL table into local lake as Maxwell bootstrap-insert events.")
    parser.add_argument("metadata_path", help="metadata/tables/<db>.<table>.json")
    parser.add_argument("--lake-root", default="data/lake")
    parser.add_argument("--output", default=None)
    parser.add_argument("--progress-root", default="data/progress")
    parser.add_argument("--container", default="cdc-warehouse-mysql")
    parser.add_argument("--user", default=os.environ.get("MYSQL_USER", "root"))
    parser.add_argument("--password", default=os.environ.get("MYSQL_ROOT_PASSWORD", os.environ.get("MYSQL_PASSWORD", "root")))
    parser.add_argument("--merge", action="store_true", help="Run ODS merge after bootstrap sink.")
    parser.add_argument("--replace-binlog", action="store_true", help="Replace ODS binlog partition with bootstrap events instead of append.")
    parser.add_argument("--replace-ods", action="store_true", help="Replace ODS snapshot from current MySQL full data.")
    parser.add_argument("--max-delay-seconds", type=int, default=None)
    args = parser.parse_args()

    metadata_path = Path(args.metadata_path)
    output = Path(args.output) if args.output else Path("data/kafka") / f"bootstrap.{metadata_path.stem}.jsonl"
    event_file = bootstrap_table(metadata_path, output, args.container, args.user, args.password)
    print(f"bootstrap_events: {event_file}")

    if args.replace_binlog:
        written = replace_ods_binlog(metadata_path, Path(args.lake_root), event_file)
    else:
        written = sink_events(event_file, Path(args.lake_root), None, Path(args.progress_root))
    for path in written:
        print(f"ods_binlog: {path}")

    if args.replace_ods:
        for output_path in replace_ods_snapshot(metadata_path, Path(args.lake_root), event_file):
            print(f"ods_replaced: {output_path}")

    if args.merge:
        for path in written:
            partition_name = path.parent.name
            process_dt = partition_name[3:] if partition_name.startswith("dt=") else partition_name
            for output_path in run_merge(metadata_path, Path(args.lake_root), process_dt, Path(args.progress_root), args.max_delay_seconds):
                print(f"ods: {output_path}")


if __name__ == "__main__":
    main()
