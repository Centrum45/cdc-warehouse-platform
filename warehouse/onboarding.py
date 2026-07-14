from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from warehouse.generator.render_hive_ddl import render_ods_binlog_ddl, render_ods_ddl
from warehouse.generator.render_ods_merge_sql import render as render_ods_merge_sql


def table_code(database: str, table: str) -> str:
    return f"{database}_{table}"


def build_table_metadata(
    dba_metadata: dict[str, Any],
    primary_keys: list[str],
    version_column: str,
    partition_column: str
) -> dict[str, Any]:
    database = dba_metadata["source_database"]
    table = dba_metadata["source_table"]
    code = table_code(database, table)
    return {
        "source_database": database,
        "source_table": table,
        "ods_binlog_table": f"ods_binlog_{code}_di",
        "ods_table": f"ods_{code}_dic",
        "primary_keys": primary_keys,
        "version_column": version_column,
        "partition_column": partition_column,
        "columns": dba_metadata["columns"]
    }


def build_dolphinscheduler_task(metadata: dict[str, Any]) -> dict[str, Any]:
    merge_sql = f"warehouse/sql/ods/merge/merge_{metadata['ods_table']}.sql"
    return {
        "name": f"merge_{metadata['ods_table']}",
        "type": "SPARK_SQL",
        "command": f"spark-sql -f {merge_sql}",
        "description": f"Merge binlog to ODS snapshot for {metadata['source_database']}.{metadata['source_table']}"
    }


def onboard_table(
    dba_metadata_path: Path,
    output_root: Path,
    primary_keys: list[str],
    version_column: str,
    partition_column: str
) -> dict[str, Path]:
    dba_metadata = json.loads(dba_metadata_path.read_text(encoding="utf-8"))
    metadata = build_table_metadata(dba_metadata, primary_keys, version_column, partition_column)
    qualified_name = f"{metadata['source_database']}.{metadata['source_table']}"

    metadata_path = output_root / "metadata/tables" / f"{qualified_name}.json"
    ods_binlog_ddl_path = output_root / "warehouse/sql/ods_binlog/ddl" / f"{metadata['ods_binlog_table']}.sql"
    ods_ddl_path = output_root / "warehouse/sql/ods/ddl" / f"{metadata['ods_table']}.sql"
    merge_sql_path = output_root / "warehouse/sql/ods/merge" / f"merge_{metadata['ods_table']}.sql"
    ds_task_path = output_root / "warehouse/scheduler/dolphinscheduler/tasks" / f"merge_{metadata['ods_table']}.json"

    for path in [metadata_path, ods_binlog_ddl_path, ods_ddl_path, merge_sql_path, ds_task_path]:
        path.parent.mkdir(parents=True, exist_ok=True)

    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    ods_binlog_ddl_path.write_text(render_ods_binlog_ddl(metadata), encoding="utf-8")
    ods_ddl_path.write_text(render_ods_ddl(metadata), encoding="utf-8")
    merge_sql_path.write_text(render_ods_merge_sql(metadata), encoding="utf-8")
    ds_task_path.write_text(json.dumps(build_dolphinscheduler_task(metadata), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "metadata": metadata_path,
        "ods_binlog_ddl": ods_binlog_ddl_path,
        "ods_ddl": ods_ddl_path,
        "merge_sql": merge_sql_path,
        "dolphinscheduler_task": ds_task_path
    }
