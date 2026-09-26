@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%~dp0subtitles_app\main.py"
    exit /b 0
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%~dp0subtitles_app\main.py"
    exit /b 0
)
start "" python "%~dp0subtitles_app\main.py"
