#!/usr/bin/env python3
"""
训练鼓点检测模型
===============

使用标注数据或半监督方法训练鼓点检测模型。

如果没有标注数据，可以使用：
1. 数据增强（pitch shift, time stretch, noise）
2. 使用传统 onset detection 作为弱标签
3. 使用预训练模型进行迁移学习

训练流程：
1. 准备数据（Mel spectrogram + 标签）
2. 数据增强
3. 训练模型
4. 验证和保存
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple, Optional
import random

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import librosa

from drum_detection_model import DrumDetectionCNN, DrumDetectionCRNN


class DrumDataset(Dataset):
    """
    鼓点检测数据集
    
    如果没有标注数据，可以使用传统 onset detection 生成弱标签
    """
    
    def __init__(
        self,
        audio_files: List[Path],
        labels: Optional[List[np.ndarray]] = None,
        sr: int = 22050,
        n_mels: int = 128,
        hop_length: int = 512,
        segment_length: float = 3.0,  # 每个样本的时长（秒）
        augment: bool = True,
    ):
        self.audio_files = audio_files
        self.sr = sr
        self.n_mels = n_mels
        self.hop_length = hop_length
        self.segment_length = segment_length
        self.augment = augment
        
        # 如果没有提供标签，使用传统方法生成弱标签
        if labels is None:
            print("[数据] 未提供标签，使用传统 onset detection 生成弱标签...")
            labels = self._generate_weak_labels()
        
        self.labels = labels
    
    def _generate_weak_labels(self) -> List[np.ndarray]:
        """使用传统 onset detection 生成弱标签"""
        labels = []
        
        for audio_file in self.audio_files:
            y, sr = librosa.load(str(audio_file), sr=self.sr, mono=True)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # 计算 Mel spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, n_mels=self.n_mels, hop_length=self.hop_length
            )
            n_frames = mel_spec.shape[1]
            
            # 使用 onset detection 检测瞬态
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=self.hop_length)
            onset_frames = librosa.onset.onset_detect(
                onset_envelope=onset_env, sr=sr, hop_length=self.hop_length
            )
            
            # 创建标签：每个时间帧的鼓点类型
            # 简化：将所有 onset 标记为 kick（可以后续改进）
            label = np.zeros((n_frames, 3), dtype=np.float32)
            for frame in onset_frames:
                if frame < n_frames:
                    label[frame, 0] = 1.0  # kick
            
            labels.append(label)
        
        return labels
    
    def __len__(self) -> int:
        return len(self.audio_files)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        audio_file = self.audio_files[idx]
        label = self.labels[idx]
        
        # 加载音频
        y, sr = librosa.load(str(audio_file), sr=self.sr, mono=True)
        
        # 数据增强
        if self.augment and random.random() > 0.5:
            # Pitch shift
            if random.random() > 0.5:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=random.uniform(-2, 2))
            
            # Time stretch
            if random.random() > 0.5:
                rate = random.uniform(0.9, 1.1)
                y = librosa.effects.time_stretch(y, rate=rate)
                # 调整标签长度
                new_len = int(len(label) * rate)
                if new_len < len(label):
                    label = label[:new_len]
                else:
                    padding = np.zeros((new_len - len(label), 3), dtype=np.float32)
                    label = np.vstack([label, padding])
            
            # 添加噪声
            if random.random() > 0.7:
                noise = np.random.normal(0, 0.01, y.shape)
                y = y + noise
        
        # 计算 Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=self.n_mels, hop_length=self.hop_length
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # 归一化
        mel_spec_db = (mel_spec_db + 80) / 80.0  # 归一化到 [0, 1]
        mel_spec_db = np.clip(mel_spec_db, 0, 1)
        
        # 截取或填充到固定长度
        target_frames = int(self.segment_length * sr / self.hop_length)
        if mel_spec_db.shape[1] > target_frames:
            mel_spec_db = mel_spec_db[:, :target_frames]
            label = label[:target_frames]
        elif mel_spec_db.shape[1] < target_frames:
            padding = np.zeros((self.n_mels, target_frames - mel_spec_db.shape[1]))
            mel_spec_db = np.hstack([mel_spec_db, padding])
            label_padding = np.zeros((target_frames - len(label), 3))
            label = np.vstack([label, label_padding])
        
        # 转换为 tensor
        mel_tensor = torch.FloatTensor(mel_spec_db).unsqueeze(0)  # (1, n_mels, T)
        label_tensor = torch.FloatTensor(label)  # (T, 3)
        
        return mel_tensor, label_tensor


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> float:
    """训练一个 epoch"""
    model.train()
    total_loss = 0.0
    
    for mel_spec, labels in dataloader:
        mel_spec = mel_spec.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        
        # 前向传播
        outputs = model(mel_spec)  # (batch, T, 3)
        outputs = outputs.squeeze(0)  # (T, 3) - 假设 batch_size=1
        
        # 计算损失
        loss = criterion(outputs, labels)
        
        # 反向传播
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """验证模型"""
    model.eval()
    total_loss = 0.0
    
    with torch.no_grad():
        for mel_spec, labels in dataloader:
            mel_spec = mel_spec.to(device)
            labels = labels.to(device)
            
            outputs = model(mel_spec)
            outputs = outputs.squeeze(0)
            
            loss = criterion(outputs, labels)
            total_loss += loss.item()
    
    return total_loss / len(dataloader)


def main():
    parser = argparse.ArgumentParser(description="训练鼓点检测模型")
    parser.add_argument(
        "--audio-dir",
        type=Path,
        required=True,
        help="音频文件目录",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        choices=["cnn", "crnn"],
        default="crnn",
        help="模型类型",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="训练轮数",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="批次大小",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.001,
        help="学习率",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/drum_detector.pth"),
        help="模型输出路径",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=None,
        help="标签文件路径（JSON格式，可选）",
    )
    args = parser.parse_args()
    
    # 设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[训练] 使用设备: {device}")
    
    # 加载音频文件
    audio_files = list(args.audio_dir.glob("*.ogg")) + list(args.audio_dir.glob("*.wav")) + list(args.audio_dir.glob("*.mp3"))
    if not audio_files:
        raise ValueError(f"在 {args.audio_dir} 中未找到音频文件")
    
    print(f"[训练] 找到 {len(audio_files)} 个音频文件")
    
    # 加载标签（如果有）
    labels = None
    if args.labels and args.labels.exists():
        with open(args.labels) as f:
            label_data = json.load(f)
            labels = [np.array(l) for l in label_data]
    
    # 创建数据集
    dataset = DrumDataset(audio_files, labels=labels, augment=True)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    # 创建模型
    if args.model_type == "cnn":
        model = DrumDetectionCNN().to(device)
    else:
        model = DrumDetectionCRNN().to(device)
    
    print(f"[训练] 模型类型: {args.model_type.upper()}")
    print(f"[训练] 模型参数数量: {sum(p.numel() for p in model.parameters()):,}")
    
    # 损失函数和优化器
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # 训练
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    best_loss = float('inf')
    print(f"\n[训练] 开始训练，共 {args.epochs} 个 epoch...")
    
    for epoch in range(args.epochs):
        train_loss = train_epoch(model, dataloader, criterion, optimizer, device)
        val_loss = validate(model, dataloader, criterion, device)
        
        scheduler.step(val_loss)
        
        print(f"Epoch {epoch+1}/{args.epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # 保存最佳模型
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), args.output)
            print(f"  ✓ 保存最佳模型 (loss: {best_loss:.4f})")
    
    print(f"\n[训练] 完成！模型已保存到: {args.output}")


if __name__ == "__main__":
    main()


