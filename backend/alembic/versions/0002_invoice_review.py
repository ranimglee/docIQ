"""Add structured extraction and review metadata without modifying existing records."""
from alembic import op
import sqlalchemy as sa

revision = "0002_invoice_review"
down_revision = "0001_initial"


def upgrade() -> None:
    op.add_column("documents", sa.Column("extraction_data", sa.JSON(), nullable=True))
    op.add_column("documents", sa.Column("review_status", sa.String(30), nullable=False, server_default="NOT_REVIEWED"))
    op.add_column("documents", sa.Column("extraction_source", sa.String(30), nullable=False, server_default="AI_EXTRACTED"))


def downgrade() -> None:
    op.drop_column("documents", "extraction_source")
    op.drop_column("documents", "review_status")
    op.drop_column("documents", "extraction_data")
