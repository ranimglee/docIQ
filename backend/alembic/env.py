"""Alembic environment. Set DATABASE_URL before invoking `alembic upgrade head`."""
from app.db.session import Base
from app.models import document  # noqa
target_metadata = Base.metadata
