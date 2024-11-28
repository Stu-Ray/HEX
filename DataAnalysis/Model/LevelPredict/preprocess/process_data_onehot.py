# -*- coding: gbk -*-

import pandas as pd
from utils.category import database_categ, operator_categ

# ��ȡ����
data = pd.read_csv('../data/level_vectors.csv', encoding='gbk')

print(data.head())
print(data.info())

# ɾ������Ҫ����
data = data.drop(["��ѯ���", "���������ӱ��", "���������ӱ��","��������ʱ��","������ʱ��","��������ʱ��","��������ʱ��"], axis=1)

print(len(operator_categ))

# ����ӳ���ֵ�
db_to_index = {db: idx for idx, db in enumerate(database_categ)}
operator_to_index = {op: idx for idx, op in enumerate(operator_categ)}

# Ӧ��ӳ�䵽��Ӧ����
data['���ݿ���'] = data['���ݿ���'].map(db_to_index).fillna(-1)
data['��������'] = data['��������'].map(operator_to_index).fillna(-1)
data['����������'] = data['����������'].map(operator_to_index).fillna(-1)
data['����������'] = data['����������'].map(operator_to_index).fillna(-1)

# ȥ������ȫΪͬһֵ��EEOP��
# cols_to_drop = [col for col in data.columns if data[col].nunique() == 1]
# data = data.drop(columns=cols_to_drop)

# ������ EEOP ��ͷ���У���ֵ��Ϊ0������1
eeop_columns = [col for col in data.columns if col.startswith('EEOP')]

for col in eeop_columns:
    data[col] = data[col].apply(lambda x: 1 if x != 0 else 0)

# ���洦��������
data.to_csv('../data/processed_data_onehot.csv', index=False)
