#!/bin/bash

# 将指定的第X条TPCH查询在PG指定数据库中执行N遍，其中传入的三个参数分别为X、N和数据库名，需要设置好PG安装根目录

# 检查输入参数
if [ $# -ne 3 ]; then
    echo "Usage: $0 <X> <N> <database_name>"
    echo "  X: The number of the SQL file (1-22, e.g., for pgX.sql)"
    echo "  N: The number of times to repeat the content"
    echo "  database_name: The name of the PostgreSQL database"
    exit 1
fi

X=$1  # pgX.sql 的文件编号
N=$2  # 重复的次数
database_name=$3    # PostgreSQL 数据库名

# PG安装目录（非源码）
postgresql_dir="/opt/pg/pgsql/debug"

# tpch_queries的路径
query_dir="/opt/pg/pgsql/debug/bin/tpch_queries"

# 源SQL文件
sql_file="${query_dir}/pg${X}.sql"  

# 输出SQL文件
output_file="${query_dir}/repeated_sql/repeated_pg${X}.sql"  

sudo mkdir -p "${query_dir}"/repeated_sql

# 清空输出文件（如果已经存在）
> $output_file

sudo chmod 777 "$output_file"

# 将 pgX.sql 的内容重复 N 遍
for ((i=1; i<=N; i++)); do
    sudo sh -c "cat $sql_file >> $output_file"
done

echo "New SQL file $output_file generated with content repeated $N times."

cd "${postgresql_dir}/bin"

# 使用 psql 执行生成的 SQL 文件
psql -d "$database_name" -f "$output_file"

echo "SQL execution completed."
