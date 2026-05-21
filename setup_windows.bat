@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo  Adaptive AI Astronomy Tutor Setup
echo  Windows
echo ==============================================

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py -3
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set PYTHON_CMD=python
    ) else (
        echo Python was not found. Please install Python 3.10+ first.
        echo Download: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo Creating virtual environment if needed...
if not exist .venv (
    %PYTHON_CMD% -m venv .venv
)

echo Installing Python requirements...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if exist requirements.txt pip install -r requirements.txt

echo Checking Ollama...
where ollama >nul 2>nul
if %errorlevel%==0 (
    echo Ollama found. Pulling required local models...
    ollama pull llama3.1
    ollama pull mistral
) else (
    echo Ollama was not found.
    echo Install Ollama from: https://ollama.com/download
    echo After installing, run these commands:
    echo   ollama pull llama3.1
    echo   ollama pull mistral
)

echo.
echo Setup complete.
echo To run the GUI, double-click run_gui_windows.bat or run:
echo   run_gui_windows.bat
echo.
pause
