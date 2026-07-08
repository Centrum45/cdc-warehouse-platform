insert overwrite table dim.dim_comment_batch_type partition(dt='${biz_dt}')
select 'normal', '普通批次', 0
union all
select 'priority', '优先批次', 1;

