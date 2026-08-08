# MusicGame_Demo — 安装与使用指南

只讲一件事:在一台新机器上,把拆轨 + 分析环境装起来,然后跑起来。

---

## 1. 一句话总览

- Python **3.11.x**(3.10 ≤ x ≤ 3.12,优先 3.11)虚拟环境
- 包:`torch` `demucs` `scipy` `numpy` `soundfile`(必需);`librosa`(可选,Tab 3 自动估 BPM 用;装不上就手动填 BPM)
- 模型:`htdemucs`(4 轨主拆轨,demucs 自带下载,首次跑时拉,缓存到本地)
- 用法:`demucs ...` 拆轨 / `python3 drum_bands.py <drums.wav> [--bpm N]` 频段鼓件近似

> **Python 版本小字:**
> - **推荐 3.11.x**:demucs 4.1 + torch 2.x 这条路最稳。本项目 Mac 上跑的就是 3.13(2026-07-14 升级),Linux/Windows 推荐 3.11(更省心,torch wheel 都齐)
> - 不要 3.13 **+ 已装老的 3.10**:py 启动器(`/usr/bin/py -3`)会任意指一个,可能让脚本选了老的;**把老的 3.10 完全卸载或挪出 PATH**
> - 不要 3.9 或更老:demucs 4.1 `requires-python: >=3.10`

---

## 2. 安装

### 2.1 双击启动(免命令行,推荐)

非开发者路径:**全程不碰 Terminal / PowerShell**。

- **macOS**:Finder 双击 `MusicSplitter_Install.command`
  - 没装 Python 时,自动开浏览器到 python.org;下载页面里点 **Python 3.11.x** 大按钮(不是顶部 3.13);装好 .pkg 后回 Terminal 窗口按回车继续
- **Windows**:Explorer 双击 `MusicSplitter_Install.bat`
  - 没装 Python 时(或已装的太老 → 弹下载页),下载页面里点 **Python 3.11.x** 大按钮(不是顶部 3.13);装好 .exe **务必勾 "Add Python to PATH"**,回去按任意键继续
  - **重要**:Win 装过 Python 3.10(老 GPU 工具链、Visual Studio Installer 之类常带的)的话,旧版会留在 `C:\Python310` 之类,但 PATH 上的 `python.exe` 也指向它。**新装的 3.11 装到不同目录就行**,我们脚本优先试 `py -3` 启动器,这个无视 PATH 上是哪个,自动选注册表中标记为 "default" 的那个

装完会自动问"启动 GUI?",回车就开。

### 2.2 命令行(进阶 / 远程 / 自动化)

直接 CLI 调启动器脚本(同一个 .command/.bat):

#### 2.2.1 macOS / Linux

```bash
cd /Users/bear/Documents/MusicGame_Demo
bash MusicSplitter_Install.command
# 装完会问要不要启动 GUI,跳过即直接退出
```

装完后:
```bash
source .venv-demucs/bin/activate
export MUSIC_SPLITTER_ROOT="$PWD"   # gui.py 靠它找项目根(启动器会自动设,CLI 直跑要手动)
python3 gui.py
```

#### 2.2.2 Windows(PowerShell)

```powershell
cd $HOME\Documents\MusicGame_Demo
.\MusicSplitter_Install.bat
```

装完后:
```powershell
.venv-demucs\Scripts\Activate.ps1
$env:MUSIC_SPLITTER_ROOT = $PWD     # gui.py 靠它找项目根(启动器会自动设,CLI 直跑要手动)
python gui.py
```

### 2.3 脚本做了什么

1. 把 `models/checkpoints/*.th` 硬链 / 拷到 torch hub cache(免下载,**只有这步是新的**)
2. 检测 `python3`(Mac)/ `python`(Win) 是否存在 + 版本 ≥3.10
3. 不存在就引导到 python.org 下载页(Mac 用 .pkg 双击 / Win 用 .exe 双击,务必勾 Add to PATH)
4. 在项目根创建 `.venv-demucs/`(Apple Silicon 自动用 `arch -arm64` 跑)
5. 装 `torch torchaudio demucs scipy numpy soundfile librosa`
6. 跑一遍 import 验证
7. (双击版本)问要不要启动 GUI

### 2.4 已装完后启动 GUI

