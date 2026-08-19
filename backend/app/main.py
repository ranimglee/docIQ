import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from app.api.documents import router as documents_router
from app.core.config import settings
from app.db.session import Base, engine
from app.models import document  # noqa: F401
from app.schemas.document import HealthOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
settings.upload_dir.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)  # Alembic migration is provided for production deployment.


def apply_mvp_upgrade_columns() -> None:
    """Safely support an existing MVP database until deployments run Alembic 0002."""
    columns = {column["name"] for column in inspect(engine).get_columns("documents")}
    additions = {"extraction_data": "JSON", "review_status": "VARCHAR(30) NOT NULL DEFAULT 'NOT_REVIEWED'", "extraction_source": "VARCHAR(30) NOT NULL DEFAULT 'AI_EXTRACTED'"}
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE documents ADD COLUMN {name} {definition}"))


apply_mvp_upgrade_columns()
app = FastAPI(title="AI Document Intelligence", version="0.1.0", description="OCR-powered document analysis MVP")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["*"], allow_headers=["*"])
app.include_router(documents_router, prefix="/api")
app.mount("/files", StaticFiles(directory=str(settings.upload_dir)), name="files")

@app.get("/api/health", response_model=HealthOut, tags=["System"])
def health() -> HealthOut:
    try:
        with engine.connect() as connection: connection.execute(text("SELECT 1"))
        database = "connected"
    except Exception: database = "unavailable"
    return HealthOut(status="healthy" if database == "connected" else "degraded", database=database, version="0.1.0")
