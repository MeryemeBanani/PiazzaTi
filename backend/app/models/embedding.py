from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .document import Document
from typing import Optional, Any
import datetime
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint
from sqlalchemy import (
    Index, Integer, PrimaryKeyConstraint, Text, Uuid, text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import NullType
from .base import Base


class Embedding(Base):
    __tablename__ = 'embeddings'
    __table_args__ = (
        CheckConstraint(
            'abs(1.0::double precision - (embedding <#> embedding)) '
            '< 0.01::double precision',
            name='check_vector_normalized'
        ),
        ForeignKeyConstraint(
            ['document_id'], ['documents.id'], ondelete='CASCADE',
            name='embeddings_document_id_fkey'
        ),
        PrimaryKeyConstraint('id', name='embeddings_pkey'),
        UniqueConstraint('document_id', name='embeddings_document_id_key'),
        Index('embedding_ann_idx', 'embedding')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    embedding: Mapped[Optional[Any]] = mapped_column(
        NullType,
        comment=(
            'Embedding SBERT MiniLM-L12-v2'
        )
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        Text,
        server_default=text(
            "'sentence-transformers/MiniLM-L12-v2'::text"
        )
    )
    model_dim: Mapped[Optional[int]] = mapped_column(
        Integer,
        server_default=text('384')
    )
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        server_default=text('true')
    )
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime,
        server_default=text('now()')
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime,
        server_default=text('now()')
    )
  
    # Relationships
    document: Mapped[Optional["Document"]] = relationship(
        "Document", back_populates="embedding"
    )
