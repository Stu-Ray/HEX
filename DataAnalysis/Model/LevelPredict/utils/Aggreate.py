# -*- coding: gbk -*-

import pandas as pd

def aggregate_predictions(prediction_df):
    # ����һ���յ��ֵ䣬���ڴ洢�ϲ���Ľ��
    aggregated_data = {}

    # ����ÿһ������
    for _, row in prediction_df.iterrows():
        db_name = row['���ݿ���']
        sql_id = row['SQL���']
        expr_level = row['Ԥ�����ż���']

        # ����һ�����ϼ� (���ݿ���, SQL���)�����ںϲ���ͬ�����ݿ����� SQL ��ŵ���
        key = (db_name, sql_id)

        # ��������ݿ����� SQL��ŵ�����Ѿ����ڣ����µı��ʽ������ӵ����еļ����б���
        if key in aggregated_data:
            aggregated_data[key].append(str(expr_level))
        else:
            # �����ʼ��һ���µļ����б�
            aggregated_data[key] = [str(expr_level)]

    # ���ϲ���Ľ��ת��Ϊ DataFrame
    aggregated_rows = []
    for (db_name, sql_id), expr_levels in aggregated_data.items():
        # ʹ�� "��" ���ӱ��ʽ����
        aggregated_rows.append([db_name, sql_id] + expr_levels)

    # ��ȡ�����ʽ��������ȷ��ÿ�е�����һ��
    max_expr_count = max(len(expr_levels) for expr_levels in aggregated_data.values())

    # ���ȱʧ�ı��ʽ����Ϊ���ַ�����ʹ��ÿ�е�����һ��
    for row in aggregated_rows:
        row.extend([''] * (max_expr_count - len(row) + 2))  # +2 ����Ϊǰ���� '���ݿ���' �� 'SQL���' ����

    # ����һ���µ� DataFrame
    aggregated_df = pd.DataFrame(aggregated_rows)

    return aggregated_df