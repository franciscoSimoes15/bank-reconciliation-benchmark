@echo off
set ROOT=%~dp0..
python "%ROOT%\start_here.py"
if errorlevel 1 exit /b %errorlevel%
