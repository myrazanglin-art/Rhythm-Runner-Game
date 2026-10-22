#!/usr/bin/env python3
"""
鼓点检测推理模块
===============

使用训练好的模型检测音频中的鼓点类型（kick, snare, hihat）
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import librosa
import torch

from drum_detection_model import DrumDetectionCNN, DrumDetectionCRNN


class DrumDetector:
    """鼓点检测器"""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        model_type: str = "crnn",
        device: Optional[torch.device] = None,
        threshold: float = 0.5,
    ):
        """
        初始化鼓点检测器
        
        Args:
            model_path: 模型文件路径（如果为 None，使用传统方法）
            model_type: 模型类型 ("cnn" 或 "crnn")
            device: 设备（CPU 或 CUDA）
            threshold: 检测阈值（0-1）
        """
        self.model_path = model_path
        self.model_type = model_type
        self.threshold = threshold
        
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device = device
        
        self.model = None
        if model_path and Path(model_path).exists():
            self._load_model()
        else:
            print("[鼓点检测] 未找到模型文件，将使用传统 onset detection 作为回退")
    
    def _load_model(self) -> None:
        """加载模型"""
        try:
            if self.model_type == "cnn":
                self.model = DrumDetectionCNN()
            else:
                self.model = DrumDetectionCRNN()
            
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            print(f"[鼓点检测] 已加载模型: {self.model_path}")
        except Exception as e:
            print(f"[鼓点检测] 加载模型失败: {e}，将使用传统方法")
            self.model = None
    
    def detect_drums(
        self,
        y: np.ndarray,
        sr: int = 22050,
        hop_length: int = 512,
        n_mels: int = 128,
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        检测音频中的鼓点
        
        Args:
            y: 音频信号
            sr: 采样率
            hop_length: hop length
            n_mels: Mel 频谱的 bin 数
        
        Returns:
            (kick_times, snare_times, hihat_times) - 三种鼓点的时间列表
        """
        if self.model is None:
            # 使用传统方法作为回退
            return self._detect_traditional(y, sr, hop_length)
        
        # 使用 ML 模型
        return self._detect_with_model(y, sr, hop_length, n_mels)
    
    def _detect_traditional(
        self,
        y: np.ndarray,
        sr: int,
        hop_length: int,
    ) -> Tuple[List[float], List[float], List[float]]:
        """使用传统 onset detection 作为回退"""
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, hop_length=hop_length
        )
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length).tolist()
        
        # 简化：将所有 onset 作为 kick
        return onset_times, [], []
    
    def _detect_with_model(
        self,
        y: np.ndarray,
        sr: int,
        hop_length: int,
        n_mels: int,
    ) -> Tuple[List[float], List[float], List[float]]:
        """使用 ML 模型检测"""
        # 计算 Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=n_mels, hop_length=hop_length
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # 归一化
        mel_spec_db = (mel_spec_db + 80) / 80.0
        mel_spec_db = np.clip(mel_spec_db, 0, 1)
        
        # 转换为 tensor
        mel_tensor = torch.FloatTensor(mel_spec_db).unsqueeze(0).unsqueeze(0)  # (1, 1, n_mels, T)
        mel_tensor = mel_tensor.to(self.device)
        
        # 推理
        with torch.no_grad():
            outputs = self.model(mel_tensor)  # (1, T, 3)
            outputs = outputs.squeeze(0).cpu().numpy()  # (T, 3)
        
        # 提取时间
        times = librosa.frames_to_time(
            np.arange(outputs.shape[0]), sr=sr, hop_length=hop_length
        )
        
        # 根据阈值提取鼓点
        kick_times = times[outputs[:, 0] >= self.threshold].tolist()
        snare_times = times[outputs[:, 1] >= self.threshold].tolist()
        hihat_times = times[outputs[:, 2] >= self.threshold].tolist()
        
        return kick_times, snare_times, hihat_times


def detect_drums_from_audio(
    audio_path: Path,
    model_path: Optional[str] = None,
    model_type: str = "crnn",
    threshold: float = 0.5,
    sr: int = 22050,
) -> Tuple[List[float], List[float], List[float]]:
    """
    从音频文件检测鼓点
    
    Args:
        audio_path: 音频文件路径
        model_path: 模型文件路径（可选）
        model_type: 模型类型
        threshold: 检测阈值
        sr: 采样率
    
    Returns:
        (kick_times, snare_times, hihat_times)
    """
    # 加载音频
    y, sr = librosa.load(str(audio_path), sr=sr, mono=True)
    
    # 创建检测器
    detector = DrumDetector(model_path=model_path, model_type=model_type, threshold=threshold)
    
    # 检测
    return detector.detect_drums(y, sr=sr)


