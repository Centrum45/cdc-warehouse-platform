drop table if exists ods.ods_trade_order_info_dic;

create external table ods.ods_trade_order_info_dic (
  id bigint,
  user_id bigint,
  order_no string,
  pay_amount double,
  order_status string,
  ctime string,
  utime string,
  ver int
)
partitioned by (dt string)
stored as parquet
location '/warehouse/ods/db=trade/table=order_info';
