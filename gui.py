"""Music Splitter — tkinter 前端,封装拆轨 + 鼓件分析。

启动:双击启动器(macOS → MusicSplitter_GUI.command,Windows → MusicSplitter_GUI.bat)。
启动器会设 MUSIC_SPLITTER_ROOT 环境变量;命令行直跑要先手动 export,否则一启动就退出。
- tkinter 是 stdlib,无需 venv 激活
- subprocess 调 venv 里的 python 跑 demucs / drum_bands
"""

import math
import os
import platform
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# 项目根 = MUSIC_SPLITTER_ROOT 环境变量(由启动器 MusicSplitter_GUI.{command,bat} 设)。
# 不用 __file__ 反推:目录改名 / 移动 / 软链都会断,而且启动器和 Python 各推一遍容易不一致。
_ROOT = os.environ.get("MUSIC_SPLITTER_ROOT", "").strip()
if not _ROOT:
    # 双击 pythonw 没 console,stderr 看不到 → 尽量弹个框再退;tk 起不来(无显示环境)就走 stderr
    try:
        _r = tk.Tk()
        _r.withdraw()
        messagebox.showerror(
            "Music Splitter",
            "缺少 MUSIC_SPLITTER_ROOT 环境变量。\n\n"
            "请双击启动器启动:\n"
            "  macOS → MusicSplitter_GUI.command\n"
            "  Windows → MusicSplitter_GUI.bat",
        )
        _r.destroy()
    except Exception:
        pass
    sys.exit(
        "[!] 没设 MUSIC_SPLITTER_ROOT 环境变量,不知道项目根在哪。\n"
        "    正常用法:双击启动器(macOS → MusicSplitter_GUI.command,Windows → MusicSplitter_GUI.bat)。\n"
        "    命令行直跑:先 export MUSIC_SPLITTER_ROOT=/path/to/project(Win: set MUSIC_SPLITTER_ROOT=...)。"
    )
PROJECT_DIR = Path(_ROOT)
VENV_DIR = PROJECT_DIR / ".venv-demucs"
INSTALL_SH = PROJECT_DIR / "MusicSplitter_Install.command"
INSTALL_BAT = PROJECT_DIR / "MusicSplitter_Install.bat"
ANALYZE_SCRIPT = PROJECT_DIR / "drum_bands.py"

# 注意:htdemucs_6s 是乐器 6 件细分,不是鼓件细分(选了会有红字提示)
MODELS = ["htdemucs", "htdemucs_ft", "htdemucs_6s"]
DEVICES = ["auto", "cpu", "cuda", "mps"]
PROGRESS_RE = re.compile(r"(\d+)%\|")
# demucs 4.x 强制 --segment ≤ 7.8(训练窗口),Spinbox 和这里双保险卡 1-7
SEGMENT_MIN, SEGMENT_MAX = 1, 7
# Tab 1 状态灯清单(顺序即显示顺序)
STATUS_ITEMS = ["venv", "torch", "demucs", "scipy", "numpy", "soundfile", "librosa"]


def platform_label() -> str:
    p = platform.system().lower()
    if p == "darwin":
        return "macOS"
    if p == "windows":
        return "Windows"
    return "Linux"


def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_python_label() -> str:
    return "Scripts\\python.exe" if sys.platform == "win32" else "bin/python"


def read_install_script() -> str:
    """读平台对应的 install 启动器(.bat GBK / .command UTF-8 均可)。"""
    if platform_label() == "Windows":
        # .bat 实际存的是 GBK(中文 REM 在 cmd CP936 下才显示正常),以 GBK 读
        return INSTALL_BAT.read_text(encoding="gbk")
    return INSTALL_SH.read_text(encoding="utf-8")


