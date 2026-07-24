from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def _default_password() -> str:
    return os.environ.get("MYSQL_ROOT_PASSWORD", os.environ.get("MYSQL_PASSWORD", "root"))


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
    user: str | None = None,
    password: str | None = None,
    mode: str = "auto",
    host: str | None = None,
    port: int | None = None,
) -> str:
    resolved_host = host or os.environ.get("SOURCE_MYSQL_HOST")
    resolved_mode = mode
    if resolved_mode == "auto":
        resolved_mode = "direct" if resolved_host else "docker"
    if resolved_mode == "direct":
        return mysql_query_tsv_direct(
            sql,
            resolved_host or "127.0.0.1",
            port or int(os.environ.get("SOURCE_MYSQL_PORT", "3306")),
            user or os.environ.get("SOURCE_MYSQL_USER", os.environ.get("MYSQL_USER", "root")),
            password or os.environ.get("SOURCE_MYSQL_PASSWORD", _default_password()),
        )
    if resolved_mode != "docker":
        raise ValueError(f"unsupported MySQL bootstrap mode: {resolved_mode}")
    return mysql_query_tsv_docker(sql, container, user, password)


def mysql_query_tsv_docker(
    sql: str,
    container: str,
    user: str | None = None,
    password: str | None = None,
) -> str:
    _user = user or os.environ.get("SOURCE_MYSQL_USER", os.environ.get("MYSQL_USER", "root"))
    _password = password or os.environ.get("SOURCE_MYSQL_PASSWORD", _default_password())
    command = [
        "docker",
        "exec",
        container,
        "mysql",
        "-u" + _user,
        "-p" + _password,
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


def mysql_query_tsv_direct(sql: str, host: str, port: int, user: str, password: str) -> str:
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("PyMySQL is required for direct MySQL bootstrap") from exc

    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset="utf8mb4",
        connect_timeout=int(os.environ.get("SOURCE_MYSQL_CONNECT_TIMEOUT", "10")),
        read_timeout=int(os.environ.get("SOURCE_MYSQL_READ_TIMEOUT", "300")),
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            lines = []
            for row in cursor:
                values = [r"\N" if value is None else str(value) for value in row]
                lines.append("\t".join(values))
        return "\n".join(lines) + ("\n" if lines else "")
    finally:
        connection.close()


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
    user: str | None = None,
    password: str | None = None,
    mode: str = "auto",
    host: str | None = None,
    port: int | None = None,
) -> Path:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    sql = build_select_sql(metadata)
    rows = rows_from_tsv(
        mysql_query_tsv(sql, container, user, password, mode, host, port),
        metadata,
    )
    return write_events(build_bootstrap_events(rows, metadata), output_path)
