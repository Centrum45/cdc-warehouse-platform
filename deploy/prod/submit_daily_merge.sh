#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
env_file="${1:-deploy/prod/jobs.env}"
biz_dt="${2:-}"

if [[ -z "${biz_dt}" ]]; then
  exec bash deploy/run_job.sh --env-file "${env_file}" daily-merge
fi

exec bash deploy/run_job.sh --env-file "${env_file}" daily-merge "${biz_dt}"
