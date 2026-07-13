#!/usr/bin/env bash
set -euo pipefail

project_root="${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
exec "${project_root}/deploy/run_job.sh" spark-streaming
