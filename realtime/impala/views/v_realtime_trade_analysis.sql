create view if not exists realtime.v_realtime_trade_analysis as
select
  order_status,
  count(1) as order_cnt,
  sum(pay_amount) as total_gmv,
  avg(pay_amount) as avg_order_value,
  max(utime) as latest_order_time
from realtime.order_info
group by order_status;
