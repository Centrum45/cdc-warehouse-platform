from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from storage.local_lake import LocalLake
from storage.binlog_parquet import read_local_parquet, row_to_event
from storage.parquet_table import read_local_parquet as read_table_parquet
from storage.parquet_table import write_local_parquet as write_table_parquet
from warehouse.metadata_loader import load_table_metadata
from warehouse.jobs.delay_gate import can_merge

BINLOG_TYPE_ORDER = {
    "insert": 1,
    "bootstrap-insert": 1,
    "update": 2,
    "delete": 3
}


def normalize_event(event: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    data = event["data"]
    row = {"binlog_type": BINLOG_TYPE_ORDER[event["type"]]}
    for column in metadata["columns"]:
        row[column["name"]] = data.get(column["name"])
    row["dt"] = str(data[metadata["partition_column"]])[:10]
    return row


def row_key(row: dict[str, Any], primary_keys: list[str]) -> tuple[Any, ...]:
    return tuple(str(row[key]) for key in primary_keys)


def merge_rows(binlog_rows: list[dict[str, Any]], old_rows: list[dict[str, Any]], metadata: dict[str, Any]) -> list[dict[str, Any]]:
    primary_keys = metadata["primary_keys"]
    version_column = metadata["version_column"]
    candidates: dict[tuple[Any, ...], dict[str, Any]] = {}

    for row in old_rows:
        candidate = dict(row)
        candidate["binlog_type"] = int(candidate.get("binlog_type", 1))
        candidate[version_column] = int(candidate[version_column])
        candidates[row_key(candidate, primary_keys)] = candidate

    for row in binlog_rows:
        key = row_key(row, primary_keys)
        current = candidates.get(key)
        if current is None:
            candidates[key] = row
            continue
        incoming_order = (int(row[version_column]), int(row["binlog_type"]))
        current_order = (int(current[version_column]), int(current["binlog_type"]))
        if incoming_order > current_order:
            candidates[key] = row

    output_columns = [column["name"] for column in metadata["columns"]] + ["dt"]
    result = []
    for row in candidates.values():
        if int(row["binlog_type"]) == 3:
            continue
        result.append({column: row.get(column) for column in output_columns})
    return sorted(result, key=lambda item: row_key(item, primary_keys))


def run_merge(
    metadata_path: Path,
    lake_root: Path,
    process_dt: str,
    progress_root: Path | None = None,
    max_delay_seconds: int | None = None
) -> list[Path]:
    metadata = load_table_metadata(metadata_path)
    database = metadata["source_database"]
    table = metadata["source_table"]
    if progress_root is not None and max_delay_seconds is not None:
        allowed, reason = can_merge(progress_root, database, table, max_delay_seconds)
        if not allowed:
            raise RuntimeError(f"merge blocked: {reason}")
    lake = LocalLake(lake_root)

    parquet_path = lake.binlog_partition(database, table, process_dt) / "part-00000.parquet"
    binlog_rows = [normalize_event(row_to_event(record), metadata) for record in read_local_parquet(parquet_path)]
    affected_dt = sorted({row["dt"] for row in binlog_rows})

    written: list[Path] = []
    columns = [column["name"] for column in metadata["columns"]] + ["dt"]
    for dt in affected_dt:
        old_parquet_path = lake.ods_partition(database, table, dt) / "part-00000.parquet"
        old_rows = read_table_parquet(old_parquet_path)
        scoped_binlog_rows = [row for row in binlog_rows if row["dt"] == dt]
        merged = merge_rows(scoped_binlog_rows, old_rows, metadata)
        output_path = lake.ods_partition(database, table, dt) / "part-00000.parquet"
        for old_file in output_path.parent.glob("part-*"):
            old_file.unlink()
        write_table_parquet(output_path, merged, columns)
        written.append(output_path)
    return written


def main() -> None:
    metadata_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("metadata/tables/basiccomment.avatar_commentbatchsource.json")
    lake_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/lake")
    process_dt = sys.argv[3] if len(sys.argv) > 3 else "2026-07-06"
    progress_root = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    max_delay_seconds = int(sys.argv[5]) if len(sys.argv) > 5 else None
    for path in run_merge(metadata_path, lake_root, process_dt, progress_root, max_delay_seconds):
        print(path)


if __name__ == "__main__":
    main()
