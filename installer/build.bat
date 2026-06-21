@echo off
chcp 65001 >nul
title medicerti-vision Installer Build

set PYTHON=C:\Users\sinab\AppData\Local\Programs\Python\Python311\python.exe
set ROOT=%~dp0..
set DASHBOARD=%ROOT%\dashboard_app

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

:: Check Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found (required for dashboard build)
    pause
    exit /b 1
)

:: Check PyInstaller
%PYTHON% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    %PYTHON% -m pip install pyinstaller --quiet
)

:: Install Python dependencies
echo [1/5] Installing Python dependencies...
%PYTHON% -m pip install -r "%ROOT%\requirements.txt" --quiet

:: Check ONNX model
echo [2/5] Checking pose model...
if not exist "%ROOT%\models\yolov8n-pose.onnx" (
    echo [INFO] Model not found. Attempting download...
    %PYTHON% -c "from src.detector.yolo_pose import YoloPoseEstimator; YoloPoseEstimator()._download_model()"
)

:: Build React dashboard
echo [3/5] Building React dashboard...
if exist "%DASHBOARD%\package.json" (
    cd /d "%DASHBOARD%"
    call npm install --silent
    call npm run build
    cd /d "%ROOT%"
) else (
    echo [WARN] dashboard_app not found, skipping dashboard build
)

:: Build executable
echo [4/5] Building executable with PyInstaller...
%PYTHON% -m PyInstaller "%ROOT%\installer\medicerti-vision.spec" --clean --noconfirm --distpath "%ROOT%\dist"

:: Verify build
if not exist "%ROOT%\dist\medicerti-vision.exe" (
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

:: Create launcher
echo [5/5] Creating launcher...
(
echo @echo off
echo chcp 65001 ^>nul
echo title medicerti-vision
echo echo ============================================
echo echo  medicerti-vision - Medical Edge Vision AI
echo echo ============================================
echo echo.
echo echo Starting server at http://localhost:8111
echo echo.
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
echo.
echo  dist\ contains:
dir "%ROOT%\dist" /B /A-D
echo.
pause
