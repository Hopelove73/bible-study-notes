@echo off
REM 以赛亚书全书续写 · 自动监督器
REM 用法： scripts\continue_isa.cmd
cd /d "%~dp0.."
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0continue_isa.ps1" %*
