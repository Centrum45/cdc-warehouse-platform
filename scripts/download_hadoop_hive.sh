#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

hadoop_version="${HADOOP_VERSION:-3.3.6}"
hive_version="${HIVE_VERSION:-3.1.3}"
base_urls="${APACHE_MIRRORS:-https://mirrors.tuna.tsinghua.edu.cn/apache https://mirrors.aliyun.com/apache https://archive.apache.org/dist}"
hadoop_dir="docker/hadoop/dist"
hive_dir="docker/hive/dist"

mkdir -p "${hadoop_dir}" "${hive_dir}" data/hive

download_and_unpack() {
  local name="$1"
  local path="$2"
  local target_dir="$3"
  local final_link="$4"
  local marker="$5"
  local archive="/tmp/${name}.tar.gz"
  local downloaded="false"

  if [ -e "${marker}" ] && [ "$(readlink "${final_link}" 2>/dev/null || true)" = "${name}.dist" ]; then
    echo "${name} exists: ${marker}"
    return
  fi

  for base_url in ${base_urls}; do
    local url="${base_url}/${path}"
    echo "download ${name}: ${url}"
    if curl -fL "${url}" -o "${archive}"; then
      downloaded="true"
      break
    fi
  done

  if [ "${downloaded}" != "true" ]; then
    echo "download failed: ${name}" >&2
    exit 1
  fi

  rm -rf "${target_dir:?}/${name}" "${final_link}"
  tar -xzf "${archive}" -C "${target_dir}"
  mv "${target_dir}/${name}" "${target_dir}/${name}.dist"
  ln -s "${name}.dist" "${final_link}"
}

download_and_unpack \
  "hadoop-${hadoop_version}" \
  "hadoop/common/hadoop-${hadoop_version}/hadoop-${hadoop_version}.tar.gz" \
  "${hadoop_dir}" \
  "${hadoop_dir}/hadoop" \
  "${hadoop_dir}/hadoop/bin/hdfs"

download_and_unpack \
  "apache-hive-${hive_version}-bin" \
  "hive/hive-${hive_version}/apache-hive-${hive_version}-bin.tar.gz" \
  "${hive_dir}" \
  "${hive_dir}/hive" \
  "${hive_dir}/hive/bin/hiveserver2"

hadoop_guava="$(find "${hadoop_dir}/hadoop/share/hadoop/common/lib" -name 'guava-*.jar' | head -1 || true)"
if [ -n "${hadoop_guava}" ]; then
  rm -f "${hive_dir}/hive/lib/guava-"*.jar
  cp "${hadoop_guava}" "${hive_dir}/hive/lib/"
fi

echo "Hadoop: ${hadoop_dir}/hadoop"
echo "Hive: ${hive_dir}/hive"
