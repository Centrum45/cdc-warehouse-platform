from __future__ import annotations

import json
import sys
from pathlib import Path


def render_ods_binlog_ddl(metadata: dict) -> str:
    return f"""create external table if not exists ods_binlog.{metadata['ods_binlog_table']} (
  content string comment 'Maxwell binlog event JSON'
)
partitioned by (dt string)
stored as textfile;
"""


def render_ods_ddl(metadata: dict) -> str:
    columns = ",\n  ".join(f"{column['name']} {column['type']}" for column in metadata["columns"])
    return f"""create external table if not exists ods.{metadata['ods_table']} (
  {columns}
)
partitioned by (dt string)
stored as parquet;
"""


def main() -> None:
    metadata_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("metadata/tables/basiccomment.avatar_commentbatchsource.json")
    output_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("warehouse/sql")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    binlog_path = output_root / "ods_binlog/ddl" / f"{metadata['ods_binlog_table']}.sql"
    ods_path = output_root / "ods/ddl" / f"{metadata['ods_table']}.sql"
    binlog_path.parent.mkdir(parents=True, exist_ok=True)
    ods_path.parent.mkdir(parents=True, exist_ok=True)
    binlog_path.write_text(render_ods_binlog_ddl(metadata), encoding="utf-8")
    ods_path.write_text(render_ods_ddl(metadata), encoding="utf-8")
    print(binlog_path)
    print(ods_path)


if __name__ == "__main__":
    main()
