# MusicSplitter_GUI

**[English](README.md)** | 中文

基于 [demucs](https://github.com/facebookresearch/demucs) 的音乐拆轨 tkinter GUI:鼠标操作完成人声/鼓/贝斯/伴奏分离,外加频段鼓件近似分析工具(kick/snare/hat/cymbal 16 步 pattern)。

## 功能

- **Tab 1 Install**:环境状态灯(venv / torch / demucs / scipy / numpy / soundfile / librosa)+ 内嵌一键安装脚本
- **Tab 2 Separate**:选音频 → 选模型(`htdemucs` / `htdemucs_ft` / `htdemucs_6s`)→ 拆轨。支持"只去人声"(`--two-stems vocals`)、`--segment` / `--device` 调节、实时进度条、可取消;拆完自动把 `drums.wav` 填入 Analyze 页
- **Tab 3 Analyze**:`drum_bands.py` 后端 — scipy 带通把鼓轨拆成 kick/snare/hat/cymbal 四件,输出 16-step pattern + 各件 wav(**频段近似,不是真鼓件分离**)

## 快速开始

**双击党(推荐)**:

| 平台 | 首次安装 | 之后启动 |
|---|---|---|
| macOS | `MusicSplitter_Install.command` | `MusicSplitter_GUI.command` |
| Windows | `MusicSplitter_Install.bat` | `MusicSplitter_GUI.bat` |

**命令行**:

```bash
bash MusicSplitter_Install.command        # 装 venv + 依赖 + 模型入缓存
source .venv-demucs/bin/activate
export MUSIC_SPLITTER_ROOT="$PWD"         # CLI 直跑 gui.py 需要
python3 gui.py
```

纯 CLI 拆轨 / 分析:

```bash
demucs -n htdemucs --segment 7 -o separated input.wav
python3 drum_bands.py separated/htdemucs/input/drums.wav --bpm 125
```

详细安装、模型说明、故障排查见 [INSTALL.md](INSTALL.md)。

## 模型

三个 demucs checkpoint(`htdemucs` / `htdemucs_ft` / `htdemucs_6s`,共 ~213 MB)**不在 git 里**,作为 [Release v0.1.0](https://github.com/bear0328/MusicSplitter_GUI/releases/tag/v0.1.0) 的 Asset 分发:

```bash
python3 models/download_models.py   # 支持 HTTP_PROXY / HTTPS_PROXY 环境变量
```

安装脚本会把 `models/checkpoints/*.th` 硬链(macOS)/ 拷贝(Windows)进 torch hub cache;GUI 跑 demucs 时强制 `HF_HUB_OFFLINE=1`,全程不联网下模型。详见 [models/README.md](models/README.md)。

## 要求

- Python 3.10+(推荐 3.11;macOS 上 3.13 也验证过)
- 依赖:`torch` `demucs` `scipy` `numpy` `soundfile`,可选 `librosa`(自动估 BPM)
- 平台:macOS(Apple Silicon 自动走 arm64)/ Windows / Linux

## 项目结构

```
gui.py                        # tkinter GUI 主程序
drum_bands.py                 # 频段鼓件近似分析(CLI + GUI Tab 3 后端)
MusicSplitter_Install.*       # 首次安装(.command / .bat)
MusicSplitter_GUI.*           # 已安装启动器
models/download_models.py     # 从 GitHub Release 拉模型
INSTALL.md                    # 完整安装/使用/排障文档
PROGRESS.md                   # 开发进度记录
```

## 许可

暂未指定开源许可证;代码仅供参考。模型权重为 Meta 的 demucs checkpoint,遵循其原始许可。
