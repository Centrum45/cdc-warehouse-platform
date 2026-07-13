#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

./scripts/docker_up.sh
./scripts/init_hdfs_hive.sh
./scripts/check_local_stack.sh
