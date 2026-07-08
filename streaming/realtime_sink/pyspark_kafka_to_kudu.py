from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from spark_runtime.session import create_spark

# Schema registry — maps (db, table) → columns from binlog data
TABLE_SCHEMAS = {
    "basiccomment.avatar_commentbatchsource": {
        "columns": ["id", "batchnumber", "batchtype", "ctime", "utime", "ver"],
        "pk": "id",
    },
    "trade.order_info": {
        "columns": ["id", "user_id", "order_no", "pay_amount", "order_status",
                    "ctime", "utime", "ver"],
        "pk": "id",
    },
    "user.user_info": {
        "columns": ["id", "user_name", "mobile", "email", "register_time",
                    "ctime", "utime", "ver"],
        "pk": "id",
    },
}


def run_local_upsert(
    topic_file: str,
    output_root: str,
    db: str,
    table: str,
    master: str = "local[2]",
) -> str:
    """Upsert one table from binlog events into local CSV (Kudu simulation)."""
    from pyspark.sql.functions import col, from_json, row_number
    from pyspark.sql.window import Window
    from spark_runtime.maxwell_schema import maxwell_schema

    schema = TABLE_SCHEMAS[f"{db}.{table}"]
    columns = schema["columns"]
    pk = schema["pk"]

    spark = create_spark(f"cdc-realtime-{db}-{table}", master)
    raw = spark.read.text(topic_file)
    events = raw.select(
        from_json(col("value"), maxwell_schema()).alias("event")
    ).select("event.*")

    # Filter to this db + table
    filtered = events.filter(
        (col("database") == db) & (col("table") == table)
    )

    # Select data columns
    selects = [col("data").getItem(c).alias(c) for c in columns]
    selects.append(col("ts").alias("event_ts"))
    selects.append(col("type").alias("event_type"))

    rows = filtered.select(*selects)

    # Dedup: keep latest version per PK, drop deletes
    window = Window.partitionBy(pk).orderBy(
        col("ver").desc(), col("event_ts").desc()
    )
    latest = (
        rows.withColumn("rn", row_number().over(window))
        .where((col("rn") == 1) & (col("event_type") != "delete"))
    )

    output = f"{output_root}/realtime_{db}_{table}"
    output_cols = columns + ["event_ts"]
    latest.drop("rn", "event_type").select(*output_cols).write.mode("overwrite") \
        .option("header", True).csv(output)
    spark.stop()
    return output


def run_all_tables(
    topic_file: str = "data/kafka/cdc.incremental.binlog.jsonl",
    output_root: str = "data/kudu_pyspark",
    master: str = "local[2]",
) -> list[str]:
    """Process all registered tables."""
    outputs = []
    for qualified_name in TABLE_SCHEMAS:
        db, table = qualified_name.split(".")
        out = run_local_upsert(topic_file, output_root, db, table, master)
        outputs.append(out)
        print(out)
    return outputs


def main() -> None:
    topic_file = sys.argv[1] if len(sys.argv) > 1 else "data/kafka/cdc.incremental.binlog.jsonl"
    output_root = sys.argv[2] if len(sys.argv) > 2 else "data/kudu_pyspark"
    db = sys.argv[3] if len(sys.argv) > 3 else None
    table = sys.argv[4] if len(sys.argv) > 4 else None

    if db and table:
        print(run_local_upsert(topic_file, output_root, db, table))
    else:
        run_all_tables(topic_file, output_root)


if __name__ == "__main__":
    main()
