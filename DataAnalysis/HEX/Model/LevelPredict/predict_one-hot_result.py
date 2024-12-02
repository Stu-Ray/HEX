# -*- coding: gbk -*-

import joblib
import pandas as pd
import torch
from torch.utils.data import TensorDataset, DataLoader

from utils.Aggreate import aggregate_predictions
from utils.category import database_categ
from utils.tpch_sql import identify_query

# ����ģ��
model_path = "./data/model_param/ME_one-hot/model_final.pkl"
model = torch.load(model_path)
model.eval()  # ����ģ��Ϊ����ģʽ

# ʹ�� joblib ���� scaler
scaler = joblib.load('./data/model_param/ME_one-hot/scaler.pkl')

# ��ȡ������
predict_data = pd.read_csv('data/predict_data_onehot.csv')

sql_data=predict_data["��ѯ���"]
predict_data = predict_data.drop("��ѯ���", axis=1)

# �������������
categorical_columns = ["���ݿ���", "��������", "���ӱ��", "���ʽ���", "����������", "����������"]
categorical_array = predict_data[categorical_columns].values
categorical_tensor = torch.from_numpy(categorical_array).to(torch.long)

# ��ȡ��ֵ��������
number_array = predict_data.drop(columns=categorical_columns).values
number_tensor = torch.from_numpy(number_array).to(torch.float32)

# ������ֵ����
number_tensor = torch.tensor(scaler.transform(number_tensor), dtype=torch.float32)

# �����GPU���ã��������ƶ���GPU��
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
categorical_tensor = categorical_tensor.to(device)
number_tensor = number_tensor.to(device)
model = model.to(device)

# �������ݼ������ݼ�����
dataset = TensorDataset(categorical_tensor, number_tensor)
data_loader = DataLoader(dataset, batch_size=16, shuffle=False)

# Ԥ�Ⲣ������ݿ����� SQL ���
all_predictions = []
database_names = []  # ���ڴ洢���ݿ���
sql_ids = []  # ���ڴ洢 SQL ���

with torch.no_grad():
    for i, (categ_batch, num_batch) in enumerate(data_loader):
        outputs = model(categ_batch, num_batch)
        _, predicted = torch.max(outputs, 1)
        all_predictions.extend(predicted.cpu().numpy())

        # ��ȡ��ǰ���ε����ݿ�����ʹ�����ݿ��ţ�
        batch_db_indices = predict_data.iloc[i * 16: (i + 1) * 16]['���ݿ���'].tolist()

        # �����ݿ����滻Ϊʵ�����ݿ���
        batch_database_names = [database_categ[index] for index in batch_db_indices]

        # ��ȡ��ѯ��䲢�ҳ���Ӧ�� SQL ���
        batch_sql_queries = sql_data.iloc[i * 16: (i + 1) * 16].tolist()
        batch_sql_ids = [identify_query(sql) for sql in batch_sql_queries]

        # ����ǰ���ε����ݿ����� SQL �����ӵ��б���
        database_names.extend(batch_database_names)
        sql_ids.extend(batch_sql_ids)

# ��Ԥ�������浽 CSV �ļ��У��������ݿ����� SQL ���
prediction_df = pd.DataFrame({
    "���ݿ���": database_names,
    "SQL���": sql_ids,
    "Ԥ�����ż���": all_predictions
})

# �����ļ�
prediction_df.to_csv('./data/predict_result/ME_one-hot/predictions.csv', index=False)

print("Ԥ����ɣ�����ѱ���!")

# �ۺϽ��
aggregated_df = aggregate_predictions(prediction_df)

# ����ۺϺ�Ľ��
aggregated_df.to_csv('./data/predict_result/ME_one-hot/aggregated_predictions.csv', index=False)

print("�ۺ���ɣ�����ѱ���!")