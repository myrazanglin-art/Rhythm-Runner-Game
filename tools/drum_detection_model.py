#!/usr/bin/env python3
"""
鼓点检测模型（CNN/CRNN）
======================

使用深度学习模型检测音频中的鼓点类型：
- Kick（底鼓）
- Snare（军鼓）
- Hihat（踩镲）

模型架构：
- 输入：Mel Spectrogram (128 bins × T frames)
- 输出：每个时间帧的鼓点类型概率 (kick, snare, hihat)

支持两种架构：
1. CNN：简单的卷积神经网络
2. CRNN：卷积循环神经网络（更适合时序特征）
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional


class DrumDetectionCNN(nn.Module):
    """
    简单的 CNN 模型用于鼓点检测
    
    架构：
    - 输入: (batch, 1, 128, T) - Mel spectrogram
    - 输出: (batch, T, 3) - (kick, snare, hihat) 概率
    """
    
    def __init__(self, n_mels: int = 128, dropout: float = 0.3):
        super().__init__()
        self.n_mels = n_mels
        
        # 卷积层
        self.conv1 = nn.Conv2d(1, 32, kernel_size=(3, 3), padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        
        self.conv2 = nn.Conv2d(32, 64, kernel_size=(3, 3), padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        
        self.conv3 = nn.Conv2d(64, 128, kernel_size=(3, 3), padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        
        # 池化层
        self.pool = nn.MaxPool2d(kernel_size=(2, 2))
        
        # 全局平均池化
        self.global_pool = nn.AdaptiveAvgPool2d((1, None))  # 保持时间维度
        
        # 全连接层
        self.fc1 = nn.Linear(128, 64)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 3)  # kick, snare, hihat
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: (batch, 1, n_mels, time_frames)
        
        Returns:
            (batch, time_frames, 3) - 每个时间帧的鼓点概率
        """
        # Conv block 1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool(x)
        
        # Conv block 2
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool(x)
        
        # Conv block 3
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        
        # 全局平均池化（保留时间维度）
        x = self.global_pool(x)  # (batch, 128, 1, T)
        x = x.squeeze(2)  # (batch, 128, T)
        
        # 转置以便在时间维度上应用全连接层
        x = x.transpose(1, 2)  # (batch, T, 128)
        
        # 全连接层
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)  # (batch, T, 3)
        
        # Sigmoid 激活（多标签分类）
        x = torch.sigmoid(x)
        
        return x


class DrumDetectionCRNN(nn.Module):
    """
    CRNN 模型用于鼓点检测（卷积 + 循环神经网络）
    
    架构：
    - CNN 提取特征
    - RNN 处理时序信息
    - 输出每个时间帧的鼓点类型概率
    """
    
    def __init__(
        self,
        n_mels: int = 128,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.n_mels = n_mels
        self.hidden_size = hidden_size
        
        # CNN 特征提取
        self.conv1 = nn.Conv2d(1, 32, kernel_size=(3, 3), padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        
        self.conv2 = nn.Conv2d(32, 64, kernel_size=(3, 3), padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        
        self.conv3 = nn.Conv2d(64, 128, kernel_size=(3, 3), padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        
        self.pool = nn.MaxPool2d(kernel_size=(2, 2))
        self.global_pool = nn.AdaptiveAvgPool2d((1, None))
        
        # RNN 处理时序
        self.rnn = nn.LSTM(
            input_size=128,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # 输出层
        self.fc = nn.Linear(hidden_size * 2, 3)  # 双向 LSTM
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: (batch, 1, n_mels, time_frames)
        
        Returns:
            (batch, time_frames, 3) - 每个时间帧的鼓点概率
        """
        # CNN 特征提取
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool(x)
        
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool(x)
        
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        
        # 全局平均池化
        x = self.global_pool(x)  # (batch, 128, 1, T)
        x = x.squeeze(2)  # (batch, 128, T)
        x = x.transpose(1, 2)  # (batch, T, 128)
        
        # RNN 处理时序
        x, _ = self.rnn(x)  # (batch, T, hidden_size * 2)
        
        # 输出层
        x = self.fc(x)  # (batch, T, 3)
        x = torch.sigmoid(x)
        
        return x


def load_model(
    model_path: str,
    model_type: str = "crnn",
    device: Optional[torch.device] = None,
) -> nn.Module:
    """
    加载训练好的模型
    
    Args:
        model_path: 模型文件路径
        model_type: 模型类型 ("cnn" 或 "crnn")
        device: 设备（CPU 或 CUDA）
    
    Returns:
        加载的模型
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    if model_type.lower() == "cnn":
        model = DrumDetectionCNN()
    else:
        model = DrumDetectionCRNN()
    
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    return model


def create_model(model_type: str = "crnn", **kwargs) -> nn.Module:
    """
    创建新的模型实例
    
    Args:
        model_type: 模型类型 ("cnn" 或 "crnn")
        **kwargs: 模型参数
    
    Returns:
        模型实例
    """
    if model_type.lower() == "cnn":
        return DrumDetectionCNN(**kwargs)
    else:
        return DrumDetectionCRNN(**kwargs)


