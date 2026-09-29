@echo off
title Geometry Dash Vision AI Bot
chcp 65001 >nul
cd /d "%~dp0gd_ai_bot"
"C:\Users\shisn\AppData\Local\Programs\Python\Python311\python.exe" main.py
if errorlevel 1 (
    pause
)
