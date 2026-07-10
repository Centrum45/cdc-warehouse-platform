drop table if exists ads.ads_comment_dashboard_1d;

create external table if not exists ads.ads_comment_dashboard_1d (
  metric_name string,
  metric_value bigint
)
partitioned by (dt string)
row format delimited fields terminated by ','
stored as textfile
location '/warehouse/ads/ads_comment_dashboard_1d';
