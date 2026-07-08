insert overwrite table dws.dws_comment_batch_1d partition(dt='${biz_dt}')
select
  batchtype,
  count(1) as batch_cnt,
  sum(case when batchtype = 'priority' then 1 else 0 end) as priority_batch_cnt
from dwd.dwd_comment_batch_detail_di
where dt = '${biz_dt}'
group by batchtype;

