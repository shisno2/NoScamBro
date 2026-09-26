@echo off
chcp 65001 >nul
echo ======================================================================
echo   Compiling Standalone GameDev Tycoon: Studio Master Pro (C++ Native)
echo ======================================================================

set "MSVC_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if exist "%MSVC_VCVARS%" (
    echo Initializing MSVC Environment...
    call "%MSVC_VCVARS%" >nul 2>&1
    echo Compiling with MSVC (cl.exe)...
    cl.exe /O2 /std:c++17 /EHsc /DUNICODE /D_UNICODE main.cpp /Fe:GameDevTycoonPro.exe /link gdiplus.lib gdi32.lib winmm.lib user32.lib /SUBSYSTEM:WINDOWS
) else (
    echo Compiling with G++...
    g++ -O3 -static -static-libgcc -static-libstdc++ main.cpp -o GameDevTycoonPro.exe -mwindows -lgdiplus -lgdi32 -lwinmm
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] GameDevTycoonPro.exe compiled successfully!
    echo Standalone executable created.
    echo Launching game...
    start "" GameDevTycoonPro.exe
) else (
    echo.
    echo [ERROR] Compilation failed!
)
pause
