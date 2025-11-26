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
import logging

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

BACKEND_PATH = Path(__file__).parent.parent / "backend"
NLP_PATH = Path(__file__).parent / "NLP"

NLP_MODULE_PATH = str(Path(__file__).parent.parent.parent / "NLP")
if NLP_MODULE_PATH not in sys.path:
    sys.path.append(NLP_MODULE_PATH)

try:
    import NLP.cv_json_to_dataset_processor
    import NLP.normalizzatore
    import NLP.embed_generator
    logging.info("Moduli NLP importati con successo")
except ImportError as e:
    logging.error(f"Errore import moduli NLP: {e}")
    sys.exit(1)



# JD Batch Processor:
class JDBatchProcessor:
    def __init__(self):
        self.jds_path = NLP_PATH / "data" / "jds"
        self.dataset_path = NLP_PATH / "Dataset"
        self.output_path = NLP_PATH / "Dataset" / "normalized"
        self.csv_processor = NLP_PATH / "jd_json_to_dataset_processor.py"
        logging.info(f"JD Batch processor inizializzato")
        logging.info(f"   JDs path: {self.jds_path}")
        logging.info(f"   Dataset path: {self.dataset_path}")

    def process(self):
        logging.info("="*80)
        logging.info("BATCH PROCESSING JD - PIPELINE NLP COMPLETA")
        logging.info("="*80)

        # Step 1: JSON → CSV
        logging.info("Step 1: Conversione JSON → CSV JD")
        import subprocess
        if self.csv_processor.exists():
            result = subprocess.run([
                sys.executable, str(self.csv_processor)
            ], cwd=str(self.csv_processor.parent), capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("JD CSV creato.")
            else:
                logging.error(f"Errore JD CSV: {result.stderr}")
        else:
            logging.error(f"jd_json_to_dataset_processor.py non trovato: {self.csv_processor}")

        # Step 2: Normalizzazione JD
        logging.info("Step 2: Normalizzazione JD")
        try:
            ontology_path = NLP.normalizzatore.DATASET_DIR / "skill_ontology.json"
            input_jd = NLP.normalizzatore.DATASET_DIR / "jd_dataset.csv"
            output_jd = NLP.normalizzatore.OUTPUT_DIR / "jd_dataset_normalized.csv"
            ontology = NLP.normalizzatore.SkillOntology(ontology_path)
            NLP.normalizzatore.normalize_jd_dataset(input_jd, output_jd, ontology)
            logging.info(f"JD normalizzato: {output_jd}")
        except Exception as e:
            logging.error(f"JD normalization failed: {e}")

        # Step 3: Embeddings JD
        logging.info("Step 3: Generazione Embeddings JD")
        try:
            jd_df, jd_stats = NLP.embed_generator.process_jd_dataset()
            logging.info(f"Embeddings JD generati: {NLP.embed_generator.JD_OUTPUT}")
        except Exception as e:
            logging.error(f"JD embedding generation failed: {e}")

        logging.info("Pipeline JD completata!")
        # Avvia matching dopo embeddings JD
        logging.info("Step 4: Matching CV-JD")
        matching_script = NLP_PATH / "Matching.py"
        if matching_script.exists():
            result = subprocess.run([
                sys.executable, str(matching_script)
            ], cwd=str(matching_script.parent), capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("Matching completato.")
                logging.info(result.stdout)
            else:
                logging.error(f"Matching fallito: {result.stderr}")
        else:
            logging.error(f"Matching.py non trovato: {matching_script}")

# CV Batch Processor:
class CVBatchProcessor:
    def __init__(self):
        self.cvs_path = NLP_PATH / "data" / "cvs"
        self.dataset_path = NLP_PATH / "Dataset"
        self.output_path = NLP_PATH / "Dataset" / "normalized"
        self.dataset_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Batch processor inizializzato")
        logging.info(f"   CVs path: {self.cvs_path}")
        logging.info(f"   Dataset path: {self.dataset_path}")
    
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
            # Avvia matching dopo embeddings CV
            print(f"\n🔄 Step 4: Matching CV-JD")
            matching_script = NLP_PATH / "Matching.py"
            import subprocess, sys
            if matching_script.exists():
                result = subprocess.run([
                    sys.executable, str(matching_script)
                ], cwd=str(matching_script.parent), capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Matching completato.")
                    print(result.stdout)
                else:
                    print("❌ Matching fallito.")
                    print(result.stderr)
            else:
                print(f"❌ Matching.py non trovato: {matching_script}")
        except Exception as e:
            print(f"❌ Errore durante processing: {e}")
            import traceback
            traceback.print_exc()
    # --- CLI & MAIN ---
    def main():
        parser = argparse.ArgumentParser(description="Batch processor per CV/JD con pipeline NLP")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--process-cv-today", action="store_true", help="Processa CV di oggi")
        group.add_argument("--process-cv-date", type=str, metavar="YYYY-MM-DD", help="Processa CV di una data specifica")
        group.add_argument("--process-cv-range", nargs=2, metavar=("START", "END"), help="Processa CV in un range di date")
        group.add_argument("--process-cv-all", action="store_true", help="Processa tutti i CV disponibili")
        group.add_argument("--process-jd", action="store_true", help="Processa JD pipeline completa")

        args = parser.parse_args()

        if args.process_jd:
            jd_processor = JDBatchProcessor()
            jd_processor.process()
            return

        processor = CVBatchProcessor()

        if args.process_cv_today:
            processor.process_date_range()
        elif args.process_cv_date:
            processor.process_date_range(args.process_cv_date, args.process_cv_date)
        elif args.process_cv_range:
            processor.process_date_range(args.process_cv_range[0], args.process_cv_range[1])
        elif args.process_cv_all:
            all_dates = []
            for date_folder in processor.cvs_path.iterdir():
                if date_folder.is_dir() and len(date_folder.name) == 10:
                    all_dates.append(date_folder.name)
            if all_dates:
                all_dates.sort()
                processor.process_date_range(all_dates[0], all_dates[-1])
            else:
                logging.warning("Nessun CV trovato da processare")

    if __name__ == "__main__":
        main()
    
    def _normalization_pipeline(self):
        """Step 2: Normalizza il dataset usando normalizzatore.py."""
        
        # Controlla se esiste il CSV di input
        input_csv = self.dataset_path / NLP.cv_json_to_dataset_processor.OUTPUT_FILENAME
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
            NLP.normalizzatore.main()
            
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
            NLP.embed_generator.main()
            
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
        dataset_csv = self.dataset_path / NLP.cv_json_to_dataset_processor.OUTPUT_FILENAME
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

    # Trigger matching after embeddings are generated
    try:
        import subprocess, sys
        matching_script = Path(__file__).parent / "NLP" / "Matching.py"
        if matching_script.exists():
            print("\n🚀 Avvio matching semantico CV-JD...")
            result = subprocess.run([
                sys.executable, str(matching_script)
            ], cwd=str(matching_script.parent), capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Matching completato.")
                print(result.stdout)
            else:
                print("❌ Matching fallito.")
                print(result.stderr)
        else:
            print(f"❌ Matching.py non trovato: {matching_script}")
    except Exception as e:
        print(f"❌ Errore avvio matching: {e}")


if __name__ == "__main__":
    main()