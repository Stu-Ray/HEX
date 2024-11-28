# -*- coding: gbk -*-

import csv
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.utils import compute_class_weight

from model.model_func import train_model, FocalLoss, ExampleDataset, DataLoader, evaluate_model
from model.ft_transformer import FTTransformer
import torch
from torch import optim
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from matplotlib import pyplot as plt

from utils.category import operator_categ, database_categ

# 读取数据
data = pd.read_csv('data/processed_data_onehot.csv')

# 定义分类特征列
categorical_columns = ["数据库名","算子类型", "算子编号", "表达式编号", "左子树类型", "右子树类型"]
categorical_array = data[categorical_columns].values
categorical_tensor = torch.from_numpy(categorical_array).to(torch.long)
# print(categorical_tensor, categorical_tensor.shape)

# 定义标签列
label_columns = "最优级别"
label_array = data[label_columns].values
label_tensor = torch.from_numpy(label_array).to(torch.long)
# print(label_tensor, label_tensor.shape)

# 获取数值特征数据
number_array = data.drop(columns=categorical_columns + [label_columns]).values
number_tensor = torch.from_numpy(number_array).to(torch.float32)
# print(number_tensor, number_tensor.shape)

#缩放数值特征
scaler = StandardScaler()
number_tensor = torch.tensor(scaler.fit_transform(number_tensor),
                             dtype=torch.float32)

# 保存scaler参数
joblib.dump(scaler, './data/model_param/ME_one-hot/scaler.pkl')  # 添加这行代码来保存scaler
# print(number_tensor, number_tensor.shape)

# 拆分数据集
x_train_categ, x_test_categ, y_train, y_test = train_test_split(categorical_tensor, label_tensor, random_state=0,
                                                                test_size=0.15)
x_train_numer, x_test_numer, _, _ = train_test_split(number_tensor, label_tensor, random_state=0, test_size=0.15)

# 创建数据集
train_dataset = ExampleDataset(x_train_categ, x_train_numer, y_train)
test_dataset = ExampleDataset(x_test_categ, x_test_numer, y_test)

# 创建数据加载器
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

num_classes = 4

# 初始化模型、损失函数和优化器
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = FTTransformer(
    categories=[len(database_categ),len(operator_categ), 23, 106, len(operator_categ),len(operator_categ)],  # 示例类别数量
    num_continuous=x_train_numer.shape[1],  # 示例连续特征数量
    dim=64,
    depth=6,
    heads=4,
    dim_out=num_classes,
    attn_dropout=0.1,
    ff_dropout=0.1
).to(device)

# 获取各类别的权重
weights = compute_class_weight('balanced', classes=np.unique(y_train.numpy()), y=y_train.numpy())
weights = torch.tensor(weights, dtype=torch.float32).to(device)

optimizer = optim.Adam(model.parameters(), lr=1e-4)
focal_loss = FocalLoss(gamma=2., alpha=weights, num_classes=num_classes, device=device)

total_train_loss=[]
total_test_loss=[]
total_train_acc=[]
total_test_acc=[]
num_epochs = 100

# 定义存储结果的CSV文件名
train_csv_filename = './data/train_and_test_result/ME_one-hot/train_loss_and_acc.csv'
test_csv_filename = './data/train_and_test_result/ME_one-hot/test_loss_and_acc.csv'

# 写入CSV文件的列名
with open(train_csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Epoch', 'Loss', 'Accuracy'])

with open(test_csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Epoch', 'Loss', 'Accuracy','Every SQL Predict Time'])

evaluate_time=0
for epoch in range(num_epochs):

    # 训练阶段
    train_loss,train_acc = train_model(model, train_loader, optimizer, focal_loss, device)
    total_train_loss.append(train_loss)
    total_train_acc.append(train_acc)
    print(f"Epoch {epoch + 1}/{num_epochs}, Train Loss: {train_loss:.4f}, Train Accuracy: {train_acc:.4f}")

    # 将训练结果写入CSV文件
    with open(train_csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([epoch + 1, train_loss, train_acc])

    # 测试阶段
    start_time=time.time()
    test_loss, test_acc = evaluate_model(model, test_loader, focal_loss, device)
    end_time = time.time()
    evaluate_time += (end_time - start_time)
    total_test_loss.append(test_loss)
    total_test_acc.append(test_acc)
    # 将测试结果写入CSV文件
    with open(test_csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([epoch + 1, test_loss, test_acc,(end_time - start_time)/test_loader.batch_size])

    print(f"Epoch {epoch + 1}/{num_epochs}, Test Loss: {test_loss:.4f}, Test Accuracy: {test_acc:.4f},Predict time: {(end_time - start_time)/test_loader.batch_size:.4f}")

    if (epoch + 1) % 5 == 0:
        torch.save(model,f"./data/model_param/ME_one-hot/model_{epoch + 1}.pkl")
print(f"Total evaluate time: {evaluate_time:.4f},Average evaluate time: {evaluate_time/(num_epochs*test_loader.batch_size):.4f}")

torch.save(model,f"./data/model_param/ME_one-hot/model_final.pkl.")

plt.figure()
plt.grid(True)
plt.plot(range(num_epochs),total_train_loss,label='Train Loss')
plt.plot(range(num_epochs),total_test_loss,label='Test Loss')
plt.xticks(range(0,num_epochs+1,5))
plt.title('Training and Test Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.savefig("./images/ME_one-hot/loss.png",dpi=300)
plt.show()

plt.figure()
plt.grid(True)
plt.plot(range(num_epochs),total_train_acc,label='Train Accuracy')
plt.plot(range(num_epochs),total_test_acc,label='Test Accuracy')
plt.xticks(range(0,num_epochs+1,5))
plt.ylim(0, 1)
plt.title('Train and Test Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.savefig("./images/ME_one-hot/test_acc.png",dpi=300)
plt.show()

