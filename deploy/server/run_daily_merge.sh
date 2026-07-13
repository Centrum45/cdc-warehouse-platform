#!/usr/bin/env bash
set -euo pipefail

project_root="${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
mkdir -p "${project_root}/data/ops"
"${project_root}/deploy/run_job.sh" daily-merge "$@" 2>&1 | tee -a "${project_root}/data/ops/spark_sql_merge.log"
