#!/usr/bin/env bash
set -euo pipefail

database="${1:?database required}"
table="${2:?table required}"

metadata_path="metadata/tables/${database}.${table}.json"

python3 scripts/bootstrap_mysql_table.py "${metadata_path}" --replace-binlog --replace-ods
