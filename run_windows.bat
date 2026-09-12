@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo [Novel Studio] .venv가 없습니다.
    echo 먼저 다음 명령으로 설치하세요:
    echo py -3 -m venv .venv
    echo .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)
.venv\Scripts\python.exe main.py
if errorlevel 1 pause
