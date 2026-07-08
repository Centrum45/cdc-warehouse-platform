#!/usr/bin/env bash
set -euo pipefail

docker exec cdc-warehouse-mysql mysql -uroot -proot basiccomment -e "
insert into avatar_commentbatchsource (id, batchnumber, batchtype, ctime, utime, ver, source_channel)
values (9001, 'B202607069001', 'docker_seed', '2026-07-06 12:00:00', now(), 1, 'docker')
on duplicate key update batchtype='priority', utime=now(), ver=ver+1;
"

docker exec cdc-warehouse-kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic cdc.incremental.binlog \
  --from-beginning \
  --max-messages 5 \
  --timeout-ms 10000 || true
