create table if not exists realtime.avatar_commentbatchsource (
  id bigint,
  batchnumber string,
  batchtype string,
  ctime string,
  utime string,
  ver int,
  event_ts bigint,
  primary key (id)
)
partition by hash(id) partitions 8
stored as kudu
tblproperties ('kudu.num_tablet_replicas'='1');
