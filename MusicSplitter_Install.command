#!/usr/bin/env bash
# Finder 双击:首次安装 + 启动 GUI(macOS)
#   0. (Apple Silicon Rosetta shell)自动 re-exec 走 arm64 —— 保证 pip 装到 arm64 wheel
#   1. 把 models/checkpoints/*.th 硬链进 ~/.cache/torch/hub/checkpoints/(免下载)
#   2. 找 Python 3.10+:先 PATH,再常见路径(Python.org / brew)
#   3. venv + 依赖;pip 用 --extra-index-url pypi.org 防国内镜像缺包
#   4. 验证
#   5. 问要不要启动 GUI

# === Apple Silicon Rosetta shell:auto re-exec 到 arm64 ===
if /usr/bin/uname -p | grep -q '^arm'; then
    if [[ "$(/usr/bin/uname -m)" == "x86_64" ]]; then
        exec /usr/bin/arch -arm64 /bin/bash "$0" "$@"
    fi
fi

cd "$(dirname "$0")"

MIN_MINOR=10

echo "==> [1/6] 把项目里带的模型塞进 torch hub cache(免下载)"

# 装包需要先有 demucs Python,但 demucs 第一次跑要先有模型。
# 我们在 models/checkpoints/ 给三个标准 .th 留位:
#   htdemucs:    955717e8-8726e21a.th
#   htdemucs_ft: f7e0c4bc-ba3fe64a.th
#   htdemucs_6s: 5c90dfd2-34c22ccb.th
# 装好后 demucs 走 HF_HUB_OFFLINE=1 回落到这些 .th,网络不通也能跑。

CACHE_DIR="$HOME/.cache/torch/hub/checkpoints"
SRC_DIR="models/checkpoints"
mkdir -p "$CACHE_DIR"

if compgen -G "$SRC_DIR/*.th" >/dev/null; then
    n=0
    for f in "$SRC_DIR"/*.th; do
        bn=$(basename "$f")
        # 已存在且 inode 一致 → 跳过;否则 rm 后硬链,避免重复占两份空间
        if [[ -f "$CACHE_DIR/$bn" ]] && \
           [[ "$(/usr/bin/stat -f '%i' "$f")" == "$(/usr/bin/stat -f '%i' "$CACHE_DIR/$bn")" ]]; then
            continue
        fi
        /bin/rm -f "$CACHE_DIR/$bn"
        /bin/ln "$f" "$CACHE_DIR/$bn"
        n=$((n+1))
    done
    if (( n > 0 )); then
        echo "    ✓ 硬链 $n 个模型到 $CACHE_DIR(后续删本目录仍保留)"
    else
        echo "    ✓ 模型已在 cache,跳过"
    fi
else
    echo "    ⚠️  $SRC_DIR 没找到 .th;首次跑 demucs 会走网络(HF xet,可能阻塞)"
fi

echo ""
echo "==> [2/6] 找 Python 3.10+"

PYTHON_BIN=""

# 1. PATH 里 python3(主流 PATH 一般在这)。必须版本合格才接受,
#    否则 PATH 上的 3.9 会短路后面的常见路径扫描(那里可能装着合格的 3.11)
if command -v python3 >/dev/null 2>&1; then
    candidate=$(command -v python3)
    # Apple 系统自带的 /usr/bin/python3 是 3.9.6,不够用,跳过
    if [[ "$candidate" != "/usr/bin/python3" ]]; then
        cand_minor=$("$candidate" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null)
        if [[ -n "$cand_minor" ]] && [[ "$cand_minor" -ge "$MIN_MINOR" ]]; then
            PYTHON_BIN="$candidate"
        else
            echo "    PATH 上的 python3 ($candidate) 版本不足 3.$MIN_MINOR,继续扫常见路径..."
        fi
    fi
fi

# 2. PATH 没有合格 python3,扫常见位置
if [[ -z "$PYTHON_BIN" ]]; then
    for cand in \
        /Library/Frameworks/Python.framework/Versions/3.1[0-9]/bin/python3 \
        /opt/homebrew/opt/python@3.1[0-9]/bin/python3 \
        /opt/homebrew/bin/python3 \
        /usr/local/bin/python3.1[0-9]
    do
        # glob 不展开,显式 ls 处理
        for f in $cand; do
            if [[ -x "$f" ]]; then
                fver=$("$f" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null) || continue
                if [[ "$fver" -ge "$MIN_MINOR" ]]; then
                    PYTHON_BIN="$f"
                    break 2
                fi
            fi
        done
    done
fi

# 3. 真的没找到 3.10+,弹浏览器
if [[ -z "$PYTHON_BIN" ]]; then
    echo "    没找到 Python 3.10+,打开下载页..."
    open "https://www.python.org/downloads/macos/"
    echo ""
    echo "    请下载 3.11+ .pkg 双击安装,装好后再回来按回车重试。"
    read -rp "    按回车重试..."
    PYTHON_BIN=$(command -v python3 2>/dev/null)
    [[ "$PYTHON_BIN" == "/usr/bin/python3" ]] && PYTHON_BIN=""
fi

# 4. 还是没有 — 真退出
if [[ -z "$PYTHON_BIN" ]]; then
    echo "    ❌ 仍未检测到合格 Python。手动装: https://www.python.org/downloads/"
    read -rp "    按回车关闭"
    exit 1
fi

PY_VERSION=$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
PY_MINOR=$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.minor)')
echo "    ✓ Python $PY_VERSION at $PYTHON_BIN"

if [[ "$PY_MINOR" -lt "$MIN_MINOR" ]]; then
    echo "    ❌ 当前是 $PY_VERSION,需要 3.$MIN_MINOR+。"
    read -rp "    按回车关闭"
    exit 1
fi

echo ""
echo "==> [3/6] 创建 venv"
if [[ ! -d .venv-demucs ]]; then
    "$PYTHON_BIN" -m venv .venv-demucs
    echo "    ✓ .venv-demucs 已创建"
else
    echo "    .venv-demucs 已存在,跳过"
fi

# shellcheck disable=SC1091
source .venv-demucs/bin/activate

# venv 用 arch 启动器那条线上的 python,但 venv python 是 universal2 copy。
# 在 arm64 shell 下(uname -m 已经是 arm64)直接 exec,不用再 arch 包装。

echo ""
echo "==> [4/6] 升级 pip + 装依赖"
# 用户 pip config 可能指国内镜像缺 torch arm64 wheel;用 --extra-index-url pypi.org 兜底
python -m pip install --upgrade pip --extra-index-url https://pypi.org/simple 2>&1 | tail -3
python -m pip install --extra-index-url https://pypi.org/simple torch torchaudio demucs scipy numpy soundfile librosa 2>&1 | tail -10

echo ""
echo "==> [5/6] 验证"
python -c "import torch, demucs, scipy, numpy, soundfile, librosa, tkinter; print('    ✓ 所有包可用')"

echo ""
echo "==> [6/6] 安装完成"
echo ""
echo "本机以后启动 GUI: Finder 双击 MusicSplitter_GUI.command"
echo ""
read -rp "现在启动 GUI? (回车 = 是,n = 否): " ans
case "$ans" in
    [Nn]|[Nn][Oo]) exit 0 ;;
    *) exec bash "$(dirname "$0")/MusicSplitter_GUI.command" ;;
esac
