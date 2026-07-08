from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from spark_runtime.session import create_spark


def run_local_file_upsert(topic_file: str, output_root: str, master: str = "local[2]") -> str:
    from pyspark.sql.functions import col, from_json
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number
    from spark_runtime.maxwell_schema import maxwell_schema

    spark = create_spark("cdc-realtime-local-kudu", master)
    raw = spark.read.text(topic_file)
    events = raw.select(from_json(col("value"), maxwell_schema()).alias("event")).select("event.*")
    rows = events.select(
        col("data").getItem("id").alias("id"),
        col("data").getItem("batchnumber").alias("batchnumber"),
        col("data").getItem("batchtype").alias("batchtype"),
        col("data").getItem("ctime").alias("ctime"),
        col("data").getItem("utime").alias("utime"),
        col("data").getItem("ver").cast("int").alias("ver"),
        col("ts").alias("event_ts"),
        col("type").alias("event_type")
    )
    window = Window.partitionBy("id").orderBy(col("ver").desc(), col("event_ts").desc())
    latest = rows.withColumn("rn", row_number().over(window)).where((col("rn") == 1) & (col("event_type") != "delete"))
    output = f"{output_root}/realtime_avatar_commentbatchsource"
    latest.drop("rn", "event_type").write.mode("overwrite").option("header", True).csv(output)
    spark.stop()
    return output


def main() -> None:
    topic_file = sys.argv[1] if len(sys.argv) > 1 else "data/kafka/cdc.incremental.binlog.jsonl"
    output_root = sys.argv[2] if len(sys.argv) > 2 else "data/kudu_pyspark"
    print(run_local_file_upsert(topic_file, output_root))


if __name__ == "__main__":
    main()
