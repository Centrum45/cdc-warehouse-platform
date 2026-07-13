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
stored as parquet
location '/warehouse/ods/db=user/table=user_info';
