# -*- coding: gbk -*-

import joblib
import pandas as pd
import torch
from torch.utils.data import TensorDataset, DataLoader

from utils.Aggreate import aggregate_predictions
from utils.category import database_categ
from utils.tpch_sql import identify_query

# 加载模型
model_path = "./data/model_param/ME_one-hot/model_final.pkl"
model = torch.load(model_path)
model.eval()  # 设置模型为评估模式

# 使用 joblib 加载 scaler
scaler = joblib.load('./data/model_param/ME_one-hot/scaler.pkl')

# 读取新数据
predict_data = pd.read_csv('data/predict_data_onehot.csv')

sql_data=predict_data["查询语句"]
predict_data = predict_data.drop("查询语句", axis=1)

# 定义分类特征列
categorical_columns = ["数据库名", "算子类型", "算子编号", "表达式编号", "左子树类型", "右子树类型"]
categorical_array = predict_data[categorical_columns].values
categorical_tensor = torch.from_numpy(categorical_array).to(torch.long)

# 获取数值特征数据
number_array = predict_data.drop(columns=categorical_columns).values
number_tensor = torch.from_numpy(number_array).to(torch.float32)

# 缩放数值特征
number_tensor = torch.tensor(scaler.transform(number_tensor), dtype=torch.float32)

# 如果有GPU可用，则将数据移动到GPU上
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
categorical_tensor = categorical_tensor.to(device)
number_tensor = number_tensor.to(device)
model = model.to(device)

# 创建数据集和数据加载器
dataset = TensorDataset(categorical_tensor, number_tensor)
data_loader = DataLoader(dataset, batch_size=16, shuffle=False)

# 预测并添加数据库名和 SQL 编号
all_predictions = []
database_names = []  # 用于存储数据库名
sql_ids = []  # 用于存储 SQL 编号

with torch.no_grad():
    for i, (categ_batch, num_batch) in enumerate(data_loader):
        outputs = model(categ_batch, num_batch)
        _, predicted = torch.max(outputs, 1)
        all_predictions.extend(predicted.cpu().numpy())

        # 获取当前批次的数据库名（使用数据库编号）
        batch_db_indices = predict_data.iloc[i * 16: (i + 1) * 16]['数据库名'].tolist()

        # 将数据库编号替换为实际数据库名
        batch_database_names = [database_categ[index] for index in batch_db_indices]

        # 获取查询语句并找出对应的 SQL 编号
        batch_sql_queries = sql_data.iloc[i * 16: (i + 1) * 16].tolist()
        batch_sql_ids = [identify_query(sql) for sql in batch_sql_queries]

        # 将当前批次的数据库名和 SQL 编号添加到列表中
        database_names.extend(batch_database_names)
        sql_ids.extend(batch_sql_ids)

# 将预测结果保存到 CSV 文件中，包括数据库名和 SQL 编号
prediction_df = pd.DataFrame({
    "数据库名": database_names,
    "SQL编号": sql_ids,
    "预测最优级别": all_predictions
})

# 保存文件
prediction_df.to_csv('./data/predict_result/ME_one-hot/predictions.csv', index=False)

print("预测完成，结果已保存!")

# 聚合结果
aggregated_df = aggregate_predictions(prediction_df)

# 保存聚合后的结果
aggregated_df.to_csv('./data/predict_result/ME_one-hot/aggregated_predictions.csv', index=False)

print("聚合完成，结果已保存!")