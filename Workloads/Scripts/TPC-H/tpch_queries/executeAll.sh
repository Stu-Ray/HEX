#!/bin/bash

# 将所有TPCH查询在PG指定数据库组中分别执行指定的次数，其中对应的次数由repeat_counts指定，数据库组在下面的databases设置，需要设置好PG安装根目录

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

# 定义每个SQL文件对应的执行次数数组
declare -A repeat_counts=(
    [1]=20
    [2]=100
    [3]=60
    [4]=30
    [5]=90
    [6]=20
    [7]=100
    [8]=120
    [9]=90
    [10]=80
    [11]=80
    [12]=40
    [13]=50
    [14]=40
    [15]=40
    [16]=60
    [17]=60
    [18]=70
    [19]=30
    [20]=70
    [21]=80
    [22]=40
)

sudo mkdir -p "${query_dir}"/repeated_sql

# 清空输出文件（如果已经存在）
> $output_file

for db in "${databases[@]}"; do
    echo "\\c $db" >> $output_file
    echo "analyze;" >> $output_file
    for i in $(printf "%s\n" "${!repeat_counts[@]}" | sort -n); do
        sql_file="pg${i}.sql"
        if [ ! -f "$sql_file" ]; then
            echo "Error: File $sql_file does not exist!"
            exit 1
        fi
        N=${repeat_counts[$i]}
        for ((j=1; j<=N; j++)); do
            sudo sh -c "cat $sql_file >> $output_file"
        done
    done
done
echo "New SQL file $output_file generated with content repeated according to repeat_counts."

cd "${postgresql_dir}/bin"

# 使用 psql 执行生成的 SQL 文件
psql -d postgres -f "$output_file"

echo "SQL execution completed."
