@cls
@echo off 


REM Change directory to the same directory as the Script
cd "%~dp0"

REM Extract the drive letter from the current directory
set driveLetter=%~d0

REM Change to the extracted drive letter if it's not C:
if /i not "%driveLetter%"=="C:" (
    cd /d %driveLetter%
)


@REM AMEND THE BELOW - To YOUR Python.exe Folder - version 3.10 (recommended) or 3.11 (may work)
@REM ============================================================
set python_path="C:\Program Files\Python\3.10.0"
@REM ============================================================



set "python_path=%python_path%\python.exe"

@Echo Creating virtual environment using:
@echo %python_path%
@Echo.
%python_path% -m venv venv

@echo Virtual Environment Created
@Pause

