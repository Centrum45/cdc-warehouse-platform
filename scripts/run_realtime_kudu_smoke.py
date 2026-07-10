#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from realtime.impala.bootstrap import bootstrap_realtime
from realtime.impala.query import ImpalaQuery
from realtime.kudu.kudu_client import KuduClient
from streaming.realtime_sink.kafka_to_kudu import upsert_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Realtime Kudu/Impala smoke.")
    parser.add_argument("--topic-file", default="data/kafka/cdc.incremental.binlog.jsonl")
    parser.add_argument("--kudu-root", default="data/kudu")
    parser.add_argument("--checkpoint", default="data/checkpoints/realtime_sink.json")
    parser.add_argument("--real", action="store_true", help="Use real Impala/Kudu via impyla.")
    parser.add_argument("--engine", choices=["local_csv", "kudu_impala"], default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print bootstrap SQL only.")
    args = parser.parse_args()

    client = KuduClient()
    if args.dry_run:
        for result in bootstrap_realtime(client=client, dry_run=True):
            print(f"DRY {result['file']} {result['sql']}")
        return

    if args.real:
        if not client.is_available:
            raise SystemExit("impyla not installed. Install impyla thrift-sasl or omit --real.")
        results = bootstrap_realtime(client=client)
        failed = [result for result in results if not result.get("success")]
        if failed:
            raise SystemExit(f"bootstrap failed: {failed[0].get('msg')}")

    output = upsert_rows(
        Path(args.topic_file),
        Path(args.kudu_root),
        Path(args.checkpoint),
        use_real_kudu=args.real,
        realtime_engine=args.engine,
    )
    print(f"sink={output}")

    if args.real:
        query = ImpalaQuery()
        try:
            rows = query.run_view("realtime", "v_realtime_comment_analysis")
            print(f"view_rows={rows}")
        finally:
            query.close()


if __name__ == "__main__":
    main()
