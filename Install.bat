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

:: Upgrade PIP first
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip

"%~dp0venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo.
pause