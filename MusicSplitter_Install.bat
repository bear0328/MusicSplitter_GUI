@echo off
rem Explorer 双击:首次安装 + 启动 GUI(Windows)。Mac 用 MusicSplitter_Install.command
rem   1. 把 models\checkpoints\*.th 拷到 %LOCALAPPDATA%\torch\hub\checkpoints\(免下载)
rem   2. 检 Python;如缺,弹浏览器到 python.org,装好按任意键继续
rem   3. 创建 venv + 装依赖
rem   4. 验证
rem   5. 问要不要启动 GUI

setlocal EnableDelayedExpansion

cd /d "%~dp0"

set MIN_MINOR=10

echo ==^> [1/5] 把项目里带的模型拷进 torch hub cache(免下载)

rem Mac 用硬链共享 inode;Windows 没简单办法硬链(需管理员 mklink /H),直接 copy。
rem 213MB 临时多占一次,但靠网络下载失败时救得了命。
set "CACHE_DIR=%LOCALAPPDATA%\torch\hub\checkpoints"
set "SRC_DIR=models\checkpoints"
if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"

set "MODEL_COUNT=0"
if exist "%SRC_DIR%\*.th" (
    for %%f in ("%SRC_DIR%\*.th") do (
        if not exist "%CACHE_DIR%\%%~nxf" (
            copy /Y "%%f" "%CACHE_DIR%\" >nul
            set /a "MODEL_COUNT+=1"
        )
    )
    if !MODEL_COUNT! GTR 0 (
        echo     [OK] 拷贝 !MODEL_COUNT! 个模型到 %CACHE_DIR%
    ) else (
        echo     [OK] 模型已在 cache,跳过
    )
) else (
    echo     [!] %SRC_DIR% 没找到 *.th;首次跑 demucs 会走网络(HF xet,可能阻塞)
)

echo.
echo ==^> [2/5] Python 检测

rem 探测策略:py -3 启动器先(PATH 上的旧 python.exe 不影响),再退到 PATH 上的 python
rem 不再 call 子例程 — 子例程在 if (...) 块里调用会引起 cmd 解析报错
rem 全部用 !VAR! 延迟展开(setlocal EnableDelayedExpansion 已开)
set "PY_MINOR="
set "PY_BIN="

rem --- 尝试 1: py -3 启动器 ---
for /f "usebackq delims=" %%v in (`py -3 -c "import sys; print(sys.version_info.minor)" 2^>nul`) do set "PY_MINOR=%%v"
if not "!PY_MINOR!"=="" set "PY_BIN=py -3"

rem --- 尝试 2: PATH 上的 python(可能太老,无所谓,有先机)---
if "!PY_MINOR!"=="" (
    for /f "usebackq delims=" %%v in (`python -c "import sys; print(sys.version_info.minor)" 2^>nul`) do set "PY_MINOR=%%v"
    if not "!PY_MINOR!"=="" set "PY_BIN=python"
)

rem --- 两个都没找到:引导下载页,等用户装好后再重试 ---
if "!PY_MINOR!"=="" goto :py_missing

rem --- 找到但太老:打开下载页,让用户装 3.10+ 之后退出重跑 ---
if !PY_MINOR! LSS !MIN_MINOR! goto :py_too_old

echo     [OK] Python 3.!PY_MINOR!  via !PY_BIN!
goto :after_py

:py_missing
    echo     Python 未安装,正在打开下载页...
    start "" "https://www.python.org/downloads/windows/"
    echo.
    echo     请下载 Python 3.11 .exe 双击安装。
    echo     务必勾 "Add Python to PATH"(安装界面最下面那个复选框)。
    echo     装好后回来按任意键继续。
    echo.
    pause

    rem 重试:py -3 先
    for /f "usebackq delims=" %%v in (`py -3 -c "import sys; print(sys.version_info.minor)" 2^>nul`) do set "PY_MINOR=%%v"
    if not "!PY_MINOR!"=="" set "PY_BIN=py -3"

    rem 再试 PATH 的 python
    if "!PY_MINOR!"=="" (
        for /f "usebackq delims=" %%v in (`python -c "import sys; print(sys.version_info.minor)" 2^>nul`) do set "PY_MINOR=%%v"
        if not "!PY_MINOR!"=="" set "PY_BIN=python"
    )

    if "!PY_MINOR!"=="" (
        echo     [X] 仍未检测到 python,退出。
        pause
        exit /b 1
    )

    if !PY_MINOR! LSS !MIN_MINOR! goto :py_too_old
    echo     [OK] Python 3.!PY_MINOR!  via !PY_BIN!
    goto :after_py

:py_too_old
    echo     [X] 通过 !PY_BIN! 找到的 Python 是 3.!PY_MINOR!,demucs 需要 3.10+。
    echo     看上去这台机器只剩旧版 Python。
    echo.
    start "" "https://www.python.org/downloads/windows/"
    echo     已打开下载页:请下载 Python 3.11 .exe 双击安装,
    echo         务必勾 "Add Python to PATH"。装好后再双击本脚本。
    echo.
    pause
    exit /b 1

:after_py
echo.
echo ==^> [3/5] 创建 venv + 装依赖

if not exist .venv-demucs (
    !PY_BIN! -m venv .venv-demucs
    echo     [OK] .venv-demucs 已创建
) else (
    echo     .venv-demucs 已存在,跳过
)

call .venv-demucs\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install torch torchaudio demucs scipy numpy soundfile librosa
if errorlevel 1 (
    echo     [X] pip install 失败
    pause
    exit /b 1
)

echo.
echo ==^> [4/5] 验证
python -c "import torch, demucs, scipy, numpy, soundfile, librosa, tkinter; print('    [OK] 所有包可用')"

echo.
echo ==^> [5/5] 安装完成
echo.
echo 本机以后启动 GUI: Explorer 双击 MusicSplitter_GUI.bat
echo.
set /p "ANS=现在启动 GUI? (回车 = 是, n = 否): "
if /i "%ANS%"=="n" goto :end
if /i "%ANS%"=="no" goto :end

set "MUSIC_SPLITTER_ROOT=%~dp0" && start "" /D "%~dp0" pythonw gui.py

:end
exit /b 0

