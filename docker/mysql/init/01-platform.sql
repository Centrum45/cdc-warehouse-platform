create database if not exists cdc_warehouse_admin default character set utf8mb4 collate utf8mb4_unicode_ci;

use cdc_warehouse_admin;

create table if not exists table_metadata (
  id bigint primary key auto_increment,
  source_database varchar(128) not null,
  source_table varchar(128) not null,
  ods_binlog_table varchar(256) not null,
  ods_table varchar(256) not null,
  primary_keys varchar(512) not null,
  version_column varchar(128) not null,
  partition_column varchar(128) not null,
  columns_json text not null,
  enabled tinyint not null default 1,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp on update current_timestamp,
  unique key uk_source_table (source_database, source_table)
);

create table if not exists sync_task (
  id bigint primary key auto_increment,
  task_name varchar(256) not null,
  task_type varchar(64) not null,
  command text not null,
  schedule_expr varchar(128) not null,
  enabled tinyint not null default 1,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp on update current_timestamp,
  unique key uk_task_name (task_name)
);

create table if not exists replay_record (
  id bigint primary key auto_increment,
  source_database varchar(128) not null,
  source_table varchar(128) not null,
  start_time varchar(32) not null,
  end_time varchar(32) not null,
  command text not null,
  status varchar(32) not null default 'CREATED',
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp on update current_timestamp
);

create table if not exists monitor_result (
  id bigint primary key auto_increment,
  monitor_type varchar(64) not null,
  source_database varchar(128) not null,
  source_table varchar(128) not null,
  status varchar(32) not null,
  message text,
  metric_value varchar(128),
  created_at timestamp not null default current_timestamp
);

create table if not exists alert_record (
  id bigint primary key auto_increment,
  alert_type varchar(64) not null,
  target varchar(256) not null,
  title varchar(256) not null,
  body text,
  status varchar(32) not null default 'CREATED',
  created_at timestamp not null default current_timestamp
);

create table if not exists sensitive_rule (
  id bigint primary key auto_increment,
  column_pattern varchar(128) not null,
  action varchar(32) not null,
  default_value varchar(256),
  enabled tinyint not null default 1,
  created_at timestamp not null default current_timestamp,
  unique key uk_sensitive_column_pattern (column_pattern)
);

create table if not exists special_value_rule (
  id bigint primary key auto_increment,
  source_database varchar(128) not null,
  source_table varchar(128) not null,
  column_name varchar(128) not null,
  rule_type varchar(32) not null,
  rule_value varchar(512),
  enabled tinyint not null default 1,
  created_at timestamp not null default current_timestamp
);

create table if not exists schema_snapshot (
  id bigint primary key auto_increment,
  source_type varchar(32) not null,
  source_database varchar(128) not null,
  source_table varchar(128) not null,
  columns_json text not null,
  created_at timestamp not null default current_timestamp,
  key idx_schema_snapshot_table (source_type, source_database, source_table)
);

insert ignore into table_metadata (
  source_database, source_table, ods_binlog_table, ods_table,
  primary_keys, version_column, partition_column, columns_json
) values (
  'basiccomment',
  'avatar_commentbatchsource',
  'ods_binlog_basiccomment_avatar_commentbatchsource_di',
  'ods_basiccomment_avatar_commentbatchsource_dic',
  'id',
  'ver',
  'ctime',
  '[{"name":"id","type":"bigint"},{"name":"batchnumber","type":"string"},{"name":"batchtype","type":"string"},{"name":"ctime","type":"string"},{"name":"utime","type":"string"},{"name":"ver","type":"int"},{"name":"source_channel","type":"string"}]'
);

insert ignore into sync_task (task_name, task_type, command, schedule_expr) values
('offline_sink', 'SparkStreaming', 'python3 streaming/offline_sink/spark_streaming_to_hdfs.py', 'continuous'),
('ods_merge', 'SparkSQL', './scripts/run_daily_ods_merge.sh ${biz_dt}', '0 30 2 * * ?');

insert into monitor_result (monitor_type, source_database, source_table, status, message, metric_value) values
('delay', 'basiccomment', 'avatar_commentbatchsource', 'OK', 'delay within threshold', '0'),
('field', 'basiccomment', 'avatar_commentbatchsource', 'OK', 'metadata aligned', '0');

insert ignore into sensitive_rule (column_pattern, action, default_value) values
('mobile', 'md5', null),
('phone', 'md5', null),
('email', 'md5', null),
('id_card', 'default', '');

insert into special_value_rule (source_database, source_table, column_name, rule_type, rule_value) values
('basiccomment', 'avatar_commentbatchsource', 'id', 'not_null', null),
('basiccomment', 'avatar_commentbatchsource', 'ver', 'increasing', null),
('basiccomment', 'avatar_commentbatchsource', 'batchtype', 'special_values', 'unknown,test');
