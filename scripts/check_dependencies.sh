#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mode="local"

usage() {
  cat >&2 <<'EOF'
usage:
  scripts/check_dependencies.sh [--mode local|prod|ci]

local: checks local developer tools.
prod : checks server runtime tools and env placeholders.
ci   : checks static CI dependencies.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
done

ok=0
fail=0
warn=0

pass() { printf '[OK]   %s\n' "$*"; ok=$((ok + 1)); }
bad() { printf '[FAIL] %s\n' "$*"; fail=$((fail + 1)); }
note() { printf '[WARN] %s\n' "$*"; warn=$((warn + 1)); }

check_cmd() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "command ${name}"
  else
    bad "missing command ${name}"
  fi
}

check_optional_cmd() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "command ${name}"
  else
    note "optional command missing: ${name}"
  fi
}

find_python_module() {
  local module="$1"
  local candidate
  for candidate in "${PYTHON_BIN:-}" .venv/bin/python python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3 python; do
    if [[ -z "${candidate}" ]]; then
      continue
    fi
    if command -v "${candidate}" >/dev/null 2>&1 && "${candidate}" -c "import ${module}" >/dev/null 2>&1; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

check_module() {
  local module="$1"
  local python
  if python="$(find_python_module "${module}")"; then
    pass "python module ${module} ($(${python} -c 'import sys; print(sys.executable)'))"
  else
    bad "missing python module ${module}; run scripts/setup_python.sh"
  fi
}

check_optional_module() {
  local module="$1"
  local python
  if python="$(find_python_module "${module}")"; then
    pass "python module ${module} ($(${python} -c 'import sys; print(sys.executable)'))"
  else
    note "optional python module missing: ${module}"
  fi
}

case "${mode}" in
  local)
    check_cmd bash
    check_cmd docker
    check_cmd python3
    check_optional_cmd mvn
    check_module pyarrow
    check_module yaml
    check_module pyspark
    check_module pymysql
    check_optional_module impala
    ;;
  prod)
    check_cmd bash
    check_cmd java
    check_cmd python3
    check_optional_cmd spark-submit
    check_optional_cmd mvn
    check_module pyarrow
    check_module pyspark
    check_module pymysql
    if [[ -f deploy/prod/jobs.env ]]; then
      bash deploy/run_job.sh --env-file deploy/prod/jobs.env --help >/dev/null && pass "deploy/prod/jobs.env loadable"
    else
      note "deploy/prod/jobs.env not found"
    fi
    ;;
  ci)
    check_cmd bash
    check_cmd python3
    check_module pyarrow
    check_module yaml
    ;;
  *)
    echo "invalid mode: ${mode}" >&2
    usage
    exit 2
    ;;
esac

printf '\nsummary: ok=%d warn=%d fail=%d\n' "${ok}" "${warn}" "${fail}"
[[ "${fail}" -eq 0 ]]
