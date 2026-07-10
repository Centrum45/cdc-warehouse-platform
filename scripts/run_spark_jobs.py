from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from spark_runtime.session import has_pyspark


def run_offline() -> None:
    if has_pyspark():
        from streaming.offline_sink.pyspark_kafka_to_hdfs import run_local_file_batch

        try:
            run_local_file_batch("data/kafka/cdc.incremental.binlog.jsonl", "data/lake")
            print("engine=pyspark offline=ok")
            return
        except Exception as exc:
            print(f"engine=pyspark offline=failed fallback=local reason={exc}")

    from streaming.offline_sink.spark_streaming_to_hdfs import run_micro_batch

    run_micro_batch(
        Path("data/kafka/cdc.incremental.binlog.jsonl"),
        Path("data/lake"),
        Path("data/checkpoints/offline_sink.json"),
        Path("metadata/rules/sensitive_columns.json"),
        Path("data/progress")
    )
    print("engine=local offline=ok")


def run_realtime() -> None:
    if has_pyspark():
        from streaming.realtime_sink.pyspark_kafka_to_kudu import run_all_tables

        try:
            run_all_tables("data/kafka/cdc.incremental.binlog.jsonl", "data/kudu_pyspark")
            print("engine=pyspark realtime=ok")
            return
        except Exception as exc:
            print(f"engine=pyspark realtime=failed fallback=local reason={exc}")

    from streaming.realtime_sink.kafka_to_kudu import upsert_rows

    upsert_rows(
        Path("data/kafka/cdc.incremental.binlog.jsonl"),
        Path("data/kudu"),
        Path("data/checkpoints/realtime_sink.json")
    )
    print("engine=local realtime=ok")


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in {"all", "offline"}:
        run_offline()
    if target in {"all", "realtime"}:
        run_realtime()


if __name__ == "__main__":
    main()
