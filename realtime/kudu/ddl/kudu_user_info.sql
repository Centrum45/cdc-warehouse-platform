create table realtime.user_info (
  id bigint primary key,
  user_name string,
  mobile string,
  email string,
  register_time string,
  ctime string,
  utime string,
  ver int,
  event_ts bigint
)
partition by hash(id) partitions 8
stored as kudu;
