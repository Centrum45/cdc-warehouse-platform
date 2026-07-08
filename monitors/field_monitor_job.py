from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitors.field_alter_sql import build_add_columns_sql


def load_columns(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["columns"]


def diff_columns(platform_metadata: Path, dba_metadata: Path) -> list[dict[str, str]]:
    platform = {column["name"]: column for column in load_columns(platform_metadata)}
    dba = load_columns(dba_metadata)
    return [column for column in dba if column["name"] not in platform]


def main() -> None:
    platform_metadata = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("metadata/tables/basiccomment.avatar_commentbatchsource.json")
    dba_metadata = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("metadata/dba/basiccomment.avatar_commentbatchsource.json")
    missing = diff_columns(platform_metadata, dba_metadata)
    sql = build_add_columns_sql("ods", "ods_basiccomment_avatar_commentbatchsource_dic", missing)
    for statement in sql:
        print(statement)


if __name__ == "__main__":
    main()
