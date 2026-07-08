insert overwrite table dwt.dwt_comment_batch_topic_td partition(dt='${biz_dt}')
select
  coalesce(today.batchtype, yesterday.batchtype) as batchtype,
  coalesce(yesterday.total_batch_cnt, 0) + coalesce(today.batch_cnt, 0) as total_batch_cnt,
  coalesce(yesterday.priority_batch_cnt, 0) + coalesce(today.priority_batch_cnt, 0) as priority_batch_cnt,
  '${biz_dt}' as latest_batch_time
from (
  select batchtype, batch_cnt, priority_batch_cnt
  from dws.dws_comment_batch_1d
  where dt = '${biz_dt}'
) today
full outer join (
  select batchtype, total_batch_cnt, priority_batch_cnt
  from dwt.dwt_comment_batch_topic_td
  where dt = date_sub('${biz_dt}', 1)
) yesterday
on today.batchtype = yesterday.batchtype;
