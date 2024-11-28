#!/bin/bash

# 将所有TPCH查询在PG指定数据库组中分别执行N遍，其中N为传入的参数，数据库组在下面的databases设置，需要设置好PG安装根目录

# 检查输入参数
if [ $# -ne 1 ]; then
    echo "Usage: $0 <N>"
    echo "  N: The number of times to repeat the content"
    exit 1
fi

N=$1  # 重复的次数

# PG安装目录（非源码）
postgresql_dir="/opt/pg/pgsql/debug"

# tpch_queries的路径
query_dir="/opt/pg/pgsql/debug/bin/tpch_queries"

# 输出SQL文件
output_file="${query_dir}/repeated_sql/repeated_pg.sql"  

# 定义待执行的数据库数组
databases=(
  "tpch_0_1_0"
  "tpch_0_2_0"
  "tpch_0_3_0"
  "tpch_0_4_0"
  "tpch_0_5_0"
  "tpch_0_6_0"
  "tpch_0_7_0"
  "tpch_0_8_0"
  "tpch_0_9_0"
  "tpch_1_0_0"
  "tpch_2_0_0"
  "tpch_3_0_0"
  "tpch_4_0_0"
  "tpch_5_0_0"
  "tpch_6_0_0"
  "tpch_7_0_0"
  "tpch_8_0_0"
  "tpch_9_0_0"
  "tpch_10_0_0"
)


sudo mkdir -p "${query_dir}"/repeated_sql

# 清空输出文件（如果已经存在）
> $output_file

for db in "${databases[@]}"; do
    echo "\\c $db" >> $output_file
    echo "analyze;" >> $output_file
    for i in {1..22}; do
        sql_file="pg${i}.sql"
        if [ ! -f "$sql_file" ]; then
            echo "Error: File $sql_file does not exist!"
            exit 1
        fi
        for ((j=1; j<=N; j++)); do
            sudo sh -c "cat $sql_file >> $output_file"
        done
    done
done
echo "New SQL file $output_file generated with content repeated $N times."

cd "${postgresql_dir}/bin"

psql -d postgres -f "$output_file"

echo "SQL execution completed."