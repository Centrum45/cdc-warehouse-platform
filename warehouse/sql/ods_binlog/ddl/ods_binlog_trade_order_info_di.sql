drop table if exists ods_binlog.ods_binlog_trade_order_info_di;

create external table ods_binlog.ods_binlog_trade_order_info_di (
  content string comment 'Maxwell binlog event JSON'
)
partitioned by (dt string)
stored as textfile
location '/warehouse/ods_binlog/db=trade/table=order_info';
