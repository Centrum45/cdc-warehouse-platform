drop table if exists ads.ads_trade_dashboard_1d;

create external table if not exists ads.ads_trade_dashboard_1d (
  metric_name string,
  metric_value double
)
partitioned by (dt string)
stored as parquet
location '/warehouse/ads/ads_trade_dashboard_1d';
