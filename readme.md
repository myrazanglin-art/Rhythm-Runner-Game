# 🎮 Rhythm Runner: Automatic Beatmap Generation / 基于多层音频分析的自动谱面生成系统

This project is a fully automated pipeline that converts arbitrary audio files into playable rhythm game levels.
本项目构建了一个全自动的流水线，能将任意音频文件转化为可玩的音游关卡。
Through comprehensive multi-layer audio analysis (MIR/DSP) and staged procedural synthesis, it generates Easy, Normal, and Hard charts without manual charting.
通过全面的多层音频分析（MIR/DSP）与分阶段的程序化合成，无需人工打谱即可自动生成三种难度的谱面。
It combines Python-based signal processing with the Godot engine.
系统结合了基于 Python 的信号处理与 Godot 引擎。


## ⚙️ System Architecture / 系统架构

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

## 🛠️ Technology Stack / 技术栈

- **Audio Analysis / 音频分析:** Python, Librosa, NumPy
- **Game Engine / 游戏引擎:** Godot Engine, GDScript
- **Data Format / 数据格式:** JSON

*(Source code, full AIST2010 project report, and demo video are available in this repository.)*
*(完整的 Python 分析脚本、AIST2010 项目报告与演示视频已上传至本仓库。)*
1. 问题诊断：为什么纯Pygame方案风险高？

•   音频延迟与同步精度： Pygame的 mixer 模块是为一般性音频播放设计的，其时序控制（如 pygame.mixer.music.get_pos()）不够精确，无法满足节奏游戏严苛的同步要求。延迟和抖动会严重影响游戏体验。

•   性能瓶颈： 纯Python在大量对象渲染和实时音频处理时可能遇到性能瓶颈，难以保证稳定的高帧率，而帧率波动会直接干扰定时判断。

•   开发效率与调试： 从零开始实现一个高精度的音频同步引擎和关卡编辑器，对于5-6周的本科项目来说工作量巨大，且调试过程会非常复杂。

2. 修订后的技术方案（混合架构）

新的方案采用 “专业化工具+轻量级集成” 的策略，将复杂问题交给专业的工具处理，我们则专注于游戏逻辑和内容设计。

核心思路： 使用 Godot 游戏引擎 替代 Pygame 作为核心框架，并利用其强大的生态。

修订后的技术栈：

组件 推荐工具 理由

核心游戏引擎 Godot Engine (GDScript/C#) 强烈推荐。 1) 内置高性能2D渲染。2) 提供精确的音频时序API。3) 节点化场景管理，非常适合游戏状态管理。4) 社区有成熟的节奏游戏模板。

节奏游戏核心 插件/社区资源 (如 GDRhythm) 避免重复造轮子。使用专门为Godot开发的节奏游戏框架，它们已经解决了音频同步、判定窗口等核心难题。

关卡（谱面）设计 专业外部编辑器 (如 MuseScore, Audacity) + 自定义导出脚本 可行性大幅提升。 利用成熟的乐谱软件或音频编辑器进行可视化谱面设计，然后通过脚本（如Python）将设计结果转换为游戏可读的JSON谱面文件。

辅助脚本 Python 发挥Python在数据处理和脚本编写上的优势，用于：1) 将外部编辑器数据转换为游戏谱面。2) 批量处理音频、图片资源。

3. 修订后的系统组件（基于Godot引擎）

1.  Godot 场景管理器： 用Godot的场景（Scene）和节点（Node）系统替代原来的 Game Manager，天然地管理菜单、关卡、暂停等状态。
2.  高精度音频引擎： 依赖Godot内置的 AudioStreamPlayer 及其 get_playback_position() API，该API相比Pygame提供了更高精度和更低的延迟。可以结合社区插件实现自动延迟校准。
3.  谱面加载器（不变）： 依然使用JSON格式存储谱面，Godot有良好的JSON解析支持。
4.  Note生成与移动： 在Godot中，每个音符可以是一个 TextureRect 或 Sprite2D 节点，利用Godot的 Tween 或内置物理引擎实现平滑移动，性能更优。
5.  判定系统： 在社区插件的基础上进行定制，调整判定窗口和评分规则。
6.  可视化编辑器（降级为数据转换器）： 放弃开发完整的“点击放置”式编辑器。 改为开发一个 “数据转换脚本” （用Python或GDScript）。例如，在MuseScore中写好乐谱（音符代表障碍物），导出为MusicXML，然后用脚本将MusicXML转换为游戏的JSON谱面。这更务实且高效。

4. 修订后的开发路线图（更务实）

•   Phase 1 (Weeks 1-2): 技术选型与原型验证

    ◦   学习Godot引擎基础。

    ◦   导入一个节奏游戏插件（如 GDRhythm），运行示例项目。

    ◦   目标： 实现一个能播放音乐、音符按节奏落下并能接受按键判定的最小可行原型。

•   Phase 2 (Weeks 3-4): 游戏化实现

    ◦   设计游戏角色和背景。

    ◦   实现跑酷角色自动移动。

    ◦   将插件中的“音符”与游戏中的“跳跃/攻击”动作关联起来。

    ◦   开发Python脚本，将MuseScore导出的测试乐谱转换为游戏JSON。

    ◦   目标： 创建一个可玩的、包含一个完整关卡的游戏版本。

•   Phase 3 (Weeks 5-6): 内容完善与抛光

    ◦   创建第二个关卡。

    ◦   添加分数、连击显示和基本UI。

    ◦   进行用户测试，微调判定难度和谱面设计。

    ◦   准备演示视频和报告。

    ◦   目标： 交付一个功能完整、体验流畅的最终版本。

5. 结论

是的，您是正确的。 仅凭Python和Pygame完成一个高质量的音游项目风险较高。修订后的提案转向 Godot引擎+专业化插件/工具 的方案，具有以下优势：

