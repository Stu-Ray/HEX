import csv
import joblib
import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import xgboost as xgb
from catboost import CatBoostRegressor
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, Flatten, Dense, MultiHeadAttention, LayerNormalization, Dropout, LSTM, MaxPooling1D

# 本程序基于算子和表达式信息预测表达式的理论最优级别

parm_factor = 1
epoch_num = 1000

lv_file_path     =   '../Output/level_vectors.csv'  # 向量文件路径
output_vec_path =   '../Output/processed_vectors_level.csv'  # 指定处理后的向量文件路径

save_models = True

figure_path                 =   "./Figure/" + str(parm_factor) + "倍参数_Level_Predict_" + str(epoch_num) + ".png"
history_file_path           =   "./History/" + str(parm_factor) + "倍参数_Level_Predict_" + str(epoch_num) + ".csv"
model_path                  =   "./Model/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_Level_Model.h5"
scaler_path_prefix          =   "./Model/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_Level_"
output_result_file_path     =   "./Output/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_Level_Text.txt"

def level_predict(vec_file_path):
    # 读取CSV数据
    data = pd.read_csv(vec_file_path, header=0, encoding='gbk')

    # 数据预处理
    data = data.loc[:, (data != 0).any(axis=0)] # 去除为空的列
    data = data.loc[:, (data != 0.0).any(axis=0)] # 去除为空的列
    data = data.sample(frac=1, random_state=57).reset_index(drop=True)  # 打乱顺序后方便划分

    # 指定列名
    info_columns = ['查询语句', '数据库名', '表达式编号', '表达式次数', '最优级别', '算子编号', '算子类型', '启动Cost', '总Cost', '算子启动时间', '算子总时间',
                      '输入行数', '输出行数', '过滤行数', '左子树算子编号', '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号',
                      '右子树类型', '右子树启动Cost', '右子树总Cost', '右子树输出行数', '右子树总时间']
    drop_columns = ['查询语句', '数据库名', '表达式编号', '表达式次数', '最优级别',  "启动Cost", "总Cost", '算子编号', '算子启动时间', '算子总时间', '左子树算子编号',
                    '左子树类型', '右子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号', '右子树启动Cost', '右子树总Cost', '右子树输出行数', '右子树总时间']
    opType_columns = ['算子类型', '左子树类型', '右子树类型']

    # eeop_columns = [col for col in data.columns if col not in info_columns]
    # print(eeop_columns)

    # 去除重复行
    columns_to_consider = [col for col in data.columns if col not in drop_columns]
    before_rows = data.shape[0]
    data = data.drop_duplicates(subset=columns_to_consider, keep='first')
    after_rows = data.shape[0]
    print(f"去除了 {before_rows - after_rows} 行重复数据。")

    # 输出初步预处理后的文件
    data.drop(columns=drop_columns).to_csv(output_vec_path, index=False, encoding='gbk')

    # 提取标签
    labels = data['最优级别']  # 表达式计数作为输出

    # 保留一些原始数据
    input_rows = list(data['输入行数'])
    output_rows = list(data['输出行数'])
    operator_type = list(data['算子类型'])

    # 对于字符串类型的字段'算子类型'、'左子树类型'、'右子树类型'进行Label Encoding
    le = LabelEncoder()
    for column in opType_columns:
        data[column] = le.fit_transform(data[column])

    # 数据归一化处理
    # --------- 单独提取EEOP部分和其他部分 ---------
    data_opt        =   pd.DataFrame(data[info_columns].drop(columns=drop_columns)).values
    data_eeops      =   pd.DataFrame(data.drop(columns=[col for col in info_columns])).values

    # 数据归一化处理
    scaler   =  StandardScaler()
    features =  np.concatenate([data_opt, data_eeops], axis=1)
    features =  scaler.fit_transform(features)

    print(features.shape)
    print(data[info_columns].drop(columns=drop_columns).columns)
    print(data.drop(columns=[col for col in info_columns]).columns)

    # 数据集划分
    split_factor = 0.8
    X_train = features[:int(split_factor*len(features))]
    y_train = labels[:int(split_factor*len(labels))]
    X_test  = features[int(split_factor*len(features)):]
    y_test  = labels[int(split_factor*len(labels)):]
    # y_train_one_hot = pd.get_dummies(y_train).values
    # y_test_one_hot = pd.get_dummies(y_test).values

    # 构建、训练、测试模型
    num_classes = 4  # 实际类别数
    model = Sequential([
        Dense(128 * parm_factor, input_shape=(X_train.shape[1],), activation='relu'),  # 输入层
        Dropout(0.5),  # Dropout，丢弃 50% 的神经元
        Dense(64 * parm_factor, activation='relu'),  # 隐藏层
        Dropout(0.5),  # Dropout
        Dense(32 * parm_factor, activation='relu'),  # 隐藏层
        Dropout(0.5),  # Dropout
        Dense(num_classes, activation='softmax')  # 输出层：softmax 激活，用于多分类
    ])

    # model = Sequential([
    #     Conv1D(64 * parm_factor, kernel_size=3, activation='relu', input_shape=(X_train.shape[1], 1)),
    #     Dropout(0.5),  # Dropout，丢弃 50% 的神经元
    #     Conv1D(32 * parm_factor, kernel_size=3, activation='relu'),
    #     Flatten(),
    #     Dropout(0.5),  # Dropout，丢弃 50% 的神经元
    #     Dense(32 * parm_factor, activation='relu'),
    #     Dropout(0.5),  # Dropout，丢弃 50% 的神经元
    #     Dense(num_classes, activation='softmax')  # 输出层
    # ])

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epoch_num, batch_size=64)
    # model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
    # history = model.fit(X_train, y_train_one_hot, validation_data=(X_test, y_test_one_hot), epochs=10000, batch_size=128)

    # 保存 scalers和model
    if save_models:
        joblib.dump(le, scaler_path_prefix + "scaler_LE.pkl")
        joblib.dump(scaler, scaler_path_prefix + "scaler_standard.pkl")
        model.save(model_path)

    # # 加载scalers和model
    # le              = joblib.load(scaler_path_prefix + "scaler_LE.pkl")
    # scaler          = joblib.load(scaler_path_prefix + "scaler_standard.pkl")
    # model           = load_model(model_path)

    # 提取训练和验证过程中的 loss 和 accuracy
    train_loss = history.history['loss']
    val_loss = history.history['val_loss']
    train_accuracy = history.history['accuracy']
    val_accuracy = history.history['val_accuracy']
    # 设置图片大小
    plt.figure(figsize=(12, 6))
    # 绘制 Loss 曲线
    plt.subplot(1, 2, 1)
    plt.plot(train_loss, label='Train Loss')
    plt.plot(val_loss, label='Validation Loss')
    plt.title('Loss over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid()
    # 绘制 Accuracy 曲线
    plt.subplot(1, 2, 2)
    plt.plot(train_accuracy, label='Train Accuracy')
    plt.plot(val_accuracy, label='Validation Accuracy')
    plt.title('Accuracy over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.ylim(0, 1)
    plt.legend()
    plt.grid()
    plt.savefig(figure_path)    # 保存图片
    with open(history_file_path, mode='w+', newline='') as file: # 保存到 CSV 文件
        writer = csv.writer(file)
        writer.writerow(['Epoch', 'Train Loss', 'Validation Loss', 'Train Accuracy', 'Validation Accuracy'])    # 写入标题
        # 写入每个 epoch 的数据
        for epoch, (t_loss, v_loss, t_acc, v_acc) in enumerate(zip(train_loss, val_loss, train_accuracy, val_accuracy), 1):
            writer.writerow([epoch, t_loss, v_loss, t_acc, v_acc])


    # 评估模型
    loss, mae = model.evaluate(X_test, y_test)
    print(f'Model Mean Absolute Error on Test Set: {mae}')
    # loss, accuracy = model.evaluate(X_test, y_test_one_hot)
    # print(f"Test Loss: {loss}, Test Accuracy: {accuracy}")

    # 获取预测值
    start_time = time.time()
    y_pred = model.predict(X_test)
    end_time = time.time()
    prediction_time = end_time - start_time
    y_pred_classes = np.argmax(y_pred, axis=1).tolist()

    # 比较预测的真实值与预测值
    with open(output_result_file_path, 'w+', newline='', encoding="gbk") as orFile:
        accNum = 0
        totalNum = 0
        for i in range(0, len(y_test)):
            predicted_num = int(round(y_pred_classes[i], 0))
            if predicted_num >= 3:
                predicted_num = 3
            if predicted_num <= 0:
                predicted_num = 0
            real_num = int(y_test.iloc[i])
            totalNum = totalNum + 1
            if predicted_num == real_num:
                accNum = accNum + 1
                print("【准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]))
                orFile.write("【准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]) + "\n")
            else:
                print("【不准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]))
                orFile.write("【不准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + ", Operator: " + str(operator_type[int(split_factor * len(features)) + i]) + "\n")
        acc = accNum / totalNum
        print(f"Predict Time: {prediction_time} (Num: {len(y_pred)}, Avg: {prediction_time/len(y_pred)})")
        print(f"ACC: {acc:.4f} (Accurate: {accNum}, Total: {totalNum})")
        orFile.write(f"Predict Time: {prediction_time} (Num: {len(y_pred)}, Avg: {prediction_time / len(y_pred)})\n")
        orFile.write(f"ACC: {acc:.4f} (Accurate: {accNum}, Total: {totalNum})\n")


def main():
    level_predict(lv_file_path)

if __name__ == "__main__":
    main()
