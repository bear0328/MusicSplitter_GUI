# MusicSplitter_GUI

基于 [demucs](https://github.com/facebookresearch/demucs) 的音乐拆轨 tkinter GUI:鼠标操作完成人声/鼓/贝斯/伴奏分离,外加频段鼓件近似分析工具(kick/snare/hat/cymbal 16 步 pattern)。

A tkinter GUI front-end for [demucs](https://github.com/facebookresearch/demucs): point-and-click splitting of vocals / drums / bass / other, plus a frequency-band drum-piece approximation tool (kick/snare/hat/cymbal 16-step patterns).

## 功能 / Features

- **Tab 1 Install**:环境状态灯(venv / torch / demucs / scipy / numpy / soundfile / librosa)+ 内嵌一键安装脚本。
  Environment status lights (venv / torch / demucs / scipy / numpy / soundfile / librosa) with the embedded one-shot install script.
- **Tab 2 Separate**:选音频 → 选模型(`htdemucs` / `htdemucs_ft` / `htdemucs_6s`)→ 拆轨。支持"只去人声"(`--two-stems vocals`)、`--segment` / `--device` 调节、实时进度条、可取消;拆完自动把 `drums.wav` 填入 Analyze 页。
  Pick audio → pick model → split. Supports vocal-remover mode (`--two-stems vocals`), `--segment` / `--device` controls, live progress bar and cancellation; on success the `drums.wav` is auto-filled into the Analyze tab.
- **Tab 3 Analyze**:`drum_bands.py` 后端 — scipy 带通把鼓轨拆成 kick/snare/hat/cymbal 四件,输出 16-step pattern + 各件 wav(**频段近似,不是真鼓件分离**)。
  Backed by `drum_bands.py` — scipy bandpass splits the drum stem into kick/snare/hat/cymbal bands, printing 16-step patterns and writing per-piece wavs (**band approximation, not true drum separation**).

## 快速开始 / Quick start

**双击党(推荐)/ Double-click (recommended)**:

| 平台 Platform | 首次安装 First-time install | 之后启动 Launch afterwards |
|---|---|---|
| macOS | `MusicSplitter_Install.command` | `MusicSplitter_GUI.command` |
| Windows | `MusicSplitter_Install.bat` | `MusicSplitter_GUI.bat` |

**命令行 / Command line**:

```bash
bash MusicSplitter_Install.command        # 装 venv + 依赖 + 模型入缓存 / venv + deps + models into torch hub cache
source .venv-demucs/bin/activate
export MUSIC_SPLITTER_ROOT="$PWD"         # CLI 直跑 gui.py 需要 / required when running gui.py directly
python3 gui.py
```

纯 CLI 拆轨 / 分析 / Pure CLI separation & analysis:

```bash
demucs -n htdemucs --segment 7 -o separated input.wav
python3 drum_bands.py separated/htdemucs/input/drums.wav --bpm 125
```

详细安装、模型说明、故障排查见 [INSTALL.md](INSTALL.md)(中文)。
Full install guide, model details and troubleshooting: [INSTALL.md](INSTALL.md) (Chinese).

## 模型 / Models

三个 demucs checkpoint(`htdemucs` / `htdemucs_ft` / `htdemucs_6s`,共 ~213 MB)**不在 git 里**,作为 [Release v0.1.0](https://github.com/bear0328/MusicSplitter_GUI/releases/tag/v0.1.0) 的 Asset 分发:

The three demucs checkpoints (~213 MB total) are **not in git** — they ship as assets of [Release v0.1.0](https://github.com/bear0328/MusicSplitter_GUI/releases/tag/v0.1.0):

```bash
python3 models/download_models.py   # 支持 HTTP_PROXY / HTTPS_PROXY 环境变量 / honors HTTP_PROXY / HTTPS_PROXY
```

安装脚本会把 `models/checkpoints/*.th` 硬链(macOS)/ 拷贝(Windows)进 torch hub cache;GUI 跑 demucs 时强制 `HF_HUB_OFFLINE=1`,全程不联网下模型。详见 [models/README.md](models/README.md)。

The install script hard-links (macOS) / copies (Windows) `models/checkpoints/*.th` into the torch hub cache, and the GUI forces `HF_HUB_OFFLINE=1`, so models never download over the network. See [models/README.md](models/README.md).

## 要求 / Requirements

- Python 3.10+(推荐 3.11;macOS 上 3.13 也验证过)/ Python 3.10+ (3.11 recommended; 3.13 verified on macOS)
- 依赖:`torch` `demucs` `scipy` `numpy` `soundfile`,可选 `librosa`(自动估 BPM)/ Dependencies: `torch` `demucs` `scipy` `numpy` `soundfile`; optional `librosa` (auto BPM estimation)
- 平台:macOS(Apple Silicon 自动走 arm64)/ Windows / Linux — macOS (auto arm64 on Apple Silicon) / Windows / Linux

## 项目结构 / Project layout

```
gui.py                        # tkinter GUI 主程序 / main GUI
drum_bands.py                 # 频段鼓件近似分析(CLI + GUI Tab 3 后端)/ band-pass drum analysis (CLI + Tab 3 backend)
MusicSplitter_Install.*       # 首次安装(.command / .bat)/ first-time installer
MusicSplitter_GUI.*           # 已安装启动器 / launcher for installed setups
models/download_models.py     # 从 GitHub Release 拉模型 / fetch models from GitHub Release
INSTALL.md                    # 完整安装/使用/排障文档(中文)/ full install & troubleshooting doc (Chinese)
PROGRESS.md                   # 开发进度记录(中文)/ development log (Chinese)
```

## 许可 / License

暂未指定开源许可证;代码仅供参考。模型权重为 Meta 的 demucs checkpoint,遵循其原始许可。

No open-source license specified yet; code is provided as-is for reference. Model weights are Meta's demucs checkpoints, subject to their original license.
