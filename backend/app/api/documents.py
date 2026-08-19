from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.document import DocumentStatus
from app.schemas.document import DocumentListOut, DocumentOut, ExtractionUpdateIn, UploadOut
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=UploadOut, summary="Upload a supported document")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadOut:
    document = await DocumentService(db).upload(file)
    return UploadOut(id=document.id, status=document.status, message="Uploaded. Call process to analyze it.")

@router.post("/{document_id}/process", response_model=DocumentOut, summary="Run OCR, classification, and extraction")
def process_document(document_id: int, db: Session = Depends(get_db)) -> DocumentOut:
    service = DocumentService(db)
    return service.output(service.process(document_id))

@router.get("", response_model=DocumentListOut)
def list_documents(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), search: str | None = None, status: DocumentStatus | None = None, document_type: str | None = None, db: Session = Depends(get_db)) -> DocumentListOut:
    items, total = DocumentService(db).list(page, page_size, search, status, document_type)
    service = DocumentService(db)
    return DocumentListOut(items=[service.output(item) for item in items], total=total, page=page, page_size=page_size)

@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentOut:
    service = DocumentService(db)
    return service.output(service.get(document_id))

@router.put("/{document_id}/extraction", response_model=DocumentOut, summary="Save reviewed invoice extraction and re-run validation")
def update_extraction(document_id: int, payload: ExtractionUpdateIn, db: Session = Depends(get_db)) -> DocumentOut:
    service = DocumentService(db)
    return service.output(service.save_extraction(document_id, payload.extraction.model_dump(mode="json")))

@router.get("/{document_id}/file", summary="View original document")
def get_document_file(document_id: int, db: Session = Depends(get_db)) -> FileResponse:
    document = DocumentService(db).get(document_id)
    return FileResponse(document.file_path, media_type=document.mime_type, filename=document.filename)

@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)) -> None:
    DocumentService(db).delete(document_id)
