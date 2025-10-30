"""004_schema_hardening_enums_indexes_constraints

Revision ID: 586594a0af72
Revises: 249a1c84fd5a
Create Date: 2025-10-07 18:22:59.453022

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "586594a0af72"
down_revision: Union[str, Sequence[str], None] = "249a1c84fd5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


"""004_schema_hardening_enums_indexes_constraints

SCHEMA HARDENING FINALE basato su db_PiazzaTi2.json:
Le modifiche principali sono già implementate, aggiungiamo:
1. Indice performance per JD + language  
2. Constraint per language format validation
3. Constraint per vector normalization
4. CASCADE constraint per search_results
5. Performance tuning

Revision ID: 586594a0af72
Revises: 249a1c84fd5a
Create Date: 2025-10-07 18:22:59.453022

"""


def upgrade() -> None:
    """
    Schema hardening finale - Completamento sicurezza e performance

    Basato su db_PiazzaTi2.json, aggiunge le modifiche mancanti:
    - Indice performance per JD + language
    - Validazione formato lingua
    - Constraint per vettori normalizzati
    - CASCADE constraint per search_results
    - Performance tuning
    """

    # Indice performance per JD filtrati per lingua
    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_jd_open_lang 
        ON documents(language, created_at) 
        WHERE type = 'jd' AND status = 'open'
    """
        )
    )

    # Validazione formato lingua (2 lettere minuscole)
    op.execute(
        text(
            """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'check_language_format' 
                AND table_name = 'documents'
            ) THEN
                ALTER TABLE documents 
                ADD CONSTRAINT check_language_format 
                CHECK (language ~ '^[a-z]{2}$');
            END IF;
        END $$
    """
        )
    )

    # Constraint per vettori normalizzati (cosine similarity)
    op.execute(
        text(
            """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'check_vector_normalized' 
                AND table_name = 'embeddings'
            ) THEN
                ALTER TABLE embeddings 
                ADD CONSTRAINT check_vector_normalized 
                CHECK (abs(1.0 - (embedding <#> embedding)) < 0.01);
            END IF;
        END $$
    """
        )
    )

    # Aggiornamento constraint CASCADE per search_results
    op.execute(
        text(
            """
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'search_results_search_id_fkey' 
                AND table_name = 'search_results'
            ) THEN
                ALTER TABLE search_results 
                DROP CONSTRAINT search_results_search_id_fkey;
            END IF;
        END $$
    """
        )
    )

    op.execute(
        text(
            """
        ALTER TABLE search_results 
        ADD CONSTRAINT search_results_search_id_fkey 
        FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE
    """
        )
    )

    # Indice per query_vector se non esiste
    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_searches_query_vector 
        ON searches USING ivfflat (query_vector vector_cosine_ops)
        WITH (lists = 100)
    """
        )
    )

    # Aggiornamento statistiche
    op.execute(text("ANALYZE documents"))
    op.execute(text("ANALYZE embeddings"))
    op.execute(text("ANALYZE searches"))
    op.execute(text("ANALYZE search_results"))


def downgrade() -> None:
    """Rollback delle modifiche"""

    # Rimuovi constraints aggiunti
    op.execute(
        text("ALTER TABLE documents DROP CONSTRAINT IF EXISTS check_language_format")
    )
    op.execute(
        text("ALTER TABLE embeddings DROP CONSTRAINT IF EXISTS check_vector_normalized")
    )

    # Rimuovi indice performance
    op.execute(text("DROP INDEX IF EXISTS idx_jd_open_lang"))

    # Ripristina constraint senza CASCADE
    op.execute(
        text(
            "ALTER TABLE search_results DROP CONSTRAINT IF EXISTS search_results_search_id_fkey"
        )
    )
    op.execute(
        text(
            """
        ALTER TABLE search_results 
        ADD CONSTRAINT search_results_search_id_fkey 
        FOREIGN KEY (search_id) REFERENCES searches(id)
    """
        )
    )
