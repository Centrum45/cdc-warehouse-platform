from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.spark_streaming_kafka_to_hdfs_loop import export_topic, reconcile_checkpoint
from streaming.offline_sink.spark_streaming_to_hdfs import run_micro_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one SparkStreaming-style Kafka to HDFS micro-batch.")
    parser.add_argument("--topic", default="cdc.incremental.binlog")
    parser.add_argument("--bootstrap-server", default="kafka:9092")
    parser.add_argument("--lake-root", default="hdfs://hdfs-namenode:8020/warehouse")
    parser.add_argument("--checkpoint", default="data/checkpoints/offline_sink.json")
    parser.add_argument("--rules", default="metadata/rules/sensitive_columns.json")
    parser.add_argument("--progress-root", default="data/progress")
    parser.add_argument("--work-root", default="data/kafka")
    parser.add_argument("--max-messages", type=int, default=500)
    parser.add_argument("--timeout-ms", type=int, default=5000)
    args = parser.parse_args()

    topic_file = Path(args.work_root) / f"{args.topic}.jsonl"
    total = export_topic(args.topic, topic_file, args.bootstrap_server, args.max_messages, args.timeout_ms)
    offset = reconcile_checkpoint(topic_file, Path(args.checkpoint), total)
    written = run_micro_batch(
        topic_file,
        args.lake_root,
        Path(args.checkpoint),
        Path(args.rules),
        Path(args.progress_root),
    )
    print(
        "spark-streaming-once topic={} total={} start_offset={} new={} written={}".format(
            args.topic,
            total,
            offset,
            max(total - offset, 0),
            ",".join(str(path) for path in written) if written else "-",
        )
    )


if __name__ == "__main__":
    main()
