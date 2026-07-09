#!/usr/bin/env bash
set -euo pipefail

action="${1:-status}"
units=(cdc-admin.service cdc-spark-streaming.service cdc-ops-refresh.service cdc-daily-merge.timer)

case "${action}" in
  start)
    systemctl enable --now "${units[@]}"
    ;;
  stop)
    systemctl stop "${units[@]}" || true
    ;;
  restart)
    systemctl restart cdc-admin.service cdc-spark-streaming.service cdc-ops-refresh.service
    systemctl restart cdc-daily-merge.timer
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
    echo "usage: $0 {start|stop|restart|status|logs [unit]|merge|health|preflight|smoke [--biz-dt yyyy-mm-dd] [--merge]}" >&2
    exit 2
    ;;
esac
