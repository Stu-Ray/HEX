import csv
import time
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score

# 本程序基于表达式和算子信息预测算子本身的执行时间
parm_factor = 1
epoch_num = 1000

tv_file_path = './time_vectors.csv'  # 数据集路径
output_vec_path = './processed_vectors_time.csv'  # 输出结果路径


# Define the PyTorch Model
class TimePredictionModel(nn.Module):
    def __init__(self, input_dim):
        super(TimePredictionModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, 128 * parm_factor)
        self.fc2 = nn.Linear(128 * parm_factor, 64 * parm_factor)
        self.fc3 = nn.Linear(64 * parm_factor, 32 * parm_factor)
        self.fc4 = nn.Linear(32 * parm_factor, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.fc4(x)
        return x


def time_predict(vec_file_path):
    # 读取CSV数据
    data = pd.read_csv(vec_file_path, header=0, encoding='gbk')

    # 数据预处理
    data = data.loc[:, (data != 0).any(axis=0)]
    data = data[data['算子总时间'] > 0.1]
    data.drop(columns=["EEOP_DONE"], inplace=True)
    data = data.sample(frac=1, random_state=57).reset_index(drop=True)

    # 指定列名
    info_columns = ['查询语句', '数据库名', '算子编号', '算子类型', '启动Cost', '总Cost', '算子启动时间', '算子总时间', '输入行数', '输出行数', '过滤行数', '左子树算子编号',
                    '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号', '右子树类型', '右子树启动Cost', '右子树总Cost',
                    '右子树输出行数', '右子树总时间']
    drop_columns = ['查询语句', '数据库名', '算子编号', '算子启动时间', '算子总时间', '左子树算子编号', '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间',
                    '右子树算子编号', '右子树类型', '右子树启动Cost', '右子树总Cost', '右子树输出行数', '右子树总时间']
    opType_columns = ['算子类型', '左子树类型', '右子树类型']

    # 去除重复数据
    columns_to_consider = [col for col in data.columns if col not in drop_columns]
    data = data.drop_duplicates(subset=columns_to_consider, keep='first')

    # 保存初步预处理后的数据文件
    data.to_csv(output_vec_path, index=False, encoding='gbk')

    # 定义存储结果的CSV文件名
    train_csv_filename = './train_loss_and_acc.csv'
    test_csv_filename = './test_loss_and_acc.csv'

    # 写入CSV文件的列名
    with open(train_csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Epoch', 'Loss', 'R-squared'])

    with open(test_csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Epoch', 'Loss', 'R-squared'])

    # 提取标签
    labels = data['算子总时间']

    # 对于字符串类型的字段'算子类型'、'左子树类型'、'右子树类型'进行Label Encoding
    le = LabelEncoder()
    for column in opType_columns:
        data[column] = le.fit_transform(data[column])

    # 提取各部分特征
    data_opt_type = pd.DataFrame(data['算子类型']).values
    data_opt_tcost = pd.DataFrame(data['总Cost']).values
    data_opt_rows = pd.DataFrame(data[['输入行数', '输出行数', '过滤行数']]).values
    data_eeops = pd.DataFrame(data.drop(columns=[col for col in info_columns])).values
    # 标准化处理
    scaler = StandardScaler()
    features = np.concatenate([data_opt_type, data_opt_tcost, data_opt_rows, data_eeops], axis=1)
    features = scaler.fit_transform(features)

    joblib.dump(le,  "./scaler_LE.pkl")
    joblib.dump(scaler,  "./scaler_standard.pkl")

    # 将数据集拆分为训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=57)

    # Convert data to PyTorch tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train.values, dtype=torch.float32).view(-1, 1)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test.values, dtype=torch.float32).view(-1, 1)

    # 初始化模型、损失函数和优化器
    model = TimePredictionModel(X_train.shape[1])
    criterion = nn.HuberLoss(delta=1.0)
    optimizer = optim.Adam(model.parameters(), lr=0.0001)

    # 设置 ReduceLROnPlateau 调度器，监控验证集的损失 val_loss
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=10, factor=0.1, verbose=True)

    # 训练模型
    train_losses = []
    val_losses = []
    train_accuracy = []  # 添加训练R-squared
    val_accuracy = []  # 添加验证R-squared

    for epoch in range(epoch_num):
        model.train()
        optimizer.zero_grad()
        y_pred = model(X_train_tensor)
        train_loss = criterion(y_pred, y_train_tensor)
        train_losses.append(train_loss.item())

        # 计算训练集R-squared
        train_acc = calculate_r2(y_pred, y_train_tensor)
        train_accuracy.append(train_acc)

        train_loss.backward()
        optimizer.step()

        # 将训练结果写入CSV文件
        with open(train_csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([epoch + 1, train_loss.item(), train_acc])

        # 测试模型
        model.eval()
        with torch.no_grad():
            y_val_pred = model(X_test_tensor)
            val_loss = criterion(y_val_pred, y_test_tensor)
            val_losses.append(val_loss.item())

            # 计算验证集R-squared
            val_acc = calculate_r2(y_val_pred, y_test_tensor)
            val_accuracy.append(val_acc)

        # 调整学习率
        scheduler.step(val_loss)

        # 将测试结果写入CSV文件
        with open(test_csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([epoch + 1, val_loss.item(), val_acc])

        if (epoch + 1) % 100 == 0:
            torch.save(model, f"model_{epoch + 1}.pkl")
            print(f"Epoch [{epoch + 1}/{epoch_num}], Train Loss: {train_loss.item()}, Val Loss: {val_loss.item()}")

    torch.save(model, "model_final.pkl")

    # 绘画训练和测试损失
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.title('Loss over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid()

    # 绘画训练和测试准确度
    plt.subplot(1, 2, 2)
    plt.plot(train_accuracy, label='Train R2')
    plt.plot(val_accuracy, label='Validation R2')
    plt.title('R-squared over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('R-squared')
    plt.legend()
    plt.grid()
    plt.savefig("./Loss_and_R2.png")
    plt.show()
    print(f"R^2 score: {calculate_r2(y_val_pred, y_test_tensor)}")


def calculate_r2(y_pred, y_true):
    return r2_score(y_true.detach().numpy(), y_pred.detach().numpy())

def main():
    time_predict(tv_file_path)


if __name__ == "__main__":
    main()
