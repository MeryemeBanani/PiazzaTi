"""003_remove_deprecated_failed_enum

Revision ID: 249a1c84fd5a
Revises: a43383a2f45c
Create Date: 2025-10-03 18:23:47.740820

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "249a1c84fd5a"
down_revision: Union[str, Sequence[str], None] = "a43383a2f45c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rimuove il valore enum 'failed' deprecato."""

    # IMPORTANTE: PostgreSQL non permette di rimuovere valori enum direttamente
    # Uso approccio con colonna temporanea per evitare problemi di conversione

    # 1. Rimuovo temporaneamente le view che dipendono dalla colonna status
    op.execute("DROP VIEW IF EXISTS cv_documents;")
    op.execute("DROP VIEW IF EXISTS jd_documents;")

    # 2. Creo nuovo enum con valori corretti (senza 'failed')
    op.execute(
        """
        CREATE TYPE document_status_new AS ENUM (
            'uploaded', 'parsed', 'parsing_failed', 'embedding_failed',
            'draft', 'open', 'closed'
        );
    """
    )

    # 3. Aggiungo colonna temporanea con nuovo enum
    op.execute("ALTER TABLE documents ADD COLUMN status_new document_status_new;")

    # 4. Copio i dati dalla vecchia colonna alla nuova (tutti valori sono compatibili)
    op.execute(
        """
        UPDATE documents 
        SET status_new = status::text::document_status_new;
    """
    )

    # 5. Rimuovo la vecchia colonna
    op.execute("ALTER TABLE documents DROP COLUMN status;")

    # 6. Rinomino la nuova colonna
    op.execute("ALTER TABLE documents RENAME COLUMN status_new TO status;")

    # 7. Rimuovo il vecchio enum
    op.execute("DROP TYPE document_status;")

    # 8. Rinomino il nuovo enum
    op.execute("ALTER TYPE document_status_new RENAME TO document_status;")

    # 9. Ricreo le view
    op.execute(
        """
        CREATE VIEW cv_documents AS
        SELECT * FROM documents 
        WHERE type = 'cv' AND is_latest = true;
    """
    )

    op.execute(
        """
        CREATE VIEW jd_documents AS
        SELECT * FROM documents WHERE type = 'jd';
    """
    )


def downgrade() -> None:
    """Ripristina il valore enum 'failed'."""

    # Rimuovo le view
    op.execute("DROP VIEW IF EXISTS cv_documents;")
    op.execute("DROP VIEW IF EXISTS jd_documents;")

    # Ricreo enum con 'failed' incluso per rollback
    op.execute(
        """
        CREATE TYPE document_status_new AS ENUM (
            'uploaded', 'parsed', 'failed', 'parsing_failed', 'embedding_failed',
            'draft', 'open', 'closed'
        );
    """
    )

    # Aggiungo colonna temporanea
    op.execute("ALTER TABLE documents ADD COLUMN status_new document_status_new;")

    # Copio dati
    op.execute(
        """
        UPDATE documents 
        SET status_new = status::text::document_status_new;
    """
    )

    # Sostituisco colonna
    op.execute("ALTER TABLE documents DROP COLUMN status;")
    op.execute("ALTER TABLE documents RENAME COLUMN status_new TO status;")

    op.execute("DROP TYPE document_status;")
    op.execute("ALTER TYPE document_status_new RENAME TO document_status;")

    # Ricreo le view
    op.execute(
        """
        CREATE VIEW cv_documents AS
        SELECT * FROM documents 
        WHERE type = 'cv' AND is_latest = true;
    """
    )

    op.execute(
        """
        CREATE VIEW jd_documents AS
        SELECT * FROM documents WHERE type = 'jd';
    """
    )
