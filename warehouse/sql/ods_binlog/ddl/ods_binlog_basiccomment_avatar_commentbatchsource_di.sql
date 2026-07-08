drop table if exists ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di;

create external table ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di (
  content string comment 'Maxwell binlog event JSON'
)
partitioned by (dt string)
stored as textfile
location '/warehouse/ods_binlog/db=basiccomment/table=avatar_commentbatchsource';
