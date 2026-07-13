create table if not exists realtime.user_info (
  id bigint,
  user_name string,
  mobile string,
  email string,
  register_time string,
  ctime string,
  utime string,
  ver int,
  event_ts bigint,
  primary key (id)
)
partition by hash(id) partitions 8
stored as kudu
tblproperties ('kudu.num_tablet_replicas'='1');
