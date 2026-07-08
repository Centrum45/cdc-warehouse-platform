#!/usr/bin/env bash
set -euo pipefail

python3 ingestion/mock/generate_binlog_events.py
python3 streaming/offline_sink/kafka_to_local_lake.py data/kafka/cdc.incremental.binlog.jsonl data/lake metadata/rules/sensitive_columns.json data/progress
python3 warehouse/jobs/merge_ods_snapshot.py metadata/tables/basiccomment.avatar_commentbatchsource.json data/lake 2026-07-06 data/progress 999999999
python3 warehouse/generator/render_ods_merge_sql.py metadata/tables/basiccomment.avatar_commentbatchsource.json warehouse/sql/ods/merge/merge_ods_basiccomment_avatar_commentbatchsource_dic.sql

echo "ODS snapshot:"
sed -n '1,20p' data/lake/ods/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-06/part-00000.csv
