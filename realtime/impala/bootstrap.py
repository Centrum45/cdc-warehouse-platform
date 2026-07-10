from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from realtime.kudu.kudu_client import KuduClient


REALTIME_DB = "realtime"
DDL_DIR = ROOT / "realtime" / "kudu" / "ddl"
VIEW_DIR = ROOT / "realtime" / "impala" / "views"


def sql_files() -> list[Path]:
    return sorted(DDL_DIR.glob("*.sql")) + sorted(VIEW_DIR.glob("*.sql"))


def split_sql(text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue
        current.append(raw_line)
        if line.endswith(";"):
            statement = "\n".join(current).strip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    tail = "\n".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def load_statements() -> list[tuple[Path, str]]:
    loaded: list[tuple[Path, str]] = []
    for path in sql_files():
        for statement in split_sql(path.read_text(encoding="utf-8")):
            loaded.append((path, statement))
    return loaded


def bootstrap_realtime(client: KuduClient | None = None, dry_run: bool = False) -> list[dict[str, Any]]:
    """Create realtime DB, Kudu tables, and Impala views."""
    results: list[dict[str, Any]] = []
    client = client or KuduClient()

    statements = [(Path("<database>"), f"CREATE DATABASE IF NOT EXISTS {REALTIME_DB}")]
    statements.extend(load_statements())

    for path, statement in statements:
        if dry_run:
            results.append({"success": True, "file": str(path), "sql": statement})
            continue
        result = client.execute(statement)
        result["file"] = str(path)
        result["sql"] = statement[:120]
        results.append(result)
        if not result.get("success"):
            break
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize realtime Kudu/Impala objects.")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without connecting to Impala.")
    args = parser.parse_args()

    client = KuduClient()
    if not args.dry_run and not client.is_available:
        raise SystemExit("impyla not installed. Run dry-run or install impyla thrift-sasl.")

    results = bootstrap_realtime(client=client, dry_run=args.dry_run)
    for result in results:
        status = "OK" if result.get("success") else "FAIL"
        print(f"{status} {result.get('file')} {result.get('sql', result.get('msg', ''))}")
    if any(not result.get("success") for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
