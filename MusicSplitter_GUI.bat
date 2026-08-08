@echo off
rem Explorer 双击启动 GUI(Windows)。Mac 用 MusicSplitter_GUI.command
rem 不依赖 cwd,只依赖 .bat 自己的位置

set "GUI_DIR=%~dp0"
set "ROOT=%GUI_DIR%"

if not exist "%ROOT%.venv-demucs\Scripts\activate.bat" (
    echo.
    echo  [X] 还没安装。先在 PowerShell 跑一次:
    echo         %ROOT%MusicSplitter_Install.bat
    echo.
    pause
    exit /b 1
)

rem 把项目根显式告诉 Python(不用让 Python 用 __file__ 反推)
set "MUSIC_SPLITTER_ROOT=%ROOT%"

call "%ROOT%.venv-demucs\Scripts\activate.bat"

rem start "" 让 CMD 立刻关掉,pythonw 自己起 GUI(无 console 窗口)
start "" pythonw "%GUI_DIR%gui.py"

pause
