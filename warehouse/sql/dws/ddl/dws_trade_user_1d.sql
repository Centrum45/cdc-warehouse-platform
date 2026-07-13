drop table if exists dws.dws_trade_user_1d;

create external table if not exists dws.dws_trade_user_1d (
  user_id bigint,
  order_cnt bigint,
  pay_amount double
)
partitioned by (dt string)
stored as parquet
location '/warehouse/dws/dws_trade_user_1d';
