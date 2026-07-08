create table realtime.avatar_commentbatchsource (
  id bigint primary key,
  batchnumber string,
  batchtype string,
  ctime string,
  utime string,
  ver int,
  event_ts bigint
)
partition by hash(id) partitions 8
stored as kudu;

