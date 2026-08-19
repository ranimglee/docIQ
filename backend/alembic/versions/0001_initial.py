"""Initial document-intelligence schema."""
from alembic import op
import sqlalchemy as sa
revision = "0001_initial"
down_revision = None
def upgrade():
    doc_status = sa.Enum("UPLOADED", "PROCESSING", "COMPLETED", "FAILED", name="documentstatus")
    doc_type = sa.Enum("INVOICE", "RECEIPT", "CV", "CONTRACT", "DELIVERY_NOTE", "OTHER", "UNKNOWN", name="documenttype")
    op.create_table("documents", sa.Column("id", sa.Integer, primary_key=True), sa.Column("filename", sa.String(255), nullable=False), sa.Column("file_path", sa.String(1024), nullable=False, unique=True), sa.Column("mime_type", sa.String(100), nullable=False), sa.Column("file_size", sa.Integer, nullable=False), sa.Column("page_count", sa.Integer, nullable=False), sa.Column("document_type", doc_type, nullable=False), sa.Column("status", doc_status, nullable=False), sa.Column("error_message", sa.Text), sa.Column("processing_time", sa.Float), sa.Column("created_at", sa.DateTime, nullable=False), sa.Column("updated_at", sa.DateTime, nullable=False))
    op.create_index("ix_documents_status", "documents", ["status"]); op.create_index("ix_documents_created_at", "documents", ["created_at"])
    op.create_table("ocr_results", sa.Column("id", sa.Integer, primary_key=True), sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("page_number", sa.Integer, nullable=False), sa.Column("text", sa.Text, nullable=False), sa.Column("bounding_boxes", sa.JSON, nullable=False), sa.Column("confidence", sa.Float, nullable=False), sa.Column("created_at", sa.DateTime, nullable=False))
    op.create_index("ix_ocr_results_document_id", "ocr_results", ["document_id"])
    op.create_table("extracted_fields", sa.Column("id", sa.Integer, primary_key=True), sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("field_name", sa.String(100), nullable=False), sa.Column("field_value", sa.Text), sa.Column("confidence", sa.Float, nullable=False), sa.Column("created_at", sa.DateTime, nullable=False))
    op.create_index("ix_extracted_fields_document_id", "extracted_fields", ["document_id"]); op.create_index("ix_fields_document_name", "extracted_fields", ["document_id", "field_name"])

def downgrade():
    op.drop_table("extracted_fields"); op.drop_table("ocr_results"); op.drop_table("documents")
