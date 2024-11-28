#!/bin/bash

# Require generate_pg_data.sh and create_tpch_databases.sh pre-executed.

# Import the generated data into PostgreSQL.

# PG安装目录（非源码）
postgresql_dir="/opt/pg/pgsql/debug"

# 数据目录根路径
data_dir="/data/tpchdata"

# 自动生成导入 SQL 脚本的路径
sql_file="/opt/tpch_data_import.sql"

# 临时目录用于数据生成
temp_dir="/data/tmp"

# 清空之前的 SQL 脚本文件
> $sql_file

# 开始导入数据
start_scale=1.00  # 起始scale(GB)
step_scale=1.00   # 每次增加(GB)
end_scale=10.00    # 终止scale(GB)

# 起始数据
current_scale=$start_scale

while (( $(echo "$current_scale <= $end_scale" | bc -l) )); do
    # 获取scale的个位、十分位、百分位
    integer_part=$(echo "scale=0; $current_scale/1" | bc)  # 获取整数部分，作为个位
    decimal_part=$(printf "%.2f" "$current_scale" | cut -d '.' -f 2)  # 获取两位小数部分

    # 分别提取十分位和百分位
    tens_digit=$(echo $decimal_part | cut -c 1)  # 十分位
    hundred_digit=$(echo $decimal_part | cut -c 2)  # 百分位

    # 格式化数据库名称，例如：tpch_0_5_5，tpch_1_0_0
    db_name="tpch_${integer_part}_${tens_digit}_${hundred_digit}"

    echo "Importing $current_scale GB of data for $db_name..."

    # 创建或清空临时目录
    rm -rf $temp_dir
    mkdir -p $temp_dir

    echo "\c $db_name" >> $sql_file
    for table in region nation customer lineitem orders part partsupp supplier; do
        echo "COPY $table FROM '$data_dir/$db_name/$table.tbl' DELIMITER '|' CSV HEADER;" >> $sql_file
    done
    echo "" >> $sql_file  # 增加一个空行用于分隔不同数据库的导入语句
    
    # 递增更新scale值
    current_scale=$(echo "$current_scale + $step_scale" | bc)
done

echo "SQL import script generated at $sql_file."

cd "${postgresql_dir}/bin"

./psql -d postgres -f "$sql_file"