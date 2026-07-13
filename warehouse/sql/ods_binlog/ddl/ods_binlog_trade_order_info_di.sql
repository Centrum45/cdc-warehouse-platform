drop table if exists ods_binlog.ods_binlog_trade_order_info_di;

create external table ods_binlog.ods_binlog_trade_order_info_di (
  database_name string comment 'source database',
  table_name string comment 'source table',
  type string comment 'Maxwell event type',
  ts bigint comment 'Maxwell event timestamp',
  xid bigint comment 'MySQL transaction id',
  raw_json string comment 'raw Maxwell event JSON',
  data_json string comment 'Maxwell data JSON',
  old_json string comment 'Maxwell old JSON'
)
partitioned by (dt string)
stored as parquet
location '/warehouse/ods_binlog/db=trade/table=order_info';
