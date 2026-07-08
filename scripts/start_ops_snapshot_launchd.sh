#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/ops

uid="$(id -u)"
plist="$PWD/scripts/com.cdcwarehouse.ops-refresh.plist"

launchctl bootout "gui/${uid}" "${plist}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/${uid}" "${plist}"
launchctl enable "gui/${uid}/com.cdcwarehouse.ops-refresh"
launchctl kickstart -k "gui/${uid}/com.cdcwarehouse.ops-refresh"

echo "ops launchd refresher started: com.cdcwarehouse.ops-refresh"
