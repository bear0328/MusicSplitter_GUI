#!/usr/bin/env python3
"""从 GitHub Release 下载 bundled demucs checkpoints。

没有本地模型时（例如刚 clone 仓库），运行：
    python3 models/download_models.py

如果系统开了代理，脚本会读取 HTTP_PROXY / HTTPS_PROXY 环境变量。
"""
import os
import sys
import urllib.request
from pathlib import Path

CHECKPOINTS = [
    ("955717e8-8726e21a.th", "htdemucs (默认 4 轨)"),
    ("f7e0c4bc-ba3fe64a.th", "htdemucs_ft (fine-tuned 集合)"),
    ("5c90dfd2-34c22ccb.th", "htdemucs_6s (6 轨乐器)"),
]

RELEASE_URL = "https://github.com/bear0328/MusicSplitter_GUI/releases/download/v0.1.0"


def build_opener() -> urllib.request.OpenerDirector:
    """根据环境变量配置代理；没有则直接连接。"""
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") \
        or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if proxy:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        )
    return urllib.request.build_opener()


def download(url: str, dest: Path) -> None:
    opener = build_opener()
    req = urllib.request.Request(url, headers={"User-Agent": "MusicSplitter_GUI/0.1.0"})
    with opener.open(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  {pct}% ({downloaded // (1024*1024)}/{total // (1024*1024)} MB)", end="", flush=True)
        print()  # newline after progress


def main() -> int:
    out_dir = Path(__file__).parent.resolve() / "checkpoints"
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = [(name, desc) for name, desc in CHECKPOINTS if not (out_dir / name).exists()]
    if not missing:
        print("[i] 所有模型 checkpoint 已就位，无需下载。")
        return 0

    print(f"[i] 将从 GitHub Release 下载 {len(missing)} 个模型到 {out_dir}")
    for name, desc in missing:
        dest = out_dir / name
        url = f"{RELEASE_URL}/{name}"
        print(f"\n[↓] {name} ({desc})")
        try:
            download(url, dest)
            print(f"[OK] 已保存 {dest}")
        except Exception as e:
            print(f"\n[X] 下载失败: {e}", file=sys.stderr)
            if dest.exists():
                dest.unlink()
            return 1

    print("\n[OK] 全部模型下载完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
