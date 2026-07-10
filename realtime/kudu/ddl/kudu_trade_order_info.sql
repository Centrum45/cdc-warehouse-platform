create table realtime.order_info (
  id bigint primary key,
  user_id bigint,
  order_no string,
  pay_amount double,
  order_status string,
  ctime string,
  utime string,
  ver int,
  event_ts bigint
)
partition by hash(id) partitions 8
stored as kudu;
