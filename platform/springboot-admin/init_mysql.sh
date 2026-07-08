#!/usr/bin/env bash
set -euo pipefail

mysql_host="${MYSQL_HOST:-127.0.0.1}"
mysql_port="${MYSQL_PORT:-3306}"
mysql_user="${MYSQL_USER:-root}"
mysql_password="${MYSQL_PASSWORD:-root}"

mysql -h"${mysql_host}" -P"${mysql_port}" -u"${mysql_user}" -p"${mysql_password}" < src/main/resources/schema.sql
mysql -h"${mysql_host}" -P"${mysql_port}" -u"${mysql_user}" -p"${mysql_password}" < src/main/resources/data.sql

echo "cdc_warehouse_admin initialized"