不需要再开 Terminal / PowerShell,直接双击:

| 平台 | 文件 | 行为 |
|---|---|---|
| macOS | `MusicSplitter_GUI.command` | Finder 双击 → 自动开 Terminal 跑 GUI |
| Windows | `MusicSplitter_GUI.bat` | Explorer 双击 → CMD 闪一下关掉,GUI 弹出(`pythonw` 不带 console) |

首次安装未完成时,GUI 启动器会提示先去跑 `MusicSplitter_Install.command` / `MusicSplitter_Install.bat`。

### 2.5 纯 CLI 用法(已装完,不启动 GUI)

```bash
source .venv-demucs/bin/activate        # Mac
# .venv-demucs\Scripts\Activate.ps1    # Win

demucs -n htdemucs --segment 7 --overlap 0.1 -o separated whiplash_seg.wav
python3 drum_bands.py separated/htdemucs/<your_track>/drums.wav --bpm 125
```

> **`MUSIC_SPLITTER_ROOT` 只有 `gui.py` 需要**:GUI 不靠 `__file__` 反推项目根(目录改名 / 软链会断),改由启动器显式设置。GUI 启动器(`MusicSplitter_GUI.{command,bat}`)已经自动设了,双击不用管;CLI 直跑 `gui.py` 才要手动 export(见 §2.2)。`demucs` 和 `drum_bands.py` 都不需要它。

---

## 3. 模型

demucs 模型是 Meta 训练好的一组权重文件,首次跑某个模型时 demucs 会自动从 `dl.fbaipublicfiles.com`(或 HuggingFace Hub)下载到本地缓存,后续复用。三个模型**作用完全不同,选错了要么拆不出东西要么拆得没意义**。

### 3.1 模型清单

#### `htdemucs` —— **默认**(你大部分时候就该用这个)

| | |
|---|---|
| 下载 URL | `https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th` |
| 大小 | ~84 MB |
| 内部结构 | **Hybrid Transformer**(CNN + Transformer 混合),4 源 bag-of-1 |
| 输出 | 4 轨 WAV:`vocals.wav` / `drums.wav` / `bass.wav` / `other.wav` |
| 训练集 | MusDB-HQ |
| 何时用 | **本项目默认**;任何 "我要 vocal / 鼓 / bass / 伴奏 各一轨" 的场景 |
| 速度(M3 CPU) | ~5–6× realtime(190s 音频 ~35s 跑完) |

Hybrid Demucs 是 demucs 3.x 的奠基性架构,4.x 仍在用。是**最稳、最快、产物最规矩**的选择。

#### `htdemucs_ft` —— **更强但更慢**(人声 / 难件 时再换)

| | |
|---|---|
| 下载 URL | `https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/f7e0c4bc-ba3fe64a.th` |
| 大小 | ~84 MB(单文件,但内部是 **bag of 4**:`f7e0c4bc` / `d12395a8` / `92cfc3b6` / `04573f0d`) |
| 内部结构 | 同 `htdemucs`,但 fine-tuned 跑了 4 个不同种子,demucs 跑**每个权重一次**再求平均 |
| 输出 | 同 htdemucs,4 轨 |
| 何时用 | ① 想要更难的人声抠,② 处理多人声 / 强混响 / 反相位对齐 |
| 速度(M3 CPU) | **~1× realtime 或更慢**,190s 音频可能 3–4 分钟;GPU 上稍好 |

`ft` = "fine-tuned"。跑一次相当于跑 4 次 htdemucs 再平均。对**难件**(人声抠不干净、混响强、多人声重叠)提升明显,简单歌曲差别不大,默认不用,卡人声再用。

#### `htdemucs_6s` —— **乐器级**(本项目不用,但你要拿来做乐器 cover 可能用得上)

| | |
|---|---|
| 下载 URL | `https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/5c90dfd2-34c22ccb.th` |
| 大小 | ~52 MB |
| 内部结构 | Hybrid Demucs,**6 个 source**(乐器级) |
| 输出 | 6 轨 WAV:`vocals.wav` / `drums.wav` / `bass.wav` / `guitar.wav` / `piano.wav` / `other.wav` |
| 何时用 | 你想把 bass / guitar / piano **单独**拆出来(比如要 cover 一首原版) |
| **不要**用于 | **鼓件细分**(名字误导:6s = 6 个 source,不是 kick/snare/hat) |

