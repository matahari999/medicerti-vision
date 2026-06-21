@echo off
chcp 65001 >nul
echo.
echo =========================================
echo  Medicerti Vision - Launcher EXE Build
echo =========================================
echo.

:: Python 경로
set PYTHON=C:\Python311\python.exe

:: 의존성 확인
%PYTHON% -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [설치] PyInstaller 설치 중...
    %PYTHON% -m pip install pyinstaller --quiet
)

:: 이전 빌드 정리
if exist "build\launcher" rmdir /s /q "build\launcher"
if exist "dist\medicerti-launcher.exe" del /f /q "dist\medicerti-launcher.exe"

echo [빌드] launcher_gui.py → medicerti-launcher.exe

%PYTHON% -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name medicerti-launcher ^
    --icon brand\icon.ico ^
    --distpath dist ^
    --workpath build\launcher ^
    --specpath build\launcher ^
    launcher_gui.py

if errorlevel 1 (
    echo.
    echo [실패] 빌드 오류가 발생했습니다.
    pause
    exit /b 1
)

echo.
echo [완료] dist\medicerti-launcher.exe 생성됨
echo.

:: 파일 크기 확인
for %%F in ("dist\medicerti-launcher.exe") do (
    set SIZE=%%~zF
)
echo 파일 크기: %SIZE% bytes

echo.
echo 다음 단계: Inno Setup으로 installer\setup.iss 재빌드
pause
