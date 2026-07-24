#!/usr/bin/env bash
set -euo pipefail

jobs_env="${JOBS_ENV_FILE:-/etc/cdc-warehouse/jobs.env}"
if [[ -f "${jobs_env}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${jobs_env}"
  set +a
fi

action="${1:-status}"
units=(cdc-admin.service cdc-spark-streaming.service cdc-ops-refresh.service cdc-daily-merge.timer cdc-monitor.timer)
if [[ "${REALTIME_STREAMING_ENABLED:-false}" == "true" ]]; then
  units+=(cdc-realtime-streaming.service)
fi

case "${action}" in
  start)
    systemctl enable --now "${units[@]}"
    ;;
  stop)
    systemctl stop "${units[@]}" || true
    ;;
  restart)
    systemctl restart cdc-admin.service cdc-spark-streaming.service cdc-ops-refresh.service
    if [[ "${REALTIME_STREAMING_ENABLED:-false}" == "true" ]]; then
      systemctl restart cdc-realtime-streaming.service
    fi
    systemctl restart cdc-daily-merge.timer
    systemctl restart cdc-monitor.timer
    ;;
  status)
    systemctl status "${units[@]}" --no-pager
    ;;
  logs)
    unit="${2:-cdc-admin.service}"
    journalctl -u "${unit}" -f
    ;;
  merge)
    systemctl start cdc-daily-merge.service
    journalctl -u cdc-daily-merge.service -n 200 --no-pager
    ;;
  monitors)
    systemctl start cdc-monitor.service
    journalctl -u cdc-monitor.service -n 200 --no-pager
    ;;
  health)
    "$(cd "$(dirname "$0")" && pwd)/healthcheck.sh"
    ;;
  preflight)
    "$(cd "$(dirname "$0")" && pwd)/preflight.sh"
    ;;
  smoke)
    shift
    "$(cd "$(dirname "$0")" && pwd)/prod_smoke.sh" "$@"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|status|logs [unit]|merge|monitors|health|preflight|smoke [--biz-dt yyyy-mm-dd] [--merge]}" >&2
    exit 2
    ;;
esac
