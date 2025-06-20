@echo off
echo ========================================
echo PhaseGrid Blocker Fix Setup
echo ========================================

echo.
echo Step 1: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Creating config files...
python setup_config.py
if errorlevel 1 (
    echo ERROR: Failed to create config files
    pause
    exit /b 1
)

echo.
echo Step 3: Running sheet repairs...
python scripts/repair_sheets.py
if errorlevel 1 (
    echo WARNING: Sheet repair failed - check credentials
    echo Continuing with paper trader...
)

echo.
echo Step 4: Running paper trader simulation...
python paper_trader.py
if errorlevel 1 (
    echo ERROR: Paper trader failed
    pause
    exit /b 1
)

echo.
echo Step 5: Running tests with coverage...
pytest tests/test_repair_sheets.py --cov=scripts --cov=. --cov-report=term
if errorlevel 1 (
    echo WARNING: Some tests failed
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
pause