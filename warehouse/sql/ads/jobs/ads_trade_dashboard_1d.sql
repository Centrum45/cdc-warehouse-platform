insert overwrite table ads.ads_trade_dashboard_1d partition(dt='${biz_dt}')
-- daily metrics from DWS
select 'gmv', sum(pay_amount)
from dws.dws_trade_user_1d
where dt = '${biz_dt}'
union all
select 'pay_user_cnt', count(distinct user_id)
from dws.dws_trade_user_1d
where dt = '${biz_dt}'
union all
-- cumulative metrics from DWT
select 'total_gmv', sum(total_pay_amount)
from dwt.dwt_trade_user_td
where dt = '${biz_dt}'
union all
select 'total_user_cnt', count(distinct user_id)
from dwt.dwt_trade_user_td
where dt = '${biz_dt}'
union all
select 'avg_order_per_user', cast(sum(total_order_cnt) as double) / nullif(count(distinct user_id), 0)
from dwt.dwt_trade_user_td
where dt = '${biz_dt}';
