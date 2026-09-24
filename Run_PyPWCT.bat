@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw PyPWCT.pyw %*
) else (
    start "" pyw PyPWCT.pyw %*
)
