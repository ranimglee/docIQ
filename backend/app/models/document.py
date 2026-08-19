import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"; PROCESSING = "PROCESSING"; COMPLETED = "COMPLETED"; FAILED = "FAILED"


class DocumentType(str, enum.Enum):
    INVOICE = "INVOICE"; RECEIPT = "RECEIPT"; CV = "CV"; CONTRACT = "CONTRACT"; DELIVERY_NOTE = "DELIVERY_NOTE"; OTHER = "OTHER"; UNKNOWN = "UNKNOWN"


class ReviewStatus(str, enum.Enum):
    NOT_REVIEWED = "NOT_REVIEWED"; REVIEWED = "REVIEWED"


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.UNKNOWN)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_status: Mapped[ReviewStatus] = mapped_column(String(30), default=ReviewStatus.NOT_REVIEWED, nullable=False)
    extraction_source: Mapped[str] = mapped_column(String(30), default="AI_EXTRACTED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ocr_results = relationship("OCRResult", cascade="all, delete-orphan", back_populates="document")
    extracted_fields = relationship("ExtractedField", cascade="all, delete-orphan", back_populates="document")


class OCRResult(Base):
    __tablename__ = "ocr_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    bounding_boxes: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="ocr_results")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    field_name: Mapped[str] = mapped_column(String(100))
    field_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="extracted_fields")

Index("ix_fields_document_name", ExtractedField.document_id, ExtractedField.field_name)
