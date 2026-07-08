drop table if exists ods.ods_user_user_info_dic;

create external table ods.ods_user_user_info_dic (
  id bigint,
  user_name string,
  mobile string,
  email string,
  register_time string,
  ctime string,
  utime string,
  ver int
)
partitioned by (dt string)
row format delimited fields terminated by ','
stored as textfile
location '/warehouse/ods/db=user/table=user_info'
tblproperties ('skip.header.line.count'='1');
