@echo off
REM 全圣经章节笔记 · 自动监督器（Python 版）
REM 用法： scripts\supervisor.cmd
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py "%~dp0supervisor.py" %*
) else (
  "C:\Users\admin\AppData\Local\Programs\Python\Python314\python.exe" "%~dp0supervisor.py" %*
)
