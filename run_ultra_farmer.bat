@echo off
title GitHub Activity Farmer [ULTRA 24/7]
cd /d "%~dp0"
echo ========================================================
echo       GITHUB ACTIVITY FARMER 24/7 - ULTRA MODE
echo       Target: shisno2 (shisno21@gmail.com)
echo ========================================================
echo.
py activity_farmer.py --name "shisno2" --email "shisno21@gmail.com" daemon --interval-min 300 --interval-max 900 --batch-min 2 --batch-max 6
pause
