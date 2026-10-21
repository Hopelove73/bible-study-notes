@echo off
REM 全圣经章节笔记 · 自动监督器
REM 用法： scripts\continue_all.cmd
cd /d "%~dp0.."
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0continue_all.ps1" %*
