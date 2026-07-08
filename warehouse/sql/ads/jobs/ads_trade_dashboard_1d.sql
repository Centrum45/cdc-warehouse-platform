insert overwrite table ads.ads_trade_dashboard_1d partition(dt='${biz_dt}')
select 'gmv', sum(pay_amount)
from dws.dws_trade_user_1d
where dt = '${biz_dt}'
union all
select 'pay_user_cnt', count(distinct user_id)
from dws.dws_trade_user_1d
where dt = '${biz_dt}';
