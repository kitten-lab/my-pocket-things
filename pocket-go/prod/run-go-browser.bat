@echo off
cd /d "%~dp0www_sys"
start "" http://127.0.0.1:43210/
python server.py
if errorlevel 1 pause
