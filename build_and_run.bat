@echo off
echo ======================================================================
echo   Compiling Standalone GameDev Tycoon: Studio Master Pro (C++ Native)
echo ======================================================================
echo Compiling with static linking (-static -static-libgcc -static-libstdc++)...
g++ -O3 -static -static-libgcc -static-libstdc++ main.cpp -o GameDevTycoonPro.exe -mwindows -lgdiplus -lgdi32 -lwinmm
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] GameDevTycoonPro.exe compiled successfully!
    echo Standalone executable created (no external MinGW DLLs required).
    echo Launching game...
    start "" GameDevTycoonPro.exe
) else (
    echo.
    echo [ERROR] Compilation failed!
)
pause
