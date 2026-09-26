@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHON_EXE=python"
"%PYTHON_EXE%" --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    )
)
start "" "%PYTHON_EXE%" main.py
