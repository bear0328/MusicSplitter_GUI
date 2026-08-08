#!/usr/bin/env bash
# Finder 双击:启动 GUI(macOS)
# Apple Silicon + Rosetta shell:自动 re-exec 到 arm64,venv 跑成 arm64

if /usr/bin/uname -p | grep -q '^arm'; then
    if [[ "$(/usr/bin/uname -m)" == "x86_64" ]]; then
        exec /usr/bin/arch -arm64 /bin/bash "$0" "$@"
    fi
fi

# 项目根 = 自己所在的父目录,显式告诉 Python(不用让它猜)
export MUSIC_SPLITTER_ROOT="$(cd "$(dirname "$0")" && pwd -P)"

if [[ ! -f "$MUSIC_SPLITTER_ROOT/.venv-demucs/bin/activate" ]]; then
    echo ""
    echo "❌ 还没安装。先双击 MusicSplitter_Install.command"
    echo ""
    read -rp "按回车关闭"
    exit 1
fi

cd "$MUSIC_SPLITTER_ROOT"

# shellcheck disable=SC1091
source .venv-demucs/bin/activate

exec python3 gui.py