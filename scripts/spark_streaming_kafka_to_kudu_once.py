#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingestion.kafka.kafka_topic_to_jsonl import export_topic_to_jsonl
from realtime.impala.bootstrap import bootstrap_realtime
from realtime.kudu.kudu_client import KuduClient
from streaming.realtime_sink.kafka_to_kudu import upsert_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Kafka-to-Kudu realtime micro-batch.")
    parser.add_argument("--topic", default="cdc.incremental.binlog")
    parser.add_argument("--bootstrap-server", default="kafka:9092")
    parser.add_argument("--container", default="cdc-warehouse-kafka")
    parser.add_argument("--max-messages", type=int, default=5000)
    parser.add_argument("--topic-file", default="data/kafka/cdc.incremental.binlog.realtime.jsonl")
    parser.add_argument("--checkpoint", default="data/checkpoints/realtime_kafka_to_kudu.json")
    parser.add_argument("--bootstrap-objects", action="store_true")
    parser.add_argument("--reset-checkpoint", action="store_true")
    args = parser.parse_args()

    topic_file = Path(args.topic_file)
    checkpoint = Path(args.checkpoint)
    if args.reset_checkpoint and checkpoint.exists():
        checkpoint.unlink()

    if args.bootstrap_objects:
        client = KuduClient()
        if not client.is_available:
            raise SystemExit("impyla not installed. Run: scripts/setup_python.sh")
        failed = [item for item in bootstrap_realtime(client=client) if not item.get("success")]
        if failed:
            raise SystemExit("bootstrap failed: " + failed[0].get("msg", "unknown"))

    export_topic_to_jsonl(
        args.topic,
        topic_file,
        bootstrap_server=args.bootstrap_server,
        container=args.container,
        max_messages=args.max_messages,
    )
    output = upsert_rows(
        topic_file,
        checkpoint,
    )
    print("sink=" + str(output))


if __name__ == "__main__":
    main()
