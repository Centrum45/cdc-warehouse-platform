#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/docker-compose.kudu.yml"

cd "${ROOT_DIR}"

if ! python3 - <<'PY' >/dev/null 2>&1; then
import impala.dbapi
PY
  echo "Missing Python dependency: impyla. Run: scripts/setup_python.sh" >&2
  exit 1
fi

docker compose -f "${COMPOSE_FILE}" up -d

echo "Waiting for Impala on localhost:21050 ..."
for _ in $(seq 1 90); do
  if docker exec cdc-impala bash -lc "timeout 2 bash -c '</dev/tcp/127.0.0.1/21050'" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

docker exec cdc-impala impala-shell --protocol=hs2 -i 127.0.0.1:21050 -q "show databases;" >/dev/null

export IMPALA_HOST="${IMPALA_HOST:-localhost}"
export IMPALA_PORT="${IMPALA_PORT:-21050}"
export KUDU_MASTERS="${KUDU_MASTERS:-kudu-master:7051}"

python3 -m realtime.impala.bootstrap
rm -f data/checkpoints/realtime_sink_real.json
python3 scripts/run_realtime_kudu_smoke.py \
  --topic-file data/kafka/cdc.incremental.binlog.jsonl \
  --checkpoint data/checkpoints/realtime_sink_real.json
