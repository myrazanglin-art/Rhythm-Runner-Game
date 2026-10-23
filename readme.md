# 🎮 Rhythm Runner: AI-Driven Automated Beatmap Generation / 基于多层音频分析的自动谱面生成系统

This project is a fully automated pipeline that converts arbitrary audio files into playable rhythm game levels.
本项目构建了一个全自动的流水线，能将任意音频文件转化为可玩的音游关卡。

Through comprehensive multi-layer audio analysis (MIR/DSP) and staged procedural synthesis, it generates Easy, Normal, and Hard charts without manual charting.
通过全面的多层音频分析（MIR/DSP）与分阶段的程序化合成，无需人工打谱即可自动生成三种难度的谱面。

It combines Python-based signal processing with the Godot engine.
系统结合了基于 Python 的信号处理与 Godot 引擎。

## 🚨 Market Gap & User Persona / 痛点与市场空白

**The Problem:** 
- For Players: Official rhythm game charts are highly limited. Niche indie, experimental electronic, or post-rock tracks rarely have playable charts. 
- For Studios: Hiring professional "Beatmappers" requires both musical expertise and game design sense. It is expensive, subjective, and creates a massive bottleneck for content updates.

**Target Audience:** Core rhythm game players who want to play their own Spotify/NetEase playlists, and indie game studios looking to rapidly prototype rhythm-based mechanics.

**痛点：** 
- 对于玩家：官方曲库极其有限，小众的独立音乐、实验电子或后摇歌曲很难找到可玩的谱面。
- 对于厂商：雇佣专业“打谱师”成本极高且周期长，严重制约了游戏的内容更新速度。
**目标受众：** 渴望把自己网易云/Spotify 歌单变成游戏的硬核音游玩家，以及希望快速验证音游核心玩法的独立游戏工作室。

## 🥊 Competitive Analysis / 竞品分析

| Solution / 方案 | AudioSurf | Beat Saber Auto-Mappers | **Rhythm Runner** |
| :--- | :--- | :--- | :--- |
| **Mapping Logic / 映射逻辑** | Simple Tempo/Energy | Heavy ML training needed | **Rule-based DSP + MIR** |
| **Note Variety / 音符种类** | Low (Only lanes) | Medium | **High (Holds, Enemies, Obstacles)**|
| **Dynamic Difficulty / 动态难度**| Non-existent | Limited | **Yes (Based on section intensity)**|
| **Playability / 可玩性** | Monotonous | Requires human tweak | **Immediate & Musical Coherent**|

**Our Advantage:** Traditional auto-generators only rely on simple BPM detection, resulting in chaotic, unmusical charts. Rhythm Runner extracts **15+ multidimensional audio features** to ensure the generated notes actually follow the song's emotional and structural flow.
**核心优势：** 传统的自动生成器仅依赖简单的 BPM 检测，导致谱面极其混乱且缺乏乐感。Rhythm Runner 提取了 **15+ 种多维音频特征**，确保生成的音符能够完美契合歌曲的情感与结构起伏。

## 🚀 Key Product Decisions (PRD) / 核心产品决策

### 1. Dynamic Difficulty Shaping / 动态难度塑造
- **Decision:** Instead of rigid, uniform note density, the algorithm reads the "Energy" (RMS) and "Section Intensity" of the track.
- **Result:** Quiet ambient bridges have sparse obstacles to give players a breather, while choruses and drops trigger high-density, adrenaline-pumping patterns.

- **决策：** 抛弃死板的均匀音符密度，算法会动态读取音轨的“能量(RMS)”和“段落强度”。
- **结果：** 安静的桥段障碍物稀疏，让玩家喘息；而高潮副歌部分则触发高密度的爽快谱面。

### 2. Meaningful Note Typing / 有意义的音符分类
- **Decision:** Not all notes are the same. We utilize **HPSS (Harmonic-Percussive Source Separation)** to split the audio.
- **Result:** Harmonic elements (like vocals and synths) are mapped to **Hold Notes (long presses)**, while percussive elements (drums/kicks) are mapped to **Enemies (timed attacks)**. This mirrors the natural human auditory expectation.

- **决策：** 拒绝单一的“点点点”。我们利用 **HPSS (谐波打击分离)** 技术对音频进行拆分。
- **结果：** 谐波元素（人声、合成器）被映射为**长按音符 (Hold Notes)**，而打击乐（鼓点）被映射为**敌人 (需要精准攻击)**。这让游玩过程完全符合人类的听觉直觉。

