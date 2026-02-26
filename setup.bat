@echo off
setlocal enabledelayedexpansion

echo [*] Starting setup process for InstaSend...

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [^!] uv was not found on your system.
    set /p "install_uv=[?] Would you like to install uv now? (y/n): "
    
    set "is_yes="
    if /I "!install_uv!"=="y" set "is_yes=1"
    if /I "!install_uv!"=="yes" set "is_yes=1"
    
    if defined is_yes (
        echo [*] Installing uv via official script...
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        
        set "PATH=%PATH%;%USERPROFILE%\.cargo\bin"
        
        where uv >nul 2>nul
        if !errorlevel! neq 0 (
            echo [X] Error: uv installation failed or not found in PATH.
            pause
            exit /b 1
        )
    ) else (
        echo [X] Setup aborted. uv is required to proceed.
        pause
        exit /b 1
    )
) else (
    echo [*] uv is already installed.
)

if exist ".venv" (
    echo [*] Existing .venv detected. Removing old environment...
    rmdir /s /q ".venv"
)

echo [*] Creating a new virtual environment...
uv venv --clear

if exist "requirements.txt" (
    echo [*] Installing dependencies from requirements.txt...
    uv pip install -r requirements.txt
) else (
    echo [^!] Warning: requirements.txt not found.
)

echo.
echo [*] Setup completed successfully^!
pause