@echo off
setlocal
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Novel Studio 실행 중 오류가 발생했습니다.
    pause
)
endlocal
