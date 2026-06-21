@echo off
chcp 65001 >nul
title medicerti-vision Installer Build

set PYTHON=C:\Users\sinab\AppData\Local\Programs\Python\Python311\python.exe
set ROOT=%~dp0..

echo ============================================
echo  medicerti-vision - Installer Build
echo ============================================
echo.

:: Check Python
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found at %PYTHON%
    pause
    exit /b 1
)

:: Check PyInstaller
%PYTHON% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    %PYTHON% -m pip install pyinstaller --quiet
)

:: Install dependencies
echo [1/4] Installing dependencies...
%PYTHON% -m pip install -r "%ROOT%\requirements.txt" --quiet

:: Build executable
echo [2/4] Building executable with PyInstaller...
%PYTHON% -m PyInstaller "%ROOT%\installer\medicerti-vision.spec" --clean --noconfirm --distpath "%ROOT%\dist"

:: Verify build
if not exist "%ROOT%\dist\medicerti-vision.exe" (
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

:: Copy assets
echo [3/4] Copying assets...
if not exist "%ROOT%\dist\src\dashboard" mkdir "%ROOT%\dist\src\dashboard"
copy /Y "%ROOT%\src\dashboard\index.html" "%ROOT%\dist\src\dashboard\" >nul
copy /Y "%ROOT%\version.json" "%ROOT%\dist\" >nul

:: Create run script
echo [4/4] Creating launcher...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo Starting medicerti-vision...
echo start http://localhost:8111
echo "%%~dp0medicerti-vision.exe" --auto-scan --port 8111
echo pause
) > "%ROOT%\dist\run_medicerti.bat"

echo.
echo ============================================
echo  BUILD COMPLETE
echo  Output: dist\medicerti-vision.exe
echo  Launcher: dist\run_medicerti.bat
echo ============================================
pause
