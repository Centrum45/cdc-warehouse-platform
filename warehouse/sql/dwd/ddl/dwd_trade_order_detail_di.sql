create external table if not exists dwd.dwd_trade_order_detail_di (
  order_id bigint,
  user_id bigint,
  order_no string,
  pay_amount double,
  order_status string,
  user_name string,
  ctime string,
  utime string
)
partitioned by (dt string)
stored as parquet;
