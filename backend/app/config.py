from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://agrocare:agrocare@localhost:5432/agrocare"
    secret_key: str = "dev-only-change-me-use-a-32-byte-secret-in-prod"
    access_token_minutes: int = 60 * 12
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:5173"
    admin_email: str = "admin@agrocare.local"
    admin_password: str = "admin12345"
    confidence_threshold: float = 0.70  # RN04
    max_photos: int = 4  # RF18
    max_upload_mb: int = 8
    model_path: str | None = None
    labels_path: str | None = None


settings = Settings()
