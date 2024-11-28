import shap
import csv
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import tensorflow as tf
import xgboost as xgb
from catboost import CatBoostRegressor
import matplotlib.pyplot as plt
from keras.callbacks import Callback
from sklearn.metrics import r2_score
from tensorflow.keras.callbacks import ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, Flatten, Dense, MultiHeadAttention, LayerNormalization, Dropout, LSTM

# 本程序基于表达式和算子信息预测算子本身的执行时间
parm_factor = 1
epoch_num = 1000

tv_file_path        =   '../Output/time_vectors.csv'                # 向量数据文件路径

factor_file_path    =   './Factor/factors.csv'                      # EEOP因子文件

tv1_file_path       =   '../Output/time_vectors1.csv'               # 向量数据文件1路径
tv2_file_path       =   '../Output/time_vectors2.csv'               # 向量数据文件2路径
output_vec_path     =   '../Output/processed_vectors_time.csv'      # 指定处理后的向量文件路径

save_models = False

figure_path                 =   "./Figure/" + str(parm_factor) + "倍参数_Time_Predict_" + str(epoch_num) + ".png"
history_file_path           =   "./History/" + str(parm_factor) + "倍参数_Time_Predict_" + str(epoch_num) + ".csv"
model_path                  =   "./Model/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_Time_Model.h5"
scaler_path_prefix          =   "./Model/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_Time_"
output_result_file_path     =   "./Output/" + str(parm_factor) + "倍参数_" + str(epoch_num) + "_Time_Text.txt"


