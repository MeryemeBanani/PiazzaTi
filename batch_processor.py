#!/usr/bin/env python3
"""
Script di Batch Processing per CV con modulo NLP completo.
Esegue la pipeline completa: JSON → CSV → Normalizzazione → Embeddings

Uso:
    python batch_processor.py --process-today
    python batch_processor.py --process-date 2025-11-12
    python batch_processor.py --process-all
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json

# Aggiungi paths
BACKEND_PATH = Path(__file__).parent.parent / "backend"
NLP_PATH = Path(__file__).parent / "NLP"

if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))
if str(NLP_PATH) not in sys.path:
    sys.path.append(str(NLP_PATH))

try:
    # Import moduli NLP
    from cv_json_to_dataset_processor import process_cv_folder, OUTPUT_FILENAME
    from normalizzatore import main as normalize_main, DATASET_DIR, OUTPUT_DIR
    from embed_generator import main as embeddings_main
    print("✅ Moduli NLP importati con successo")
except ImportError as e:
    print(f"❌ Errore import moduli NLP: {e}")
    sys.exit(1)


class CVBatchProcessor:
    """Processore batch per CV con pipeline NLP completa."""
    
    def __init__(self):
        self.cvs_path = NLP_PATH / "data" / "cvs"
        self.dataset_path = NLP_PATH / "Dataset"
        self.output_path = NLP_PATH / "Dataset" / "normalized"
        
        # Assicurati che le directory esistano
        self.dataset_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Batch processor inizializzato")
        print(f"   CVs path: {self.cvs_path}")
        print(f"   Dataset path: {self.dataset_path}")
    
    def process_date_range(self, start_date: str = None, end_date: str = None):
        """
        Processa CV in un range di date.
        
        Args:
            start_date: Data inizio (YYYY-MM-DD) o None per oggi
            end_date: Data fine (YYYY-MM-DD) o None per start_date
        """
        print(f"\n{'='*80}")
        print(f"BATCH PROCESSING CV - PIPELINE NLP COMPLETA")
        print(f"{'='*80}")
        
        # Determina date
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if end_date is None:
            end_date = start_date
            
        print(f"📅 Processing range: {start_date} → {end_date}")
        
        # 1. Trova cartelle con CV da processare
        date_folders = self._find_date_folders(start_date, end_date)
        if not date_folders:
            print(f"⚠️ Nessun CV trovato per il range {start_date} - {end_date}")
            return
        
        total_files = sum(len(list(folder.glob("*.json"))) for folder in date_folders)
        print(f"📊 Trovati {total_files} CV in {len(date_folders)} cartelle")
        
        if total_files == 0:
            print("⚠️ Nessun file JSON da processare")
            return
        
        # 2. Esegui pipeline completa
        try:
            # Step 1: JSON → CSV
            print(f"\n🔄 Step 1: Conversione JSON → CSV")
            self._json_to_csv_pipeline(date_folders)
            
            # Step 2: CSV → CSV Normalizzato
            print(f"\n🔄 Step 2: Normalizzazione Dataset")
            self._normalization_pipeline()
            
            # Step 3: CSV Normalizzato → Embeddings
            print(f"\n🔄 Step 3: Generazione Embeddings")
            self._embeddings_pipeline()
            
            print(f"\n✅ Pipeline completata con successo!")
            self._print_summary()
            
        except Exception as e:
            print(f"\n❌ Errore durante processing: {e}")
            import traceback
            traceback.print_exc()
    
    def _find_date_folders(self, start_date: str, end_date: str) -> list:
        """Trova cartelle per le date specificate."""
        date_folders = []
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        current_dt = start_dt
        while current_dt <= end_dt:
            date_str = current_dt.strftime("%Y-%m-%d")
            date_folder = self.cvs_path / date_str
            
            if date_folder.exists() and date_folder.is_dir():
                json_files = list(date_folder.glob("*.json"))
                if json_files:
                    date_folders.append(date_folder)
                    print(f"   📂 {date_str}: {len(json_files)} CV")
            
            current_dt += timedelta(days=1)
        
        return date_folders
    
    def _json_to_csv_pipeline(self, date_folders: list):
        """Step 1: Converte JSON in CSV usando cv_json_to_dataset_processor."""
        
        # Crea un symlink temporaneo o copia i file nella struttura attesa dal processor
        temp_cvs_folder = NLP_PATH / "data" / "temp_processing"
        temp_cvs_folder.mkdir(exist_ok=True)
        
        # Pulisci cartella temporanea
        for old_file in temp_cvs_folder.glob("*.json"):
            old_file.unlink()
        
        # Copia tutti i JSON nella cartella temporanea
        file_count = 0
        for date_folder in date_folders:
            for json_file in date_folder.glob("*.json"):
                # Crea nome unico per evitare collisioni
                new_name = f"{date_folder.name}_{json_file.name}"
                temp_file = temp_cvs_folder / new_name
                
                # Copia contenuto
                import shutil
                shutil.copy2(json_file, temp_file)
                file_count += 1
        
        print(f"   📋 Copiati {file_count} JSON in cartella temporanea")
        
        # Imposta input folder per il processor
        import cv_json_to_dataset_processor as processor
        original_input = processor.INPUT_FOLDER
        processor.INPUT_FOLDER = str(temp_cvs_folder)
        
        try:
            # Esegui conversione
            print(f"   🔄 Conversione JSON → CSV...")
            process_cv_folder()
            print(f"   ✅ CSV creato: {self.dataset_path / OUTPUT_FILENAME}")
            
        finally:
            # Ripristina path originale
            processor.INPUT_FOLDER = original_input
            
            # Pulisci cartella temporanea
            shutil.rmtree(temp_cvs_folder)
    
    def _normalization_pipeline(self):
        """Step 2: Normalizza il dataset usando normalizzatore.py."""
        
        # Controlla se esiste il CSV di input
        input_csv = self.dataset_path / OUTPUT_FILENAME
        if not input_csv.exists():
            raise FileNotFoundError(f"CV dataset non trovato: {input_csv}")
        
        print(f"   📊 Input CSV: {input_csv} ({input_csv.stat().st_size // 1024} KB)")
        
        # Cambia working directory per il normalizzatore
        import os
        original_cwd = os.getcwd()
        os.chdir(NLP_PATH)
        
        try:
            # Esegui normalizzazione
            print(f"   🔄 Normalizzazione in corso...")
            normalize_main()
            
            # Controlla output
            output_csv = self.output_path / "cv_dataset_normalized.csv"
            if output_csv.exists():
                print(f"   ✅ CSV normalizzato: {output_csv} ({output_csv.stat().st_size // 1024} KB)")
            else:
                raise FileNotFoundError(f"Output normalizzazione non trovato: {output_csv}")
                
        finally:
            os.chdir(original_cwd)
    
    def _embeddings_pipeline(self):
        """Step 3: Genera embeddings usando embed_generator.py."""
        
        # Controlla se esiste il CSV normalizzato
        normalized_csv = self.output_path / "cv_dataset_normalized.csv"
        if not normalized_csv.exists():
            raise FileNotFoundError(f"CSV normalizzato non trovato: {normalized_csv}")
        
        print(f"   📊 Input normalizzato: {normalized_csv}")
        
        # Cambia working directory per l'embed generator
        import os
        original_cwd = os.getcwd()
        os.chdir(NLP_PATH)
        
        try:
            # Esegui generazione embeddings
            print(f"   🔄 Generazione embeddings...")
            embeddings_main()
            
            # Controlla output
            embeddings_dir = NLP_PATH / "embeddings"
            cv_embeddings = embeddings_dir / "cv_embeddings.csv"
            
            if cv_embeddings.exists():
                print(f"   ✅ Embeddings generati: {cv_embeddings} ({cv_embeddings.stat().st_size // 1024} KB)")
            else:
                print(f"   ⚠️ File embeddings non trovato: {cv_embeddings}")
                
        finally:
            os.chdir(original_cwd)
    
    def _print_summary(self):
        """Stampa riassunto del processing."""
        print(f"\n📈 RIASSUNTO PROCESSING")
        print(f"{'='*50}")
        
        # Dataset files
        dataset_csv = self.dataset_path / OUTPUT_FILENAME
        normalized_csv = self.output_path / "cv_dataset_normalized.csv"
        embeddings_csv = NLP_PATH / "embeddings" / "cv_embeddings.csv"
        
        files_info = [
            ("Dataset grezzo", dataset_csv),
            ("Dataset normalizzato", normalized_csv),
            ("Embeddings CV", embeddings_csv),
        ]
        
        for name, filepath in files_info:
            if filepath.exists():
                size_kb = filepath.stat().st_size // 1024
                # Conta righe se è CSV
                try:
                    import pandas as pd
                    df = pd.read_csv(filepath)
                    rows = len(df)
                    print(f"   {name:20}: {rows:4} righe, {size_kb:4} KB")
                except:
                    print(f"   {name:20}: {size_kb:4} KB")
            else:
                print(f"   {name:20}: ❌ Non trovato")
        
        print(f"\n🎯 Pipeline pronta per:")
        print(f"   • Matching semantico CV-JD")
        print(f"   • Analytics avanzati su skills")
        print(f"   • Insights su trend tecnologici")


def main():
    parser = argparse.ArgumentParser(description="Batch processor per CV con pipeline NLP")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--process-today", action="store_true", 
                      help="Processa CV di oggi")
    group.add_argument("--process-date", type=str, metavar="YYYY-MM-DD",
                      help="Processa CV di una data specifica")
    group.add_argument("--process-range", nargs=2, metavar=("START", "END"),
                      help="Processa CV in un range di date")
    group.add_argument("--process-all", action="store_true",
                      help="Processa tutti i CV disponibili")
    
    args = parser.parse_args()
    
    processor = CVBatchProcessor()
    
    if args.process_today:
        processor.process_date_range()
    elif args.process_date:
        processor.process_date_range(args.process_date, args.process_date)
    elif args.process_range:
        processor.process_date_range(args.process_range[0], args.process_range[1])
    elif args.process_all:
        # Trova tutte le date disponibili
        all_dates = []
        for date_folder in processor.cvs_path.iterdir():
            if date_folder.is_dir() and len(date_folder.name) == 10:  # YYYY-MM-DD
                all_dates.append(date_folder.name)
        
        if all_dates:
            all_dates.sort()
            processor.process_date_range(all_dates[0], all_dates[-1])
        else:
            print("⚠️ Nessun CV trovato da processare")


if __name__ == "__main__":
    main()