create table if not exists realtime.order_info (
  id bigint,
  user_id bigint,
  order_no string,
  pay_amount double,
  order_status string,
  ctime string,
  utime string,
  ver int,
  event_ts bigint,
  primary key (id)
)
partition by hash(id) partitions 8
stored as kudu
tblproperties ('kudu.num_tablet_replicas'='1');
