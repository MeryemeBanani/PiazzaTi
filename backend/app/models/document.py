from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    ForeignKey, CheckConstraint, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import datetime

from app.models.base import Base
from app.models.enums import document_status_enum, document_type_enum

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    type = Column(document_type_enum)
    raw_file_url = Column(String)
    parsed_json = Column(JSONB)
    language = Column(String(2))  # Normalizzato a 2 caratteri
    status = Column(document_status_enum)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Campi aggiuntivi per MVP
    title = Column(String)
    description_raw = Column(Text)
    version = Column(Integer)
    is_latest = Column(Boolean, default=False)

    # Relazioni
    user = relationship("User", back_populates="documents")
    embedding = relationship("Embedding", uselist=False, back_populates="document")
    search_results = relationship("SearchResult", back_populates="document")

    # Vincoli
    __table_args__ = (
        CheckConstraint("status IN ('uploaded', 'parsed', 'failed')", name="check_status_valid"),
    )
