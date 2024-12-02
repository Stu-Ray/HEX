# -*- coding: gbk -*-

import pandas as pd

def aggregate_predictions(prediction_df):
    # 创建一个空的字典，用于存储合并后的结果
    aggregated_data = {}

    # 遍历每一行数据
    for _, row in prediction_df.iterrows():
        db_name = row['数据库名']
        sql_id = row['SQL编号']
        expr_level = row['预测最优级别']

        # 创建一个复合键 (数据库名, SQL编号)，用于合并相同的数据库名和 SQL 编号的行
        key = (db_name, sql_id)

        # 如果该数据库名和 SQL编号的组合已经存在，则将新的表达式级别添加到已有的级别列表中
        if key in aggregated_data:
            aggregated_data[key].append(str(expr_level))
        else:
            # 否则初始化一个新的级别列表
            aggregated_data[key] = [str(expr_level)]

    # 将合并后的结果转换为 DataFrame
    aggregated_rows = []
    for (db_name, sql_id), expr_levels in aggregated_data.items():
        # 使用 "，" 连接表达式级别
        aggregated_rows.append([db_name, sql_id] + expr_levels)

    # 获取最大表达式级别数，确保每行的列数一致
    max_expr_count = max(len(expr_levels) for expr_levels in aggregated_data.values())

    # 填充缺失的表达式级别为空字符串，使得每行的列数一致
    for row in aggregated_rows:
        row.extend([''] * (max_expr_count - len(row) + 2))  # +2 是因为前面有 '数据库名' 和 'SQL编号' 两列

    # 创建一个新的 DataFrame
    aggregated_df = pd.DataFrame(aggregated_rows)

    return aggregated_df