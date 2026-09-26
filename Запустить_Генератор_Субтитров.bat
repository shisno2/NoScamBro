@echo off
chcp 65001 >nul
title AI WordSync Subtitles — Генератор субтитров слово в слово

echo ========================================================
echo   🎯 AI WordSync Subtitles (Слово в слово)
echo ========================================================
echo Запуск приложения...

set "PYTHON_EXE=python"

:: Check if standard python command works
"%PYTHON_EXE%" --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else if exist "C:\Python311\python.exe" (
        set "PYTHON_EXE=C:\Python311\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else (
        echo [ОШИБКА] Python не найден! Убедитесь, что Python установлен.
        pause
        exit /b 1
    )
)

start "" "%PYTHON_EXE%" "%~dp0subtitles_app\main.py"
