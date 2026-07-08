#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
topic="${1:-cdc.incremental.binlog}"
output="${2:-data/kafka/cdc.incremental.binlog.jsonl}"
max_messages="${3:-100}"

python3 ingestion/kafka/kafka_topic_to_jsonl.py "${topic}" "${output}" "${max_messages}"
