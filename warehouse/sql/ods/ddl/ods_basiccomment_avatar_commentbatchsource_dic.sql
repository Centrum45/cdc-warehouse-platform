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
