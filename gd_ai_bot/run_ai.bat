@echo off
title Geometry Dash Vision AI Bot
chcp 65001 >nul
echo ========================================================
echo   Geometry Dash Real-Time Vision AI Bot v2.0
echo   Запуск ИИ автопилота для Geometry Dash...
echo ========================================================
cd /d "%~dp0"
"C:\Users\shisn\AppData\Local\Programs\Python\Python311\python.exe" main.py
if errorlevel 1 (
    echo.
    echo Ошибка при запуске. Нажмите любую клавишу для выхода...
    pause >nul
)
