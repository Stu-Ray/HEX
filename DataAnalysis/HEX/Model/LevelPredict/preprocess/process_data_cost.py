# -*- coding: gbk -*-

import pandas as pd
from utils.category import database_categ,operator_categ

data = pd.read_csv('../data/level_vectors.csv', encoding='gbk')

print(data.head())
print(data.info())

data = data.drop(["查询语句","左子树算子编号","右子树算子编号","算子启动时间","算子总时间","左子树总时间","右子树总时间"], axis=1)

print(len(operator_categ))

# 创建映射字典
db_to_index = {db: idx for idx, db in enumerate(database_categ)}
operator_to_index = {op: idx for idx, op in enumerate(operator_categ)}

# 应用映射到相应的列
data['数据库名'] = data['数据库名'].map(db_to_index).fillna(-1)
data['算子类型'] = data['算子类型'].map(operator_to_index).fillna(-1)
data['左子树类型'] = data['左子树类型'].map(operator_to_index).fillna(-1)
data['右子树类型'] = data['右子树类型'].map(operator_to_index).fillna(-1)

#去除数量全为同一值的EEOP
# cols_to_drop = [col for col in data.columns if data[col].nunique() == 1]
# data= data.drop(columns=cols_to_drop)


data.to_csv('../data/processed_data_cost.csv', index=False)
