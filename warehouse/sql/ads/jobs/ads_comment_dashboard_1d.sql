insert overwrite table ads.ads_comment_dashboard_1d partition(dt='${biz_dt}')
select 'comment_batch_total', sum(total_batch_cnt)
from dwt.dwt_comment_batch_topic_td
where dt = '${biz_dt}'
union all
select 'comment_batch_priority_total', sum(priority_batch_cnt)
from dwt.dwt_comment_batch_topic_td
where dt = '${biz_dt}';
