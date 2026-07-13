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
stored as parquet
location '/warehouse/ods/db=basiccomment/table=avatar_commentbatchsource';
