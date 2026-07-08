from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from spark_runtime.session import create_spark


def run_local_file_batch(topic_file: str, output_root: str, master: str = "local[2]") -> None:
    from pyspark.sql.functions import col, from_json, to_json
    from spark_runtime.maxwell_schema import maxwell_schema

    spark = create_spark("cdc-offline-local-file", master)
    raw = spark.read.text(topic_file)
    events = raw.select(from_json(col("value"), maxwell_schema()).alias("event")).select("event.*")
    out = (
        events
        .withColumn("dt", col("data").getItem("ctime").substr(1, 10))
        .select(to_json(col("*")).alias("content"), col("database").alias("db"), col("table"), col("dt"))
    )
    out.write.mode("append").partitionBy("db", "table", "dt").json(f"{output_root}/ods_binlog_pyspark")
    spark.stop()


def run_kafka_stream(bootstrap_servers: str, topic: str, output_root: str, checkpoint: str, master: str = "local[2]") -> None:
    from pyspark.sql.functions import col, from_json, to_json
    from spark_runtime.maxwell_schema import maxwell_schema

    spark = create_spark("cdc-offline-kafka-stream", master)
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", bootstrap_servers)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .load()
    )
    events = (
        kafka_df
        .selectExpr("CAST(value AS STRING) AS value")
        .select(from_json(col("value"), maxwell_schema()).alias("event"))
        .select("event.*")
        .withColumn("dt", col("data").getItem("ctime").substr(1, 10))
        .select(to_json(col("*")).alias("content"), col("database").alias("db"), col("table"), col("dt"))
    )
    query = (
        events.writeStream
        .format("json")
        .option("path", f"{output_root}/ods_binlog")
        .option("checkpointLocation", checkpoint)
        .partitionBy("db", "table", "dt")
        .outputMode("append")
        .start()
    )
    query.awaitTermination()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"
    if mode == "local":
        topic_file = sys.argv[2] if len(sys.argv) > 2 else "data/kafka/cdc.incremental.binlog.jsonl"
        output_root = sys.argv[3] if len(sys.argv) > 3 else "data/lake"
        run_local_file_batch(topic_file, output_root)
        return
    if mode == "kafka":
        bootstrap_servers = sys.argv[2]
        topic = sys.argv[3]
        output_root = sys.argv[4]
        checkpoint = sys.argv[5]
        run_kafka_stream(bootstrap_servers, topic, output_root, checkpoint)
        return
    raise SystemExit(f"unknown mode: {mode}")


if __name__ == "__main__":
    main()