def time_predict(vec_file_path):
    # 读取CSV数据
    data = pd.read_csv(vec_file_path, header=0, encoding='gbk')

    # 数据预处理
    data = data.loc[:, (data != 0).any(axis=0)]
    data = data[data['算子总时间'] > 0.1]
    data.drop(columns = ["EEOP_DONE"], inplace=True)
    data = data.sample(frac=1, random_state=57).reset_index(drop=True)

    # 指定列名
    info_columns    =   ['查询语句', '数据库名', '算子编号', '算子类型', '启动Cost', '总Cost', '算子启动时间', '算子总时间', '输入行数', '输出行数', '过滤行数', '左子树算子编号',
                        '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号', '右子树类型', '右子树启动Cost', '右子树总Cost',
                        '右子树输出行数', '右子树总时间']
    drop_columns    =   ['查询语句', '数据库名', '算子编号', '算子启动时间', '算子总时间', '左子树算子编号', '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间',
                        '右子树算子编号', '右子树类型',  '右子树启动Cost', '右子树总Cost', '右子树输出行数', '右子树总时间']
    opType_columns  =   ['算子类型', '左子树类型', '右子树类型']
    input_columns   =   ['算子类型', '总Cost', '输入行数', '输出行数', '过滤行数'] + [col for col in data.columns if col not in info_columns]

    # 去除重复数据
    columns_to_consider = [col for col in data.columns if col not in drop_columns]
    before_rows = data.shape[0]
    data = data.drop_duplicates(subset=columns_to_consider, keep='first')
    after_rows = data.shape[0]
    print(f"去除了 {before_rows - after_rows} 行重复数据。")

    # 保存初步预处理后的数据文件
    data.to_csv(output_vec_path, index=False, encoding='gbk')

    # 提取标签
    labels = data['算子总时间']

    # 对于字符串类型的字段'算子类型'、'左子树类型'、'右子树类型'进行Label Encoding
    le = LabelEncoder()
    for column in opType_columns:
        data[column] = le.fit_transform(data[column])

    # --------- 单独提取EEOP部分和其他部分 ---------
    # # 提取各部分特征
    # data_opt    =   pd.DataFrame(data[info_columns].drop(columns=drop_columns)).values
    # data_eeops  =   pd.DataFrame(data.drop(columns=[col for col in info_columns if col not in opType_columns])).values
    # print(data_opt)
    # print(data_eeops)
    # # 数据归一化处理
    # scaler_opt  = StandardScaler()
    # scaler_eeop = StandardScaler()
    # data_opt    = scaler_opt.fit_transform(data_opt)
    # data_eeops  = scaler_eeop.fit_transform(data_eeops)
    # 保存 scalers
    # if save_models:
    #     joblib.dump(le, scaler_path_prefix + "scaler_LE.pkl")
    #     joblib.dump(scaler_opt, scaler_path_prefix + "scaler_OPT.pkl")
    #     joblib.dump(scaler_eeop, scaler_path_prefix + "scaler_EEOP.pkl")
    # # 特征获取
    # features = np.concatenate([data_opt, data_eeops], axis=1)

    # 提取各部分特征
    data_opt_type       =   pd.DataFrame(data['算子类型']).values
    data_opt_tcost      =   pd.DataFrame(data['总Cost']).values
    data_opt_rows       =   pd.DataFrame(data[['输入行数', '输出行数', '过滤行数']]).values
    data_eeops          =   pd.DataFrame(data.drop(columns=[col for col in info_columns])).values
    # 归一化处理
    scaler              =   StandardScaler()
    features            =   np.concatenate([data_opt_type, data_opt_tcost, data_opt_rows, data_eeops], axis=1)
    features            =   scaler.fit_transform(features)

    # 保存 scalers
    if save_models:
        joblib.dump(le, scaler_path_prefix + "scaler_LE.pkl")
        joblib.dump(scaler, scaler_path_prefix + "scaler_standard.pkl")

    # 将数据集拆分为训练集和测试集
    split_factor = 0.8
    X_train     =   features[:int(split_factor * len(features))]
    y_train     =   labels[:int(split_factor * len(labels))]
    X_test      =   features[int(split_factor * len(features)):]
    y_test      =   labels[int(split_factor * len(labels)):]

    # 创建模型、训练、保存和测试模型
    model = Sequential([
        Dense(128 * parm_factor, input_shape=(X_train.shape[1],), activation='relu', kernel_regularizer=l2(0.001)),
        Dense(64 * parm_factor, activation='relu', kernel_regularizer=l2(0.001)),
        Dense(32 * parm_factor, activation='relu', kernel_regularizer=l2(0.001)),
        Dense(1)
    ])

    # model = Sequential([
    #     Conv1D(64 * parm_factor, kernel_size=3, activation='relu', input_shape=(X_train.shape[1], 1)),
    #     Conv1D(32 * parm_factor, kernel_size=3, activation='relu'),
    #     Flatten(),
    #     Dense(32 * parm_factor, activation='relu'),
    #     Dense(1)
    # ])

    # 编译模型
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mean_squared_error', metrics=['mean_absolute_error'])


    # 训练模型
    lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6)
    history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epoch_num, batch_size=128, callbacks=[lr_scheduler])

    # 保存 model
    if save_models:
        model.save(model_path)

    # 提取训练和验证过程中的 loss 和 accuracy
    train_loss = history.history['loss']
    val_loss = history.history['val_loss']
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(train_loss, label='Train Loss')
    plt.plot(val_loss, label='Validation Loss')
    plt.title('Loss over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid()
    # plt.subplot(1, 2, 2)
    plt.savefig(figure_path)    # 保存图片

    # with open(history_file_path, mode='w+', newline='') as file: # 保存到 CSV 文件
    #     writer = csv.writer(file)
    #     writer.writerow(['Epoch', 'Train Loss', 'Validation Loss'])    # 写入标题
    #     # 写入每个 epoch 的数据
    #     for epoch, (t_loss, v_loss, t_acc, v_acc) in enumerate(zip(train_loss, val_loss), 1):
    #         writer.writerow([epoch, t_loss, v_loss, t_acc, v_acc])

    # # 加载scalers和model
    # le      = joblib.load(scaler_path_prefix + "scaler_LE.pkl")
    # scaler  = joblib.load(scaler_path_prefix + "scaler_standard.pkl")
    # model   = load_model(model_path)

    # 比较预测的真实值与预测值
    y_pred = model.predict(X_test)  # 获取预测值

    # 计算EEOP因子
    X_train = np.array(X_train)
    y_train = np.array(y_train)
    # 将 X_train 转换为 TensorFlow 的 Tensor
    X_train_tensor = tf.convert_to_tensor(X_train, dtype=tf.float32)
    # 计算梯度
    with tf.GradientTape() as tape:
        tape.watch(X_train_tensor)  # 监视输入数据
        predictions = model(X_train_tensor)  # 前向传播
    grads = tape.gradient(predictions, X_train_tensor)
    abs_grads = np.abs(grads.numpy())   # 对每个特征的梯度进行求绝对值（展示特征的重要性）
    # 计算每个特征的平均重要性（如果是回归任务，可以对每个样本求均值）
    feature_importance = np.mean(abs_grads, axis=0)

    for i in range(len(input_columns)):
        print(str(input_columns[i]), "\t", feature_importance[i])

    # 可视化特征重要性
    # plt.bar(range(X_train.shape[1]), feature_importance)
    # plt.xlabel('Feature Index')
    # plt.ylabel('Importance')
    # plt.title('Feature Importance using Grad-CAM')
    # plt.show()

    with open(output_result_file_path, 'w+', newline='', encoding="gbk") as orFile:
        accNum = 0
        totalNum = 0
        for i in range(0, len(y_test)):
            predicted_num = y_pred[i][0]
            real_num = list(labels)[int(split_factor*len(features))+i]
            totalNum = totalNum + 1
            if 0.75 <= float(predicted_num) / float(real_num) <= 1.25:
                accNum = accNum + 1
                orFile.write("【准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + "\n")
            else:
                orFile.write("【不准确】Predicted: " + str(predicted_num) + ", Real: " + str(real_num) + "\n")
        acc = accNum / totalNum
        print(f"ACC: {acc:.4f} (Accurate: {accNum}, Total: {totalNum})")
        orFile.write(f"ACC: {acc:.4f} (Accurate: {accNum}, Total: {totalNum})\n")

def main():
    time_predict(tv_file_path)

if __name__ == "__main__":
    main()

