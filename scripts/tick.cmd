@echo off
REM 心跳：几秒内退出，确保监督器在跑
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py "%~dp0tick.py" %*
) else (
  "C:\Users\admin\AppData\Local\Programs\Python\Python314\python.exe" "%~dp0tick.py" %*
)
