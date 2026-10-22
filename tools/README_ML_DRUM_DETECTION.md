# ML 鼓点检测使用说明

## 概述

本项目使用深度学习模型（CNN/CRNN）来检测音频中的鼓点类型，替代传统的 onset detection 方法。模型可以识别三种鼓点类型：
- **Kick（底鼓）**：通常映射为 obstacle（需要躲避）
- **Snare（军鼓）**：通常映射为 enemy（可以攻击）
- **Hihat（踩镲）**：通常映射为 enemy（可以攻击）

## 文件结构

```
tools/
├── drum_detection_model.py      # 模型定义（CNN/CRNN）
├── drum_detection_inference.py   # 推理模块
├── train_drum_detector.py        # 训练脚本
└── audio_to_beatmap.py           # 主脚本（已集成 ML 检测）
```

## 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `torch>=2.0.0` - PyTorch 深度学习框架
- `torchaudio>=2.0.0` - 音频处理
- `librosa>=0.10.0` - 音频分析
- `numpy` - 数值计算

## 使用方法

### 1. 训练模型（可选）

如果没有预训练模型，可以训练一个新模型：

```bash
# 使用项目中的音频文件训练
python tools/train_drum_detector.py \
    --audio-dir godot/assets/audio \
    --model-type crnn \
    --epochs 50 \
    --batch-size 8 \
    --output models/drum_detector.pth
```

**注意**：如果没有标注数据，训练脚本会自动使用传统 onset detection 生成弱标签。这对于课程项目来说已经足够，但如果有标注数据，效果会更好。

### 2. 使用 ML 检测生成谱面

ML 检测已集成到 `audio_to_beatmap.py` 中，会自动使用：

```bash
python tools/audio_to_beatmap.py godot/assets/audio/song1.ogg
```

**工作流程**：
1. 首先尝试加载训练好的模型（从 `models/drum_detector.pth` 或默认位置）
2. 如果模型不存在，自动回退到传统 onset detection
3. 使用 ML 检测的鼓点优先生成音符：
   - Kick → obstacle（80% 概率）
   - Snare → enemy（70% 概率）
   - Hihat → enemy（60% 概率）
4. 传统 onset 作为补充

### 3. 模型架构

#### CNN 模型
- 3 层卷积 + BatchNorm + ReLU
- MaxPooling 降维
- 全局平均池化保留时间维度
- 全连接层输出 3 类概率

#### CRNN 模型（推荐）
- CNN 特征提取（同上）
- 双向 LSTM 处理时序信息
- 全连接层输出 3 类概率

## 创新点

1. **深度学习替代传统方法**：使用 CNN/CRNN 模型替代传统的 onset detection，提高检测准确性和稳定性
2. **多类型鼓点识别**：不仅检测鼓点位置，还识别鼓点类型（kick/snare/hihat）
3. **智能音符映射**：根据鼓点类型智能映射到游戏中的 enemy/obstacle
4. **优雅降级**：如果模型不可用，自动回退到传统方法，保证系统稳定性

## 训练数据准备（可选，用于改进模型）

如果有标注数据，可以创建 JSON 格式的标签文件：

```json
[
  [[0, 0, 0], [1, 0, 0], [0, 0, 0], ...],  // 音频1的标签（每帧 [kick, snare, hihat]）
  [[0, 1, 0], [0, 0, 0], [0, 0, 1], ...],  // 音频2的标签
  ...
]
```

然后训练：

```bash
python tools/train_drum_detector.py \
    --audio-dir godot/assets/audio \
    --labels labels.json \
    --model-type crnn \
    --epochs 100
```

## 技术细节

### 输入格式
- **Mel Spectrogram**: 128 bins × T frames
- 归一化到 [0, 1] 范围

### 输出格式
- 每个时间帧的 3 类概率：`[kick_prob, snare_prob, hihat_prob]`
- 默认阈值：0.4（可调整）

### 数据增强
训练时自动应用：
- Pitch shift（±2 半音）
- Time stretch（0.9x - 1.1x）
- 噪声添加

## 故障排除

1. **模型加载失败**：检查模型文件路径，或重新训练模型
2. **CUDA 错误**：如果没有 GPU，模型会自动使用 CPU
3. **内存不足**：减小 batch_size 或使用 CNN 模型（比 CRNN 更轻量）

## 未来改进方向

1. 使用更大的数据集训练
2. 使用预训练模型（如 MusicNet、MUSDB）进行迁移学习
3. 添加更多鼓点类型（crash, ride, tom 等）
4. 实时检测支持

