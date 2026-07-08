insert overwrite table ods.ods_basiccomment_avatar_commentbatchsource_dic
partition(dt)
select id, batchnumber, batchtype, ctime, utime, ver, source_channel, dt
from (
  select
    *,
    row_number() over(partition by id order by ver desc, binlog_type desc) rn
  from (
    select
      case
        when get_json_object(content, '$.type') in ('insert', 'bootstrap-insert') then 1
        when get_json_object(content, '$.type') = 'update' then 2
        when get_json_object(content, '$.type') = 'delete' then 3
      end as binlog_type,
      cast(get_json_object(get_json_object(content, '$.data'), '$.id') as bigint) id,
      cast(get_json_object(get_json_object(content, '$.data'), '$.batchnumber') as string) batchnumber,
      cast(get_json_object(get_json_object(content, '$.data'), '$.batchtype') as string) batchtype,
      case
        when get_json_object(content, '$.type') != 'bootstrap-insert'
        then from_unixtime(unix_timestamp(get_json_object(get_json_object(content, '$.data'), '$.ctime')) + 28800, 'yyyy-MM-dd HH:mm:ss')
        else get_json_object(get_json_object(content, '$.data'), '$.ctime')
      end as ctime,
      case
        when get_json_object(content, '$.type') != 'bootstrap-insert'
        then from_unixtime(unix_timestamp(get_json_object(get_json_object(content, '$.data'), '$.utime')) + 28800, 'yyyy-MM-dd HH:mm:ss')
        else get_json_object(get_json_object(content, '$.data'), '$.utime')
      end as utime,
      cast(get_json_object(get_json_object(content, '$.data'), '$.ver') as int) ver,
      cast(get_json_object(get_json_object(content, '$.data'), '$.source_channel') as string) source_channel,
      substr(
        case
          when get_json_object(content, '$.type') != 'bootstrap-insert'
          then from_unixtime(unix_timestamp(get_json_object(get_json_object(content, '$.data'), '$.ctime')) + 28800, 'yyyy-MM-dd HH:mm:ss')
          else get_json_object(get_json_object(content, '$.data'), '$.ctime')
        end,
        1,
        10
      ) dt
    from ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di
    where dt >= date_add(current_date, -1)
      and get_json_object(content, '$.type') != 'bootstrap-insert'
      and from_unixtime(cast(get_json_object(content, '$.ts') as bigint), 'yyyy-MM-dd HH:mm:ss') >= date_add(current_date, -1)
      and from_unixtime(cast(get_json_object(content, '$.ts') as bigint), 'yyyy-MM-dd HH:mm:ss') <= concat(date_add(current_date, 0), ' 00:00:00')

    union all

    select
      1 as binlog_type,
      id, batchnumber, batchtype, ctime, utime, ver, source_channel, dt
    from ods.ods_basiccomment_avatar_commentbatchsource_dic
    where dt in (
      select distinct substr(
        case
          when get_json_object(content, '$.type') != 'bootstrap-insert'
          then from_unixtime(unix_timestamp(get_json_object(get_json_object(content, '$.data'), '$.ctime')) + 28800, 'yyyy-MM-dd HH:mm:ss')
          else get_json_object(get_json_object(content, '$.data'), '$.ctime')
        end,
        1,
        10
      ) dt
      from ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di
      where dt >= date_add(current_date, -1)
        and get_json_object(content, '$.type') != 'bootstrap-insert'
    )
  ) t
) tt
where tt.rn = 1
  and tt.binlog_type != 3;
