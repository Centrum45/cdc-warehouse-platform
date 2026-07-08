from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streaming.common.checkpoint import FileCheckpoint
from streaming.offline_sink.spark_streaming_to_hdfs import run_micro_batch


def export_topic(
    topic: str,
    output_path: Path,
    bootstrap_server: str,
    max_messages: int,
    timeout_ms: int,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "kafka-console-consumer",
        "--bootstrap-server",
        bootstrap_server,
        "--topic",
        topic,
        "--from-beginning",
        "--max-messages",
        str(max_messages),
        "--timeout-ms",
        str(timeout_ms),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr or completed.stdout)
    lines = [line for line in completed.stdout.splitlines() if line.strip().startswith("{")]
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def reconcile_checkpoint(topic_file: Path, checkpoint_path: Path, total_lines: int) -> int:
    topic = topic_file.stem
    checkpoint = FileCheckpoint(checkpoint_path)
    offset = checkpoint.load_offset(topic)
    if offset > total_lines:
        checkpoint.save_offset(topic, total_lines)
        return total_lines
    return offset


def run_loop(
    topic: str,
    bootstrap_server: str,
    lake_root: str,
    checkpoint_path: Path,
    rules_path: Path,
    progress_root: Path,
    work_root: Path,
    interval_seconds: int,
    max_messages: int,
    timeout_ms: int,
) -> None:
    topic_file = work_root / f"{topic}.jsonl"
    while True:
        try:
            total = export_topic(topic, topic_file, bootstrap_server, max_messages, timeout_ms)
            offset = reconcile_checkpoint(topic_file, checkpoint_path, total)
            written = run_micro_batch(topic_file, lake_root, checkpoint_path, rules_path, progress_root)
            print(
                "spark-streaming topic={} total={} start_offset={} new={} written={}".format(
                    topic,
                    total,
                    offset,
                    max(total - offset, 0),
                    ",".join(str(path) for path in written) if written else "-",
                ),
                flush=True,
            )
        except Exception as exc:
            print(f"spark-streaming error: {exc}", flush=True)
        time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuously sink Maxwell Kafka events into local ods_binlog via SparkStreaming-style micro-batches.")
    parser.add_argument("--topic", default="cdc.incremental.binlog")
    parser.add_argument("--bootstrap-server", default="kafka:9092")
    parser.add_argument("--lake-root", default="data/lake")
    parser.add_argument("--checkpoint", default="data/checkpoints/offline_sink.json")
    parser.add_argument("--rules", default="metadata/rules/sensitive_columns.json")
    parser.add_argument("--progress-root", default="data/progress")
    parser.add_argument("--work-root", default="data/kafka")
    parser.add_argument("--interval-seconds", type=int, default=5)
    parser.add_argument("--max-messages", type=int, default=500)
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()

    run_loop(
        topic=args.topic,
        bootstrap_server=args.bootstrap_server,
        lake_root=args.lake_root,
        checkpoint_path=Path(args.checkpoint),
        rules_path=Path(args.rules),
        progress_root=Path(args.progress_root),
        work_root=Path(args.work_root),
        interval_seconds=args.interval_seconds,
        max_messages=args.max_messages,
        timeout_ms=args.timeout_ms,
    )


if __name__ == "__main__":
    main()
