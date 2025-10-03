"""Add enum values only

Revision ID: 10a4127237bb
Revises: 7f6dea0bea2f
Create Date: 2025-10-03 17:27:26.933255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10a4127237bb'
down_revision: Union[str, Sequence[str], None] = '001_mvp_update'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aggiunge solo i nuovi valori all'enum document_status."""
    # PostgreSQL richiede commit separato per nuovi valori enum
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'parsing_failed';")
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'embedding_failed';")
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'draft';")
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'open';")
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'closed';")


def downgrade() -> None:
    """Non possiamo rimuovere valori enum in PostgreSQL facilmente."""
    pass
