insert overwrite table dwd.dwd_trade_order_detail_di partition(dt='${biz_dt}')
select
  o.id as order_id,
  o.user_id,
  o.order_no,
  o.pay_amount,
  o.order_status,
  u.user_name,
  o.ctime,
  o.utime
from ods.ods_trade_order_info_dic o
left join ods.ods_user_user_info_dic u
  on o.user_id = u.id
where o.dt = '${biz_dt}';
