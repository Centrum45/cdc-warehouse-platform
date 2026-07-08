create database if not exists ods_binlog;
create database if not exists ods;
create database if not exists dim;
create database if not exists dwd;
create database if not exists dws;
create database if not exists dwt;
create database if not exists ads;

-- warehouse/sql/ads/ddl/ads_comment_dashboard_1d.sql
create external table if not exists ads.ads_comment_dashboard_1d (
  metric_name string,
  metric_value bigint
)
partitioned by (dt string)
stored as parquet;


-- warehouse/sql/ads/ddl/ads_trade_dashboard_1d.sql
create external table if not exists ads.ads_trade_dashboard_1d (
  metric_name string,
  metric_value double
)
partitioned by (dt string)
stored as parquet;

-- warehouse/sql/dim/ddl/dim_comment_batch_type.sql
create external table if not exists dim.dim_comment_batch_type (
  batchtype string,
  batchtype_name string,
  is_priority int
)
partitioned by (dt string)
stored as parquet;


-- warehouse/sql/dwd/ddl/dwd_comment_batch_detail_di.sql
create external table if not exists dwd.dwd_comment_batch_detail_di (
  id bigint,
  batchnumber string,
  batchtype string,
  batchtype_name string,
  ctime string,
  utime string,
  ver int
)
partitioned by (dt string)
stored as parquet;


-- warehouse/sql/dwd/ddl/dwd_trade_order_detail_di.sql
create external table if not exists dwd.dwd_trade_order_detail_di (
  order_id bigint,
  user_id bigint,
  order_no string,
  pay_amount double,
  order_status string,
  user_name string,
  ctime string,
  utime string
)
partitioned by (dt string)
stored as parquet;

-- warehouse/sql/dws/ddl/dws_comment_batch_1d.sql
create external table if not exists dws.dws_comment_batch_1d (
  batchtype string,
  batch_cnt bigint,
  priority_batch_cnt bigint
)
partitioned by (dt string)
stored as parquet;


-- warehouse/sql/dws/ddl/dws_trade_user_1d.sql
create external table if not exists dws.dws_trade_user_1d (
  user_id bigint,
  order_cnt bigint,
  pay_amount double
)
partitioned by (dt string)
stored as parquet;

-- warehouse/sql/dwt/ddl/dwt_comment_batch_topic_td.sql
create external table if not exists dwt.dwt_comment_batch_topic_td (
  batchtype string,
  total_batch_cnt bigint,
  priority_batch_cnt bigint,
  latest_batch_time string
)
partitioned by (dt string)
stored as parquet;

-- warehouse/sql/ods/ddl/ods_basiccomment_avatar_commentbatchsource_dic.sql
drop table if exists ods.ods_basiccomment_avatar_commentbatchsource_dic;

create external table ods.ods_basiccomment_avatar_commentbatchsource_dic (
  id bigint,
  batchnumber string,
  batchtype string,
  ctime string,
  utime string,
  ver int,
  source_channel string
)
partitioned by (dt string)
row format delimited fields terminated by ','
stored as textfile
location '/warehouse/ods/db=basiccomment/table=avatar_commentbatchsource'
tblproperties ('skip.header.line.count'='1');

-- warehouse/sql/ods/ddl/ods_trade_order_info_dic.sql
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
row format delimited fields terminated by ','
stored as textfile
location '/warehouse/ods/db=trade/table=order_info'
tblproperties ('skip.header.line.count'='1');

-- warehouse/sql/ods/ddl/ods_user_user_info_dic.sql
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

-- warehouse/sql/ods_binlog/ddl/ods_binlog_basiccomment_avatar_commentbatchsource_di.sql
drop table if exists ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di;

create external table ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di (
  content string comment 'Maxwell binlog event JSON'
)
partitioned by (dt string)
stored as textfile
location '/warehouse/ods_binlog/db=basiccomment/table=avatar_commentbatchsource';

-- warehouse/sql/ods_binlog/ddl/ods_binlog_trade_order_info_di.sql
drop table if exists ods_binlog.ods_binlog_trade_order_info_di;

create external table ods_binlog.ods_binlog_trade_order_info_di (
  content string comment 'Maxwell binlog event JSON'
)
partitioned by (dt string)
stored as textfile
location '/warehouse/ods_binlog/db=trade/table=order_info';

-- warehouse/sql/ods_binlog/ddl/ods_binlog_user_user_info_di.sql
drop table if exists ods_binlog.ods_binlog_user_user_info_di;

create external table ods_binlog.ods_binlog_user_user_info_di (
  content string comment 'Maxwell binlog event JSON'
)
partitioned by (dt string)
stored as textfile
location '/warehouse/ods_binlog/db=user/table=user_info';

