#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
uid="$(id -u)"
plist="$PWD/scripts/com.cdcwarehouse.ops-refresh.plist"

launchctl bootout "gui/${uid}" "${plist}" >/dev/null 2>&1 || true
echo "ops launchd refresher stopped: com.cdcwarehouse.ops-refresh"