•   更高的可行性： 借助成熟框架和工具，规避了最困难的技术陷阱。

•   更短的学习曲线： Godot易于上手，且社区支持良好。

•   更强的教育价值： 学生可以专注于游戏设计、音乐映射和集成，而不是陷入底层技术细节。

•   更佳的项目成果： 最终更有可能交付一个同步精准、体验良好的游戏。

这个修订方案既回应了您的技术关切，又保持了项目的核心目标，使其在有限的学期时间内真正可行。

6. 使用指南（运行与开发）

•   目录结构（关键）

    godot/
      ├── project.godot                      Godot 项目配置
      ├── scenes/
      │   ├── Main.tscn                      主场景（含Audio、Player与UI）
      │   ├── Player.tscn                     玩家角色场景
      │   └── Note.tscn                      音符/敌人场景
      ├── scripts/
      │   ├── Game.gd                        游戏主逻辑（谱面加载/生成/判定/UI）
      │   ├── Player.gd                       玩家控制器（跳跃、攻击、移动）
      │   └── Note.gd                        音符/敌人移动逻辑
      ├── data/beatmaps/example.json         示例谱面（需自备音频）
      └── assets/
          ├── audio/                          放置 .ogg 音频
          ├── player/                         玩家贴图（手动添加）
          ├── enemies/                        敌人贴图（手动添加）
          └── obstacles/                      障碍物贴图（手动添加）

•   运行步骤

    1) 安装 Godot 4（推荐 4.2+）。
    2) 用 Godot 打开 `godot/` 目录。
    3) 将一首 .ogg 音频放入 `godot/assets/audio/` 并命名为 `example.ogg`，或修改 `data/beatmaps/example.json` 中的 `audio` 路径。
    4) 运行主场景 `scenes/Main.tscn`。
    5) 游戏操作：
       - K键：跳跃（跳过地面障碍物 ground_obstacle）
       - J键：攻击（击败敌人 enemy）
       - 玩家角色固定在屏幕左侧（x=150），不移动
       - 敌人和障碍物从右侧生成，向左移动到玩家位置（判定线）
       - 障碍物类型：
         - 橙色：地面障碍物（需要跳跃）
         - 红色：空中障碍物（在玩家上方，可正常通过）
         - 紫色：敌人（需要攻击）

•   谱面格式（JSON）

    {
      "title": "Example Song",
      "bpm": 120,
      "offset": 0.0,
      "audio": "res://assets/audio/example.ogg",
      "notes": [
        { "time": 1.000, "type": "obstacle", "lane": "lower" },
        { "time": 1.500, "type": "enemy", "lane": "upper" }
      ]
    }

    说明：
    - time：音符时机（秒，基于音频播放时间）。玩家应该在这个时机按下相应按键。
    - type：音符类型
      - "obstacle"：障碍物，需要按 K键 切换跑道躲避
      - "enemy"：敌人，需要按 J键 攻击击败
    - lane：跑道位置
      - "upper"：上方跑道（分界线上方）
      - "lower"：下方跑道（分界线下方）
    - 重要规则：
      - 同一时间（time）不能有两个障碍物出现在不同的跑道上
      - 怪物根据音符（notes数组）生成，不是根据节拍（BPM）
      - 怪物会在音符时机（hit_time）之前0.2秒到达判定线，这样玩家在音符时机按下J键时正好能攻击到怪物
    - offset：全局校准（可用于系统延迟校准，当前未应用，可在 Game.gd 中扩展）。

•   MusicXML → JSON 转换脚本

    依赖：`music21`（已在 `requirements.txt`）。

    安装依赖：
    pip install -r requirements.txt

    用法：
    python tools/musicxml_to_json.py <input.musicxml> godot/data/beatmaps/<output>.json

    转换逻辑（简化版）：
    - 读取第一个速度标记为 BPM（缺省 120）。
    - 将音高按 (MIDI % 3) 映射到三车道。
    - 使用 note.offset（秒）作为时间戳；结果已排序。

•   添加玩家和敌人贴图

    1) 玩家贴图：
       - 准备玩家的图片（PNG格式，建议 32x48 像素或更大）
       - 在Godot中导入到 `assets/player/` 目录
       - 打开 `scenes/Player.tscn`，选择 `Sprite2D` 节点
       - 在 Inspector 的 Texture 属性中，将你的贴图拖入

    2) 敌人贴图：
       - 准备敌人的图片（PNG格式，建议 32x32 像素或更大）
       - 在Godot中导入到 `assets/enemies/` 目录
       - 打开 `scenes/Note.tscn`，选择 `Sprite2D` 节点
       - 在 Inspector 的 Texture 属性中，将你的贴图拖入
       - 注意：障碍物和敌人使用同一个场景，但可以通过 `Note.gd` 中的 `modulate` 颜色区分
       - 也可以在代码中为不同类型加载不同的贴图

    3) 障碍物贴图：
       - 准备障碍物的图片（PNG格式）
       - 在Godot中导入到 `assets/obstacles/` 目录
       - 将贴图命名为 `obstacle.png`（或修改 `Note.gd` 中的路径）
       - 障碍物会自动加载贴图，如果加载失败会显示橙色

•   后续可扩展点

    - 动画系统：为玩家添加跳跃和攻击动画（使用 AnimationPlayer）
    - 敌人多样化和贴图区分：为不同类型敌人加载不同贴图
    - 背景滚动：添加滚动背景，营造跑酷感
    - 更细的判定与打击感：在 `Game.gd` 扩展偏移校准、视觉反馈
    - 生命值系统：添加玩家生命值，被敌人或障碍物碰撞时扣除
    - 资源与UI美化：完善分数结算界面、添加暂停菜单
