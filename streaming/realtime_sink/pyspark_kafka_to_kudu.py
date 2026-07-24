from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from realtime.kudu.kudu_client import KuduClient
from streaming.realtime_sink.kafka_to_kudu import TABLE_REGISTRY
from warehouse.spark_runtime.maxwell_schema import maxwell_schema
from warehouse.spark_runtime.session import create_spark


EVENT_PRIORITY = {
    "insert": 1,
    "bootstrap-insert": 1,
    "update": 2,
    "delete": 3,
}


def _version(data: dict[str, Any], ts: int, event_type: str) -> tuple[int, int, int]:
    try:
        version = int(data.get("ver") or 0)
    except (TypeError, ValueError):
        version = 0
    return version, int(ts or 0), EVENT_PRIORITY.get(event_type, 0)


def latest_events(rows: list[dict[str, Any]], primary_keys: list[str]) -> list[dict[str, Any]]:
    latest: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        data = row.get("data") or {}
        key = tuple(data.get(column) for column in primary_keys)
        if any(value is None for value in key):
            raise ValueError(f"missing primary key {primary_keys}: {data}")
        current = latest.get(key)
        if current is None or _version(data, row.get("ts", 0), row.get("type", "")) >= _version(
            current.get("data") or {},
            current.get("ts", 0),
            current.get("type", ""),
        ):
            latest[key] = row
    return list(latest.values())


def _coerce(value: Any, column: str) -> Any:
    if value is None:
        return None
    if column in {"id", "user_id", "ver", "event_ts"}:
        return int(value)
    if column in {"pay_amount"}:
        return float(value)
    return value


def write_micro_batch(rows: list[dict[str, Any]]) -> dict[str, int]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        qualified_name = f"{row.get('database')}.{row.get('table')}"
        if qualified_name not in TABLE_REGISTRY:
            raise ValueError(f"realtime table is not registered: {qualified_name}")
        grouped[qualified_name].append(row)

    totals = {"upserted": 0, "deleted": 0}
    client = KuduClient()
    if not client.is_available:
        raise RuntimeError("impyla not installed")
    try:
        for qualified_name, table_rows in grouped.items():
            meta = TABLE_REGISTRY[qualified_name]
            upserts: list[dict[str, Any]] = []
            deletes: list[dict[str, Any]] = []
            for event in latest_events(table_rows, meta["primary_keys"]):
                data = event.get("data") or {}
                if event.get("type") == "delete":
                    deletes.append({key: _coerce(data.get(key), key) for key in meta["primary_keys"]})
                    continue
                record = {
                    column: _coerce(event.get("ts") if column == "event_ts" else data.get(column), column)
                    for column in meta["columns"]
                }
                upserts.append(record)

            if upserts:
                result = client.upsert_rows(meta["impala_db"], meta["impala_table"], upserts, meta["primary_keys"])
                if not result.get("success"):
                    raise RuntimeError(str(result))
                totals["upserted"] += int(result.get("upserted", 0))
            if deletes:
                result = client.delete_rows(meta["impala_db"], meta["impala_table"], deletes)
                if not result.get("success"):
                    raise RuntimeError(str(result))
                totals["deleted"] += int(result.get("deleted", 0))
    finally:
        client.close()
    return totals


def run_stream(
    bootstrap_servers: str,
    topic: str,
    checkpoint: str,
    master: str,
    starting_offsets: str,
    max_offsets_per_trigger: int | None,
    trigger_seconds: int,
) -> None:
    from pyspark.sql.functions import col, from_json

    spark = create_spark("cdc-realtime-kafka-to-kudu", master)
    reader = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap_servers)
        .option("subscribe", topic)
        .option("startingOffsets", starting_offsets)
        .option("failOnDataLoss", "false")
    )
    if max_offsets_per_trigger:
        reader = reader.option("maxOffsetsPerTrigger", str(max_offsets_per_trigger))

    events = (
        reader.load()
        .select(
            from_json(col("value").cast("string"), maxwell_schema()).alias("event"),
            col("partition").alias("kafka_partition"),
            col("offset").alias("kafka_offset"),
        )
        .where(col("event").isNotNull())
        .select("event.*", "kafka_partition", "kafka_offset")
    )

    def process_batch(batch_df, batch_id: int) -> None:
        rows = [row.asDict(recursive=True) for row in batch_df.collect()]
        if not rows:
            return
        result = write_micro_batch(rows)
        print(f"[realtime-kudu] batch={batch_id} rows={len(rows)} result={result}", flush=True)

    query = (
        events.writeStream.foreachBatch(process_batch)
        .option("checkpointLocation", checkpoint)
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .start()
    )
    query.awaitTermination()


def main() -> None:
    parser = argparse.ArgumentParser(description="Structured Streaming Kafka to Kudu sink.")
    parser.add_argument("bootstrap_servers")
    parser.add_argument("topic")
    parser.add_argument("checkpoint")
    parser.add_argument("--master", default="local[2]")
    parser.add_argument("--starting-offsets", choices=["earliest", "latest"], default="latest")
    parser.add_argument("--max-offsets-per-trigger", type=int, default=5000)
    parser.add_argument("--trigger-seconds", type=int, default=5)
    args = parser.parse_args()
    run_stream(
        args.bootstrap_servers,
        args.topic,
        args.checkpoint,
        args.master,
        args.starting_offsets,
        args.max_offsets_per_trigger,
        args.trigger_seconds,
    )


if __name__ == "__main__":
    main()
