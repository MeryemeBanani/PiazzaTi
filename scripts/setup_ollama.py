#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Ollama llama3.1:8b con monitoring periodico (aggiornamenti ogni 20s)
"""

import subprocess
import time
import requests
import re
import sys
from datetime import datetime
from typing import Optional, Tuple

# ============================================================================
# CONFIGURAZIONE
# ============================================================================

MODEL_NAME = "llama3.1:8b"
OLLAMA_HOST = "http://localhost:11434"
MAX_DOWNLOAD_TIME = 1800  # 30 minuti timeout
SERVER_STARTUP_TIMEOUT = 30  # 30 secondi per avvio server
PROGRESS_UPDATE_INTERVAL = 20  # Aggiornamento ogni 20 secondi

# ============================================================================
# CLASSE PROGRESS BAR CON AGGIORNAMENTI PERIODICI
# ============================================================================


class PeriodicProgressTracker:
    """Tracker progresso con aggiornamenti periodici"""

    def __init__(self, update_interval: int = 20, total_mb: float = 4700):
        self.update_interval = update_interval
        self.total_mb = total_mb
        self.last_update_time = time.time()
        self.start_time = time.time()
        self.current_progress = 0
        self.last_progress = 0
        self.status_message = "Inizializzazione..."

    def should_update(self) -> bool:
        """Verifica se è ora di mostrare aggiornamento"""
        return (time.time() - self.last_update_time) >= self.update_interval

    def update(self, progress_percent: int, status: str = ""):
        """Aggiorna progresso (mostra solo se intervallo raggiunto)"""
        self.current_progress = progress_percent
        if status:
            self.status_message = status

        if self.should_update() or progress_percent == 100:
            self._display_progress()
            self.last_update_time = time.time()
            self.last_progress = progress_percent

    def _display_progress(self):
        """Mostra barra di progresso"""
        elapsed = time.time() - self.start_time
        downloaded_mb = (self.current_progress / 100) * self.total_mb

        # Calcola velocità media
        if elapsed > 0:
            speed_mbps = downloaded_mb / elapsed
            eta_seconds = (self.total_mb - downloaded_mb) / speed_mbps if speed_mbps > 0 else 0
        else:
            speed_mbps = 0
            eta_seconds = 0

        # Barra visuale
        bar_width = 40
        filled = int(bar_width * self.current_progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # Timestamp
        timestamp = f"[{int(elapsed//60):02d}:{int(elapsed%60):02d}]"

        # Output formattato
        print(f"\n{timestamp} 📊 AGGIORNAMENTO DOWNLOAD")
        print(f"  └─ Progresso: |{bar}| {self.current_progress}%")
        print(f"  └─ Scaricati: {downloaded_mb:.1f} / {self.total_mb:.1f} MB")
        print(f"  └─ Velocità: {speed_mbps:.1f} MB/s")
        if eta_seconds > 0 and self.current_progress < 100:
            print(f"  └─ Tempo rimasto stimato: {int(eta_seconds//60)} min {int(eta_seconds%60)} sec")
        print(f"  └─ Status: {self.status_message}")

    def force_update(self, message: str = ""):
        """Forza visualizzazione immediata"""
        if message:
            self.status_message = message
        self._display_progress()

# ============================================================================
# FUNZIONI DI VERIFICA (VERSIONI COMPATTE)
# ============================================================================


def check_system_resources():
    """Verifica risorse sistema"""
    print("\n" + "="*70)
    print("🔍 VERIFICA RISORSE SISTEMA")
    print("="*70)

    try:
        # RAM
        result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')[:2]
        print("\n💾 Memoria:")
        for line in lines:
            if line.strip():
                print(f"  {line}")

        # Disco
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')[:2]
        print("\n💿 Disco:")
        for line in lines:
            if line.strip():
                print(f"  {line}")

        print("\n✅ Risorse verificate (necessari ~5GB liberi)")
        return True

    except Exception as e:
        print(f"⚠️  Impossibile verificare risorse: {e}")
        return True


def verify_ollama_installation() -> bool:
    """Verifica Ollama installato"""
    print("\n" + "="*70)
    print("🔍 VERIFICA OLLAMA")
    print("="*70)

    try:
        result = subprocess.run(["which", "ollama"], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print(f"✅ Ollama trovato: {result.stdout.strip()}")

            version = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            print(f"📌 {version.stdout.strip()}")
            return True
        else:
            print("❌ Ollama NON installato")
            return False

    except Exception as e:
        print(f"❌ Errore: {e}")
        return False


def start_ollama_server() -> Tuple[bool, Optional[subprocess.Popen]]:
    """Avvia server Ollama"""
    print("\n" + "="*70)
    print("🚀 AVVIO SERVER OLLAMA")
    print("="*70)

    try:
        # Verifica se già attivo
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            if response.status_code == 200:
                print("✅ Server già attivo!")
                return True, None
        except:
            pass

        # Avvia server
        print("🔄 Avvio server...", end="", flush=True)
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Attendi connessione
        for i in range(SERVER_STARTUP_TIMEOUT):
            try:
                response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=1)
                if response.status_code == 200:
                    print(f" OK ({i+1}s)")
                    print(f"✅ Server pronto su {OLLAMA_HOST}")
                    return True, process
            except:
                pass

            if i % 3 == 0:
                print(".", end="", flush=True)
            time.sleep(1)

        print(" TIMEOUT")
        print("❌ Server non risponde dopo 30s")
        process.kill()
        return False, None

    except Exception as e:
        print(f"❌ Errore: {e}")
        return False, None


def check_model_exists(model_name: str) -> bool:
    """Verifica se modello già presente"""
    print("\n" + "="*70)
    print(f"🔍 VERIFICA MODELLO {model_name}")
    print("="*70)

    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                if model.get("name") == model_name:
                    size_gb = model.get("size", 0) / (1024**3)
                    print(f"✅ Modello GIÀ PRESENTE (dimensione: {size_gb:.2f} GB)")
                    print("   └─ Skip download")
                    return True

            print(f"📥 Modello NON trovato - download necessario")
            return False
    except Exception as e:
        print(f"⚠️  Errore verifica: {e}")
        return False


def download_model_with_periodic_updates(model_name: str) -> bool:
    """Download con aggiornamenti ogni 20 secondi"""
    print("\n" + "="*70)
    print(f"📥 DOWNLOAD {model_name} (~4.7GB)")
    print("="*70)
    print(f"⏰ Inizio: {datetime.now().strftime('%H:%M:%S')}")
    print(f"⚠️  Tempo stimato: 10-20 minuti su Colab")
    print(f"📊 Aggiornamenti ogni {PROGRESS_UPDATE_INTERVAL} secondi")
    print("="*70)

    start_time = time.time()

    try:
        # Avvia download
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Pattern regex
        progress_pattern = re.compile(r'(\d+)%')

        # Tracker progresso
        tracker = PeriodicProgressTracker(
            update_interval=PROGRESS_UPDATE_INTERVAL,
            total_mb=4700
        )

        print("\n🔄 Download in corso... (attendi primo aggiornamento)\n")

        current_status = "Inizializzazione"
        last_line = ""

        # Leggi output
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            last_line = line

            # Estrai percentuale
            progress_match = progress_pattern.search(line)
            if progress_match:
                progress = int(progress_match.group(1))

                # Determina status
                if 'pulling manifest' in line.lower():
                    current_status = "Scaricamento manifest"
                elif 'pulling' in line.lower():
                    current_status = "Download layers"
                elif 'verifying' in line.lower():
                    current_status = "Verifica integrità"
                elif 'writing' in line.lower():
                    current_status = "Scrittura su disco"

                # Aggiorna (mostra solo se 20s passati)
                tracker.update(progress, current_status)

        # Attendi completamento
        return_code = process.wait(timeout=MAX_DOWNLOAD_TIME)

        # Aggiornamento finale
        if return_code == 0:
            tracker.current_progress = 100
            tracker.status_message = "Completato con successo"
            tracker.force_update()

            elapsed = time.time() - start_time
            print(f"\n{'='*70}")
            print(f"✅ DOWNLOAD COMPLETATO!")
            print(f"⏱️  Tempo totale: {int(elapsed//60)} min {int(elapsed%60)} sec")
            print(f"{'='*70}")
            return True
        else:
            print(f"\n❌ Download fallito (exit code: {return_code})")
            print(f"   Ultima linea: {last_line}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n❌ TIMEOUT dopo {MAX_DOWNLOAD_TIME//60} minuti")
        process.kill()
        return False

    except KeyboardInterrupt:
        print(f"\n⚠️  Download interrotto dall'utente")
        process.kill()
        return False

    except Exception as e:
        print(f"\n❌ Errore: {e}")
        return False


def verify_model_ready(model_name: str) -> bool:
    """Test modello funzionante"""
    print("\n" + "="*70)
    print("🧪 TEST MODELLO")
    print("="*70)

    try:
        print("🔄 Eseguo test rapido...", end="", flush=True)

        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model_name,
                "prompt": "Say 'OK' if you work correctly.",
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get("response", "").strip()
            print(" OK")
            print(f"✅ Modello funzionante!")
            print(f"   Risposta: '{text[:50]{"..." if len(text) > 50 else ""}}'")
            return True
        else:
            print(f" ERRORE ({response.status_code})")
            return False

    except Exception as e:
        print(f" ERRORE")
        print(f"❌ Test fallito: {e}")
        return False

# ============================================================================
# FUNZIONE PRINCIPALE
# ============================================================================


def setup_ollama_complete():
    """Setup completo con monitoring periodico"""

    print("\n" + "="*70)
    print("🎯 SETUP OLLAMA + LLAMA3.1:8B")
    print("="*70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    overall_start = time.time()

    # Step 1: Risorse
    if not check_system_resources():
        print("\n⚠️  Attenzione: risorse limitate")

    # Step 2: Installazione
    if not verify_ollama_installation():
        print("\n❌ ERRORE CRITICO: Ollama non installato")
        print("💡 Soluzione: curl -fsSL https://ollama.com/install.sh | sh")
        return False

    # Step 3: Server
    server_ok, ollama_process = start_ollama_server()
    if not server_ok:
        print("\n❌ ERRORE CRITICO: Server non avviabile")
        return False

    # Step 4: Verifica modello esistente
    if check_model_exists(MODEL_NAME):
        print("\n🎉 Modello già disponibile - procedendo al test...")
    else:
        # Step 5: Download
        print(f"\n⚡ Inizio download {MODEL_NAME}...")
        if not download_model_with_periodic_updates(MODEL_NAME):
            print("\n❌ ERRORE: Download fallito")
            return False

    # Step 6: Test
    if not verify_model_ready(MODEL_NAME):
        print("\n⚠️  Modello presente ma test fallito")
        return False

    # Riepilogo
    total_time = time.time() - overall_start
    print("\n" + "="*70)
    print("🎉 SETUP COMPLETATO!")
    print("="*70)
    print(f"⏱️  Tempo totale: {int(total_time//60)} min {int(total_time%60)} sec")
    print(f"✅ Modello: {MODEL_NAME}")
    print(f"🌐 Server: {OLLAMA_HOST}")
    print(f"📝 Pronto per parsing CV/JD")
    print("="*70 + "\n")

    return True

# ============================================================================
# ESECUZIONE
# ============================================================================


if __name__ == "__main__":
    print("🚀 Avvio setup Ollama...")
    print("⏱️  Gli aggiornamenti appariranno ogni 20 secondi durante il download\n")

    success = setup_ollama_complete()

    if success:
        print("✅ Setup completato - puoi procedere con il codice NLP")
        print("💡 Usa: llm = Ollama(model='llama3.1:8b')")
    else:
        print("❌ Setup fallito - leggi gli errori sopra per diagnostica")
