#!/bin/bash
# 快速训练示例脚本
# 使用项目中的音频文件训练一个基础的鼓点检测模型

echo "开始训练鼓点检测模型..."
echo "注意：如果没有标注数据，将使用传统 onset detection 生成弱标签"

# 创建模型输出目录
mkdir -p models

# 训练模型（使用 CRNN 架构，50 个 epoch）
python tools/train_drum_detector.py \
    --audio-dir godot/assets/audio \
    --model-type crnn \
    --epochs 50 \
    --batch-size 4 \
    --lr 0.001 \
    --output models/drum_detector.pth

echo ""
echo "训练完成！模型已保存到: models/drum_detector.pth"
echo "现在可以使用 audio_to_beatmap.py 生成谱面，它会自动使用这个模型"

