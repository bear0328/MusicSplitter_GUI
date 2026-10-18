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

### 2026-08-08 GitHub 闭源仓库 + 模型 Release Asset

- [x] 创建 GitHub 私有仓库：`https://github.com/bear0328/MusicSplitter_GUI`
- [x] 配置 `http.proxy` / `https.proxy` / `http.version` / `http.postBuffer` 以通过本地代理 push。
- [x] 用 orphan branch 重新整理初始提交，避免历史里残留已删除的 16 MB 示例音频。
- [x] 推送代码到 GitHub 私有仓库。
- [x] 创建 Release `v0.1.0` 并上传 3 个模型 `.th` 文件作为 Asset。
- [x] 新增 `models/download_models.py`，支持从 Release 自动下载模型（读代理环境变量）。
- [x] 更新 `models/README.md` 说明模型获取方式。

### 2026-10-18 复查修复

- [x] 修复 `INSTALL.md` 残留旧项目名 `MusicGame_Demo`(标题 + §2.2.1/§2.2.2 的 `cd` 示例路径),改为 `MusicSplitter_GUI` 真实路径。
- [x] 修复 `MusicSplitter_GUI.bat` 末尾多余 `pause`:导致双击后 CMD 窗口不关闭,与自身注释及 `INSTALL.md` 的"CMD 闪一下关掉"矛盾。已删除(GBK + CRLF 保持)。
- [x] 修复 `MusicSplitter_Install.command` Python 检测逻辑:PATH 上的旧版 python3(如 3.9)不再短路常见路径扫描,版本不合格会继续找 `/Library/Frameworks` / Homebrew 下的合格版本。
- [x] `drum_bands.py --threshold` 改用 `non_negative_float` 校验,拒绝 nan/inf/负数(与 `--offset` 一致;GUI 侧原本已校验,CLI 直跑补齐)。
- [x] README 中英文切换:`README.md` 默认英文,顶部链接切到 `README_CN.md`(中文),两文件互相链接。
- [x] 沉淀技能 `~/.kimi-code/skills/musicsplitter-ops/SKILL.md`:启动器约定、模型分发、代理 push 绕过、README 双语、验证套路、已修坑清单。
- [x] 仓库转为 **public**(Release Asset 模型随之公开可下,demucs 权重本身公开分发,无敏感内容)。
- [x] 回归验证:`bash -n` ×2、`py_compile` ×3 通过;Python 检测新逻辑用假 python3(报 3.9)模拟验证可正确拒绝并落入 fallback。

## 当前状态

| 项 | 状态 |
|---|---|
| 代码 | 已推送到 GitHub **public** repo(2026-10-18 转公开) |
| 模型文件 | 作为 Release Asset 上传，不在 git 里 |
| `.venv-demucs` | **未安装** |

## GitHub 地址

- 仓库：`https://github.com/bear0328/MusicSplitter_GUI`（公开，2026-10-18 由私有转公开）
- Release：`https://github.com/bear0328/MusicSplitter_GUI/releases/tag/v0.1.0`
- 模型下载：
  ```bash
  cd /Users/bear/Documents/AI_Project/MusicSplitter_GUI
  python3 models/download_models.py
  ```

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
