import csv
import time
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import tensorflow as tf
import matplotlib.pyplot as plt
import xgboost as xgb
from catboost import CatBoostRegressor
from tensorflow.keras.callbacks import ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, Flatten, Dense, MultiHeadAttention, LayerNormalization, Dropout

# 本程序用于预测表达式执行次数

parm_factor = 1
epoch_num = 1000

v_file_path     =   '../Output/vectors.csv'  # 向量文件路径
output_vec_path =   '../Output/processed_vectors.csv'  # 指定处理后的向量文件路径

save_models = False

figure_path                 =   "./Figure/" + str(parm_factor) + "倍参数_Count_Predict_" + str(epoch_num) + ".png"
history_file_path           =   "./History/" + str(parm_factor) + "倍参数_Count_Predict_" + str(epoch_num) + ".csv"
model_path                  =   "./Model/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_ExprCount_Model.h5"
scaler_path_prefix          =   "./Model/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_ExprCount_"
output_result_file_path     =   "./Output/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_ExprCount_Text.txt"

def row_predict(vec_file_path):
    # 读取CSV数据
    data = pd.read_csv(vec_file_path, header=0, encoding='gbk')

    # 数据预处理
    data = data.loc[:, (data != 0).any(axis=0)]
    # data = data[~data['算子类型'].isin(["T_HashJoin"])]
    # data = data[data['表达式次数模式'] != 0]
    data = data[data['表达式次数'] != 0]
    data = data.sample(frac=1, random_state=57).reset_index(drop=True)  # 打乱顺序后方便划分

    # 指定列名
    info_columns        =   ['查询语句', '数据库名', '表达式编号', '表达式次数', '表达式次数模式', '算子编号', '算子类型', '启动Cost', '总Cost', '算子启动时间', '算子总时间', '输出行数',
                        '输入行数', '过滤行数', '左子树算子编号', '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号', '右子树类型',
                        '右子树启动Cost', '右子树总Cost', '右子树输出行数', '右子树总时间']
    drop_columns        =   ['查询语句', '数据库名', '表达式编号', '表达式次数', '表达式次数模式', '算子编号', "启动Cost", "总Cost", '算子启动时间', '算子总时间', '左子树算子编号', '左子树类型',
                             '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号', '右子树类型',  '右子树启动Cost', '右子树总Cost', '右子树输出行数', '右子树总时间']
    opType_columns      =   ['算子类型', '左子树类型', '右子树类型']

    # 去除重复数据
    columns_to_consider = [col for col in data.columns if col not in drop_columns]
    before_rows = data.shape[0]
    data = data.drop_duplicates(subset=columns_to_consider, keep='first')
    after_rows = data.shape[0]
    print(f"去除了 {before_rows - after_rows} 行重复数据。")

    # 提取标签
    labels = data['表达式次数模式']  # 表达式计数作为输出

    # 保留一些原始数据
    input_rows      =   list(data['输入行数'])
    output_rows     =   list(data['输出行数'])
    filtered_rows   =   list(data['过滤行数'])
    expr_count      =   list(data['表达式次数'])
    operator_type   =   list(data['算子类型'])

    # 输出初步预处理后的文件
    data.drop(columns=drop_columns).to_csv(output_vec_path, index=False, encoding='gbk')

    # 对于字符串类型的字段'算子类型'、'左子树类型'、'右子树类型'进行Label Encoding
    le = LabelEncoder()
    for column in opType_columns:
        data[column] = le.fit_transform(data[column])

    # --------- 单独提取EEOP部分和其他部分 ---------
    data_opt = pd.DataFrame(data[info_columns].drop(columns=drop_columns)).values
    data_eeops   =   pd.DataFrame(data.drop(columns=[col for col in info_columns])).values

    # 数据归一化处理
    scaler = StandardScaler()
    features = np.concatenate([data_opt, data_eeops], axis=1)
    features = scaler.fit_transform(features)

    print(features)
    print(features.shape)

    # 数据集划分
    split_factor = 0.8
    X_train = features[:int(split_factor*len(features))]
    y_train = labels[:int(split_factor*len(labels))]
    X_test  = features[int(split_factor*len(features)):]
    y_test  = labels[int(split_factor*len(labels)):]

    # 构建、编译、训练、测试模型
    # model = Sequential([
    #     Dense(128 * parm_factor, input_shape=(X_train.shape[1],), activation='relu'),  # 增加层数和神经元数量
    #     Dense(64 * parm_factor, activation='relu'),
    #     Dense(32 * parm_factor, activation='relu'),
    #     Dense(1)
    # ])

    num_classes = 6  # 实际类别数
    model = Sequential([
        Dense(128 * parm_factor, input_shape=(X_train.shape[1],), activation='relu', kernel_regularizer=l2(0.001)),
        Dropout(0.3),
        Dense(64 * parm_factor, activation='relu', kernel_regularizer=l2(0.001)),
        Dropout(0.3),
        Dense(32 * parm_factor, activation='relu', kernel_regularizer=l2(0.001)),
        Dense(num_classes, activation='softmax')
    ])
    # model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mean_squared_error', metrics=['mae'])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6)
    history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epoch_num, batch_size=128, callbacks=[lr_scheduler])

    # 保存 scalers和model
    if save_models:
        joblib.dump(le, scaler_path_prefix + "scaler_LE.pkl")
        joblib.dump(scaler, scaler_path_prefix + "scaler_standard.pkl")
        model.save(model_path)

    # 提取训练和验证过程中的 loss 和 accuracy
    train_loss = history.history['loss']
    val_loss = history.history['val_loss']
    train_accuracy = history.history['accuracy']
    val_accuracy = history.history['val_accuracy']
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(train_loss, label='Train Loss')
    plt.plot(val_loss, label='Validation Loss')
    plt.title('Loss over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid()
    plt.subplot(1, 2, 2)
    plt.plot(train_accuracy, label='Train Accuracy')
    plt.plot(val_accuracy, label='Validation Accuracy')
    plt.title('Accuracy over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid()
    plt.savefig(figure_path)    # 保存图片

    with open(history_file_path, mode='w+', newline='') as file: # 保存到 CSV 文件
        writer = csv.writer(file)
        writer.writerow(['Epoch', 'Train Loss', 'Validation Loss', 'Train Accuracy', 'Validation Accuracy'])    # 写入标题
        # 写入每个 epoch 的数据
        for epoch, (t_loss, v_loss, t_acc, v_acc) in enumerate(zip(train_loss, val_loss, train_accuracy, val_accuracy), 1):
            writer.writerow([epoch, t_loss, v_loss, t_acc, v_acc])

    # # 加载scalers和model
    # le      = joblib.load(scaler_path_prefix + "scaler_LE.pkl")
    # scaler = joblib.load(scaler_path_prefix + "scaler_standard.pkl")
    # model   = load_model(model_path)

    # 评估模型
    loss, mae = model.evaluate(X_test, y_test)
    print(f'Model Mean Absolute Error on Test Set: {mae}')

    # 获取预测值
    start_time = time.time()
    y_pred = model.predict(X_test)
    end_time = time.time()
    prediction_time = end_time - start_time
    y_pred_classes = np.argmax(y_pred, axis=1).tolist()

    # 比较预测的真实值与预测值
    accNum = 0
    totalNum = 0
    with open(output_result_file_path, 'w+', newline='', encoding="gbk") as orFile:
        for i in range(0, len(y_test)):
            predict_list = [output_rows[int(split_factor*len(features))+i], 2 * output_rows[int(split_factor*len(features))+i], input_rows[int(split_factor*len(features))+i], 2 * input_rows[int(split_factor*len(features))+i]]
            predict_choice = int(round(y_pred_classes[i], 0))
            if predict_choice >= 3:
                predict_choice = 3
            if predict_choice <= 0:
                predict_choice = 0
            predicted_num = predict_list[predict_choice]
            # predict_list = []
            # predicted_num = int(y_pred[i][0])
            real_num = expr_count[int(split_factor*len(features))+i]
            totalNum = totalNum + 1

            if 0.75 <= float(predicted_num) / float(real_num) <= 1.25:
                accNum = accNum + 1
                print("【准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]) + ", PredictList: " + str(predict_list))
                orFile.write("【准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]) + ", PredictList: " + str(predict_list) + "\n")
            else:
                print("【不准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]) + ", PredictList: " + str(predict_list))
                orFile.write("【不准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]) + ", PredictList: " + str(predict_list) + "\n")
        acc = accNum / totalNum
        print(f"Predict Time: {prediction_time} (Num: {len(y_pred)}, Avg: {prediction_time / len(y_pred)})")
        print(f"ACC: {acc:.4f} (Accurate: {accNum}, Total: {totalNum})")
        orFile.write(f"Predict Time: {prediction_time} (Num: {len(y_pred)}, Avg: {prediction_time / len(y_pred)})\n")
        orFile.write(f"ACC: {acc:.4f} (Accurate: {accNum}, Total: {totalNum})\n")

def main():
    row_predict(v_file_path)

if __name__ == "__main__":
    main()
