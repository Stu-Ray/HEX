# -*- coding: gbk -*-

import pandas as pd
from utils.category import database_categ,operator_categ

data = pd.read_csv('../data/level_vectors.csv', encoding='gbk')

print(data.head())
print(data.info())

data = data.drop(["��ѯ���","���������ӱ��","���������ӱ��","��������ʱ��","������ʱ��","��������ʱ��","��������ʱ��"], axis=1)

print(len(operator_categ))

# ����ӳ���ֵ�
db_to_index = {db: idx for idx, db in enumerate(database_categ)}
operator_to_index = {op: idx for idx, op in enumerate(operator_categ)}

# Ӧ��ӳ�䵽��Ӧ����
data['���ݿ���'] = data['���ݿ���'].map(db_to_index).fillna(-1)
data['��������'] = data['��������'].map(operator_to_index).fillna(-1)
data['����������'] = data['����������'].map(operator_to_index).fillna(-1)
data['����������'] = data['����������'].map(operator_to_index).fillna(-1)

#ȥ������ȫΪͬһֵ��EEOP
# cols_to_drop = [col for col in data.columns if data[col].nunique() == 1]
# data= data.drop(columns=cols_to_drop)


data.to_csv('../data/processed_data_cost.csv', index=False)
