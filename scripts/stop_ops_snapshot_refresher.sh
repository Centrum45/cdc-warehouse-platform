#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
pid_file="data/ops/refresher.pid"

if [[ ! -f "${pid_file}" ]]; then
  echo "ops refresher not running"
  exit 0
fi

pid="$(cat "${pid_file}")"
if kill -0 "${pid}" 2>/dev/null; then
  kill "${pid}"
  echo "ops refresher stopped: ${pid}"
else
  echo "ops refresher already stopped: ${pid}"
fi
