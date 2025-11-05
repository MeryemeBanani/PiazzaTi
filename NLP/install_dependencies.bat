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

REM Installa python-dateutil (per normalizzatore)
echo [INFO] Installazione python-dateutil...
python -m pip install python-dateutil --quiet
if errorlevel 1 (
    echo [ERRORE] Impossibile installare python-dateutil
    pause
    exit /b 1
)
echo [OK] python-dateutil installato
echo.

REM Verifica installazione completa
echo [INFO] Verifica dipendenze...
python -c "import pandas as pd; print('[OK] pandas versione:', pd.__version__)"
if errorlevel 1 (
    echo [ERRORE] Verifica pandas fallita
    pause
    exit /b 1
)

python -c "from dateutil import parser; print('[OK] python-dateutil disponibile')"
if errorlevel 1 (
    echo [ERRORE] Verifica python-dateutil fallita
    pause
    exit /b 1
)

python -c "import json; print('[OK] json disponibile')"
python -c "from pathlib import Path; print('[OK] pathlib disponibile')"
python -c "from typing import List, Dict, Set, Tuple; print('[OK] typing disponibile')"
python -c "from datetime import datetime; print('[OK] datetime disponibile')"
python -c "import re; print('[OK] re disponibile')"
python -c "from collections import defaultdict; print('[OK] collections disponibile')"
echo.

echo ============================================================================
echo [SUCCESS] Installazione completata con successo
echo ============================================================================
echo.
echo Dipendenze verificate:
echo   - pandas (per CSV processing)
echo   - python-dateutil (per parsing date nel normalizzatore)
echo   - json (built-in Python)
echo   - pathlib (built-in Python)
echo   - typing (built-in Python)
echo   - datetime (built-in Python)
echo   - re (built-in Python)
echo   - collections (built-in Python)
echo.
echo Script disponibili:
echo   - python json_to_csv_processor.py
echo   - python normalize_dataset.py
echo   - python add_user_id_and_tags_ordered.py
echo.
pause
