@echo off
REM AI Employee - Quick Setup Script for Windows
REM Run this script to install all dependencies

echo ========================================
echo AI Employee - Silver Tier Setup
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.13+
    pause
    exit /b 1
)
echo.

REM Check Node.js
echo [2/5] Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js v24+
    pause
    exit /b 1
)
echo.

REM Install Python dependencies
echo [3/5] Installing Python dependencies...
cd scripts
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo.

REM Install Playwright browsers
echo [4/5] Installing Playwright browsers...
playwright install
if errorlevel 1 (
    echo WARNING: Playwright browser installation failed
    echo You can run 'playwright install' manually later
)
echo.

REM Install Node.js dependencies
echo [5/5] Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo WARNING: NPM install failed
    echo You can run 'npm install' manually later
)
echo.

cd ..

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open Obsidian and load AI_Employee_Vault/ folder
echo 2. Run: python scripts\filesystem_watcher.py AI_Employee_Vault --interval 5
echo 3. Run: python scripts\orchestrator.py AI_Employee_Vault
echo 4. Check Dashboard.md in Obsidian
echo.
echo For Gmail/WhatsApp/LinkedIn setup, see SETUP.md
echo.
pause
