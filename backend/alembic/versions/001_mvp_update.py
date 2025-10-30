"""MVP database updates

Revision ID: 001_mvp_update
Revises:
Create Date: 2025-10-02 14:35:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001_mvp_update"
down_revision = None  # Prima migrazione
branch_labels = None
depends_on = None


def upgrade():

    op.add_column("documents", sa.Column("title", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("description_raw", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.alter_column("documents", "language", type_=sa.String(length=2))
    op.create_check_constraint(
        "check_status_valid", "documents", "status IN ('uploaded', 'parsed', 'failed')"
    )

    op.execute("CREATE INDEX gin_parsed_json_idx ON documents USING GIN (parsed_json)")
    op.execute(
        """
        CREATE INDEX open_jd_idx ON documents (status)
        WHERE type = 'jd' AND status = 'parsed'
    """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX unique_latest_cv_per_user ON documents(user_id)
        WHERE type = 'cv' AND is_latest = true
    """
    )

    # D view per CV e JD:
    op.execute(
        """
        CREATE VIEW cv_documents AS
        SELECT * FROM documents WHERE type = 'cv'
    """
    )
    op.execute(
        """
        CREATE VIEW jd_documents AS
        SELECT * FROM documents WHERE type = 'jd'
    """
    )

    # EMBEDDINGS: FK + indice ANN (verifica se non esistono già):
    try:
        op.create_foreign_key(
            "fk_embeddings_document",
            "embeddings",
            "documents",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )
    except Exception:
        pass  # FK potrebbe già esistere

    # Indice ANN per embedding similarity search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS embedding_ann_idx ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """
    )

    # SEARCHES: indice cronologia
    op.execute("CREATE INDEX user_search_history_idx ON searches(user_id, created_at)")

    # SEARCH_RESULTS: nuovi campi + vincoli + indici
    op.add_column(
        "search_results",
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()")),
    )
    op.alter_column("search_results", "clicked", server_default=sa.text("false"))

    # FK constraints (verifica se non esistono già)
    try:
        op.create_foreign_key(
            "fk_search_results_document",
            "search_results",
            "documents",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )
    except Exception:
        pass

    try:
        op.create_foreign_key(
            "fk_search_results_search",
            "search_results",
            "searches",
            ["search_id"],
            ["id"],
            ondelete="CASCADE",
        )
    except Exception:
        pass

    op.execute("CREATE INDEX search_rank_idx ON search_results(search_id, rank)")


def downgrade():

    op.drop_index("search_rank_idx", table_name="search_results")
    op.drop_constraint("fk_search_results_search", "search_results", type_="foreignkey")
    op.drop_constraint(
        "fk_search_results_document", "search_results", type_="foreignkey"
    )
    op.drop_column("search_results", "created_at")
    op.alter_column("search_results", "clicked", server_default=None)

    op.drop_index("user_search_history_idx", table_name="searches")

    op.execute("DROP INDEX IF EXISTS embedding_ann_idx")
    op.drop_constraint("fk_embeddings_document", "embeddings", type_="foreignkey")

    op.execute("DROP VIEW IF EXISTS cv_documents")
    op.execute("DROP VIEW IF EXISTS jd_documents")

    op.drop_index("gin_parsed_json_idx", table_name="documents")
    op.drop_index("open_jd_idx", table_name="documents")
    op.drop_index("unique_latest_cv_per_user", table_name="documents")

    op.drop_constraint("check_status_valid", "documents", type_="check")
    op.alter_column("documents", "language", type_=sa.String())

    op.drop_column("documents", "title")
    op.drop_column("documents", "description_raw")
    op.drop_column("documents", "version")
    op.drop_column("documents", "is_latest")
