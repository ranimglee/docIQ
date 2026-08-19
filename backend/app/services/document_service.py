import logging
import time
from pathlib import Path
from uuid import uuid4
import cv2
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.core.config import settings
from app.ml.classifier import BaselineClassifier
from app.ml.extractor import RuleBasedExtractor
from app.models.document import Document, DocumentStatus, ExtractedField, OCRResult, ReviewStatus
from app.schemas.document import DocumentOut, InvoiceExtractionOut
from app.services.ocr_service import OCRService
from app.services.pdf_service import PDFService
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)
ALLOWED = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.ocr, self.pdf, self.classifier, self.extractor = OCRService(), PDFService(), BaselineClassifier(), RuleBasedExtractor()
        self.validator = ValidationService()

    async def upload(self, upload: UploadFile) -> Document:
        content_type = upload.content_type or ""
        if content_type not in ALLOWED:
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only PDF, PNG, JPG, and JPEG files are supported")
        data = await upload.read()
        if not data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "The uploaded file is empty")
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds configured size limit")
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid4().hex}{ALLOWED[content_type]}"
        path = settings.upload_dir / safe_name
        path.write_bytes(data)
        document = Document(filename=upload.filename or "document", file_path=str(path), mime_type=content_type, file_size=len(data))
        self.db.add(document); self.db.commit(); self.db.refresh(document)
        logger.info("document_uploaded id=%s size=%s", document.id, len(data))
        return document

    def get(self, document_id: int) -> Document:
        stmt = select(Document).options(selectinload(Document.ocr_results), selectinload(Document.extracted_fields)).where(Document.id == document_id)
        result = self.db.scalar(stmt)
        if not result: raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        return result

    def output(self, document: Document) -> DocumentOut:
        result = DocumentOut.model_validate(document)
        if document.extraction_data:
            result.extraction = InvoiceExtractionOut.model_validate(document.extraction_data)
            result.validation = self.validator.validate_invoice(document.extraction_data)
            result.review = {"status": document.review_status, "source": document.extraction_source}
        return result

    def list(self, page: int, page_size: int, search: str | None, doc_status: DocumentStatus | None, doc_type: str | None) -> tuple[list[Document], int]:
        stmt = select(Document)
        if search: stmt = stmt.where(Document.filename.ilike(f"%{search}%"))
        if doc_status: stmt = stmt.where(Document.status == doc_status)
        if doc_type: stmt = stmt.where(Document.document_type == doc_type)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = self.db.scalars(stmt.order_by(Document.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
        return list(items), total

    def process(self, document_id: int) -> Document:
        document = self.get(document_id)
        if document.status == DocumentStatus.PROCESSING: return document
        started = time.perf_counter(); document.status = DocumentStatus.PROCESSING; document.error_message = None; self.db.commit()
        try:
            path = Path(document.file_path)
            if document.mime_type == "application/pdf": images = self.pdf.pages(path)
            else:
                image = cv2.imread(str(path))
                if image is None: raise ValueError("Unreadable image")
                images = [image]
            document.page_count = len(images)
            self.db.query(OCRResult).filter_by(document_id=document.id).delete()
            self.db.query(ExtractedField).filter_by(document_id=document.id).delete()
            all_text = []
            for page, image in enumerate(images, 1):
                payload = self.ocr.recognize(image, page); all_text.append(payload["text"])
                self.db.add(OCRResult(document_id=document.id, page_number=page, text=payload["text"], confidence=payload["confidence"], bounding_boxes=payload["blocks"]))
            document.document_type = self.classifier.classify("\n".join(all_text))
            combined_text = "\n".join(all_text)
            for name, (value, confidence) in self.extractor.extract(document.document_type, combined_text).items():
                self.db.add(ExtractedField(document_id=document.id, field_name=name, field_value=value, confidence=confidence))
            document.extraction_data = self.extractor.extract_invoice_structured(combined_text) if document.document_type.name == "INVOICE" else None
            document.review_status = ReviewStatus.NOT_REVIEWED; document.extraction_source = "AI_EXTRACTED"
            document.status = DocumentStatus.COMPLETED; document.processing_time = round(time.perf_counter()-started, 3)
            self.db.commit(); logger.info("document_processed id=%s seconds=%s", document.id, document.processing_time)
        except Exception as exc:
            logger.exception("document_processing_failed id=%s", document.id)
            document.status = DocumentStatus.FAILED; document.error_message = "Processing failed. Please verify the document and retry."; document.processing_time = round(time.perf_counter()-started, 3); self.db.commit()
        return self.get(document.id)

    def save_extraction(self, document_id: int, extraction: dict) -> Document:
        document = self.get(document_id)
        if document.document_type.name != "INVOICE":
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Structured review is currently available for invoices only")
        document.extraction_data = extraction
        document.review_status = ReviewStatus.REVIEWED
        document.extraction_source = "USER_CORRECTED"
        self.db.commit()
        return self.get(document_id)

    def delete(self, document_id: int) -> None:
        document = self.get(document_id)
        path = Path(document.file_path)
        if path.is_file() and path.parent.resolve() == settings.upload_dir.resolve(): path.unlink()
        self.db.delete(document); self.db.commit()
