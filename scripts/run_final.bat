@echo off
set ROOT=%~dp0..
python "%ROOT%\scripts\run_final.py"
if errorlevel 1 exit /b %errorlevel%
