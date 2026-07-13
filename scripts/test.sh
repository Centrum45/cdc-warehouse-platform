#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  cat >&2 <<'EOF'
usage:
  scripts/test.sh [--python PYTHON] [unittest args...]

Default args:
  discover -s tests -v

The script picks a Python interpreter that can import pyarrow. This avoids
failures when system python3 points to a different environment.
EOF
}

python_bin="${PYTHON_BIN:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      python_bin="${2:-}"
      if [[ -z "${python_bin}" ]]; then
        usage
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

find_python_with_pyarrow() {
  local candidate
  for candidate in "${python_bin}" .venv/bin/python python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3 python; do
    if [[ -z "${candidate}" ]]; then
      continue
    fi
    if command -v "${candidate}" >/dev/null 2>&1 && "${candidate}" -c 'import pyarrow' >/dev/null 2>&1; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

test_python="$(find_python_with_pyarrow)" || {
  echo "python with pyarrow not found" >&2
  echo "install dependencies: scripts/setup_python.sh" >&2
  echo "or run: scripts/test.sh --python /path/to/python" >&2
  exit 1
}

if [[ $# -eq 0 ]]; then
  set -- discover -s tests -v
fi

echo "using python: $(${test_python} -c 'import sys; print(sys.executable)')"
exec "${test_python}" -m unittest "$@"
