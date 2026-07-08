create external table if not exists dwt.dwt_trade_user_td (
  user_id bigint,
  total_order_cnt bigint,
  total_pay_amount double,
  first_order_date string,
  last_order_date string
)
partitioned by (dt string)
stored as parquet;
