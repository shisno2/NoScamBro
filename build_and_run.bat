@echo off
echo ========================================================
echo   Compiling GameDev Tycoon: Studio Master Pro (C++)
echo ========================================================
g++ -O3 main.cpp -o GameDevTycoonPro.exe -mwindows -lgdiplus -lgdi32 -lwinmm
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] GameDevTycoonPro.exe built successfully!
    echo Launching game...
    start "" GameDevTycoonPro.exe
) else (
    echo.
    echo [ERROR] Compilation failed!
)
pause
