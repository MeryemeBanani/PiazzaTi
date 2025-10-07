# Database Schemas - PiazzaTi

Questa cartella contiene tutti i file JSON relativi agli schemi del database PiazzaTi.

## File presenti:

### `db_schema_export.json` ⭐ **SCHEMA ATTUALE**
- **Data**: 2025-10-07 19:39:45
- **Fonte**: Database PostgreSQL Docker (db_piazzati)
- **Versione**: PostgreSQL 15.14 con pgvector 0.8.1
- **Stato**: Schema finale con tutte le ottimizzazioni applicate
- **Contenuto**: 
  - 6 tabelle complete (users, documents, embeddings, searches, search_results, alembic_version)
  - 26 vincoli di integrità
  - 15 indici per performance
  - 4 tipi ENUM definiti
  - Estensione pgvector per ricerca semantica

### File di Backup/Storici:

#### `db_PiazzaTi2.json`
- **Data**: 2025-10-03 18:59
- **Fonte**: Database locale aggiornato
- **Stato**: Versione evolutiva (intermedia)

#### `db_PiazzaTi.json` 
- **Data**: 2025-10-03 18:59
- **Fonte**: Database locale originale
- **Stato**: Versione storica (iniziale)

#### `db_PiazzaTi`
- **Data**: 2025-10-03 18:56
- **Tipo**: File di backup testuale
- **Stato**: Backup aggiuntivo

#### `diagramma1.pgerd`
- **Data**: 2025-10-03 18:59
- **Tipo**: Diagramma ER del database (pgAdmin/pgModeler)
- **Stato**: Rappresentazione visuale dello schema

## Struttura Schema Attuale (db_schema_export.json):

### Tabelle Principali:
1. **users** - Gestione utenti (candidate, recruiter, admin)
2. **documents** - CV e Job Descriptions con validazione lingua
3. **embeddings** - Vettori semantici normalizzati per ricerca
4. **searches** - Query di ricerca con filtri
5. **search_results** - Risultati ranking con feedback utente

### Caratteristiche Avanzate:
- **pgvector**: Ricerca semantica con indici IVFFlat
- **Check constraints**: Validazione formato lingua, vettori normalizzati
- **Foreign keys CASCADE**: Integrità referenziale completa
- **Indici strategici**: Performance ottimizzate per query frequenti
- **JSONB**: Memorizzazione efficiente dati strutturati

### Vincoli di Sicurezza:
- Formato lingua: `^[a-z]{2}$`
- Vettori normalizzati: `|1.0 - (embedding <#> embedding)| < 0.01`
- Email unique per utenti
- Un solo CV latest per utente

## Migrazione Alembic:
Schema allineato alla versione **586594a0af72** (004_schema_hardening_enums_indexes_constraints)