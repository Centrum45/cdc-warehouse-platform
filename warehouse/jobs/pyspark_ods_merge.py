from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from warehouse.spark_runtime.session import create_spark
from warehouse.storage.hdfs_web import is_hdfs_root
from warehouse.metadata_loader import data_columns, load_table_metadata

DEFAULT_HDFS_ROOT = "hdfs://localhost:8020/warehouse"


def _spark_type(type_name: str) -> str:
    normalized = type_name.lower()
    if normalized in {"bigint", "long"}:
        return "bigint"
    if normalized in {"int", "integer"}:
        return "int"
    if normalized in {"double", "float", "decimal"}:
        return normalized
    return "string"


def _write_audit(audit_root: str | None, payload: dict) -> None:
    if not audit_root:
        return
    audit_dir = Path(audit_root)
    audit_dir.mkdir(parents=True, exist_ok=True)
    name = "{database}.{table}.{process_dt}.{run_id}.json".format(**payload)
    (audit_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def run_pyspark_merge(
    metadata_path: str,
    lake_root: str,
    process_dt: str,
    master: str = "local[2]",
    audit_root: str | None = "data/ops/merge_audit",
    backup_root: str | None = None,
) -> str:
    from pyspark.sql.functions import col, from_json, lit, row_number, when
    from pyspark.sql.window import Window
    from warehouse.spark_runtime.maxwell_schema import maxwell_schema

    metadata = load_table_metadata(metadata_path)
    database = metadata["source_database"]
    table = metadata["source_table"]
    version_column = metadata["version_column"]
    partition_column = metadata["partition_column"]
    columns = data_columns(metadata)
    column_types = {column["name"]: _spark_type(column["type"]) for column in metadata["columns"]}
    run_id = str(int(time.time()))
    spark = create_spark("cdc-ods-merge", master)
    audit = {
        "database": database,
        "table": table,
        "process_dt": process_dt,
        "run_id": run_id,
        "lake_root": lake_root,
        "metadata_path": metadata_path,
        "partitions": [],
    }

    binlog_path = f"{lake_root}/ods_binlog/db={database}/table={table}/dt={process_dt}"
    try:
        raw = spark.read.parquet(binlog_path)
        events = raw.select(from_json(col("raw_json"), maxwell_schema()).alias("event")).select("event.*")
    except Exception:
        from pyspark.sql.types import StructField, StructType
        wrapper_schema = StructType([StructField("content", maxwell_schema(), True)])
        raw = spark.read.text(binlog_path)
        events = raw.select(from_json(col("value"), wrapper_schema).alias("row")).select("row.content.*")
    binlog_rows = events.select(
        when(col("type").isin("insert", "bootstrap-insert"), lit(1))
        .when(col("type") == "update", lit(2))
        .when(col("type") == "delete", lit(3))
        .alias("binlog_type"),
        *[col("data").getItem(column).cast(column_types[column]).alias(column) for column in columns],
        col("data").getItem(partition_column).substr(1, 10).alias("dt")
    )

    affected_dt = [row["dt"] for row in binlog_rows.select("dt").distinct().collect()]
    if not affected_dt:
        audit["status"] = "skipped"
        audit["reason"] = "empty_binlog"
        _write_audit(audit_root, audit)
        spark.stop()
        return f"{lake_root}/ods/db={database}/table={table}:empty"
    old_paths = [
        f"{lake_root}/ods/db={database}/table={table}/dt={dt}"
        if is_hdfs_root(lake_root)
        else f"{lake_root}/ods/db={database}/table={table}/dt={dt}/part-00000.parquet"
        for dt in affected_dt
    ]
    try:
        old_rows = spark.read.parquet(*old_paths).withColumn("binlog_type", lit(1))
    except Exception:
        old_rows = spark.createDataFrame([], binlog_rows.schema)
    old_rows = old_rows.select(
        *[col(column).cast(column_types[column]).alias(column) for column in columns],
        col("dt").cast("string").alias("dt"),
        col("binlog_type").cast("int").alias("binlog_type"),
    )

    unioned = binlog_rows.unionByName(old_rows.select(binlog_rows.columns), allowMissingColumns=True)
    window = Window.partitionBy(*metadata["primary_keys"]).orderBy(col(version_column).cast("int").desc(), col("binlog_type").desc())
    merged = (
        unioned
        .withColumn("rn", row_number().over(window))
        .where((col("rn") == 1) & (col("binlog_type") != 3))
        .select(*[col(column).cast(column_types[column]).alias(column) for column in columns], col("dt"))
    )
    # Materialize before overwriting touched ODS partitions. Otherwise Spark may
    # lazily read files from the same directory it is deleting for overwrite.
    binlog_rows = binlog_rows.cache()
    old_rows = old_rows.cache()
    merged = merged.cache()
    merged.count()

    for dt in affected_dt:
        target_dir = f"{lake_root}/ods/db={database}/table={table}/dt={dt}"
        scoped_old = old_rows.where(col("dt") == dt)
        scoped_merged = merged.where(col("dt") == dt)
        old_count = scoped_old.count()
        output_count = scoped_merged.count()
        binlog_count = binlog_rows.where(col("dt") == dt).count()
        if backup_root and old_count > 0:
            backup_dir = f"{backup_root.rstrip('/')}/db={database}/table={table}/dt={dt}/run_id={run_id}"
            scoped_old.coalesce(1).write.mode("overwrite").option("header", True).csv(backup_dir)
        audit["partitions"].append({
            "dt": dt,
            "binlog_rows": binlog_count,
            "old_rows": old_count,
            "output_rows": output_count,
            "target_dir": target_dir,
        })
        if is_hdfs_root(lake_root):
            scoped_merged.coalesce(1).write.mode("overwrite").parquet(target_dir)
        else:
            target_path = Path(target_dir)
            target_file = target_path / "part-00000.parquet"
            target_path.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="pyspark_ods_merge_") as tmp:
                tmp_path = Path(tmp) / "parquet"
                scoped_merged.coalesce(1).write.mode("overwrite").parquet(str(tmp_path))
                part_files = sorted(tmp_path.glob("part-*.parquet"))
                if not part_files:
                    raise RuntimeError(f"missing spark parquet part file: {tmp_path}")
                target_file.write_bytes(part_files[0].read_bytes())

    try:
        audit["status"] = "success"
        _write_audit(audit_root, audit)
        return f"{lake_root}/ods/db={database}/table={table}" if is_hdfs_root(lake_root) else str(Path(lake_root) / "ods" / f"db={database}" / f"table={table}")
    finally:
        binlog_rows.unpersist()
        old_rows.unpersist()
        merged.unpersist()
        spark.stop()


def main() -> None:
    metadata_path = sys.argv[1] if len(sys.argv) > 1 else "metadata/tables/basiccomment.avatar_commentbatchsource.json"
    lake_root = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_HDFS_ROOT
    process_dt = sys.argv[3] if len(sys.argv) > 3 else "2026-07-06"
    print(run_pyspark_merge(metadata_path, lake_root, process_dt))


if __name__ == "__main__":
    main()