def check_status() -> dict[str, bool]:
    """Return dict of {check_name: passed}."""
    py = venv_python()
    venv_ok = py.exists()
    checks = {"venv": venv_ok}
    if not venv_ok:
        for k in STATUS_ITEMS:
            checks[k] = False
        return checks
    # one-shot import test inside venv。
    # numpy/soundfile 真 import(快,且能抓到"装了但架构不对 import 就炸"的情况);
    # torch/demucs/scipy/librosa 只 find_spec(真 import 要好几秒,Tab 1 每次刷新都跑,不值)
    code = (
        "import importlib.util as u\n"
        "mods = {}\n"
        "for m in ('torch', 'demucs', 'scipy', 'librosa'):\n"
        "    mods[m] = u.find_spec(m) is not None\n"
        "for m in ('numpy', 'soundfile'):\n"
        "    try:\n"
        "        __import__(m); mods[m] = True\n"
        "    except Exception:\n"
        "        mods[m] = False\n"
        "print(','.join(f'{k}={v}' for k, v in mods.items()))\n"
    )
    try:
        out = subprocess.check_output([str(py), "-c", code],
                                      stderr=subprocess.DEVNULL,
                                      timeout=20).decode()
        for kv in out.strip().split(","):
            name, _, val = kv.partition("=")
            checks[name] = (val.strip() == "True")
    except Exception:
        # venv 状态是上面真实检测过的,别跟着打红;只把包检测标失败
        for k in STATUS_ITEMS:
            if k != "venv":
                checks[k] = False
    return checks


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Music Splitter")
        root.geometry("820x680")
        root.minsize(700, 520)

        self.log_queue: queue.Queue = queue.Queue()
        # Tab 2 / Tab 3 各跑各的(拆轨是长任务,分析是秒级,不该互相堵)
        self.sep_proc: subprocess.Popen | None = None
        self.ana_proc: subprocess.Popen | None = None
        self.sep_running = False
        self.ana_running = False
        # 用户主动取消的标记:进程被 terminate 后 rc=-15 也会推 __DONE__,
        # done 回调据此区分"已取消"和"真失败",避免日志自相矛盾
        self._sep_cancelled = False
        self._ana_cancelled = False
        self._last_dir: Path | None = None  # Browse 记住上次目录

        nb = ttk.Notebook(root)
        nb.pack(expand=True, fill="both", padx=8, pady=8)
        self.tab_install = ttk.Frame(nb)
        self.tab_separate = ttk.Frame(nb)
        self.tab_analyze = ttk.Frame(nb)
        nb.add(self.tab_install, text="1. Install")
        nb.add(self.tab_separate, text="2. Separate")
        nb.add(self.tab_analyze, text="3. Analyze")

        self._build_install_tab()
        self._build_separate_tab()
        self._build_analyze_tab()

        # 关窗前先杀子进程,不然 demucs 变孤儿还在烧 CPU/GPU
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 启动后排空日志队列
        self.root.after(100, self._drain_queue)

    # ---------- Tab 1: Install ----------
    def _build_install_tab(self) -> None:
        f = self.tab_install
        top = ttk.Frame(f)
        top.pack(fill="x", padx=8, pady=(8, 4))

        self.platform_var = tk.StringVar(value=f"Detected: {platform_label()} ({platform.machine()})")
        ttk.Label(top, textvariable=self.platform_var).pack(side="left")

        ttk.Button(top, text="Re-check", command=self._refresh_install_tab).pack(side="right")

        # 状态灯
        status_box = ttk.LabelFrame(f, text="Environment status")
        status_box.pack(fill="x", padx=8, pady=4)
        self.status_labels: dict[str, tuple[tk.Label, tk.Label]] = {}
        for i, name in enumerate(STATUS_ITEMS):
            row = ttk.Frame(status_box)
            row.grid(row=i // 3, column=i % 3, sticky="w", padx=8, pady=4)
            dot = tk.Label(row, text="●", fg="grey")
            dot.pack(side="left")
            txt = ttk.Label(row, text=name)
            txt.pack(side="left", padx=(2, 0))
            self.status_labels[name] = (dot, txt)

        # 脚本文本框
        script_frame = ttk.LabelFrame(f, text="One-shot install script")
        script_frame.pack(expand=True, fill="both", padx=8, pady=4)
        self.script_text = tk.Text(script_frame, wrap="none", font=("Menlo", 10),
                                   bg="#1e1e1e", fg="#d4d4d4", insertbackground="#d4d4d4")
        self.script_text.pack(expand=True, fill="both", padx=4, pady=4)

        btn_row = ttk.Frame(f)
        btn_row.pack(fill="x", padx=8, pady=(4, 8))
        ttk.Button(btn_row, text="Copy to clipboard", command=self._copy_script).pack(side="left", padx=2)
        ttk.Button(btn_row, text="How to install",
                   command=self._show_install_hint).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Re-detect",
                   command=self._refresh_install_tab).pack(side="right", padx=2)

        self._refresh_install_tab()

    def _refresh_install_tab(self) -> None:
        self.platform_var.set(f"Detected: {platform_label()} ({platform.machine()})")
        try:
            self.script_text.configure(state="normal")
            self.script_text.delete("1.0", "end")
            self.script_text.insert("1.0", read_install_script())
            self.script_text.configure(state="disabled")
        except Exception as e:
            self.script_text.configure(state="normal")
            self.script_text.delete("1.0", "end")
            self.script_text.insert("1.0", f"(could not read install script: {e})")
            self.script_text.configure(state="disabled")

        # 异步检测状态(避免阻塞 UI)
        threading.Thread(target=self._refresh_status, daemon=True).start()

    def _refresh_status(self) -> None:
        # 后台线程跑 subprocess,通过 log_queue 把结果推回主线程
        def _check():
            status = check_status()
            self.log_queue.put(("__STATUS__", status))
        threading.Thread(target=_check, daemon=True).start()

    def _copy_script(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self.script_text.get("1.0", "end-1c"))
        self._toast("Copied.")

    def _show_install_hint(self) -> None:
        # 已经不需要跑 install.sh/.ps1 了,直接双击启动器即可
        if platform_label() == "Windows":
            hint = (f"Explorer 里双击:\n\n"
                    f"  {INSTALL_BAT.name}  (首次安装)\n"
                    f"  MusicSplitter_GUI.bat  (已装完启动 GUI)\n\n"
                    f"注意:要回到项目根目录。")
        else:
            hint = (f"Finder 里双击:\n\n"
                    f"  {INSTALL_SH.name}  (首次安装)\n"
                    f"  MusicSplitter_GUI.command  (已装完启动 GUI)\n\n"
                    f"注意:要回到项目根目录。")
        messagebox.showinfo("Install", hint)

    # ---------- Tab 2: Separate ----------
    def _build_separate_tab(self) -> None:
        f = self.tab_separate
        pad = {"padx": 8, "pady": 4}

        # 输入
        ttk.Label(f, text="Input audio:").grid(row=0, column=0, sticky="w", **pad)
        self.input_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.input_var).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(f, text="Browse…",
                   command=lambda: self._pick_file(self.input_var, "Audio files",
                                                   [("Audio", "*.wav *.mp3 *.flac"),
                                                    ("All", "*.*")])
                   ).grid(row=0, column=2, **pad)

        # 输出
        ttk.Label(f, text="Output dir:").grid(row=1, column=0, sticky="w", **pad)
        self.output_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(f, text="Browse…",
                   command=lambda: self._pick_dir(self.output_var)
                   ).grid(row=1, column=2, **pad)

        # 模型
        ttk.Label(f, text="Model:").grid(row=2, column=0, sticky="w", **pad)
        self.model_var = tk.StringVar(value=MODELS[0])
        model_combo = ttk.Combobox(f, textvariable=self.model_var, state="readonly",
                                   values=MODELS)
        model_combo.grid(row=2, column=1, sticky="ew", **pad)
        model_combo.bind("<<ComboboxSelected>>", self._on_model_change)
        self.model_warn = ttk.Label(f, text="", foreground="#ef4444")
        self.model_warn.grid(row=2, column=2, sticky="w", **pad)

        # 只去人声开关(走 demucs --two-stems vocals)
        # 单独占一行 —— 跟 model_warn 同行会因为 grid cell 冲突互相覆盖
        self.vocal_remover_var = tk.BooleanVar(value=False)
        vocal_row = ttk.Frame(f)
        vocal_row.grid(row=3, column=0, columnspan=3, sticky="ew", **pad)
        self.vocal_remover_chk = ttk.Checkbutton(
            vocal_row, text="只去人声 (--two-stems vocals)  ",
            variable=self.vocal_remover_var, command=self._on_vocal_remover_change,
        )
        self.vocal_remover_chk.pack(side="left")
        self.vocal_info = ttk.Label(vocal_row, text="", foreground="#10b981")
        self.vocal_info.pack(side="left", padx=8)

        # 参数。demucs 4.x 强制 ≤7.8(训练窗口),传大立刻报错
        ttk.Label(f, text="--segment:").grid(row=4, column=0, sticky="w", **pad)
        self.segment_var = tk.IntVar(value=7)
        ttk.Spinbox(f, from_=SEGMENT_MIN, to=SEGMENT_MAX, textvariable=self.segment_var,
                    width=8).grid(row=4, column=1, sticky="w", **pad)

        ttk.Label(f, text="--device:").grid(row=5, column=0, sticky="w", **pad)
        self.device_var = tk.StringVar(value="auto")
        ttk.Combobox(f, textvariable=self.device_var, state="readonly",
                     values=DEVICES).grid(row=5, column=1, sticky="w", **pad)

        f.columnconfigure(1, weight=1)

        # Run + Cancel + 进度
        run_row = ttk.Frame(f)
        run_row.grid(row=6, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
        self.run_btn = ttk.Button(run_row, text="Run demucs", command=self._run_separate)
        self.run_btn.pack(side="left")
        self.sep_cancel_btn = ttk.Button(run_row, text="Cancel",
                                         command=self._cancel_separate, state="disabled")
        self.sep_cancel_btn.pack(side="left", padx=(6, 0))
        self.progress = ttk.Progressbar(run_row, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True, padx=8)

        # 日志
        log_frame = ttk.LabelFrame(f, text="Log")
        log_frame.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=8, pady=4)
        f.rowconfigure(7, weight=1)
        self.sep_log = tk.Text(log_frame, wrap="word", font=("Menlo", 10), height=12,
                               bg="#1e1e1e", fg="#d4d4d4", state="disabled")
        self.sep_log.pack(expand=True, fill="both", padx=4, pady=4)

        self._on_model_change()

    def _on_model_change(self, *_args) -> None:
        if "6s" in self.model_var.get():
            self.model_warn.configure(text="⚠ 乐器 6 件,不是鼓件细分")
        else:
            self.model_warn.configure(text="")

    def _on_vocal_remover_change(self) -> None:
        # 只去人声生效时,锁定模型 htdemucs(htdemucs_ft 也支持 two-stems,但更慢)
        if self.vocal_remover_var.get():
            self.vocal_info.configure(
                text="输出: vocals.wav + no_vocals.wav(伴奏)"
            )
            # htdemucs / htdemucs_ft 都行,但 htdemucs_ft 是 4 模型 bag,慢 4 倍
            if self.model_var.get() != "htdemucs":
                self.model_var.set("htdemucs")
        else:
            self.vocal_info.configure(text="")

    def _pick_file(self, var: tk.StringVar, title: str, filetypes: list[tuple[str, str]]) -> None:
        kwargs: dict = {"title": title, "filetypes": filetypes}
        if self._last_dir:
            kwargs["initialdir"] = str(self._last_dir)
        p = filedialog.askopenfilename(**kwargs)
        if p:
            var.set(p)
            self._last_dir = Path(p).parent

    def _pick_dir(self, var: tk.StringVar) -> None:
        kwargs: dict = {}
        if self._last_dir:
            kwargs["initialdir"] = str(self._last_dir)
        d = filedialog.askdirectory(**kwargs)
        if d:
            var.set(d)
            self._last_dir = Path(d)

    def _run_separate(self) -> None:
        if self.sep_running:
            return
        inp = self.input_var.get().strip()
        if not inp or not Path(inp).exists():
            messagebox.showerror("Missing input", "Pick an input audio file first.")
            return
        out_dir = self.output_var.get().strip()
        if not out_dir:
            # 留空会把 `-o ""` 传给 demucs = 产物静默写到项目根,非开发者根本找不到
            messagebox.showerror("Missing output", "Pick an output dir first.\n(留空的话产物会写到项目根目录,不好找。)")
            return
        if not venv_python().exists():
            messagebox.showerror("Venv missing", "Run the install script first (Tab 1).")
            return

        try:
            seg = self.segment_var.get()
        except tk.TclError:
            # Spinbox 允许手输非整数,IntVar.get() 会抛 TclError
            messagebox.showerror("Invalid segment",
                                 f"Segment must be an integer ({SEGMENT_MIN}-{SEGMENT_MAX}).")
            return
        seg = max(SEGMENT_MIN, min(SEGMENT_MAX, seg))
        cmd = [str(venv_python()), "-m", "demucs",
               "-n", self.model_var.get(),
               "--segment", str(seg),
               "-o", out_dir]
        if self.vocal_remover_var.get():
            cmd += ["--two-stems", "vocals"]
        if self.device_var.get() != "auto":
            cmd += ["-d", self.device_var.get()]
        cmd.append(inp)

        self._clear_log(self.sep_log)
        self.progress["value"] = 0
        self._append_log(self.sep_log, f"$ {' '.join(cmd)}\n")
        self._set_sep_running(True)
        threading.Thread(target=self._run_proc,
                         args=(cmd, self.sep_log, self._on_separate_done, "sep_proc"),
                         daemon=True).start()

    def _cancel_separate(self) -> None:
        self._cancel_proc("sep_proc", self.sep_log)

    def _on_separate_done(self, returncode: int) -> None:
        self._set_sep_running(False)
        if self._sep_cancelled:
            # 用户主动取消(terminate 的 rc=-15 不算失败);取消日志 _cancel_proc 已写
            self._sep_cancelled = False
            return
        if returncode == 0:
            inp = Path(self.input_var.get())
            if self.vocal_remover_var.get():
                # vocals/no_vocals 模式,没有 drums.wav
                self._append_log(
                    self.sep_log,
                    f"\n✓ Done. 产物: {self.output_var.get()}/{self.model_var.get()}/{inp.stem}/"
                    f"{{vocals,no_vocals}}.wav\n",
                )
            else:
                # 4-stem 模式:自动把 drums.wav 填到 Analyze tab
                drums_auto = Path(self.output_var.get()) / self.model_var.get() / inp.stem / "drums.wav"
                if drums_auto.exists():
                    self.analyze_input_var.set(str(drums_auto))
                    self._toast(f"已自动把 drums.wav 填到 Analyze 页")
                self._append_log(
                    self.sep_log,
                    f"\n✓ Done. 产物: {self.output_var.get()}/{self.model_var.get()}/{inp.stem}/"
                    f"{{vocals,drums,bass,other}}.wav\n",
                )
        else:
            log_text = self.sep_log.get("1.0", "end")
            hint = self._explain_error(log_text, "拆轨")
            self._append_log(self.sep_log, f"\n✗ Failed (exit {returncode}).{hint}\n")

    # ---------- Tab 3: Analyze ----------
    def _build_analyze_tab(self) -> None:
        f = self.tab_analyze
        pad = {"padx": 8, "pady": 4}

        ttk.Label(f, text="drums.wav path:").grid(row=0, column=0, sticky="w", **pad)
        self.analyze_input_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.analyze_input_var).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(f, text="Browse…",
                   command=lambda: self._pick_file(self.analyze_input_var, "drums.wav",
                                                   [("WAV", "*.wav")])
                   ).grid(row=0, column=2, **pad)

        # 参数行:BPM / offset / threshold(都可走默认)
        param_row = ttk.Frame(f)
        param_row.grid(row=1, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(param_row, text="BPM:").pack(side="left")
        self.bpm_var = tk.StringVar(value="auto")
        ttk.Entry(param_row, textvariable=self.bpm_var, width=7).pack(side="left", padx=(2, 10))
        ttk.Label(param_row, text="offset (s):").pack(side="left")
        self.offset_var = tk.StringVar(value="0")
        ttk.Entry(param_row, textvariable=self.offset_var, width=6).pack(side="left", padx=(2, 10))
        ttk.Label(param_row, text="threshold:").pack(side="left")
        self.threshold_var = tk.StringVar(value="")
        ttk.Entry(param_row, textvariable=self.threshold_var, width=8).pack(side="left", padx=(2, 4))
        ttk.Label(param_row, text="(空 = 自动)", foreground="#888888").pack(side="left")

        run_row = ttk.Frame(f)
        run_row.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
        self.analyze_btn = ttk.Button(run_row, text="Run drum_bands.py",
                                      command=self._run_analyze)
        self.analyze_btn.pack(side="left")
        self.ana_cancel_btn = ttk.Button(run_row, text="Cancel",
                                         command=self._cancel_analyze, state="disabled")
        self.ana_cancel_btn.pack(side="left", padx=(6, 0))
        ttk.Button(run_row, text="Open output folder",
                   command=self._open_drum_pieces).pack(side="left", padx=8)

        log_frame = ttk.LabelFrame(f, text="Log")
        log_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=8, pady=4)
        f.rowconfigure(3, weight=1)
        f.columnconfigure(1, weight=1)
        self.ana_log = tk.Text(log_frame, wrap="word", font=("Menlo", 10), height=12,
                               bg="#1e1e1e", fg="#d4d4d4", state="disabled")
        self.ana_log.pack(expand=True, fill="both", padx=4, pady=4)

    def _run_analyze(self) -> None:
        if self.ana_running:
            return
        if not venv_python().exists():
            messagebox.showerror("Venv missing", "Run the install script first (Tab 1).")
            return
        # 字段里的 drums.wav 路径作为脚本的 argv[1]
        drums_arg = self.analyze_input_var.get().strip()
        if not drums_arg:
            messagebox.showerror("No drums.wav", "Pick a drums.wav path (or run Tab 2 first).")
            return
        drums_p = Path(drums_arg)
        if not drums_p.exists():
            messagebox.showerror("File missing", f"{drums_p}\n不存在。先跑 Tab 2 出 drums.wav,或用 Browse 选。")
            return

        # 参数校验:BPM 数字或 auto;offset / threshold 数字(threshold 可空)
        bpm = self.bpm_var.get().strip() or "auto"
        if bpm.lower() != "auto":
            try:
                bpm_f = float(bpm)
            except ValueError:
                messagebox.showerror("Bad BPM", f"BPM 给数字或 auto,当前: {bpm!r}")
                return
            if not math.isfinite(bpm_f):
                messagebox.showerror("Bad BPM", f"BPM 必须是有限数字(nan/inf 不行),当前: {bpm!r}")
                return
        offset = self.offset_var.get().strip() or "0"
        thr = self.threshold_var.get().strip()
        for label, val in (("offset", offset), ("threshold", thr)):
            if val:
                try:
                    val_f = float(val)
                except ValueError:
                    messagebox.showerror("Bad param", f"{label} 给数字,当前: {val!r}")
                    return
                if not math.isfinite(val_f):
                    messagebox.showerror("Bad param", f"{label} 必须是有限数字(nan/inf 不行),当前: {val!r}")
                    return

        cmd = [str(venv_python()), str(ANALYZE_SCRIPT), str(drums_p),
               "--bpm", bpm, "--offset", offset]
        if thr:
            cmd += ["--threshold", thr]
        self._clear_log(self.ana_log)
        self._append_log(self.ana_log, f"$ {' '.join(cmd)}\n")
        self._set_ana_running(True)
        threading.Thread(target=self._run_proc,
                         args=(cmd, self.ana_log, self._on_analyze_done, "ana_proc"),
                         daemon=True).start()

    def _cancel_analyze(self) -> None:
        self._cancel_proc("ana_proc", self.ana_log)

    def _on_analyze_done(self, returncode: int) -> None:
        self._set_ana_running(False)
        if self._ana_cancelled:
            self._ana_cancelled = False
            return
        if returncode == 0:
            inp = Path(self.analyze_input_var.get())
            pieces = inp.parent / "drum_pieces"
            self._append_log(self.ana_log, f"\n✓ Done. Output: {pieces}\n")
        else:
            log_text = self.ana_log.get("1.0", "end")
            hint = self._explain_error(log_text, "分析")
            self._append_log(self.ana_log, f"\n✗ Failed (exit {returncode}).{hint}\n")

    def _explain_error(self, log_text: str, phase: str = "") -> str:
        """根据日志关键词给出中文排障提示。"""
        text = log_text.lower()
        hints = []
        if any(k in text for k in ("out of memory", "oom")) or ("cuda" in text and "memory" in text):
            hints.append("• 显存/内存不足：尝试把 --device 改为 cpu，或把 --segment 调小（1-4）。")
        if any(k in text for k in ("403", "xet", "huggingface", "unable to connect", "connection")):
            hints.append("• 模型下载/网络问题：先运行 Tab 1 安装，确保 models/checkpoints/*.th 已就位。")
        if "no module named" in text:
            hints.append("• 依赖缺失：回到 Tab 1 重新运行安装脚本。")
        if "segment" in text and any(k in text for k in ("window", "training", "between", "valid")):
            hints.append("• --segment 参数越界：demucs 训练窗口 ≤ 7.8，请用 1-7 的整数。")
        if any(k in text for k in ("requires python", "python 3.9", "unsupported python", "version")):
            hints.append("• Python 版本问题：需要 Python 3.10+，建议 3.11。")
        if not hints:
            return ""
        prefix = f"{phase}失败，" if phase else ""
        return f"\n{prefix}可能原因：\n" + "\n".join(hints)

    def _open_drum_pieces(self) -> None:
        inp = self.analyze_input_var.get().strip()
        if not inp:
            messagebox.showerror("No drums.wav", "先填 drums.wav 路径,才知道去哪开 drum_pieces。")
            return
        target = Path(inp).parent / "drum_pieces"
        if not target.exists():
            messagebox.showinfo("Not yet", f"{target}\n还不存在 —— 先 Run 一次分析。")
            return
        if platform_label() == "Windows":
            os.startfile(target)  # type: ignore[attr-defined]
        elif platform_label() == "macOS":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])

    # ---------- 共享:日志 + 进程 ----------
    def _run_proc(self, cmd: list[str], log_widget: tk.Text, on_done, proc_attr: str) -> None:
        """在后台线程跑 subprocess,逐行推日志到 queue。proc_attr = self 上放 Popen 的属性名。"""
        # demucs 4.x 默认走 HuggingFace Hub + hf_xet;xet 网络差时会卡 403 重试循环。
        # 走 HF_HUB_OFFLINE=1 让它落到 cache(legacy .th 在 torch hub 里),demucs 内部
        # 自动 fallback 到 AWS;如果 cache 没命中再让用户手动控制。
        env = None
        if "-m" in cmd and "demucs" in cmd:
            env = {**os.environ, "HF_HUB_OFFLINE": "1"}
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=str(PROJECT_DIR), bufsize=1, text=True, env=env,
            )
            setattr(self, proc_attr, proc)
            for line in proc.stdout:  # type: ignore[union-attr]
                self.log_queue.put((log_widget, line))
            proc.wait()
            rc = proc.returncode
        except FileNotFoundError as e:
            self.log_queue.put((log_widget, f"\n✗ Cannot start: {e}\n"))
            rc = -1
        except Exception as e:
            self.log_queue.put((log_widget, f"\n✗ Error: {e}\n"))
            rc = -1
        finally:
            setattr(self, proc_attr, None)
        self.log_queue.put(("__DONE__", log_widget, on_done, rc))

    def _cancel_proc(self, proc_attr: str, log_widget: tk.Text) -> None:
        proc = getattr(self, proc_attr)
        if proc and proc.poll() is None:
            # 先立标记,done 回调看到它就不再按 rc=-15 报失败
            if proc_attr == "sep_proc":
                self._sep_cancelled = True
            elif proc_attr == "ana_proc":
                self._ana_cancelled = True
            proc.terminate()  # Win: TerminateProcess;Mac/Linux: SIGTERM
            self._append_log(log_widget, "\n[x] 已取消(用户手动停止)\n")
            # torch/demucs 可能几秒后才响应 SIGTERM,兜底 kill
            threading.Thread(target=self._kill_if_alive, args=(proc,), daemon=True).start()

    @staticmethod
    def _kill_if_alive(proc: subprocess.Popen) -> None:
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _on_close(self) -> None:
        running = []
        if self.sep_running:
            running.append("拆轨")
        if self.ana_running:
            running.append("分析")
        if running:
            if not messagebox.askyesno(
                "Quit", f"{' 和 '.join(running)}还在跑,退出会终止任务。确定退出?"
            ):
                return
        for proc in (self.sep_proc, self.ana_proc):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        self.root.destroy()

    def _drain_queue(self) -> None:
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple) and len(item) == 4 and item[0] == "__DONE__":
                    _, log_widget, on_done, rc = item
                    on_done(rc)
                elif isinstance(item, tuple) and len(item) == 2 and item[0] == "__STATUS__":
                    _, status = item
                    for name, (dot_lbl, _) in self.status_labels.items():
                        ok = bool(status.get(name, False))
                        dot_lbl.configure(fg="#22c55e" if ok else "#ef4444")
                else:
                    log_widget, line = item  # type: ignore[misc]
                    self._append_log(log_widget, line)
                    # 只有 Tab 2 的日志才驱动进度条(Tab 3 输出里混有 % 也不该动它)
                    if log_widget is self.sep_log:
                        m = PROGRESS_RE.search(line)
                        if m:
                            try:
                                pct = max(0, min(100, int(m.group(1))))
                                self.progress["value"] = pct
                            except Exception:
                                pass
        except queue.Empty:
            pass
        finally:
            # 放在 finally:循环体内任何异常都不能让日志泵停摆
            self.root.after(100, self._drain_queue)

    def _append_log(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    def _clear_log(self, widget: tk.Text) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.configure(state="disabled")

    def _set_sep_running(self, running: bool) -> None:
        self.sep_running = running
        if running:
            self.run_btn.configure(state="disabled", text="Running…")
            self.sep_cancel_btn.configure(state="normal")
        else:
            self.run_btn.configure(state="normal", text="Run demucs")
            self.sep_cancel_btn.configure(state="disabled")

    def _set_ana_running(self, running: bool) -> None:
        self.ana_running = running
        if running:
            self.analyze_btn.configure(state="disabled", text="Running…")
            self.ana_cancel_btn.configure(state="normal")
        else:
            self.analyze_btn.configure(state="normal", text="Run drum_bands.py")
            self.ana_cancel_btn.configure(state="disabled")

    def _toast(self, msg: str) -> None:
        # 简单 "toast"—— 在状态栏显示 2s
        if not hasattr(self, "_toast_var"):
            self._toast_var = tk.StringVar()
            bar = ttk.Label(self.root, textvariable=self._toast_var, relief="sunken", anchor="w")
            bar.pack(fill="x", side="bottom")
        self._toast_var.set(msg)
        self.root.after(2500, lambda: self._toast_var.set(""))


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
