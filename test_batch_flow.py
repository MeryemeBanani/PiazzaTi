#!/usr/bin/env python3
"""
Script di test per verificare il flusso completo:
Upload CV → Parsing → Salvataggio JSON → Batch Processing NLP

Uso: python test_batch_flow.py
"""

import sys
from pathlib import Path
import json
import time

# Aggiungi path del backend
BACKEND_PATH = Path(__file__).parent / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))

def test_json_storage():
    """Testa il sistema di salvataggio JSON."""
    print("🧪 Test JSON Storage System")
    print("="*50)
    
    try:
        from app.services.cv_batch_storage import get_batch_storage
        from app.schemas.parsed_document import ParsedDocument, DocumentType, Skill, SkillSource
        
        # Crea documento di test
        doc = ParsedDocument(
            document_type=DocumentType.cv,
            document_id="test_doc_001",
            user_id="test_user_123"
        )
        
        # Aggiungi alcune skills di test
        doc.skills = [
            Skill(name="Python", source=SkillSource.extracted, confidence=0.9),
            Skill(name="React", source=SkillSource.heuristic, confidence=0.7),
            Skill(name="Docker", source=SkillSource.extracted, confidence=0.8)
        ]
        
        # Salva nel batch storage
        batch_storage = get_batch_storage()
        json_path = batch_storage.save_parsed_cv(doc, "test_cv.pdf")
        
        print(f"✅ JSON salvato: {json_path}")
        
        # Verifica contenuto
        if json_path and Path(json_path).exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            print(f"📊 Contenuto JSON:")
            print(f"   Document ID: {saved_data.get('document_id')}")
            print(f"   User ID: {saved_data.get('user_id')}")
            print(f"   Skills: {len(saved_data.get('skills', []))}")
            print(f"   Batch Ready: {saved_data.get('batch_metadata', {}).get('ready_for_batch')}")
        
        # Ottieni statistiche
        stats = batch_storage.get_batch_stats()
        print(f"\n📈 Statistiche batch:")
        print(f"   File totali: {stats['total_files']}")
        print(f"   Pronti per processing: {stats['processing_ready']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_processor():
    """Testa il batch processor NLP."""
    print(f"\n🧪 Test Batch Processor NLP")
    print("="*50)
    
    try:
        # Controlla se ci sono JSON da processare
        from app.services.cv_batch_storage import get_batch_storage
        
        batch_storage = get_batch_storage()
        stats = batch_storage.get_batch_stats()
        
        if stats['total_files'] == 0:
            print("⚠️ Nessun JSON disponibile per il test. Esegui prima il test JSON storage.")
            return False
        
        print(f"📁 Trovati {stats['total_files']} CV da processare")
        
        # Esegui batch processing
        import subprocess
        script_path = Path(__file__).parent / "batch_processor.py"
        
        if not script_path.exists():
            print(f"❌ Batch processor non trovato: {script_path}")
            return False
        
        print(f"🚀 Esecuzione batch processor...")
        
        result = subprocess.run([
            sys.executable, str(script_path), "--process-today"
        ], capture_output=True, text=True, timeout=300)  # 5 minuti timeout
        
        if result.returncode == 0:
            print(f"✅ Batch processing completato!")
            print(f"Output:\n{result.stdout}")
            
            # Controlla output files
            nlp_path = Path(__file__).parent / "NLP"
            output_files = [
                nlp_path / "Dataset" / "cv_dataset.csv",
                nlp_path / "Dataset" / "normalized" / "cv_dataset_normalized.csv",
                nlp_path / "embeddings" / "cv_embeddings.csv"
            ]
            
            print(f"\n📂 File generati:")
            for output_file in output_files:
                if output_file.exists():
                    size_kb = output_file.stat().st_size // 1024
                    print(f"   ✅ {output_file.name}: {size_kb} KB")
                else:
                    print(f"   ❌ {output_file.name}: Non trovato")
            
            return True
        else:
            print(f"❌ Batch processing fallito!")
            print(f"Errore: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Errore test batch processor: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Esegui tutti i test."""
    print("🎯 Test Flusso Completo: CV Parsing → JSON Storage → NLP Batch Processing")
    print("="*80)
    
    # Test 1: JSON Storage
    json_ok = test_json_storage()
    
    if not json_ok:
        print("\n❌ Test JSON storage fallito. Interrompo i test.")
        return
    
    # Pausa tra test
    print(f"\n⏱️ Pausa 2 secondi...")
    time.sleep(2)
    
    # Test 2: Batch Processing
    batch_ok = test_batch_processor()
    
    # Risultato finale
    print(f"\n" + "="*80)
    print(f"📋 RISULTATO FINALE:")
    print(f"   JSON Storage: {'✅ OK' if json_ok else '❌ FALLITO'}")
    print(f"   Batch Processing: {'✅ OK' if batch_ok else '❌ FALLITO'}")
    
    if json_ok and batch_ok:
        print(f"\n🎉 SUCCESSO! Il flusso completo funziona correttamente!")
        print(f"   Ora puoi:")
        print(f"   1. Caricare CV tramite API /parse/upload")
        print(f"   2. I JSON vengono salvati automaticamente")
        print(f"   3. Eseguire batch processing con /parse/batch/process")
        print(f"   4. Ottenere embeddings per matching semantico")
    else:
        print(f"\n⚠️ Alcuni test sono falliti. Controlla i log sopra.")

if __name__ == "__main__":
    main()