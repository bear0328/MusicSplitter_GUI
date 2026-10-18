# MusicSplitter_GUI

English | **[中文](README_CN.md)**

A tkinter GUI front-end for [demucs](https://github.com/facebookresearch/demucs): point-and-click splitting of vocals / drums / bass / other, plus a frequency-band drum-piece approximation tool (kick/snare/hat/cymbal 16-step patterns).

## Features

- **Tab 1 Install**: environment status lights (venv / torch / demucs / scipy / numpy / soundfile / librosa) with the embedded one-shot install script
- **Tab 2 Separate**: pick audio → pick model (`htdemucs` / `htdemucs_ft` / `htdemucs_6s`) → split. Supports vocal-remover mode (`--two-stems vocals`), `--segment` / `--device` controls, live progress bar and cancellation; on success the `drums.wav` is auto-filled into the Analyze tab
- **Tab 3 Analyze**: backed by `drum_bands.py` — scipy bandpass splits the drum stem into kick/snare/hat/cymbal bands, printing 16-step patterns and writing per-piece wavs (**band approximation, not true drum separation**)

## Quick start

**Double-click (recommended)**:

| Platform | First-time install | Launch afterwards |
|---|---|---|
| macOS | `MusicSplitter_Install.command` | `MusicSplitter_GUI.command` |
| Windows | `MusicSplitter_Install.bat` | `MusicSplitter_GUI.bat` |

**Command line**:

```bash
bash MusicSplitter_Install.command        # venv + deps + models into torch hub cache
source .venv-demucs/bin/activate
export MUSIC_SPLITTER_ROOT="$PWD"         # required when running gui.py directly
python3 gui.py
```

Pure CLI separation & analysis:

```bash
demucs -n htdemucs --segment 7 -o separated input.wav
python3 drum_bands.py separated/htdemucs/input/drums.wav --bpm 125
```

Full install guide, model details and troubleshooting: [INSTALL.md](INSTALL.md) (Chinese).

## Models

The three demucs checkpoints (`htdemucs` / `htdemucs_ft` / `htdemucs_6s`, ~213 MB total) are **not in git** — they ship as assets of [Release v0.1.0](https://github.com/bear0328/MusicSplitter_GUI/releases/tag/v0.1.0):

```bash
python3 models/download_models.py   # honors HTTP_PROXY / HTTPS_PROXY
```

The install script hard-links (macOS) / copies (Windows) `models/checkpoints/*.th` into the torch hub cache, and the GUI forces `HF_HUB_OFFLINE=1`, so models never download over the network. See [models/README.md](models/README.md).

## Requirements

- Python 3.10+ (3.11 recommended; 3.13 verified on macOS)
- Dependencies: `torch` `demucs` `scipy` `numpy` `soundfile`; optional `librosa` (auto BPM estimation)
- Platforms: macOS (auto arm64 on Apple Silicon) / Windows / Linux

## Project layout

```
gui.py                        # tkinter GUI
drum_bands.py                 # band-pass drum analysis (CLI + GUI Tab 3 backend)
MusicSplitter_Install.*       # first-time installer (.command / .bat)
MusicSplitter_GUI.*           # launcher for installed setups
models/download_models.py     # fetch models from GitHub Release
INSTALL.md                    # full install/usage/troubleshooting doc (Chinese)
PROGRESS.md                   # development log (Chinese)
```

## License

No open-source license specified yet; code is provided as-is for reference. Model weights are Meta's demucs checkpoints, subject to their original license.
