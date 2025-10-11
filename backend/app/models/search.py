from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
    from .document import Document
from typing import Optional, Any
import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Double, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Uuid, text, Enum

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import NullType
from .base import Base


class Search(Base):
    __tablename__ = 'searches'
    __table_args__ = (
        ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE',
            name='searches_user_id_fkey'
        ),
        PrimaryKeyConstraint('id', name='searches_pkey'),
        Index('idx_searches_query_vector', 'query_vector'),
        Index('user_search_history_idx', 'user_id', 'created_at')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    query_text: Mapped[Optional[str]] = mapped_column(String)
    query_vector: Mapped[Optional[Any]] = mapped_column(
        NullType,
        comment=(
            'Embedding semantico della query'
        )
    )
    type: Mapped[Optional[str]] = mapped_column(
        Enum('cv_search', 'jd_search', name='search_type')
    )
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime,
        server_default=text('now()'))

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="searches"
    )
    search_results: Mapped[list["SearchResult"]] = relationship(
        "SearchResult", back_populates="search"
    )


class SearchResult(Base):
    __tablename__ = 'search_results'
    __table_args__ = (
            ForeignKeyConstraint(
                ['document_id'], ['documents.id'], ondelete='CASCADE',
                name='search_results_document_id_fkey'
            ),
            ForeignKeyConstraint(
                ['search_id'], ['searches.id'], ondelete='CASCADE',
                name='search_results_search_id_fkey'
            ),
            PrimaryKeyConstraint('id', name='search_results_pkey'),
            Index('search_rank_idx', 'search_id', 'rank')
    )
  

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    search_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    score: Mapped[Optional[float]] = mapped_column(Double(53))
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    clicked: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    feedback: Mapped[Optional[str]] = mapped_column(
        String,
        comment=(
            "Valutazione esplicita dell'utente"
        )
    )
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    # Relationships
    document: Mapped[Optional["Document"]] = relationship(
        "Document", back_populates="search_results"
    )
    search: Mapped[Optional["Search"]] = relationship(
        "Search", back_populates="search_results"
    )