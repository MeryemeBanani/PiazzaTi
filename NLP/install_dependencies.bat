@echo off
REM ============================================================================
REM install_dependencies.bat - Setup dipendenze progetto matching
REM ============================================================================

echo Installing dependencies...
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Aggiorna pip
python -m pip install --upgrade pip --quiet

REM ============================================================================
REM DIPENDENZE
REM ============================================================================

echo Installing packages...

REM Base dependencies
python -m pip install pandas --quiet
python -m pip install numpy --quiet
python -m pip install python-dateutil --quiet

REM ML/NLP dependencies
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet
python -m pip install sentence-transformers --quiet

REM ============================================================================
REM VERIFICA
REM ============================================================================

echo.
echo Verifying installation...

python -c "import pandas; print('pandas:', pandas.__version__)" || goto error
python -c "import numpy; print('numpy:', numpy.__version__)" || goto error
python -c "import torch; print('torch:', torch.__version__)" || goto error
python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers: OK')" || goto error
python -c "from dateutil import parser; print('python-dateutil: OK')" || goto error

echo.
echo ============================================================================
echo Installation completed successfully
echo ============================================================================
pause
exit /b 0

:error
echo.
echo ERROR: Installation failed
pause
exit /b 1
