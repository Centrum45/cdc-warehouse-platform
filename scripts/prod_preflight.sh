#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

jobs_env="${1:-deploy/prod/jobs.env}"
admin_env="${2:-deploy/prod/admin.env}"

if [[ ! -f "${jobs_env}" ]]; then
  echo "missing jobs env file: ${jobs_env}" >&2
  echo "copy deploy/prod/jobs.env.example first" >&2
  exit 1
fi

if [[ ! -f "${admin_env}" ]]; then
  echo "missing admin env file: ${admin_env}" >&2
  echo "copy deploy/prod/admin.env.example first" >&2
  exit 1
fi

bash deploy/run_job.sh --env-file "${jobs_env}" --help >/dev/null
bash scripts/check_dependencies.sh --mode prod
bash deploy/server/preflight.sh "${admin_env}" "${jobs_env}"
