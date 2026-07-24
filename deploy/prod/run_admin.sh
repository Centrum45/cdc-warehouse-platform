#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
env_file="${1:-deploy/prod/admin.env}"
jobs_env_file="${2:-deploy/prod/jobs.env}"

if [[ ! -f "${env_file}" ]]; then
  echo "missing env file: ${env_file}" >&2
  echo "copy deploy/prod/admin.env.example first" >&2
  exit 1
fi

set -a
source "${env_file}"
if [[ -f "${jobs_env_file}" ]]; then
  source "${jobs_env_file}"
fi
set +a

cd platform/springboot-admin
mvn -q -DskipTests package
java -jar target/cdc-warehouse-admin-0.1.0.jar
