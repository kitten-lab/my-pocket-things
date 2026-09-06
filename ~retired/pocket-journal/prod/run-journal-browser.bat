@echo off
cd /d "%~dp0journal_sys"
start "" http://127.0.0.1:43166/
python server.py
if errorlevel 1 pause
