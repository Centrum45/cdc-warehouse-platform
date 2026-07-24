from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from warehouse.spark_runtime.session import create_spark

DEFAULT_HDFS_ROOT = "hdfs://localhost:8020/warehouse"


def _apply_sensitive_rules(parsed, rules_path: str | None):
    if not rules_path:
        return parsed
    path = Path(rules_path)
    if not path.exists():
        raise FileNotFoundError(f"sensitive rules not found: {path}")
    rules = json.loads(path.read_text(encoding="utf-8"))
    if not rules.get("columns"):
        return parsed

    from pyspark.sql.functions import col, udf
    from pyspark.sql.types import ArrayType, MapType, StringType, StructField, StructType
    from streaming.common.sensitive_masker import mask_event

    result_schema = StructType([
        StructField("data", MapType(StringType(), StringType()), True),
        StructField("hits", ArrayType(StringType()), True),
    ])

    def mask(data):
        masked, hits = mask_event({"data": data or {}}, rules)
        return masked["data"], hits

    masked = parsed.withColumn("_mask", udf(mask, result_schema)(col("data")))
    return (
        masked.withColumn("data", col("_mask.data"))
        .withColumn("sensitive_hits", col("_mask.hits"))
        .drop("_mask")
    )


def run_local_file_batch(
    topic_file: str,
    output_root: str,
    master: str = "local[2]",
    sensitive_rules: str | None = "metadata/rules/sensitive_columns.json",
) -> None:
    from pyspark.sql.functions import col, from_json, struct, to_json
    from warehouse.spark_runtime.maxwell_schema import maxwell_schema

    spark = create_spark("cdc-offline-local-file", master)
    raw = spark.read.text(topic_file)
    parsed = raw.select(from_json(col("value"), maxwell_schema()).alias("event")).select("event.*")
    parsed = _apply_sensitive_rules(parsed, sensitive_rules)
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
    sensitive_rules: str | None = "metadata/rules/sensitive_columns.json",
    sensitive_alert_path: str | None = None,
    progress_root: str | None = None,
) -> None:
    from pyspark.sql.functions import col, current_timestamp, from_json, max as spark_max, size, struct, to_json
    from warehouse.spark_runtime.maxwell_schema import maxwell_schema
    from warehouse.jobs.delay_gate import write_progress

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
    parsed = _apply_sensitive_rules(parsed, sensitive_rules)
    if progress_root:
        def update_progress(batch_df, batch_id):
            rows = (
                batch_df.withColumn("partition_dt", col("data").getItem("ctime").substr(1, 10))
                .groupBy("database", "table")
                .agg(spark_max("ts").alias("latest_event_ts"), spark_max("partition_dt").alias("partition_dt"))
                .collect()
            )
            for row in rows:
                write_progress(
                    progress_root,
                    row["database"],
                    row["table"],
                    int(row["latest_event_ts"]),
                    row["partition_dt"] or "",
                )
            if rows:
                print(f"[offline-progress] batch={batch_id} tables={len(rows)}", flush=True)

        (
            parsed.writeStream.foreachBatch(update_progress)
            .option("checkpointLocation", f"{checkpoint.rstrip('/')}/progress")
            .outputMode("append")
            .start()
        )
    if sensitive_alert_path and "sensitive_hits" in parsed.columns:
        (
            parsed.where(size(col("sensitive_hits")) > 0)
            .select("database", "table", "ts", "sensitive_hits")
            .writeStream.format("json")
            .option("path", sensitive_alert_path)
            .option("checkpointLocation", f"{checkpoint.rstrip('/')}/sensitive_alerts")
            .outputMode("append")
            .start()
        )
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
    writer.start()
    spark.streams.awaitAnyTermination()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sink Maxwell CDC events to HDFS ods_binlog.")
    subparsers = parser.add_subparsers(dest="mode", required=False)

    local = subparsers.add_parser("local", help="Read a local JSONL file once.")
    local.add_argument("topic_file", nargs="?", default="data/kafka/cdc.incremental.binlog.jsonl")
    local.add_argument("output_root", nargs="?", default=DEFAULT_HDFS_ROOT)
    local.add_argument("--master", default="local[2]")
    local.add_argument("--sensitive-rules", default="metadata/rules/sensitive_columns.json")

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
    kafka.add_argument("--sensitive-rules", default="metadata/rules/sensitive_columns.json")
    kafka.add_argument("--sensitive-alert-path", default=None)
    kafka.add_argument("--progress-root", default=None)

    args = parser.parse_args()
    mode = args.mode or "local"
    if mode == "local":
        run_local_file_batch(args.topic_file, args.output_root, args.master, args.sensitive_rules)
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
            args.sensitive_rules,
            args.sensitive_alert_path,
            args.progress_root,
        )
        return
    raise SystemExit(f"unknown mode: {mode}")


if __name__ == "__main__":
    main()
