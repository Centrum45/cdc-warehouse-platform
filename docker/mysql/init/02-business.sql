create database if not exists basiccomment default character set utf8mb4 collate utf8mb4_unicode_ci;
create database if not exists trade default character set utf8mb4 collate utf8mb4_unicode_ci;
create database if not exists user default character set utf8mb4 collate utf8mb4_unicode_ci;

create user if not exists 'maxwell'@'%' identified by 'maxwell';
grant select, replication slave, replication client on *.* to 'maxwell'@'%';
grant all privileges on maxwell.* to 'maxwell'@'%';
flush privileges;

use basiccomment;

create table if not exists avatar_commentbatchsource (
  id bigint primary key,
  batchnumber varchar(64),
  batchtype varchar(32),
  ctime datetime,
  utime datetime,
  ver int,
  source_channel varchar(64)
);

insert into avatar_commentbatchsource (id, batchnumber, batchtype, ctime, utime, ver, source_channel)
values (1, 'B20260706001', 'normal', '2026-07-06 09:00:00', '2026-07-06 09:00:00', 1, 'seed')
on duplicate key update batchnumber=values(batchnumber);

use trade;

create table if not exists order_info (
  id bigint primary key,
  user_id bigint,
  order_no varchar(64),
  pay_amount decimal(18,2),
  order_status varchar(32),
  ctime datetime,
  utime datetime,
  ver int
);

insert into order_info (id, user_id, order_no, pay_amount, order_status, ctime, utime, ver)
values (1001, 501, 'O20260706001', 128.50, 'PAID', '2026-07-06 10:00:00', '2026-07-06 10:05:00', 1)
on duplicate key update pay_amount=values(pay_amount);

use user;

create table if not exists user_info (
  id bigint primary key,
  user_name varchar(64),
  mobile varchar(32),
  email varchar(128),
  register_time datetime,
  ctime datetime,
  utime datetime,
  ver int
);

insert into user_info (id, user_name, mobile, email, register_time, ctime, utime, ver)
values (501, 'alice', '13800000000', 'alice@example.com', '2026-07-01 00:00:00', '2026-07-01 00:00:00', '2026-07-01 00:00:00', 1)
on duplicate key update user_name=values(user_name);
