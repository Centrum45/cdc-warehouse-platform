from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitors.field_monitor_job import diff_schema
from monitors.notifier import Notifier
from monitors.result_store import MonitorResultStore
from monitors.row_count_monitor import load_rules
from warehouse.jobs.delay_gate import can_merge
from warehouse.spark_runtime.session import create_spark


def _metadata_files() -> list[Path]:
    return sorted(Path("metadata/tables").glob("*.json"))


def _previous_dt(biz_dt: str) -> str:
    return (datetime.strptime(biz_dt, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()


def _path_exists(spark, path: str) -> bool:
    jvm = spark._jvm
    hadoop_path = jvm.org.apache.hadoop.fs.Path(path)
    return bool(hadoop_path.getFileSystem(spark._jsc.hadoopConfiguration()).exists(hadoop_path))


def _record(
    store: MonitorResultStore,
    notifier: Notifier,
    monitor_type: str,
    database: str,
    table: str,
    passed: bool,
    message: str,
    metric: Any = "",
) -> None:
    status = "OK" if passed else "FAIL"
    store.append(monitor_type, database, table, status, message, metric)
    if not passed:
        notifier.send_default(f"CDC {monitor_type} alert", f"{database}.{table}: {message}")


def _check_field_drift(store, notifier, metadata_path: Path, database: str, table: str) -> None:
    dba_path = Path("metadata/dba") / metadata_path.name
    if not dba_path.exists():
        _record(store, notifier, "field", database, table, False, f"missing DBA metadata: {dba_path}")
        return
    changes = diff_schema(metadata_path, dba_path)
    changed = any(changes.values())
    message = "metadata aligned" if not changed else json.dumps(changes, ensure_ascii=False)
    _record(
        store,
        notifier,
        "field",
        database,
        table,
        not changed,
        message,
        sum(len(items) for items in changes.values()),
    )


def _check_delay(store, notifier, progress_root: str, database: str, table: str, max_delay: int) -> None:
    allowed, reason = can_merge(progress_root, database, table, max_delay)
    _record(store, notifier, "delay", database, table, allowed, reason)


def _check_ods_data(
    spark,
    store,
    notifier,
    metadata: dict[str, Any],
    lake_root: str,
    biz_dt: str,
    rules: dict[str, Any],
    special_rules: dict[str, Any],
) -> None:
    from pyspark.sql.functions import col, max as spark_max, sum as spark_sum, when

    database = metadata["source_database"]
    table = metadata["source_table"]
    qualified_name = f"{database}.{table}"
    path = f"{lake_root.rstrip('/')}/ods/db={database}/table={table}/dt={biz_dt}"
    if not _path_exists(spark, path):
        _record(store, notifier, "partition", database, table, False, f"missing partition: {path}")
        return

    frame = spark.read.parquet(path).cache()
    try:
        row_count = frame.count()
        _record(store, notifier, "partition", database, table, True, f"partition rows={row_count}", row_count)

        null_cfg = rules.get("null_rate", {})
        threshold = float(null_cfg.get("max_null_rate", 0.05))
        skipped = set(null_cfg.get("skip_columns", []))
        columns = [name for name in frame.columns if name not in skipped]
        if row_count and columns:
            expressions = [
                spark_sum(when(col(name).isNull() | (col(name).cast("string") == ""), 1).otherwise(0)).alias(name)
                for name in columns
            ]
            counts = frame.agg(*expressions).first().asDict()
            failed = {name: int(value or 0) / row_count for name, value in counts.items() if int(value or 0) / row_count > threshold}
            _record(
                store,
                notifier,
                "null_rate",
                database,
                table,
                not failed,
                "null rates within threshold" if not failed else f"over threshold: {failed}",
            )

        table_rules = special_rules.get(qualified_name, {})
        for column_name in table_rules.get("not_null", []):
            if column_name not in frame.columns:
                _record(store, notifier, "not_null", database, table, False, f"missing column: {column_name}")
                continue
            bad = frame.where(col(column_name).isNull() | (col(column_name).cast("string") == "")).count()
            _record(store, notifier, "not_null", database, table, bad == 0, f"{column_name} bad_count={bad}", bad)

        for column_name, values in table_rules.get("special_values", {}).items():
            if column_name not in frame.columns:
                _record(store, notifier, "special_value", database, table, False, f"missing column: {column_name}")
                continue
            bad = frame.where(col(column_name).isin(values)).count()
            _record(store, notifier, "special_value", database, table, bad == 0, f"{column_name} bad_count={bad}", bad)

        update_column = "utime" if "utime" in frame.columns else metadata.get("partition_column")
        if update_column in frame.columns:
            latest = frame.agg(spark_max(col(update_column)).alias("latest")).first()["latest"]
            threshold_minutes = int(rules.get("table_update", {}).get("max_stale_minutes", 2880))
            stale = True
            if latest:
                try:
                    latest_time = datetime.fromisoformat(str(latest).replace("Z", "+00:00"))
                    current = datetime.now(latest_time.tzinfo) if latest_time.tzinfo else datetime.now()
                    stale = (current - latest_time).total_seconds() > threshold_minutes * 60
                except ValueError:
                    stale = True
            _record(store, notifier, "table_update", database, table, not stale, f"latest={latest}", latest or "")

        previous_path = f"{lake_root.rstrip('/')}/ods/db={database}/table={table}/dt={_previous_dt(biz_dt)}"
        if _path_exists(spark, previous_path):
            previous = spark.read.parquet(previous_path)
            keys = metadata["primary_keys"]
            for value_column in table_rules.get("increasing", []):
                if value_column not in frame.columns or value_column not in previous.columns:
                    continue
                joined = frame.alias("today").join(previous.alias("yesterday"), keys, "inner")
                bad = joined.where(col(f"today.{value_column}") < col(f"yesterday.{value_column}")).count()
                _record(store, notifier, "increasing", database, table, bad == 0, f"{value_column} decreased={bad}", bad)
    finally:
        frame.unpersist()


def _check_row_counts(spark, store, notifier, lake_root: str, biz_dt: str, rules: dict[str, Any]) -> None:
    config = rules.get("row_count", {})
    min_ratio = float(config.get("min_ratio", 0.99))
    max_ratio = float(config.get("max_ratio", 1.01))
    for item in config.get("comparisons", []):
        source = f"{lake_root.rstrip('/')}/{item['source'].format(biz_dt=biz_dt)}"
        target = f"{lake_root.rstrip('/')}/{item['target'].format(biz_dt=biz_dt)}"
        if not _path_exists(spark, source) or not _path_exists(spark, target):
            _record(store, notifier, "row_count", item.get("database", "*"), item.get("table", "*"), False, "comparison partition missing")
            continue
        source_count = spark.read.parquet(source).count()
        target_count = spark.read.parquet(target).count()
        ratio = target_count / source_count if source_count else (1.0 if target_count == 0 else float("inf"))
        passed = min_ratio <= ratio <= max_ratio
        _record(
            store,
            notifier,
            "row_count",
            item.get("database", "*"),
            item.get("table", "*"),
            passed,
            f"source={source_count} target={target_count} ratio={ratio:.4f}",
            ratio,
        )


def run_suite(
    biz_dt: str | None = None,
    lake_root: str | None = None,
    master: str | None = None,
) -> None:
    biz_dt = biz_dt or os.environ.get("BIZ_DT") or (date.today() - timedelta(days=1)).isoformat()
    lake_root = lake_root or os.environ.get("LAKE_ROOT", "data/lake")
    master = master or os.environ.get("SPARK_MASTER", "local[2]")
    progress_root = os.environ.get("PROGRESS_ROOT", "data/progress")
    max_delay = int(os.environ.get("DELAY_GATE_MAX_SECONDS", "1800"))
    store = MonitorResultStore()
    notifier = Notifier()
    rules = load_rules()
    special_rules_path = Path("metadata/rules/special_value_rules.json")
    special_rules = json.loads(special_rules_path.read_text(encoding="utf-8")) if special_rules_path.exists() else {}
    spark = create_spark("cdc-monitor-suite", master)
    try:
        for metadata_path in _metadata_files():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            database = metadata["source_database"]
            table = metadata["source_table"]
            _check_delay(store, notifier, progress_root, database, table, max_delay)
            _check_field_drift(store, notifier, metadata_path, database, table)
            _check_ods_data(spark, store, notifier, metadata, lake_root, biz_dt, rules, special_rules)
        _check_row_counts(spark, store, notifier, lake_root, biz_dt, rules)
    finally:
        spark.stop()
    print(store.path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run production-capable warehouse monitor suite.")
    parser.add_argument("--biz-dt", default=None)
    parser.add_argument("--lake-root", default=None)
    parser.add_argument("--master", default=None)
    args = parser.parse_args()
    run_suite(args.biz_dt, args.lake_root, args.master)


if __name__ == "__main__":
    main()
