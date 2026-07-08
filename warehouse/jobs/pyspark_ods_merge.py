from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from spark_runtime.session import create_spark
from storage.hdfs_web import is_hdfs_root


def run_pyspark_merge(metadata_path: str, lake_root: str, process_dt: str, master: str = "local[2]") -> str:
    from pyspark.sql.functions import col, from_json, lit, row_number, when
    from pyspark.sql.types import StructField, StructType
    from pyspark.sql.window import Window
    from spark_runtime.maxwell_schema import maxwell_schema

    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    database = metadata["source_database"]
    table = metadata["source_table"]
    version_column = metadata["version_column"]
    partition_column = metadata["partition_column"]
    columns = [column["name"] for column in metadata["columns"]]
    spark = create_spark("cdc-ods-merge", master)

    binlog_path = f"{lake_root}/ods_binlog/db={database}/table={table}/dt={process_dt}/part-00000.jsonl"
    wrapper_schema = StructType([StructField("content", maxwell_schema(), True)])
    raw = spark.read.text(binlog_path)
    events = raw.select(from_json(col("value"), wrapper_schema).alias("row")).select("row.content.*")
    binlog_rows = events.select(
        when(col("type").isin("insert", "bootstrap-insert"), lit(1))
        .when(col("type") == "update", lit(2))
        .when(col("type") == "delete", lit(3))
        .alias("binlog_type"),
        *[col("data").getItem(column).alias(column) for column in columns],
        col("data").getItem(partition_column).substr(1, 10).alias("dt")
    )

    affected_dt = [row["dt"] for row in binlog_rows.select("dt").distinct().collect()]
    old_paths = [
        f"{lake_root}/ods/db={database}/table={table}/dt={dt}"
        if is_hdfs_root(lake_root)
        else f"{lake_root}/ods/db={database}/table={table}/dt={dt}/part-00000.csv"
        for dt in affected_dt
    ]
    try:
        old_rows = spark.read.option("header", True).csv(old_paths).withColumn("binlog_type", lit(1))
    except Exception:
        old_rows = spark.createDataFrame([], binlog_rows.schema)

    unioned = binlog_rows.unionByName(old_rows.select(binlog_rows.columns), allowMissingColumns=True)
    window = Window.partitionBy(*metadata["primary_keys"]).orderBy(col(version_column).cast("int").desc(), col("binlog_type").desc())
    merged = (
        unioned
        .withColumn("rn", row_number().over(window))
        .where((col("rn") == 1) & (col("binlog_type") != 3))
        .select(*columns, "dt")
    )
    # Materialize before overwriting touched ODS partitions. Otherwise Spark may
    # lazily read files from the same directory it is deleting for overwrite.
    merged = merged.cache()
    merged.count()

    for dt in affected_dt:
        target_dir = f"{lake_root}/ods/db={database}/table={table}/dt={dt}"
        if is_hdfs_root(lake_root):
            merged.where(col("dt") == dt).coalesce(1).write.mode("overwrite").option("header", True).csv(target_dir)
        else:
            target_path = Path(target_dir)
            target_file = target_path / "part-00000.csv"
            target_path.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="pyspark_ods_merge_") as tmp:
                tmp_path = Path(tmp) / "csv"
                merged.where(col("dt") == dt).coalesce(1).write.mode("overwrite").option("header", True).csv(str(tmp_path))
                part_files = sorted(tmp_path.glob("part-*.csv"))
                if not part_files:
                    raise RuntimeError(f"missing spark csv part file: {tmp_path}")
                target_file.write_bytes(part_files[0].read_bytes())

    try:
        return f"{lake_root}/ods/db={database}/table={table}" if is_hdfs_root(lake_root) else str(Path(lake_root) / "ods" / f"db={database}" / f"table={table}")
    finally:
        merged.unpersist()
        spark.stop()


def main() -> None:
    metadata_path = sys.argv[1] if len(sys.argv) > 1 else "metadata/tables/basiccomment.avatar_commentbatchsource.json"
    lake_root = sys.argv[2] if len(sys.argv) > 2 else "data/lake"
    process_dt = sys.argv[3] if len(sys.argv) > 3 else "2026-07-06"
    print(run_pyspark_merge(metadata_path, lake_root, process_dt))


if __name__ == "__main__":
    main()
