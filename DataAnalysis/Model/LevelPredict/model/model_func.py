import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


class FocalLoss(torch.nn.Module):
    def __init__(self, gamma=2., alpha=None, reduction='mean', num_classes=None, device=None):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.num_classes = num_classes
        self.device = device  # 保存设备信息以便后续使用

        # 如果alpha没有提供，则初始化为均匀分布
        if alpha is None:
            self.alpha = torch.ones(num_classes, device=device) / num_classes
        else:
            assert len(alpha) == num_classes, "alpha的长度应该与类别数相同"
            self.alpha = torch.tensor(alpha, dtype=torch.float32, device=device)

        self.reduction = reduction

    def forward(self, inputs, targets):
        # 确保inputs和targets都在正确的设备上
        inputs = inputs.to(self.device)
        targets = targets.to(self.device).long()  # 确保targets是长整型

        # 创建目标的one-hot编码
        one_hot = F.one_hot(targets, num_classes=self.num_classes).float()

        # 计算p_t（真实类别的概率）
        pt = (inputs * one_hot).sum(dim=1)  # 对类别求和得到每个样本的p_t
        pt = pt.view(-1, 1)  # 重塑以匹配广播要求

        # 为了避免数值稳定性问题，给pt加一个小的epsilon
        epsilon = 1e-9
        pt_hat = torch.clamp(pt, epsilon, 1. - epsilon)  # 将pt值限制在[epsilon, 1-epsilon]范围内

        # 计算每个样本的Focal Loss
        cross_entropy = -torch.log(pt_hat + 1e-9)  # 真实类别概率的对数（已经one-hot编码）的负值

        focal_loss = self.alpha[targets] * (1 - pt_hat) ** self.gamma * cross_entropy

        # 根据reduction参数对损失进行求和/平均
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss


class ExampleDataset(Dataset):
    def __init__(self, x_categ, x_numer, y):
        self.x_categ = x_categ
        self.x_numer = x_numer
        self.y = y

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.x_categ[idx], self.x_numer[idx], self.y[idx]


# 训练过程
def train_model(model, train_loader, optimizer, focal_loss, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for x_categ, x_numer, y in train_loader:
        x_categ, x_numer, y = x_categ.to(device), x_numer.to(device), y.to(device)

        optimizer.zero_grad()

        output = model(x_categ, x_numer)

        # 计算损失
        loss = focal_loss(output, y)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        # 获取预测结果
        _, predicted = torch.max(output, 1)  # 获取最大值的索引作为预测类别
        correct += (predicted == y).sum().item()

        total += y.size(0)

    accuracy = correct / total
    return running_loss,accuracy


def evaluate_model(model, test_loader, focal_loss, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for x_categ, x_numer, y in test_loader:
            x_categ, x_numer, y = x_categ.to(device), x_numer.to(device), y.to(device)

            output = model(x_categ, x_numer)

            # 计算损失
            loss = focal_loss(output, y)
            running_loss += loss.item()

            # 如果模型的输出是一个一维张量（batch_size,），将其调整为二维张量
            if output.dim() == 1:
                output = output.unsqueeze(1)  # Add a second dimension if it's missing

            # 获取预测结果
            _, predicted = torch.max(output, 1)  # 获取最大值的索引作为预测类别
            correct += (predicted == y).sum().item()

            total += y.size(0)

    accuracy = correct / total
    return running_loss, accuracy
