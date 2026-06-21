@echo off
chcp 65001 >nul
title medicerti-vision Installer Build

echo ============================================
echo  medicerti-vision - Installer Build
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ first.
    pause
    exit /b 1
)

:: Check PyInstaller
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    python -m pip install pyinstaller --quiet
)

:: Install dependencies
echo [1/4] Installing dependencies...
python -m pip install -r requirements.txt --quiet

:: Build executable
echo [2/4] Building executable with PyInstaller...
python -m PyInstaller installer\medicerti-vision.spec --clean --noconfirm

:: Verify build
if not exist "dist\medicerti-vision.exe" (
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

:: Copy assets
echo [3/4] Copying assets...
if not exist "dist\src\dashboard" mkdir "dist\src\dashboard"
copy /Y "src\dashboard\index.html" "dist\src\dashboard\" >nul
copy /Y "version.json" "dist\" >nul

:: Create run script
echo [4/4] Creating launcher...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo Starting medicerti-vision...
echo start http://localhost:8111
echo "%%~dp0medicerti-vision.exe" --auto-scan --port 8111
echo pause
) > "dist\run_medicerti.bat"

echo.
echo ============================================
echo  BUILD COMPLETE
echo  Output: dist\medicerti-vision.exe
echo  Launcher: dist\run_medicerti.bat
echo ============================================
pause
