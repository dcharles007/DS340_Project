@echo off
cd /d "%~dp0"
python src\project.py demo --out results\my_demo
if errorlevel 1 goto done
python src\project.py charts --experiment results\my_demo
:done
pause
