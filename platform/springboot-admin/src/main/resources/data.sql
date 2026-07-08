use cdc_warehouse_admin;

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
