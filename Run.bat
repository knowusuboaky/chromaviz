@echo off

REM Change directory to the same directory as the Script
cd "%~dp0"

REM Extract the drive letter from the current directory
set driveLetter=%~d0

REM Change to the extracted drive letter if it's not C:
if /i not "%driveLetter%"=="C:" (
    cd /d %driveLetter%
)


:: Activate the virtual environment (without changing the system environment)
call "%~dp0venv\Scripts\activate.bat"


cls


echo ==========================================
echo Activating Python 3.10 Virtual Environment
echo Launching Chroma Flow Studio 
echo ==========================================
start "%~dp0venv\Scripts\python.exe" app.py
echo.
echo.


echo ###########################
echo This window can be closed
echo    (auto closes anyway)
echo ###########################
echo.

echo Closing THIS window in...
@timeout /t 10 /nobreak
echo.
echo.