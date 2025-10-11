from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .document import Document
    from .search import Search
from typing import Optional
import datetime
import uuid

from sqlalchemy import Boolean, DateTime, String, Uuid, text, UniqueConstraint, PrimaryKeyConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    password_hash: Mapped[Optional[str]] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(
        Enum('candidate', 'recruiter', 'admin', name='user_role'),
        comment=(
            'Ruolo utente: candidate, recruiter, admin'
        )
    )
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime,
        server_default=text('now()')
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime,
        server_default=text('now()')
    )
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        server_default=text('true')
    )
    phone: Mapped[Optional[str]] = mapped_column(String)
    company: Mapped[Optional[str]] = mapped_column(String)
  
    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="user"
    )
    searches: Mapped[list["Search"]] = relationship(
        "Search", back_populates="user"
    )