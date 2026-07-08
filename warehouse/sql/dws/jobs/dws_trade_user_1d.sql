insert overwrite table dws.dws_trade_user_1d partition(dt='${biz_dt}')
select
  user_id,
  count(1) as order_cnt,
  sum(pay_amount) as pay_amount
from dwd.dwd_trade_order_detail_di
where dt = '${biz_dt}'
group by user_id;
