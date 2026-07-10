insert overwrite table dwt.dwt_trade_user_td partition(dt='${biz_dt}')
select
  coalesce(today.user_id, yesterday.user_id) as user_id,
  coalesce(yesterday.total_order_cnt, 0) + coalesce(today.order_cnt, 0) as total_order_cnt,
  coalesce(yesterday.total_pay_amount, 0) + coalesce(today.pay_amount, 0) as total_pay_amount,
  coalesce(yesterday.first_order_date, '${biz_dt}') as first_order_date,
  '${biz_dt}' as last_order_date
from (
  select user_id, order_cnt, pay_amount
  from dws.dws_trade_user_1d
  where dt = '${biz_dt}'
) today
full outer join (
  select user_id, total_order_cnt, total_pay_amount, first_order_date
  from dwt.dwt_trade_user_td
  where dt = date_sub('${biz_dt}', 1)
) yesterday
on today.user_id = yesterday.user_id;