> ⚠️ 名字误导:**`6s` 是 6 个 source(乐器),不是 6 秒 segment**。`--segment` 还是 ≤7.8。

### 3.2 怎么选

- 拆四轨 / 本项目主用例 / 速度老火:👉 `htdemucs`
- 人声不稳 / 好不容易拆得不干净:👉 `htdemucs_ft`(代价是 4× 慢)
- 要的不是人声 + 鼓 + bass,而是要"分身吉他手 / 键盘":👉 `htdemucs_6s`
- 只要“伴奏 / 干声”一对:👉 `htdemucs` + GUI 右上“只去人声”checkbox(走 `--two-stems vocals`)

### 3.3 缓存位置(避免重复下载)

- macOS / Linux:`~/.cache/torch/hub/checkpoints/`
- Windows:`%LOCALAPPDATA%\torch\hub\checkpoints\`
- 项目本地 bundle:`models/checkpoints/`(见 §3.5)

### 3.4 不用装的(本项目不依赖)

- ❌ MDX-DrumSep / `mdxnet-infer` —— 依赖 numba,Windows wheel 经常缺
- ⚠️ librosa —— **可选**:装上了 Tab 3 支持 `--bpm auto` 自动估速(`librosa.beat.beat_track`);装不上就手动填 BPM,频段分析本身走 scipy,不依赖它

### 3.5 已经在 `models/checkpoints/` 里(免下载)

为了对付 HuggingFace Hub 在国内 / 防火墙后面频繁 403,这套项目**把三个标准 demucs `.th` 跟代码一起发**:

```
models/checkpoints/
  955717e8-8726e21a.th   80 MB   htdemucs
  f7e0c4bc-ba3fe64a.th   80 MB   htdemucs_ft
  5c90dfd2-34c22ccb.th   52 MB   htdemucs_6s
  + README.md  +  .gitkeep
