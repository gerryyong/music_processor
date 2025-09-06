@echo off
echo Music Audio Processor - Starting...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if pip is available (try both methods)
pip --version >nul 2>&1
if errorlevel 1 (
    python -m pip --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: pip is not available
        echo Please ensure pip is installed with Python
        pause
        exit /b 1
    ) else (
        echo Using python -m pip method
    )
)

echo Checking dependencies...

REM Install requirements if they don't exist
python -c "import librosa" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    python -m pip install -r requirements.txt --user
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed
)

echo.
echo Starting Audio Processor GUI...
echo.

REM Run the audio processor GUI
start "" python audio_processor_gui.py

REM Close this terminal window immediately
exit