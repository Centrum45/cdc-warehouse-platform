from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from spark_runtime.session import create_spark

DEFAULT_HDFS_ROOT = "hdfs://localhost:8020/warehouse"


def run_local_file_batch(topic_file: str, output_root: str, master: str = "local[2]") -> None:
    from pyspark.sql.functions import col, from_json, struct, to_json
    from spark_runtime.maxwell_schema import maxwell_schema

    spark = create_spark("cdc-offline-local-file", master)
    raw = spark.read.text(topic_file)
    parsed = raw.select(from_json(col("value"), maxwell_schema()).alias("event")).select("event.*")
    out = (
        parsed
        .withColumn("dt", col("data").getItem("ctime").substr(1, 10))
        .select(
            col("database").alias("database_name"),
            col("table").alias("table_name"),
            col("type"),
            col("ts"),
            col("xid"),
            to_json(struct(*[col(name) for name in parsed.columns])).alias("raw_json"),
            to_json(col("data")).alias("data_json"),
            to_json(col("old")).alias("old_json"),
            col("database").alias("db"),
            col("table"),
            col("dt"),
        )
    )
    out.write.mode("append").partitionBy("db", "table", "dt").parquet(f"{output_root}/ods_binlog")
    spark.stop()


def run_kafka_stream(
    bootstrap_servers: str,
    topic: str,
    output_root: str,
    checkpoint: str,
    master: str = "local[2]",
    starting_offsets: str = "latest",
    max_offsets_per_trigger: int | None = None,
    fail_on_data_loss: bool = False,
    bad_records_path: str | None = None,
    trigger_seconds: int | None = None,
) -> None:
    from pyspark.sql.functions import col, current_timestamp, from_json, struct, to_json
    from spark_runtime.maxwell_schema import maxwell_schema

    spark = create_spark("cdc-offline-kafka-stream", master)
    reader = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", bootstrap_servers)
        .option("subscribe", topic)
        .option("startingOffsets", starting_offsets)
        .option("failOnDataLoss", str(fail_on_data_loss).lower())
    )
    if max_offsets_per_trigger:
        reader = reader.option("maxOffsetsPerTrigger", str(max_offsets_per_trigger))
    kafka_df = reader.load()
    parsed = (
        kafka_df
        .selectExpr("CAST(value AS STRING) AS value")
        .select(col("value"), from_json(col("value"), maxwell_schema()).alias("event"))
    )
    if bad_records_path:
        bad_records = (
            parsed
            .where(col("event").isNull())
            .select(col("value"), current_timestamp().alias("created_at"))
        )
        bad_records.writeStream.format("json").option("path", bad_records_path).option(
            "checkpointLocation", f"{checkpoint.rstrip('/')}/bad_records"
        ).outputMode("append").start()

    parsed = parsed.where(col("event").isNotNull()).select("event.*")
    events = (
        parsed
        .withColumn("dt", col("data").getItem("ctime").substr(1, 10))
        .select(
            col("database").alias("database_name"),
            col("table").alias("table_name"),
            col("type"),
            col("ts"),
            col("xid"),
            to_json(struct(*[col(name) for name in parsed.columns])).alias("raw_json"),
            to_json(col("data")).alias("data_json"),
            to_json(col("old")).alias("old_json"),
            col("database").alias("db"),
            col("table"),
            col("dt"),
        )
    )
    writer = (
        events.writeStream
        .format("parquet")
        .option("path", f"{output_root}/ods_binlog")
        .option("checkpointLocation", checkpoint)
        .partitionBy("db", "table", "dt")
        .outputMode("append")
    )
    if trigger_seconds:
        writer = writer.trigger(processingTime=f"{trigger_seconds} seconds")
    query = writer.start()
    query.awaitTermination()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sink Maxwell CDC events to HDFS ods_binlog.")
    subparsers = parser.add_subparsers(dest="mode", required=False)

    local = subparsers.add_parser("local", help="Read a local JSONL file once.")
    local.add_argument("topic_file", nargs="?", default="data/kafka/cdc.incremental.binlog.jsonl")
    local.add_argument("output_root", nargs="?", default=DEFAULT_HDFS_ROOT)
    local.add_argument("--master", default="local[2]")

    kafka = subparsers.add_parser("kafka", help="Run Structured Streaming from Kafka.")
    kafka.add_argument("bootstrap_servers")
    kafka.add_argument("topic")
    kafka.add_argument("output_root")
    kafka.add_argument("checkpoint")
    kafka.add_argument("--master", default="local[2]")
    kafka.add_argument("--starting-offsets", default="latest", choices=["earliest", "latest"])
    kafka.add_argument("--max-offsets-per-trigger", type=int, default=None)
    kafka.add_argument("--fail-on-data-loss", action="store_true")
    kafka.add_argument("--bad-records-path", default=None)
    kafka.add_argument("--trigger-seconds", type=int, default=None)

    args = parser.parse_args()
    mode = args.mode or "local"
    if mode == "local":
        run_local_file_batch(args.topic_file, args.output_root, args.master)
        return
    if mode == "kafka":
        run_kafka_stream(
            args.bootstrap_servers,
            args.topic,
            args.output_root,
            args.checkpoint,
            args.master,
            args.starting_offsets,
            args.max_offsets_per_trigger,
            args.fail_on_data_loss,
            args.bad_records_path,
            args.trigger_seconds,
        )
        return
    raise SystemExit(f"unknown mode: {mode}")


if __name__ == "__main__":
    main()
