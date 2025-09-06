@echo off
echo Music Audio Processor - Installing Dependencies...
echo.
echo This will install the required Python packages for audio processing.
echo.
pause

echo Installing packages...
echo.

REM Try different methods to install packages
echo Trying python -m pip install method 1...
python -m pip install librosa==0.10.1 numpy==1.24.3 scipy==1.11.1 soundfile==0.12.1 tkinterdnd2==0.3.0 resampy==0.4.2 --user

if errorlevel 1 (
    echo.
    echo Method 1 failed, trying without version constraints...
    python -m pip install --user librosa numpy scipy soundfile tkinterdnd2 resampy
    
    if errorlevel 1 (
        echo.
        echo Method 2 failed, trying with pip directly...
        pip install --user librosa numpy scipy soundfile tkinterdnd2 resampy
        
        if errorlevel 1 (
            echo.
            echo ERROR: All installation methods failed.
            echo.
            echo Please try manually:
            echo 1. Open Command Prompt as Administrator
            echo 2. Run: python -m pip install librosa numpy scipy soundfile tkinterdnd2 resampy --user
            echo.
            pause
            exit /b 1
        )
    )
)

echo.
echo Installation completed successfully!
echo You can now run the audio processor.
echo.
pause