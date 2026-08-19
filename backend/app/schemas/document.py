from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentStatus, DocumentType, ReviewStatus


class OCRBlockOut(BaseModel):
    text: str
    confidence: float
    bbox: list[float]


class OCRResultOut(BaseModel):
    page_number: int
    text: str
    confidence: float
    bounding_boxes: list[OCRBlockOut]

    model_config = ConfigDict(from_attributes=True)


class FieldOut(BaseModel):
    field_name: str
    field_value: str | None
    confidence: float
    model_config = ConfigDict(from_attributes=True)


class ValueWithConfidence(BaseModel):
    value: str | float | None = None
    confidence: float = 0.0


class PartyOut(BaseModel):
    name: ValueWithConfidence = ValueWithConfidence()
    address: ValueWithConfidence = ValueWithConfidence()
    email: ValueWithConfidence = ValueWithConfidence()
    phone: ValueWithConfidence = ValueWithConfidence()
    tax_id: ValueWithConfidence = ValueWithConfidence()


class LineItemOut(BaseModel):
    description: ValueWithConfidence = ValueWithConfidence()
    quantity: ValueWithConfidence = ValueWithConfidence()
    unit: ValueWithConfidence = ValueWithConfidence()
    unit_price: ValueWithConfidence = ValueWithConfidence()
    vat_rate: ValueWithConfidence = ValueWithConfidence()
    amount: ValueWithConfidence = ValueWithConfidence()


class InvoiceExtractionOut(BaseModel):
    invoice_number: ValueWithConfidence = ValueWithConfidence()
    issue_date: ValueWithConfidence = ValueWithConfidence()
    due_date: ValueWithConfidence = ValueWithConfidence()
    currency: ValueWithConfidence = ValueWithConfidence()
    supplier: PartyOut = PartyOut()
    customer: PartyOut = PartyOut()
    items: list[LineItemOut] = []
    financials: dict[str, ValueWithConfidence] = {}
    payment_information: dict[str, ValueWithConfidence] = {}
    notes: list[ValueWithConfidence] = []


class ValidationCheckOut(BaseModel):
    name: str; status: str; expected: float | None = None; actual: float | None = None; difference: float | None = None; message: str


class ValidationOut(BaseModel):
    is_valid: bool
    checks: list[ValidationCheckOut]


class ReviewOut(BaseModel):
    status: ReviewStatus
    source: str


class DocumentOut(BaseModel):
    id: int; filename: str; mime_type: str; file_size: int; page_count: int
    document_type: DocumentType; status: DocumentStatus; processing_time: float | None
    error_message: str | None; created_at: datetime; updated_at: datetime
    ocr_results: list[OCRResultOut] = []
    extracted_fields: list[FieldOut] = []
    extraction: InvoiceExtractionOut | None = None
    validation: ValidationOut | None = None
    review: ReviewOut | None = None
    model_config = ConfigDict(from_attributes=True)


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    total: int
    page: int
    page_size: int


class UploadOut(BaseModel):
    id: int
    status: DocumentStatus
    message: str


class HealthOut(BaseModel):
    status: str
    database: str
    version: str


class ExtractionUpdateIn(BaseModel):
    extraction: InvoiceExtractionOut
