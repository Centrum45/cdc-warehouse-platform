from __future__ import annotations

from warehouse.replay.replay_plan import ReplayPlan


def build_replay_sql(plan: ReplayPlan, ods_binlog_table: str) -> str:
    return f"""insert into table ods_binlog.{ods_binlog_table}
select content, dt
from ods_binlog.{ods_binlog_table}
where get_json_object(content, '$.database') = '{plan.database}'
  and get_json_object(content, '$.table') = '{plan.table}'
  and from_unixtime(cast(get_json_object(content, '$.ts') as bigint), 'yyyy-MM-dd HH:mm:ss') >= '{plan.start_time}'
  and from_unixtime(cast(get_json_object(content, '$.ts') as bigint), 'yyyy-MM-dd HH:mm:ss') < '{plan.end_time}';
"""

