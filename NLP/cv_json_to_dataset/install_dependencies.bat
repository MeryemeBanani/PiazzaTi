@echo off
REM ============================================================================
REM install_dependencies.bat
REM Script per installare le dipendenze necessarie su Windows
REM ============================================================================

echo.
echo ============================================================================
echo INSTALLAZIONE DIPENDENZE - CV Processor
echo ============================================================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato
    echo Scarica Python da: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python installato
python --version
echo.

REM Verifica pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] pip non trovato. Installazione in corso...
    python -m ensurepip --default-pip
)

echo [OK] pip disponibile
echo.

REM Aggiorna pip
echo [INFO] Aggiornamento pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip aggiornato
echo.

REM Installa pandas
echo [INFO] Installazione pandas...
python -m pip install pandas --quiet
if errorlevel 1 (
    echo [ERRORE] Impossibile installare pandas
    pause
    exit /b 1
)
echo [OK] pandas installato
echo.

REM Verifica installazione
echo [INFO] Verifica installazione...
python -c "import pandas as pd; print('[OK] pandas versione:', pd.__version__)"
if errorlevel 1 (
    echo [ERRORE] Verifica fallita
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo [SUCCESS] Installazione completata con successo
echo ============================================================================
echo.
echo Esegui ora: python json_to_csv_processor.py
echo.
pause