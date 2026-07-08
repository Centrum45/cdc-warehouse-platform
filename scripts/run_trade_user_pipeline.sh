#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 ingestion/mock/generate_trade_user_binlog_events.py
python3 streaming/offline_sink/kafka_to_local_lake.py data/kafka/cdc.trade_user.binlog.jsonl data/lake metadata/rules/sensitive_columns.json data/progress
python3 scripts/onboard_table.py metadata/dba/user.user_info.json id ver ctime
python3 scripts/onboard_table.py metadata/dba/trade.order_info.json id ver ctime
python3 warehouse/jobs/merge_ods_snapshot.py metadata/tables/user.user_info.json data/lake 2026-07-01 data/progress 999999999
python3 warehouse/jobs/merge_ods_snapshot.py metadata/tables/trade.order_info.json data/lake 2026-07-06 data/progress 999999999
python3 warehouse/jobs/local_trade_ads.py

sed -n '1,20p' data/lake/ads/trade_dashboard_1d/dt=2026-07-06/part-00000.csv
