from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any


def quote_identifier(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def build_select_sql(metadata: dict[str, Any]) -> str:
    columns = [quote_identifier(column["name"]) for column in metadata["columns"]]
    primary_keys = [quote_identifier(column) for column in metadata["primary_keys"]]
    database = quote_identifier(metadata["source_database"])
    table = quote_identifier(metadata["source_table"])
    order_by = ", ".join(primary_keys)
    return f"select {', '.join(columns)} from {database}.{table} order by {order_by};"


def mysql_query_tsv(
    sql: str,
    container: str = "cdc-warehouse-mysql",
    user: str = "root",
    password: str = "root",
) -> str:
    command = [
        "docker",
        "exec",
        container,
        "mysql",
        "-u" + user,
        "-p" + password,
        "--batch",
        "--raw",
        "--skip-column-names",
        "--default-character-set=utf8mb4",
        "-e",
        sql,
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return completed.stdout


def coerce_value(value: str | None, hive_type: str) -> Any:
    if value is None or value == r"\N":
        return None
    normalized_type = hive_type.lower()
    if normalized_type in {"bigint", "int", "integer", "smallint", "tinyint"}:
        return int(value)
    if normalized_type in {"double", "float", "decimal"}:
        return float(value)
    return value


def rows_from_tsv(tsv: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    columns = metadata["columns"]
    rows: list[dict[str, Any]] = []
    for line in tsv.splitlines():
        if not line:
            continue
        values = line.split("\t")
        row = {}
        for index, column in enumerate(columns):
            value = values[index] if index < len(values) else None
            row[column["name"]] = coerce_value(value, column["type"])
        rows.append(row)
    return rows


def build_bootstrap_events(rows: list[dict[str, Any]], metadata: dict[str, Any], event_ts: int | None = None) -> list[dict[str, Any]]:
    ts = int(event_ts or time.time())
    database = metadata["source_database"]
    table = metadata["source_table"]
    return [
        {
            "database": database,
            "table": table,
            "type": "bootstrap-insert",
            "ts": ts,
            "xid": index + 1,
            "commit": True,
            "data": row,
        }
        for index, row in enumerate(rows)
    ]


def write_events(events: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        for event in events:
            fp.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
            fp.write("\n")
    return output_path


def bootstrap_table(
    metadata_path: Path,
    output_path: Path,
    container: str = "cdc-warehouse-mysql",
    user: str = "root",
    password: str = "root",
) -> Path:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    sql = build_select_sql(metadata)
    rows = rows_from_tsv(mysql_query_tsv(sql, container, user, password), metadata)
    return write_events(build_bootstrap_events(rows, metadata), output_path)
