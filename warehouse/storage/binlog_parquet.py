from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Iterable

from warehouse.storage.hdfs_web import HdfsPath, WebHdfsLake

BINLOG_PARQUET_COLUMNS = [
    "database_name",
    "table_name",
    "type",
    "ts",
    "xid",
    "raw_json",
    "data_json",
    "old_json",
]


def event_to_binlog_row(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data") or {}
    old = event.get("old") or {}
    return {
        "database_name": event.get("database"),
        "table_name": event.get("table"),
        "type": event.get("type"),
        "ts": event.get("ts"),
        "xid": event.get("xid"),
        "raw_json": json.dumps(event, ensure_ascii=False, sort_keys=True),
        "data_json": json.dumps(data, ensure_ascii=False, sort_keys=True),
        "old_json": json.dumps(old, ensure_ascii=False, sort_keys=True),
    }


def row_to_event(row: dict[str, Any]) -> dict[str, Any]:
    raw_json = row.get("raw_json")
    if raw_json:
        return json.loads(raw_json)
    return {
        "database": row.get("database_name"),
        "table": row.get("table_name"),
        "type": row.get("type"),
        "ts": row.get("ts"),
        "xid": row.get("xid"),
        "data": json.loads(row.get("data_json") or "{}"),
        "old": json.loads(row.get("old_json") or "{}"),
    }


def _pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except Exception as exc:
        raise RuntimeError("pyarrow is required for ods_binlog parquet read/write") from exc
    return pa, pq


def _schema():
    pa, _ = _pyarrow()
    return pa.schema([
        pa.field("database_name", pa.string()),
        pa.field("table_name", pa.string()),
        pa.field("type", pa.string()),
        pa.field("ts", pa.int64()),
        pa.field("xid", pa.int64()),
        pa.field("raw_json", pa.string()),
        pa.field("data_json", pa.string()),
        pa.field("old_json", pa.string()),
    ])


def parquet_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    pa, pq = _pyarrow()
    materialized = list(rows)
    columns = {
        column: [row.get(column) for row in materialized]
        for column in BINLOG_PARQUET_COLUMNS
    }
    table = pa.Table.from_pydict(columns, schema=_schema())
    output = io.BytesIO()
    pq.write_table(table, output, compression="snappy")
    return output.getvalue()


def read_parquet_bytes(payload: bytes) -> list[dict[str, Any]]:
    if not payload:
        return []
    _, pq = _pyarrow()
    table = pq.read_table(io.BytesIO(payload))
    return table.to_pylist()


def write_local_parquet(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(parquet_bytes(rows))
    tmp_path.replace(path)


def read_local_parquet(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return read_parquet_bytes(path.read_bytes())


def write_hdfs_parquet(lake: WebHdfsLake, path: HdfsPath, rows: Iterable[dict[str, Any]]) -> None:
    lake.write_bytes(path, parquet_bytes(rows))


def read_hdfs_parquet(lake: WebHdfsLake, path: HdfsPath) -> list[dict[str, Any]]:
    return read_parquet_bytes(lake.read_bytes(path))
