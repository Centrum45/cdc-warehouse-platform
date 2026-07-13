#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

./scripts/check_local_stack.sh
./scripts/verify_end_to_end.sh
