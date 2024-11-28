#!/bin/bash

# Generate TPC-H data at the $data_dir and process the format, each scale generated seperately.

# TPCH数据生成目录 (dbgen所在目录)
tpch_dir="/opt/pg/tpch"

# 数据存储根目录
data_dir="/data/tpchdata"

# 临时目录用于数据生成
temp_dir="/data/tmp"

# 开始生成和移动数据
start_scale=1.00  # 起始scale(GB)
step_scale=1.00   # 每次增加(GB)
end_scale=10.00    # 终止scale(GB)

# 生成数据
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

    echo "Generating $current_scale GB of data for $db_name..."

    # 创建或清空临时目录
    rm -rf $temp_dir
    mkdir -p $temp_dir

    # 生成数据到临时目录
    cd $tpch_dir
    ./dbgen -s $current_scale -f
    mv ./*.tbl $temp_dir/

    # 创建目标目录并移动生成的数据
    mkdir -p "$data_dir/$db_name"
    mv $temp_dir/*.tbl "$data_dir/$db_name"

    # 更新scale值，每次递增
    current_scale=$(echo "$current_scale + $step_scale" | bc)
done

# 遍历目录下的所有子目录，处理生成的 .tbl 文件
for dir in "$data_dir"/*; do
    if [[ -d "$dir" ]]; then
        echo "Processing directory: $dir"

        # 遍历目录下的所有 .tbl 文件
        for tbl_file in "$dir"/*.tbl; do
            if [[ -f "$tbl_file" ]]; then
                echo "Processing file: $tbl_file"

                # 移除每一行最后的 '|'
                sed -i 's/|$//' "$tbl_file"

                echo "$tbl_file processed."
            fi
        done
    fi
done

echo "All TPCH data generation and transfer completed!"