### 3. Lane Allocation Logic / 轨道分配逻辑
- **Decision:** Which lane (upper or lower) does a note go to?
- **Result:** Determined by frequency band dominance. High-frequency sounds go to the upper lane, while low-frequency sounds go to the lower lane, aligning visual flow with auditory expectation.

- **决策：** 音符应该出现在上轨还是下轨？
- **结果：** 根据频段主导权决定。高频声音走向上轨，低频走向下轨，实现视觉流向与听觉的绝对统一。

## ⚙️ System Architecture / 系统架构

This project bridges offline DSP analysis with a real-time game engine (Godot).
本项目将离线 DSP 分析与实时游戏引擎（Godot）完美结合。

### Stage 1: Python Audio Analysis / 阶段一：Python 音频分析
Uses `librosa` and `numpy` for offline audio analysis, extracting 15+ complementary descriptors.
使用 `librosa` 和 `numpy` 进行离线音频分析，提取超过 15 种互补的描述符：
- **Temporal / 时域:** Tempo, beats, onset times, and strengths. (BPM、节拍、起音时间及强度)
- **Spectral / 频谱:** Spectral centroid, rolloff, flatness, flux. (频谱质心、滚降、平坦度、通量)
- **Energy & Dynamics / 能量与动态:** RMS energy, dynamic range, frequency band energy. (RMS 能量、动态范围、频段能量)
- **Structure & Melody / 结构与旋律:** HPSS, CQT chroma, recurrence segmentation, melodic contours. (谐波/打击乐分离、色度特征、重复性分段、旋律轮廓提取)

### Stage 2: Godot Gameplay Execution / 阶段二：Godot 游戏执行
The generated JSON beatmaps are ingested by the Godot engine.
生成的 JSON 谱面被导入 Godot 引擎。
The engine synchronizes note spawning to the playback timeline.
引擎将音符生成与音乐播放时间轴完美同步。
It runs a dual-lane side-scrolling game with a distance-based judgment system.
运行带有基于空间距离判定系统的双轨横版游戏。

---

## 💡 Technical Trade-offs: Why Godot over Pygame? / 技术方案取舍：为什么弃用 Pygame 选择 Godot？

**Diagnosis / 问题诊断**
- **Audio Latency:** Pygame's `mixer` is designed for general audio, failing to meet the strict sync requirements of rhythm games.
- **Performance Bottleneck:** Pure Python struggles with high-frame-rate rendering and real-time audio processing.
- **Dev Efficiency:** Building a high-precision engine from scratch in 5-6 weeks was high-risk.

**诊断：** Pygame 的音频延迟无法满足音游严苛的同步要求；纯 Python 存在渲染性能瓶颈；5-6 周内从零开发高精度引擎风险过高。

**Revised Stack / 修订后的技术栈**
- **Engine:** **Godot Engine (GDScript)**. Built-in high-performance 2D rendering and precise audio timing API (`AudioStreamPlayer.get_playback_position()`).
- **Core Rhythm Logic:** Community plugins (e.g., GDRhythm) to avoid reinventing the wheel for audio sync and timing windows.
- **Beatmap Design:** External tools (MuseScore) + Custom Python conversion script (MusicXML to JSON).

**修订方案：** 转向 **Godot 引擎**，利用其内置高性能 2D 渲染与精确的音频时序 API。使用成熟的音游社区插件解决判定窗口，专注于内容设计，并开发 Python 转换脚本实现自动化。

---

## 🛠️ Usage Guide & Run Steps / 使用指南与运行步骤

### Directory Structure / 目录结构
```text
godot/
  ├── project.godot                      Godot 项目配置
  ├── scenes/
  │   ├── Main.tscn                      主场景（含Audio、Player与UI）
  │   ├── Player.tscn                    玩家角色场景
  │   └── Note.tscn                      音符/敌人场景
  ├── scripts/
  │   ├── Game.gd                        游戏主逻辑（谱面加载/生成/判定/UI）
  │   ├── Player.gd                      玩家控制器（跳跃、攻击、移动）
  │   └── Note.gd                        音符/敌人移动逻辑
  ├── data/beatmaps/example.json         示例谱面（需自备音频）
  └── assets/
      ├── audio/                         放置 .ogg 音频
      ├── player/                        玩家贴图
      ├── enemies/                       敌人贴图
      └── obstacles/                     障碍物贴图
