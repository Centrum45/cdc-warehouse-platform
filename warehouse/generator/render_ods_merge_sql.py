from __future__ import annotations

import json
import sys
from pathlib import Path


def hive_expr(column: dict, table_alias: str = "content") -> str:
    name = column["name"]
    col_type = column["type"]
    raw = f"get_json_object(get_json_object({table_alias}, '$.data'), '$.{name}')"
    if name in {"ctime", "utime"}:
        return f"""case
        when get_json_object({table_alias}, '$.type') != 'bootstrap-insert'
        then from_unixtime(unix_timestamp({raw}) + 28800, 'yyyy-MM-dd HH:mm:ss')
        else {raw}
      end as {name}"""
    if col_type in {"bigint", "int", "double", "float"}:
        return f"cast({raw} as {col_type}) {name}"
    return f"cast({raw} as string) {name}"


def render(metadata: dict) -> str:
    columns = [column["name"] for column in metadata["columns"]]
    select_columns = ", ".join(columns + ["dt"])
    json_columns = ",\n      ".join(hive_expr(column) for column in metadata["columns"])
    old_columns = ", ".join(columns + ["dt"])
    pk = ", ".join(metadata["primary_keys"])
    version = metadata["version_column"]
    partition_column = metadata["partition_column"]
    ods_binlog = f"ods_binlog.{metadata['ods_binlog_table']}"
    ods = f"ods.{metadata['ods_table']}"

    return f"""insert overwrite table {ods}
partition(dt)
select {select_columns}
from (
  select
    *,
    row_number() over(partition by {pk} order by {version} desc, binlog_type desc) rn
  from (
    select
      case
        when get_json_object(content, '$.type') in ('insert', 'bootstrap-insert') then 1
        when get_json_object(content, '$.type') = 'update' then 2
        when get_json_object(content, '$.type') = 'delete' then 3
      end as binlog_type,
      {json_columns},
      substr(
        case
          when get_json_object(content, '$.type') != 'bootstrap-insert'
          then from_unixtime(unix_timestamp(get_json_object(get_json_object(content, '$.data'), '$.{partition_column}')) + 28800, 'yyyy-MM-dd HH:mm:ss')
          else get_json_object(get_json_object(content, '$.data'), '$.{partition_column}')
        end,
        1,
        10
      ) dt
    from {ods_binlog}
    where dt >= date_add(current_date, -1)
      and get_json_object(content, '$.type') != 'bootstrap-insert'
      and from_unixtime(cast(get_json_object(content, '$.ts') as bigint), 'yyyy-MM-dd HH:mm:ss') >= date_add(current_date, -1)
      and from_unixtime(cast(get_json_object(content, '$.ts') as bigint), 'yyyy-MM-dd HH:mm:ss') <= concat(date_add(current_date, 0), ' 00:00:00')

    union all

    select
      1 as binlog_type,
      {old_columns}
    from {ods}
    where dt in (
      select distinct substr(
        case
          when get_json_object(content, '$.type') != 'bootstrap-insert'
          then from_unixtime(unix_timestamp(get_json_object(get_json_object(content, '$.data'), '$.{partition_column}')) + 28800, 'yyyy-MM-dd HH:mm:ss')
          else get_json_object(get_json_object(content, '$.data'), '$.{partition_column}')
        end,
        1,
        10
      ) dt
      from {ods_binlog}
      where dt >= date_add(current_date, -1)
        and get_json_object(content, '$.type') != 'bootstrap-insert'
    )
  ) t
) tt
where tt.rn = 1
  and tt.binlog_type != 3;
"""


def main() -> None:
    metadata_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("metadata/tables/basiccomment.avatar_commentbatchsource.json")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("warehouse/sql/ods/merge/merge_ods_basiccomment_avatar_commentbatchsource_dic.sql")
    with metadata_path.open("r", encoding="utf-8") as fp:
        metadata = json.load(fp)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render(metadata), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
