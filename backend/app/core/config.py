from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./document_intelligence.db"
    upload_dir: Path = Path("/app/data/uploads")
    processed_dir: Path = Path("/app/data/processed")
    max_file_size_mb: int = 20
    ocr_language: str = "en"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
