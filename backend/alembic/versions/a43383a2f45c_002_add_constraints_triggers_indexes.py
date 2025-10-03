"""002_add_constraints_triggers_indexes

Revision ID: a43383a2f45c
Revises: 10a4127237bb
Create Date: 2025-10-03 17:33:06.555704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a43383a2f45c'
down_revision: Union[str, Sequence[str], None] = '10a4127237bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Implementa le correzioni del reviewer per MVP schema."""
    
    # NOTA: I valori enum sono già stati aggiunti nella migrazione precedente
    
    # 1. AGGIORNAMENTO CONSTRAINT: Check per CV vs JD
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS check_status_valid;")
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS check_status_by_type;")
    op.execute("""
        ALTER TABLE documents ADD CONSTRAINT check_status_by_type CHECK (
            (type = 'cv' AND status IN ('uploaded', 'parsed', 'parsing_failed', 'embedding_failed'))
            OR 
            (type = 'jd' AND status IN ('draft', 'open', 'closed'))
        );
    """)
    
    # 2. CORREZIONE INDICE JD APERTI: da 'parsed' a 'open'
    op.execute("DROP INDEX IF EXISTS open_jd_idx;")
    op.execute("""
        CREATE INDEX idx_jd_open ON documents(created_at)
        WHERE type = 'jd' AND status = 'open';
    """)
    
    # 3. TRIGGER PER GESTIONE is_latest AUTOMATICA
    # Funzione trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION manage_cv_latest() 
        RETURNS TRIGGER AS $$
        BEGIN
            -- Se è un CV e lo stiamo marcando come latest
            IF NEW.type = 'cv' AND NEW.is_latest = true THEN
                -- Disattiva tutti gli altri CV latest dello stesso utente
                UPDATE documents 
                SET is_latest = false 
                WHERE user_id = NEW.user_id 
                  AND type = 'cv' 
                  AND id != NEW.id 
                  AND is_latest = true;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Trigger
    op.execute("""
        CREATE TRIGGER trigger_cv_latest_management
        BEFORE INSERT OR UPDATE ON documents
        FOR EACH ROW
        WHEN (NEW.type = 'cv' AND NEW.is_latest = true)
        EXECUTE FUNCTION manage_cv_latest();
    """)
    
    # 4. AGGIORNAMENTO VIEW cv_documents: solo is_latest = true
    op.execute("DROP VIEW IF EXISTS cv_documents;")
    op.execute("""
        CREATE VIEW cv_documents AS
        SELECT * FROM documents 
        WHERE type = 'cv' AND is_latest = true;
    """)


def downgrade() -> None:
    """Rollback delle modifiche."""
    
    # Rimuovi trigger e function
    op.execute("DROP TRIGGER IF EXISTS trigger_cv_latest_management ON documents;")
    op.execute("DROP FUNCTION IF EXISTS manage_cv_latest();")
    
    # Ripristina view originale
    op.execute("DROP VIEW IF EXISTS cv_documents;")
    op.execute("""
        CREATE VIEW cv_documents AS
        SELECT * FROM documents WHERE type = 'cv';
    """)
    
    # Ripristina indice vecchio
    op.execute("DROP INDEX IF EXISTS idx_jd_open;")
    op.execute("""
        CREATE INDEX open_jd_idx ON documents (status)
        WHERE type = 'jd' AND status = 'parsed';
    """)
    
    # Ripristina constraint originale
    op.drop_constraint('check_status_by_type', 'documents', type_='check')
    op.create_check_constraint('check_status_valid', 'documents', 
                              "status IN ('uploaded', 'parsed', 'failed')")
    
    # NOTA: Non rimuovo i valori enum perché PostgreSQL non lo supporta facilmente
