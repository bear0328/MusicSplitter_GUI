# MusicSplitter_GUI 项目进度

> 记录项目状态、已完成改动与待办事项。

## 项目结构

当前为扁平结构（项目根即 `MusicSplitter_GUI/` 目录本身）：

```
MusicSplitter_GUI/
├── gui.py                      # tkinter GUI 主程序
├── drum_bands.py               # 频段鼓件近似分析脚本
├── MusicSplitter_GUI.command   # macOS 已安装启动器
├── MusicSplitter_Install.command  # macOS 首次安装脚本
├── MusicSplitter_GUI.bat       # Windows 已安装启动器
├── MusicSplitter_Install.bat   # Windows 首次安装脚本
├── models/
│   ├── README.md
│   └── checkpoints/            # 213 MB .th 模型文件（不被 git 跟踪）
├── INSTALL.md                # 安装与使用指南
└── .gitignore
```

## 已完成

### 2026-08-08 路径修复与优化

- [x] 修复启动器路径错误：项目根现在等于脚本所在目录，不再错误地 `cd ..`。
- [x] 修复 `gui.py` 中 `INSTALL_SH` / `INSTALL_BAT` / `ANALYZE_SCRIPT` 路径常量。
- [x] 修复 `MusicSplitter_Install.command` / `.bat` 中模型 checkpoints 路径：`models/checkpoints`。
- [x] 更新 `INSTALL.md` 和 `models/README.md` 中所有旧路径引用。
- [x] 保持 Windows `.bat` 文件为 GBK 编码 + CRLF 换行，双击不乱码。
- [x] 初始化 git 仓库，添加 `.gitignore`：忽略 `.venv-demucs`、模型 `.th`、输出目录等。
- [x] 拆轨（4-stem 模式）成功后，自动把 `drums.wav` 路径填入 Analyze 页。
- [x] 新增 `_explain_error()` 中文排障提示：OOM/CUDA、模型下载、依赖缺失、segment 越界、Python 版本等。
- [x] 验证 `bash -n` 语法、`gui.py` import、GBK/CRLF 编码均通过。

### 2026-08-08 清理临时资源

- [x] 删除 `htdemucs/` 旧示例输出（~192 MB）。
- [x] 删除 `whiplash_audio.wav` 示例输入（~16 MB）。
- [x] 从 git 跟踪中移除 `whiplash_audio.wav`。
- [x] `.gitignore` 增加 `*.wav`，避免后续音频文件误提交。
- [x] 更新 `INSTALL.md` 中示例路径为通用占位符。

## 当前状态

| 项 | 状态 |
|---|---|
| 代码路径 | 已修复，git 干净 |
| 模型文件 | 已就位（3 个 `.th`） |
| `.venv-demucs` | **未安装**，首次使用需运行安装脚本 |
| 启动器 | 已适配扁平结构，可直接双击 |

## 待办（后续可选）

### 高优先级

- [ ] 运行 `MusicSplitter_Install.command` / `.bat` 创建 `.venv-demucs` 并验证 end-to-end。
- [ ] 真实跑一次 demucs 拆轨，验证自动填 `drums.wav` 和进度条解析。
- [ ] 测试错误提示：手动构造一个缺模型 / 坏依赖 / 越界 segment 的场景，看提示是否出现。

### 中优先级

- [ ] 安装逻辑统一：把 `.command` 和 `.bat` 的重复安装逻辑抽成一个 `install.py`。
- [ ] 状态检测从 `find_spec` 升级到至少一次真实 import，避免“显示绿色但运行失败”。
- [ ] 进度条解析支持 demucs 多种输出格式 fallback。

### 低优先级

- [ ] Analyze 页加 sensitivity 滑块（宽松/标准/紧凑）替代固定 75 分位阈值。
- [ ] 取消后重置进度条到 0。
- [ ] 将 `gui.py` 按 Tab 拆分为多个模块，方便后续扩展。
- [ ] 编写打包脚本，生成含模型 + 启动器的 zip 分发包。

## 常用命令

```bash
# 语法检查
bash -n MusicSplitter_GUI.command
bash -n MusicSplitter_Install.command
python3 -m py_compile gui.py
python3 -m py_compile drum_bands.py

# 测试 gui.py 导入（需要先 export 根路径）
cd /Users/bear/Documents/AI_Project/MusicSplitter_GUI
export MUSIC_SPLITTER_ROOT=$(pwd -P)
python3 -c "import gui"
```
