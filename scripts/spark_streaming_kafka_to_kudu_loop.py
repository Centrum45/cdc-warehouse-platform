#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuously run Kafka-to-Kudu realtime micro-batches.")
    parser.add_argument("--interval-seconds", type=int, default=10)
    parser.add_argument("--max-messages", type=int, default=5000)
    parser.add_argument("--topic", default="cdc.incremental.binlog")
    parser.add_argument("--bootstrap-server", default="kafka:9092")
    parser.add_argument("--container", default="cdc-warehouse-kafka")
    parser.add_argument("--bootstrap-objects", action="store_true")
    args = parser.parse_args()

    first = True
    while True:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "spark_streaming_kafka_to_kudu_once.py"),
            "--topic",
            args.topic,
            "--bootstrap-server",
            args.bootstrap_server,
            "--container",
            args.container,
            "--max-messages",
            str(args.max_messages),
        ]
        if first and args.bootstrap_objects:
            command.append("--bootstrap-objects")
        completed = subprocess.run(command, cwd=str(ROOT), text=True, check=False)
        if completed.returncode != 0:
            print("micro-batch failed, exitCode=" + str(completed.returncode), flush=True)
        first = False
        time.sleep(max(1, args.interval_seconds))


if __name__ == "__main__":
    main()