```

**装的时候** `MusicSplitter_Install.{command,bat}` 会先扫这个目录,有就:
- macOS:`ln`(硬链)到 `~/.cache/torch/hub/checkpoints/` —— 同一 inode,本地磁盘占 ≈ 0
- Windows:`copy` 到 `%LOCALAPPDATA%\torch\hub\checkpoints\`(没有不需管理员的硬链办法)—— 多 ~213 MB

**怎么补回来**(如果拿了精简版没有 `.th`):
```bash
mkdir -p models/checkpoints && cd models/checkpoints
curl -L -O https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th
curl -L -O https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/f7e0c4bc-ba3fe64a.th
curl -L -O https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/5c90dfd2-34c22ccb.th
```

或者复用机器已有的:`ln ~/.cache/torch/hub/checkpoints/*.th models/checkpoints/`

**分发注意**:213 MB 挺大。git 仓库用 `.gitignore` 排除 `*.th`,LFS 或单独 zip 旁路:
```gitignore
models/checkpoints/*.th
!models/checkpoints/.gitkeep
```

GUI 跑 demucs 时强制 `HF_HUB_OFFLINE=1`,确保 demucs 走 legacy `.th` 路径而非 HuggingFace Hub xet。详见 `models/README.md`。

---

## 4. 使用

### 4.1 GUI(`python3 gui.py`)

启动后 3 个 Tab:

| Tab | 干什么 |
|---|---|
| **1. Install** | 显示当前平台、venv/各包绿/红状态、嵌入式 install 脚本(读 `MusicSplitter_Install.command` 或 `MusicSplitter_Install.bat`)。按钮:复制、How to install(双击指引) |
| **2. Separate** | 选输入音频 → 选模型(htdemucs / htdemucs_ft / htdemucs_6s)→ 选输出目录(必填,留空报错)→ 调 `--segment`(1-7)和 `--device` → Run。日志区实时显示 demucs 输出,tqdm 进度条同步,运行中可 Cancel。**右上还有"只去人声" checkbox**(勾上自动注入 `--two-stems vocals`,产物变成 `vocals.wav` + `no_vocals.wav`,不再自动跳 Analyze) |
| **3. Analyze** | Browse 选 `drums.wav`(默认留空,不自动预填)→ 选填 BPM(默认 `auto`,librosa 估速)/ offset / threshold → Run → 输出 4 件带通 wav + 16-step pattern。背后是 `drum_bands.py`(scipy bandpass + RMS,频段近似,不是真鼓件)。Tab 2 在跑也能用,运行中可 Cancel |

非开发者路径:跑 `MusicSplitter_Install.command` / `MusicSplitter_Install.bat` → 双击 `MusicSplitter_GUI.command` / `MusicSplitter_GUI.bat` → 全鼠标操作。

### 4.2 命令行(不用 GUI)

#### macOS / Linux
```bash
source .venv-demucs/bin/activate

# 验证环境
python3 -c "import torch, demucs, scipy, numpy, soundfile; print('OK')"
demucs --list-models | grep htdemucs
```

#### Windows
```powershell
.venv-demucs\Scripts\Activate.ps1
python -c "import torch, demucs, scipy, numpy, soundfile; print('OK')"
demucs --list-models | Select-String htdemucs
```

### 4.3 拆轨(主流程,4 轨)

```bash
demucs -n htdemucs --segment 7 -o separated whiplash_seg.wav
```

输出到 `separated/htdemucs/<your_track>/{bass,drums,other,vocals}.wav`,时长取决于输入长度。

参数:
- `-n htdemucs` —— 模型名
- `--segment 7` —— 每段 7s;demucs 4.x 上限 7.8(训练窗口),超了报 "Cannot use a Transformer model with a longer segment than it was trained for"
- `-o separated` —— 输出目录

### 4.4 频段鼓件近似分析

```bash
python3 drum_bands.py separated/htdemucs/<your_track>/drums.wav --bpm 125
```

读 `<输入的 drums.wav>`,做 4 段带通,输出:
- 控制台:每件每小节 16-step pattern(`X` / `.`)
- 写盘:`<drums.wav 同目录>/drum_pieces/{kick,snare,hat,cymbal}.wav`(mono 16-bit,归一化到 ~95% 满刻度)

参数:
- `--bpm N` —— 网格速度,**直接决定 step 对不对**(默认 `auto`,librosa 估速;估不出回退 125)。知道曲速就手动给,比如 `--bpm 210`
- `--offset 秒` —— 开头跳过 N 秒再对网格(第一拍不在 0s 时用)
- `--threshold N` —— RMS 阈值(不传 = 每 band 75 分位,即约 25% 的步标 X)

**注意:** 频段带通 ≠ 真鼓件分离。snare 带通里有 kick 谐波泄漏,cymbal/hat 在 2kHz+ 重叠,听感会混在一起。只能用于能量 / timing 对照。

### 4.5 GPU(可选,Windows / Linux)

有 NVIDIA 卡 + CUDA 装好后:

```bash
demucs -n htdemucs --segment 7 -d cuda -o separated whiplash_seg.wav
```

Mac 没有 CUDA,Apple Silicon 的 MPS 后端 demucs 不支持,会回退到 CPU。

---

## 5. 故障排查速查

| 报错 | 原因 | 解决 |
|---|---|---|
| `ERROR: Failed building wheel for llvmlite` | Windows 上 numba build 失败 | 跳过 librosa,精简依赖装(§2.2 末尾) |
| `Cannot use a Transformer model with a longer segment than it was trained for` | `--segment` 太大(6s 模型上限 7) | 改 `--segment 7` |
| `demucs: command not found` | venv 没激活 | `source .venv-demucs/bin/activate`(Win:`.venv-demucs\Scripts\Activate.ps1`) |
| `Activate.ps1 running scripts is disabled` | PowerShell 执行策略 | 管理员 PowerShell 跑 `Set-ExecutionPolicy RemoteSigned` |
| 首次 demucs 下载模型 `URLError: SSL EOF` | 偶发网络问题 | 重跑即可,缓存命中后不再出现 |
| `ModuleNotFoundError: No module named 'tkinter'` | Python 解释器没装 tkinter(Mac Brew `python@3.10` 不自带;Homebrew 公式 `python-tk@3.10` 与用户版本冲突) | 重跑 `MusicSplitter_Install.command` —— 启动器会自动用 `arch -arm64` 走 Python.org 的 arm64 Python(自带 tkinter) |
| `ERROR: Could not find a version that satisfies the requirement torch`(Mac Rosetta) | shell 在 Rosetta 下,x86_64 mac 进程装 torch,但 py3.13 没 x86_64 macOS wheel | 启动器已经自动 `arch -arm64` 走 arm64 模式。重跑 `MusicSplitter_Install.command` 重建 venv |
| `bash: MusicSplitter_Install.command: No such file or directory` | 跑命令时不在项目根 | `cd` 到项目根（本目录）再跑 |
| **Windows 双击 .bat 闪退 / "MusicSplitter_Install.bat" :无法识别为 cmdlet** | (1) PS 默认不让从当前目录跑脚本,要 `.\MusicSplitter_Install.bat` 或直接 Explorer 双击走 cmd.exe;(2) .bat 是 UTF-8 中文在 cmd CP936 下乱码 → "此时不应有" | 走 Explorer 双击(走 cmd 不走 PS);.bat 已 GBK + CRLF 重编码 |
| Windows `Install` 提示 "需要 Python 3.10+,当前 9" | PATH 上的 `python.exe` 是 3.9(常被 Visual Studio / NVIDIA 工具链带) | 装 Python 3.11 后,**`py -3` 启动器无视 PATH 上的旧版**,自动选新版。先看 `py -0` 列出有哪些版本,如不对用 `py -3.11` 显式指定 |
| Windows 装依赖 `OSError: [WinError 17]` / `not a valid Win32 application` | venv 是 32 位而 torch wheel 是 64 位(或反过来) | 重跑 `.\MusicSplitter_Install.bat`,它会重做 venv 到正确位数 |
| `[!] 没设 MUSIC_SPLITTER_ROOT 环境变量` | CLI 直跑 `gui.py`,没走启动器 | 双击启动器;或先 `export MUSIC_SPLITTER_ROOT=$PWD`(Win: `$env:MUSIC_SPLITTER_ROOT=$PWD`)再跑 |

### 5.1 顺带说:Apple Silicon + Rosetta 的坑(Mac arm64 专属)

如果你的 Terminal / iTerm2 跑在 Rosetta 2(也就是 `uname -m` 输出 `x86_64`,但机器是 Apple Silicon),直接 `python3` 跑出来的是 x86_64 进程。问题:
1. `pip install torch` 只找到 x86_64 macOS wheel(Python 3.10 才有,3.11+ 没有),新项目默认 Python 3.13 直接装不上
2. Brew 的 `python-tk@3.10` 跟已经装的 `python@3.10.19_1` 版本锁冲突,要 brew 从源码编译(5-10 分钟)

**解决**:启动器已经帮你处理 —— 在 Apple Silicon 上自动加 `arch -arm64`,跟 Rosetta shell 无关。如果你愿意一直用 arm64:Terminal.app → Settings → Profiles → 取消勾 "Open using Rosetta"。

---

## 6. 一键复现(完整流程)

```bash
# macOS(双击启动器,免命令行)
open MusicSplitter_Install.command   # 首次安装
open MusicSplitter_GUI.command       # 已装后启动

# 或命令行(同一脚本,跳过 GUI 提示即可)
bash MusicSplitter_Install.command
export MUSIC_SPLITTER_ROOT="$PWD"
python3 gui.py
```

```powershell
# Windows
.\MusicSplitter_Install.bat          # 首次安装
.\MusicSplitter_GUI.bat              # 已装后启动

# 或命令行(同一脚本)
.\MusicSplitter_Install.bat
$env:MUSIC_SPLITTER_ROOT = $PWD
python gui.py
```

跑 GUI:Tab 1 看装好了没有 → Tab 2 拆轨 → Tab 3 鼓件分析。

纯命令行复现(跳过 GUI):
```bash
# mac / Linux
source .venv-demucs/bin/activate
demucs -n htdemucs --segment 7 --overlap 0.1 -o separated whiplash_seg.wav
python3 drum_bands.py separated/htdemucs/<your_track>/drums.wav --bpm 125

# Windows
.venv-demucs\Scripts\Activate.ps1
demucs -n htdemucs --segment 7 --overlap 0.1 -o separated whiplash_seg.wav
python drum_bands.py separated\htdemucs\whiplash_seg\drums.wav --bpm 125
```