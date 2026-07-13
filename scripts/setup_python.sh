#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

venv_dir="${VENV_DIR:-.venv}"
python_bin="${PYTHON_BIN:-}"
python_explicit="false"

usage() {
  cat >&2 <<'EOF'
usage:
  scripts/setup_python.sh [--python PYTHON] [--venv DIR]

Creates a local virtualenv and installs requirements.txt.
Default venv: .venv
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      python_bin="${2:-}"
      if [[ -z "${python_bin}" ]]; then
        usage
        exit 2
      fi
      python_explicit="true"
      shift 2
      ;;
    --venv)
      venv_dir="${2:-}"
      if [[ -z "${venv_dir}" ]]; then
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
      echo "unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
done

python_supported() {
  "$1" - <<'PY' >/dev/null 2>&1
import sys
major, minor = sys.version_info[:2]
raise SystemExit(0 if (major, minor) >= (3, 8) and (major, minor) <= (3, 11) else 1)
PY
}

find_python() {
  local candidate
  if [[ "${python_explicit}" == "true" ]]; then
    if command -v "${python_bin}" >/dev/null 2>&1 && python_supported "${python_bin}"; then
      echo "${python_bin}"
      return 0
    fi
    return 1
  fi
  for candidate in "${python_bin}" python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3 python; do
    if [[ -z "${candidate}" ]]; then
      continue
    fi
    if command -v "${candidate}" >/dev/null 2>&1 && python_supported "${candidate}"; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

selected_python="$(find_python)" || {
  echo "no supported Python found" >&2
  echo "required: Python 3.8-3.11 for PySpark compatibility" >&2
  echo "or pass: scripts/setup_python.sh --python /path/to/python" >&2
  exit 1
}

echo "using python: $(${selected_python} -c 'import sys; print(sys.executable)')"
"${selected_python}" -m venv "${venv_dir}"
"${venv_dir}/bin/python" -m pip install --upgrade pip
"${venv_dir}/bin/python" -m pip install -r requirements.txt

echo "venv ready: ${venv_dir}"
echo "run tests: ./scripts/test.sh"
