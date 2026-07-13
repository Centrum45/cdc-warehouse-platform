drop table if exists dim.dim_user_info;

create external table if not exists dim.dim_user_info (
  user_id bigint,
  user_name string,
  mobile string,
  email string,
  register_time string
)
partitioned by (dt string)
stored as parquet
location '/warehouse/dim/dim_user_info';
