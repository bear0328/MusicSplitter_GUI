"""频段带通鼓件近似分析 — gui.py Tab 3 的后端。

输入:drums.wav(由 demucs 拆出)
输出:
  - 控制台:每件每小节 16-step pattern
  - 写盘:drums.wav 同目录下 drum_pieces/{kick,snare,hat,cymbal}.wav(各 mono 16-bit)
          + normalization.txt(每件独立归一化的增益记录,还原相对电平用)

频段划分:
  kick:    30 - 200 Hz
  snare:  200 - 2000 Hz(含 kick 谐波泄漏)
  hat:   2000 - 8000 Hz
  cymbal: 8000 - 16000 Hz(跟 hat 重叠严重)

**这不是真鼓件分离**,只是频段带通产物,只能用于能量分布和 timing 对照。

CLI(直接调):
  python3 drum_bands.py drums.wav [--bpm 210 | --bpm auto] [--offset 0.0] [--threshold 0.01]

  --bpm auto(默认)用 librosa beat_track 估速,估不出来回退 125。
  --offset 开头跳过 N 秒再对 16-step 网格(第一拍不在 0s 时用)。
  --threshold 手动指定 RMS 阈值;不传 = 每 band 取 75 分位。

纯 stdlib 路径解析,不需要 MUSIC_SPLITTER_ROOT(输出永远写在 drums.wav 旁边)。
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

BANDS = [
    ("kick",   30,    200),
    ("snare",  200,   2000),
    ("hat",    2000,  8000),
    ("cymbal", 8000,  16000),
]
FALLBACK_BPM = 125.0
STEPS_PER_BAR = 16


def non_negative_float(value: str) -> float:
    """argparse type:只接受 >= 0 的有限浮点数,否则报清晰错误。"""
    try:
        f = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"不是数字: {value!r}")
    if not np.isfinite(f):
        raise argparse.ArgumentTypeError(f"必须是有限数字(nan/inf 不行): {value!r}")
    if f < 0:
        raise argparse.ArgumentTypeError(f"不能是负数: {value!r}")
    return f


def detect_bpm(sig: np.ndarray, sr: int) -> float | None:
    """librosa beat_track 估 BPM;librosa 不在 / 估不出来都返回 None。"""
    try:
        import librosa
    except Exception:
        return None
    try:
        tempo, _ = librosa.beat.beat_track(y=sig, sr=sr)
        bpm = float(np.asarray(tempo, dtype=float).ravel()[0])
        return bpm if bpm > 0 else None
    except Exception:
        return None


def bandpass(sig: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
    """零相位 bandpass(用 sos + filtfilt 避免相位偏)。"""
    nyq = sr / 2
    hi = min(hi, nyq - 1)
    if lo >= hi:
        # 整个频段超过奈奎斯特频率(低采样率输入),无法滤波,返回全零
        return np.zeros_like(sig)
    sos = signal.butter(4, [lo, hi], btype="bandpass", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, sig)


def per_step_rms(samples: np.ndarray, sr: int, steps: int, bpm: float) -> np.ndarray:
    """返回 RMS 数组。每个 step 时长 = 60 / bpm / 4 秒(16 分音符)。

    尾部不足一步的直接丢掉 —— 以前补零参与 percentile,会把阈值拉低。
    """
    step_sec = 60.0 / bpm / 4.0
    step_len = int(round(step_sec * sr))
    out = []
    for i in range(steps):
        a = i * step_len
        b = a + step_len
        if b > len(samples):
            break
        out.append(float(np.sqrt(np.mean(samples[a:b] ** 2))))
    return np.asarray(out)


def fmt_pattern(rms: np.ndarray, threshold: float) -> str:
    """RMS 数组 → 0/1 字符串(超过 threshold 视为有击)。"""
    return "".join("X" if v >= threshold else "." for v in rms)


def main() -> int:
    ap = argparse.ArgumentParser(description="频段带通鼓件近似分析(非真鼓件分离)")
    ap.add_argument("drums", type=Path, help="demucs 拆出的 drums.wav")
    ap.add_argument("--bpm", default="auto",
                    help="歌曲 BPM(数字),或 auto(默认,librosa 估速)")
    ap.add_argument("--offset", type=non_negative_float, default=0.0,
                    help="开头跳过 N 秒再对 16-step 网格(默认 0)")
    ap.add_argument("--threshold", type=non_negative_float, default=None,
                    help="RMS 阈值(不传 = 每 band 取 75 分位)")
    args = ap.parse_args()

    drums_path = args.drums.expanduser().resolve()
    if not drums_path.exists():
        print(f"[!] {drums_path} 不存在,先用 Tab 2 拆轨出 drums.wav", file=sys.stderr)
        return 1

    print(f"[i] 读 {drums_path}")
    sig, sr = sf.read(str(drums_path), always_2d=False)
    if sig.ndim > 1:
        sig = sig.mean(axis=1)   # 折叠到 mono
    sig = sig.astype(np.float32)

    # BPM:手动指定优先,否则 librosa 估
    if str(args.bpm).strip().lower() == "auto":
        bpm = detect_bpm(sig, sr)
        if bpm is None:
            bpm = FALLBACK_BPM
            print(f"[!] librosa 估速不可用/失败,回退 BPM={bpm:.0f}(用 --bpm 手动指定更准)")
        else:
            print(f"[i] librosa 估速 BPM ~ {bpm:.1f}(不准就 --bpm 手动指定)")
    else:
        try:
            bpm = float(args.bpm)
        except ValueError:
            print(f"[!] --bpm 看不懂: {args.bpm!r}(给数字或 auto)", file=sys.stderr)
            return 2
        if not 20 <= bpm <= 400:
            print(f"[!] --bpm {bpm:g} 超出合理范围 20-400", file=sys.stderr)
            return 2

    if args.offset > 0:
        sig = sig[int(args.offset * sr):]
        print(f"[i] offset {args.offset:g}s -> 从该处起算网格(写盘 wav 同步裁剪)")

    duration = len(sig) / sr
    n_steps = int(duration * bpm * 4 / 60)
    n_steps = (n_steps // STEPS_PER_BAR) * STEPS_PER_BAR  # 整小节
    if n_steps <= 0:
        print(f"[!] 音频太短({duration:.2f}s),一小节都排不下 (BPM={bpm:g})", file=sys.stderr)
        return 1
    print(f"[i] sr={sr}, dur={duration:.2f}s, {n_steps} 步 = {n_steps // STEPS_PER_BAR} 小节 (BPM={bpm:g})")

    out_dir = drums_path.parent / "drum_pieces"
    out_dir.mkdir(parents=True, exist_ok=True)
    # 重复运行会静默覆盖产物,先明确告知用户
    outputs = [out_dir / f"{name}.wav" for name, _, _ in BANDS] + [out_dir / "normalization.txt"]
    existing = [p.name for p in outputs if p.exists()]
    if existing:
        print(f"[!] Overwriting existing output files: {', '.join(existing)}")

    print("\n=== 频段 + pattern ===")

    norm_lines = []  # 每件独立归一化 → 音量不代表真实比例,记下增益供还原
    for name, lo, hi in BANDS:
        band = bandpass(sig, sr, lo, hi)
        # 写盘
        out_wav = out_dir / f"{name}.wav"
        # 归一化到不削顶
        peak = float(np.max(np.abs(band))) or 1.0
        band_norm = (band / peak * 0.95).astype(np.float32)
        sf.write(str(out_wav), band_norm, sr, subtype="PCM_16")
        norm_lines.append(f"{name:7s} {lo:5d}-{hi:<5d} Hz  peak={peak:.6f}  gain={0.95 / peak:.4f}")
        # pattern
        rms = per_step_rms(band, sr, n_steps, bpm)
        if rms.size == 0:
            print(f"\n[{name}] {lo}-{hi} Hz, 有效步数 0,跳过")
            continue
        if args.threshold is not None:
            thr = args.threshold
        else:
            thr = float(np.percentile(rms, 75)) or float(np.max(rms) * 0.3) or 1e-6
        pat = fmt_pattern(rms, thr)
        # 分行(每行 16 步)
        lines = [pat[i:i + STEPS_PER_BAR] for i in range(0, len(pat), STEPS_PER_BAR)]
        thr_src = "手动" if args.threshold is not None else "75 分位"
        print(f"\n[{name}] {lo}-{hi} Hz, RMS 阈值 = {thr:.4f} ({thr_src})")
        for bi, line in enumerate(lines):
            print(f"  bar {bi:2d}: {line}")

    (out_dir / "normalization.txt").write_text(
        "# 每件 wav 各自归一化(÷ peak × 0.95)→ 件与件之间音量不可直接比较\n"
        "# 还原原始相对电平:wav 幅值 ÷ gain(等价于 × peak ÷ 0.95)\n"
        + "\n".join(norm_lines) + "\n",
        encoding="utf-8",
    )

    print(f"\n[OK] 4 件 wav + normalization.txt 写到 {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
